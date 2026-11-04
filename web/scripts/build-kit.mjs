// Assemble the reusable UI pack (tokens, components, charts, helpers) into dist-kit/pv-ui-kit/.
//   node scripts/build-kit.mjs
// The dashboard-specific parts (src/features, the API client) are not included.
import { cpSync, mkdirSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";

const out = "dist-kit/pv-ui-kit";
rmSync("dist-kit", { recursive: true, force: true });
mkdirSync(`${out}/lib`, { recursive: true });
mkdirSync(`${out}/charts`, { recursive: true });

cpSync("src/components/ui", `${out}/ui`, { recursive: true });
for (const f of ["TimeChart.tsx", "Heatmap.tsx"]) cpSync(`src/components/charts/${f}`, `${out}/charts/${f}`);
for (const f of ["utils.ts", "motion.ts", "chart.ts", "format.ts", "time.ts"]) cpSync(`src/lib/${f}`, `${out}/lib/${f}`);
// the dashboard freezes the clock in snapshot builds; the pack uses the real time
writeFileSync(`${out}/lib/clock.ts`, "/** The current time in milliseconds. Replace to freeze time (screenshots, snapshots). */\nexport const nowMs = () => Date.now();\n");

// tokens: everything from the app stylesheet except the map styles
let css = readFileSync("src/index.css", "utf8");
css = css.slice(0, css.indexOf("/* Leaflet map, themed */")).trimEnd() + "\n";
writeFileSync(`${out}/tokens.css`, css);

// in the pack ui/, charts/ and lib/ sit side by side, one level shallower than in the app
for (const dir of ["ui", "charts"]) {
  for (const f of readdirSync(`${out}/${dir}`)) {
    const p = `${out}/${dir}/${f}`;
    writeFileSync(p, readFileSync(p, "utf8").replaceAll('"../../lib/', '"../lib/'));
  }
}
cpSync("kit/README.md", `${out}/README.md`);
cpSync("kit/NOTICE.md", `${out}/NOTICE.md`);
console.log(`${out} ready`);
