import { useState } from "react";
import { Card } from "../components/ui/card";
import { FileDrop } from "../components/ui/file-drop";
import { Alert } from "../components/ui/alert";
import { Segmented } from "../components/ui/segmented";
import { TimeChart } from "../components/charts/TimeChart";
import { api, COLOUR_VAR, LABELS, type Actuals, type SeriesKey } from "../lib/api";
import { fmt, signed } from "../lib/format";
import { dateTime } from "../lib/time";
import type { App } from "./store";
import type { PlantView } from "./view";

/* Forecast vs actuals: drop measured plant output and see each model's error.
   Measured values are a grey filled area (a different mark), the chosen forecast a line in its colour. */
export function ActualsCard({ v, app }: { v: PlantView; app: App }) {
  const [res, setRes] = useState<Actuals | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [tz, setTz] = useState<"UTC" | "local">("UTC");
  const [key, setKey] = useState<SeriesKey>("blend");
  const { scale } = v;
  const keys: SeriesKey[] = [...v.models, "blend"];

  const upload = async (f: File) => {
    if (!app.jobId) return;
    setBusy(true); setErr(null);
    try { setRes(await api.actuals(app.jobId, v.r.plant.name, f, tz === "UTC" ? "UTC" : v.tz)); }
    catch (e) { setErr(e instanceof Error ? e.message : String(e)); setRes(null); }
    finally { setBusy(false); }
  };
  const d = (a?: (number | null)[]) => (a ?? []).map((x) => (x == null ? null : x / scale.div));

  return (
    <Card title="Forecast vs actuals" subtitle="Load measured AC power (CSV) for hours the forecast covers, for example this morning, and see how each model did."
      actions={<Segmented size="sm" label="Time zone of the file" value={tz} onChange={setTz} options={[{ value: "UTC", label: "Times in UTC" }, { value: "local", label: `Times in ${v.tz}` }]} />}>
      <FileDrop compact accept={[".csv", ".txt"]} busy={busy} onFile={upload} title="Drop a CSV with time and power"
        subtitle="First date column = start of each period; power in kW (or MW if the column name says so)" />
      {err && <div className="mt-3"><Alert tone="critical" title="Could not compare">{err}</Alert></div>}
      {res && res.periods === 0 && (
        <div className="mt-3"><Alert tone="warning" title="No overlap with the forecast">
          The file covers {dateTime(res.measured_from_utc, v.tz)} to {dateTime(res.measured_to_utc, v.tz)}; the forecast starts at the model run time. Measurements must fall in daylight inside the forecast window.
        </Alert></div>
      )}
      {res && res.periods > 0 && (
        <div className="mt-4 space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[460px] text-[12.5px]">
              <caption className="sr-only">Error measures per model</caption>
              <thead>
                <tr className="border-b border-line text-left text-muted">
                  <th className="py-1.5 pr-3 font-medium">Model</th>
                  <th className="py-1.5 pr-3 text-right font-medium">MAE</th>
                  <th className="py-1.5 pr-3 text-right font-medium">RMSE</th>
                  <th className="py-1.5 pr-3 text-right font-medium">Bias</th>
                  <th className="py-1.5 pr-3 text-right font-medium">MAE / DC</th>
                  <th className="py-1.5 text-right font-medium">Energy fc / actual</th>
                </tr>
              </thead>
              <tbody>
                {keys.map((k) => { const m = res.metrics[k]; return m && (
                  <tr key={k} className="border-b border-line last:border-0">
                    <td className="py-1.5 pr-3"><span className="flex items-center gap-1.5"><span className="inline-block h-0.5 w-3 rounded-full" style={{ background: COLOUR_VAR[k] }} />{LABELS[k]}</span></td>
                    <td className="tabular py-1.5 pr-3 text-right">{fmt(m.mae_kw / scale.div, 2)} {scale.power}</td>
                    <td className="tabular py-1.5 pr-3 text-right">{fmt(m.rmse_kw / scale.div, 2)}</td>
                    <td className="tabular py-1.5 pr-3 text-right">{signed(m.bias_kw / scale.div, 2)}</td>
                    <td className="tabular py-1.5 pr-3 text-right">{fmt(m.nmae_pct_of_dc, 1)} %</td>
                    <td className="tabular py-1.5 text-right">{fmt(m.energy_forecast_kwh / scale.div, 1)} / {fmt(m.energy_actual_kwh / scale.div, 1)} {scale.energy}</td>
                  </tr>
                ); })}
              </tbody>
            </table>
            <p className="mt-1.5 text-[11.5px] text-muted">{res.periods} daylight periods of {res.resolution_min} min, column “{res.column}”. Positive bias = forecast too high. One window is a first look, not a calibration.</p>
          </div>
          <div>
            <Segmented size="sm" label="Forecast shown" value={key} onChange={setKey} options={keys.map((k) => ({ value: k, label: LABELS[k] }))} className="mb-2" />
            <TimeChart t={res.series.t} tz={v.tz} unit={scale.power} digits={2} height={220} area={{ values: d(res.series.actual_kw), label: "Measured" }}
              series={[{ key, label: LABELS[key], color: COLOUR_VAR[key], values: d(res.series[key]), width: 2 }]} ariaLabel="Measured power and forecast" />
          </div>
        </div>
      )}
    </Card>
  );
}
