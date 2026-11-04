import { AnimatePresence, motion } from "framer-motion";
import { Command as CommandIcon, Download, Eye, Moon, Pencil, Play, RefreshCw, Settings2, Sun, SunMedium } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { Button } from "./components/ui/button";
import { Alert } from "./components/ui/alert";
import { Badge } from "./components/ui/badge";
import { Card } from "./components/ui/card";
import { LineLoader } from "./components/ui/loader";
import { Select } from "./components/ui/select";
import { Skeleton, SkeletonReveal } from "./components/ui/skeleton";
import { Accordion } from "./components/ui/accordion";
import { CommandPalette, type Command } from "./components/ui/command-palette";
import { Heatmap } from "./components/charts/Heatmap";
import { api, LABELS, SHORT, type SeriesKey } from "./lib/api";
import { relative, dateTime } from "./lib/time";
import { SNAPSHOT } from "./lib/snapshot";
import logo from "./assets/logo.svg";
import { useApp } from "./features/store";
import { usePlantView } from "./features/view";
import { PlantSheet } from "./features/PlantSheet";
import { Kpis } from "./features/Kpis";
import { PowerCard } from "./features/PowerCard";
import { DailyCard } from "./features/DailyCard";
import { WindowsCard } from "./features/WindowsCard";
import { RunChangeCard } from "./features/RunChangeCard";
import { WeatherCard } from "./features/WeatherCard";
import { ActualsCard } from "./features/ActualsCard";
import { RunsCard } from "./features/RunsCard";
import { StatusFeed } from "./features/StatusFeed";
import { PlantMap } from "./features/PlantMap";

function useTheme() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    try { localStorage.setItem("ewf-theme", dark ? "dark" : "light"); } catch { /* private mode */ }
  }, [dark]);
  return [dark, setDark] as const;
}

const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });

export default function App() {
  const app = useApp();
  const [dark, setDark] = useTheme();
  const [sheet, setSheet] = useState(false);
  const [palette, setPalette] = useState(false);
  const [visible, setVisibleState] = useState<Record<SeriesKey | "band", boolean>>({ ifs: true, aifs: true, gfs: true, blend: true, band: true });
  const setVisible = useCallback((k: SeriesKey | "band", on: boolean) => setVisibleState((s) => ({ ...s, [k]: on })), []);
  const plant = app.plants[app.selected] ?? app.plants[0];
  const v = usePlantView(app.result, plant?.name);
  const running = app.status === "running";

  const commands: Command[] = useMemo(() => {
    const c: Command[] = [
      { id: "run", group: "Forecast", label: "Run forecast", hint: plant?.name, icon: <Play />, run: () => app.run() },
      { id: "edit", group: "Forecast", label: "Edit plant and settings", icon: <Pencil />, run: () => setSheet(true) },
      { id: "prev", group: "Forecast", label: "Load previous model runs", icon: <RefreshCw />, run: () => app.runPrevious() },
      { id: "theme", group: "View", label: dark ? "Light mode" : "Dark mode", icon: dark ? <Sun /> : <Moon />, run: () => setDark(!dark) },
      ...(["ifs", "aifs", "gfs", "blend"] as SeriesKey[]).map((k) => ({ id: `t-${k}`, group: "View", label: `${visible[k] ? "Hide" : "Show"} ${LABELS[k]}`, icon: <Eye />, run: () => setVisible(k, !visible[k]) })),
      ...[["power", "Power chart"], ["daily", "Energy per day"], ["heatmap", "Heat map"], ["windows", "Maintenance windows"], ["runs", "Run-to-run changes"], ["weather", "Weather"], ["actuals", "Forecast vs actuals"], ["downloads", "Model runs and downloads"], ["about", "How it works"]]
        .map(([id, label]) => ({ id: `go-${id}`, group: "Go to", label, icon: <SunMedium />, run: () => scrollTo(id) })),
      ...app.plants.map((p, i) => ({ id: `plant-${i}`, group: "Plants", label: p.name, hint: `${(p.capacity_dc_kwp / 1000).toFixed(1)} MWp`, icon: <Settings2 />, run: () => app.setSelected(i) })),
    ];
    if (app.jobId && plant) c.splice(3, 0, { id: "zip", group: "Forecast", label: "Download everything (zip)", icon: <Download />, run: () => { window.location.href = api.downloadUrl(app.jobId!, plant.name, "zip"); } });
    return c;
  }, [app, plant, dark, setDark, visible, setVisible]);

  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-40 border-b border-line bg-[color-mix(in_srgb,var(--bg)_82%,transparent)] backdrop-blur-md">
        <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-3 px-4 sm:px-6">
          <div className="flex items-center gap-2.5">
            <img src={logo} alt="" className="size-7" />
            <div className="hidden leading-tight sm:block">
              <p className="text-[13px] font-semibold text-ink">ewf</p>
              <p className="text-[11px] text-muted">PV power forecast</p>
            </div>
          </div>
          <div className="mx-1 hidden h-6 w-px bg-[var(--border)] sm:block" />
          <div className="min-w-0 max-w-[260px] flex-1">
            {app.plants.length > 1 ? (
              <Select value={String(app.selected)} onChange={(i) => app.setSelected(Number(i))}
                options={app.plants.map((p, i) => ({ value: String(i), label: p.name, description: `${(p.capacity_dc_kwp / 1000).toFixed(1)} MWp` }))} />
            ) : (
              <button type="button" onClick={() => setSheet(true)} className="focus-ring max-w-full truncate rounded-lg px-2 py-1 text-left text-[13px] font-medium text-ink hover:bg-surface-hover">
                {plant?.name} <span className="font-normal text-muted">· {((plant?.capacity_dc_kwp ?? 0) / 1000).toFixed(1)} MWp</span>
              </button>
            )}
          </div>
          <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
            <Button variant="ghost" size="sm" onClick={() => setPalette(true)} className="hidden md:inline-flex" aria-label="Open command palette">
              <CommandIcon className="size-3.5" /> <span>Commands</span><kbd className="ml-1 rounded border border-line px-1 font-mono text-[10px] text-muted">Ctrl K</kbd>
            </Button>
            <Button variant="secondary" size="icon" onClick={() => setSheet(true)} aria-label="Edit plant" title="Edit plant"><Pencil className="size-4" /></Button>
            <Button variant="secondary" size="icon" onClick={() => setDark(!dark)} aria-label={dark ? "Light mode" : "Dark mode"} title={dark ? "Light mode" : "Dark mode"}>
              {dark ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
            {SNAPSHOT ? (
              <Badge tone="accent" dot title="New forecasts need the local server">Snapshot</Badge>
            ) : (
              <Button variant="primary" onClick={() => app.run()} loading={running}>
                {!running && <Play className="size-3.5" />}<span className="hidden sm:inline">{running ? "Running" : app.result ? "Update" : "Run forecast"}</span>
              </Button>
            )}
          </div>
        </div>
        {running && <LineLoader className="absolute right-0 bottom-0 left-0 h-0.5 rounded-none" label="Forecast running" />}
      </header>

      <main className="mx-auto max-w-[1400px] space-y-4 px-4 py-5 sm:px-6">
        {SNAPSHOT && (
          <p className="flex flex-wrap items-center gap-x-2 rounded-xl border border-line bg-surface px-4 py-2.5 text-[12.5px] text-ink-2">
            <Badge tone="accent">Snapshot</Badge>
            <span>Forecast from {dateTime(SNAPSHOT.created_utc, SNAPSHOT.plant.timezone)}. New runs, uploads and downloads need the local server.</span>
          </p>
        )}
        <AnimatePresence>
          {app.status === "error" && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Alert tone="critical" title="The forecast failed" action={<Button size="sm" onClick={() => app.run()}>Try again</Button>}>{app.error}</Alert>
            </motion.div>
          )}
        </AnimatePresence>

        {!app.result && !running && <Welcome app={app} onEdit={() => setSheet(true)} />}

        {running && (
          <div className="rounded-2xl border border-line bg-surface p-4 shadow-card">
            <p className="text-[13px] font-medium text-ink">Fetching model runs</p>
            <ol className="mt-2 space-y-1 font-mono text-[11.5px] text-muted" aria-live="polite">
              {app.messages.slice(-5).map((m, i, arr) => (
                <motion.li key={app.messages.length - arr.length + i} initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }} className={i === arr.length - 1 ? "text-ink-2" : ""}>{m}</motion.li>
              ))}
            </ol>

          </div>
        )}

        {(app.result || running) && (
          <SkeletonReveal loading={running && !app.result} skeleton={<DashboardSkeleton />}>
            {v && app.result && (
              <div className={running ? "pointer-events-none opacity-60 transition-opacity" : "transition-opacity"}>
                <p className="tabular mb-3 text-[12px] text-muted">
                  {app.result.runs.map((r) => `${SHORT[r.model]} ${r.run_utc.slice(11, 13)}Z`).join(" · ")}
                  {" · "}updated {relative(app.result.created_utc)}
                  {app.result.problems.length > 0 && <span className="text-critical"> · {app.result.problems.length} model missing</span>}
                </p>
                <Kpis v={v} history={app.history} />
                <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-12 [&>*]:min-w-0">
                  <div id="power" className="lg:col-span-8"><PowerCard v={v} visible={visible} setVisible={setVisible} /></div>
                  <div id="daily" className="lg:col-span-4"><DailyCard key={v.r.key} v={v} /></div>
                  <div id="weather" className="lg:col-span-8"><WeatherCard v={v} /></div>
                  <div className="lg:col-span-4"><StatusFeed v={v} result={app.result} history={app.history} /></div>
                  <div id="heatmap" className="lg:col-span-8">
                    <Card title="Daily profile" meta={`${v.scale.power} · local time`} info="Each row is a day, each cell 15 minutes of blend power. Dashed cells are outside the forecast window.">
                      <Heatmap t={v.r.series.t} values={v.r.series.power.blend ?? []} tz={v.tz} capacity={v.r.ac_limit_kw ?? v.r.plant.capacity_dc_kwp} unit={v.scale.power} div={v.scale.div} />
                    </Card>
                  </div>
                  <div id="windows" className="lg:col-span-4"><WindowsCard v={v} /></div>
                  <div id="runs" className="lg:col-span-6"><RunChangeCard v={v} app={app} /></div>
                  <div id="actuals" className="lg:col-span-6"><ActualsCard v={v} app={app} /></div>
                  <div id="downloads" className="lg:col-span-12"><RunsCard v={v} result={app.result} jobId={app.jobId} /></div>
                </div>
              </div>
            )}
          </SkeletonReveal>
        )}

        <div id="about"><About /></div>
        <footer className="pt-2 pb-8 text-[11.5px] text-muted">
          Contains modified ECMWF open data (IFS, AIFS), © ECMWF, CC-BY-4.0 · NOAA GFS, public domain · Map © OpenStreetMap contributors
        </footer>
      </main>

      <PlantSheet app={app} open={sheet} onClose={() => setSheet(false)} />
      <CommandPalette commands={commands} open={palette} setOpen={setPalette} />
    </div>
  );
}

function Welcome({ app, onEdit }: { app: ReturnType<typeof useApp>; onEdit: () => void }) {
  const p = app.plants[app.selected];
  return (
    <div className="grid gap-4 lg:grid-cols-5">
      <div className="flex flex-col justify-between rounded-2xl border border-line bg-surface p-6 shadow-card lg:col-span-3">
        <div>
          <h1 className="text-[28px] leading-tight font-semibold tracking-[-0.03em] text-ink sm:text-[32px]">PV power forecast</h1>
          <p className="mt-2 max-w-md text-[14px] leading-relaxed text-ink-2">15-minute AC power for the next days from ECMWF IFS, ECMWF AIFS and NOAA GFS.</p>
        </div>
        <div className="mt-6 flex flex-wrap gap-2">
          <Button variant="primary" size="lg" onClick={() => app.run()}><Play className="size-4" />Run forecast</Button>
          <Button variant="secondary" size="lg" onClick={onEdit}><Pencil className="size-4" />Edit plant</Button>
        </div>
      </div>
      <div className="rounded-2xl border border-line bg-surface p-4 shadow-card lg:col-span-2">
        <PlantMap plants={app.plants} selected={app.selected} onSelect={app.setSelected} height={200} />
        <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[12.5px]">
          <dt className="text-muted">DC capacity</dt><dd className="tabular text-right text-ink">{p.capacity_dc_kwp.toLocaleString("en-GB")} kWp</dd>
          <dt className="text-muted">AC limit</dt><dd className="tabular text-right text-ink">{p.capacity_ac_kw ? `${p.capacity_ac_kw.toLocaleString("en-GB")} kW` : "none"}</dd>
          <dt className="text-muted">Mounting</dt><dd className="text-right text-ink">{p.tracking === "fixed" ? `fixed ${p.tilt_deg}°, azimuth ${p.azimuth_deg}°` : "single-axis tracker"}</dd>
          <dt className="text-muted">Horizon</dt><dd className="text-right text-ink">{app.settings.hours} h, {app.settings.models.map((m) => LABELS[m]).join(", ")}</dd>
        </dl>
      </div>
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-[118px] rounded-2xl" />)}</div>
      <div className="grid gap-4 xl:grid-cols-3">
        <Skeleton className="h-[420px] rounded-2xl xl:col-span-2" />
        <Skeleton className="h-[420px] rounded-2xl" />
      </div>
    </div>
  );
}

function About() {
  return (
    <Card title="Method">
      <Accordion items={[
        { id: "runs", title: "1. Latest model runs", content: "For each model the newest run that reaches the horizon is found on the public archives (Google Cloud mirrors first, then AWS and the providers' servers). The run age is shown at the top." },
        { id: "fields", title: "2. Only what is needed is downloaded", content: "For each time step the GRIB2 index is read and five fields (solar radiation, 2 m temperature, 10 m wind, cloud cover) are fetched with HTTP byte ranges, then interpolated bilinearly to the plant. Results are cached on the server." },
        { id: "rad", title: "3. Radiation conventions", content: "ECMWF accumulations and GFS window averages are converted to mean irradiance per model interval (paper 01, Lemma 1)." },
        { id: "15", title: "4. To 15 minutes", content: "Irradiance is interpolated through the clear-sky index, so the daily shape comes from solar geometry and the energy of every model interval is kept exactly." },
        { id: "pv", title: "5. PV physics", content: "Erbs decomposition, Perez transposition (fixed tilt or single-axis tracking with backtracking), ASHRAE incidence-angle losses, Faiman cell temperature, PVWatts DC power, system losses, inverter with clipping at the AC capacity, optional export limit." },
        { id: "blend", title: "6. Blend and range", content: "The blend is the equal-weight mean of the models. The band shows how far the models disagree; it is not a calibrated probability interval." },
        { id: "not", title: "Not modelled yet", content: "Snow on modules, soiling events, outages, curtailment (redispatch, negative prices), shading and bifacial gain. The model has not been calibrated against measured output: use Forecast vs actuals to check it, and a year of 15-minute plant data for a statistical correction (paper 01, Sections 6 and 10)." },
      ]} />
    </Card>
  );
}
