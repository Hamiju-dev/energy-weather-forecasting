// Build a single-file snapshot of the dashboard with one real forecast embedded.
//
//   ewf serve                          (in another terminal)
//   node scripts/build-snapshot.mjs [--server http://127.0.0.1:8000] [--hours 120]
//   node scripts/build-snapshot.mjs --reuse     (rebuild the page from the last stored forecast)
//
// Writes dist-snapshot/ewf-snapshot.html: page content without <html>/<head>/<body> wrappers
// (the form a claude.ai artifact expects; browsers also open it). Nothing is simulated: the
// forecast comes from the running server, which downloads the latest model runs.
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const arg = (name, fallback) => {
  const i = process.argv.indexOf(`--${name}`);
  return i > 0 ? process.argv[i + 1] : fallback;
};
const server = arg("server", "http://127.0.0.1:8000");
const hours = Number(arg("hours", "120"));
const get = async (path, init) => {
  const r = await fetch(server + path, init);
  if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`);
  return r.json();
};

let snapshot;
if (process.argv.includes("--reuse")) {
  snapshot = JSON.parse(readFileSync(".snapshot/snapshot.json", "utf8"));
} else {
  const plant = await get("/api/example-plant");
  const { job } = await get("/api/forecast", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ plants: [plant], hours }) });
  let state;
  for (;;) {
    state = await get(`/api/jobs/${job}`);
    if (state.status !== "running") break;
    await new Promise((r) => setTimeout(r, 1000));
  }
  if (state.status !== "done") throw new Error(state.error ?? "forecast failed");
  const history = await get("/api/history", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ plant }) });
  snapshot = { result: state.result, history, plant, created_utc: state.result.created_utc };
}

// kept outside dist-snapshot/, which vite empties on every build
mkdirSync(".snapshot", { recursive: true });
if (!process.argv.includes("--reuse")) writeFileSync(".snapshot/snapshot.json", JSON.stringify(snapshot));
execFileSync("npx", ["vite", "build", "--mode", "snapshot"], { stdio: "inherit", env: { ...process.env, EWF_SNAPSHOT: ".snapshot/snapshot.json" } });

const assets = readdirSync("dist-snapshot/assets");
const css = assets.filter((f) => f.endsWith(".css")).map((f) => readFileSync(join("dist-snapshot/assets", f), "utf8")).join("\n");
const js = assets.filter((f) => f.endsWith(".js")).map((f) => readFileSync(join("dist-snapshot/assets", f), "utf8")).join("\n");
const safe = (s) => s.replace(/<\/script/gi, "<\\/script").replace(/<\/style/gi, "<\\/style");
const page = `<title>ewf PV dashboard</title>
<meta name="description" content="Snapshot of a PV power forecast from ECMWF IFS, ECMWF AIFS and NOAA GFS open data">
<script>
  (function () {
    var root = document.documentElement;
    function apply() {
      var t = root.getAttribute("data-theme"), stored = null;
      try { stored = localStorage.getItem("ewf-theme"); } catch (e) {}
      var dark = t ? t === "dark" : stored ? stored === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
      root.classList.toggle("dark", dark);
    }
    apply();
    new MutationObserver(apply).observe(root, { attributes: true, attributeFilter: ["data-theme"] });
  })();
</script>
<style>${safe(css)}</style>
<div id="root"></div>
<script type="module">${safe(js)}</script>
`;
writeFileSync("dist-snapshot/ewf-snapshot.html", page);
console.log(`dist-snapshot/ewf-snapshot.html  ${(page.length / 1024).toFixed(0)} KB, forecast created ${snapshot.created_utc}`);
