import { nowMs } from "../lib/clock";
import { useMemo, useState } from "react";
import { Card } from "../components/ui/card";
import { Switch } from "../components/ui/switch";
import { Segmented } from "../components/ui/segmented";
import { TimeChart, type Series } from "../components/charts/TimeChart";
import { COLOUR_VAR, LABELS, type SeriesKey } from "../lib/api";
import { fmt } from "../lib/format";
import { dateLabel } from "../lib/time";
import type { PlantView } from "./view";

/* The main chart: 15-minute AC power per model and the blend, the range between models,
   the AC or export limit, clipped periods, night shading and "now". Model switches are the legend. */
export function PowerCard({ v, visible, setVisible }: { v: PlantView; visible: Record<SeriesKey | "band", boolean>; setVisible: (k: SeriesKey | "band", on: boolean) => void }) {
  const [day, setDay] = useState("all");
  const { r, scale } = v;
  const [a, b] = day === "all" ? [0, r.series.t.length] : v.dayIndex.get(day) ?? [0, r.series.t.length];
  const sl = <T,>(arr: T[] | undefined) => (arr ?? []).slice(a, b);
  const d = (arr: (number | null)[] | undefined) => sl(arr).map((x) => (x == null ? null : x / scale.div));

  const series: Series[] = useMemo(() => {
    const keys: SeriesKey[] = [...v.models, "blend"];
    return keys.filter((k) => visible[k]).map((k) => ({
      key: k, label: LABELS[k], color: COLOUR_VAR[k], values: d(r.series.power[k]), width: k === "blend" ? 2.4 : 1.5,
    }));
  }, [v, visible, a, b]); // eslint-disable-line react-hooks/exhaustive-deps

  const limit = r.ac_limit_kw;
  const clipSpans = useMemo(() => {
    if (!limit) return [];
    const out: { from: number; to: number; tone: "warning" }[] = [];
    const t = sl(r.series.t), p = sl(r.series.power.blend);
    let s: number | null = null;
    p.forEach((x, i) => {
      const at = x != null && x >= 0.995 * limit;
      if (at && s == null) s = t[i];
      if (!at && s != null) { out.push({ from: s, to: t[i], tone: "warning" }); s = null; }
    });
    if (s != null) out.push({ from: s, to: t[t.length - 1] + 9e5, tone: "warning" });
    return out;
  }, [r, limit, a, b]); // eslint-disable-line react-hooks/exhaustive-deps

  const days = [...v.dayIndex.keys()];
  const clipH = r.clipping.hours.blend ?? 0;
  return (
    <Card title="AC power forecast" subtitle={`15-minute means in ${scale.power}, local time (${v.tz}). The band is the range between models, not a probability interval.`}
      actions={<Segmented size="sm" label="Days shown" value={day} onChange={setDay} options={[{ value: "all", label: "All" }, ...days.map((x) => ({ value: x, label: dateLabel(x).split(" ").slice(0, 2).join(" ") }))]} className="max-w-full overflow-x-auto scrollbar-none" />}>
      <div className="mb-3 flex flex-wrap gap-x-5 gap-y-2">
        {[...v.models, "blend" as const].map((k) => (
          <Switch key={k} color={COLOUR_VAR[k]} checked={visible[k]} onChange={(on) => setVisible(k, on)}
            label={<span className="flex items-center gap-1.5"><span className="inline-block h-0.5 w-3.5 rounded-full" style={{ background: COLOUR_VAR[k], height: k === "blend" ? 3 : 2 }} />{LABELS[k]}</span>} />
        ))}
        <Switch checked={visible.band} onChange={(on) => setVisible("band", on)} label={<span className="flex items-center gap-1.5"><span className="inline-block h-3 w-3.5 rounded-sm bg-[var(--band)]" />Model range</span>} />
      </div>
      <TimeChart
        t={sl(r.series.t)}
        series={series}
        band={visible.band ? { lo: d(r.series.power.min), hi: d(r.series.power.max), label: "Model range" } : undefined}
        refLines={limit ? [{ value: limit / scale.div, label: `${r.plant.export_limit_kw && r.plant.export_limit_kw === limit ? "Export" : "AC"} limit ${fmt(limit / scale.div, 2)} ${scale.power}` }] : []}
        spans={clipSpans}
        shadeNight={sl(r.series.ghi.clearsky)}
        nowMs={nowMs()}
        tz={v.tz}
        unit={scale.power}
        digits={2}
        height={300}
        ariaLabel={`AC power forecast for ${r.plant.name}`}
      />
      <p className="mt-2 text-[12px] text-muted">
        {clipH > 0 ? <>Blend at the limit for <span className="text-ink-2">{fmt(clipH, 1)} h</span> (yellow); power above it is lost to clipping. </> : limit ? "The blend stays below the limit in this window. " : "No AC limit set. "}
        Grey areas are night.
      </p>
    </Card>
  );
}
