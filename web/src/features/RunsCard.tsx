import { nowMs } from "../lib/clock";
import { Download, FileJson, FileSpreadsheet, FileText, Package } from "lucide-react";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { COLOUR_VAR, api, type ForecastResult } from "../lib/api";
import { relative } from "../lib/time";
import type { PlantView } from "./view";

/* Model runs used, their age and source, and the downloads (same files as the command line). */
export function RunsCard({ v, result, jobId }: { v: PlantView; result: ForecastResult; jobId: string | null }) {
  const runFmt = new Intl.DateTimeFormat("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hourCycle: "h23", timeZone: "UTC" });
  const files = [
    { kind: "csv" as const, label: "15-minute CSV", icon: <FileSpreadsheet /> },
    { kind: "daily" as const, label: "Daily CSV", icon: <FileSpreadsheet /> },
    { kind: "json" as const, label: "Summary JSON", icon: <FileJson /> },
    { kind: "html" as const, label: "HTML report", icon: <FileText /> },
    { kind: "zip" as const, label: "Everything (zip)", icon: <Package /> },
  ];
  return (
    <Card title="Model runs" info="The newest run of each model that reaches the forecast horizon.">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[440px] text-[12.5px]">
          <thead>
            <tr className="border-b border-line text-left text-muted">
              <th className="py-1.5 pr-3 font-medium">Model</th>
              <th className="py-1.5 pr-3 font-medium">Run (UTC)</th>
              <th className="py-1.5 pr-3 text-right font-medium">Steps</th>
              <th className="py-1.5 pr-3 font-medium">Source</th>
              <th className="py-1.5 font-medium">Licence</th>
            </tr>
          </thead>
          <tbody>
            {result.runs.map((r) => {
              const ageH = (nowMs() - Date.parse(r.run_utc)) / 3.6e6;
              return (
                <tr key={r.model} className="border-b border-line last:border-0">
                  <td className="py-2 pr-3"><span className="flex items-center gap-1.5 font-medium text-ink"><span className="inline-block size-2 rounded-full" style={{ background: COLOUR_VAR[r.model] }} />{r.label}</span></td>
                  <td className="py-2 pr-3"><span className="tabular">{runFmt.format(Date.parse(r.run_utc))}</span> <Badge tone={ageH > 18 ? "warning" : "neutral"} className="ml-1 h-5 px-2 text-[11px]">{relative(r.run_utc)}</Badge></td>
                  <td className="tabular py-2 pr-3 text-right">{r.steps} to {r.last_step_h} h</td>
                  <td className="py-2 pr-3 text-ink-2">{new URL(r.source).hostname}</td>
                  <td className="py-2 text-ink-2">{r.licence}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      {jobId && (
        <div className="mt-4 flex flex-wrap gap-2">
          {files.map((f) => (
            <a key={f.kind} href={api.downloadUrl(jobId, v.r.plant.name, f.kind)} download
              className="focus-ring inline-flex h-8 items-center gap-1.5 rounded-lg border border-line bg-surface px-3 text-[12px] font-medium text-ink transition-colors hover:border-line-hover hover:bg-surface-hover [&>svg]:size-3.5">
              {f.icon}{f.label}<Download className="text-muted" />
            </a>
          ))}
        </div>
      )}
    </Card>
  );
}
