import { useMemo, useState } from "react";
import { MODEL_KEYS, COLOUR_VAR, LABELS, type HistoryEntry, type ModelKey } from "../../lib/api";
import { niceRange, useElementWidth } from "../../lib/chart";
import { fmt } from "../../lib/format";
import { clamp } from "../../lib/utils";

/* How the energy forecast for one day changed from model run to model run.
   One line per model (colour follows the model), x = run time, y = energy for the chosen day. */
export function RunChanges({ history, date, unit, div, models }: { history: HistoryEntry[]; date: string; unit: string; div: number; models: ModelKey[] }) {
  const [ref, width] = useElementWidth<HTMLDivElement>(600);
  const [hover, setHover] = useState<{ m: ModelKey; i: number } | null>(null);
  const series = useMemo(() => {
    const out: Partial<Record<ModelKey, { run: number; v: number }[]>> = {};
    for (const e of history) {
      const v = e.energy_kwh[date];
      if (v == null || !models.includes(e.model)) continue;
      (out[e.model] ??= []).push({ run: Date.parse(e.run_utc), v: v / div });
    }
    Object.values(out).forEach((a) => a!.sort((p, q) => p.run - q.run));
    return out;
  }, [history, date, div, models]);
  const all = Object.values(series).flat() as { run: number; v: number }[];
  if (all.length === 0) return null;

  const height = 190, padL = 44, padR = 16, padT = 14, padB = 28;
  const runs = all.map((p) => p.run);
  const r0 = Math.min(...runs) - 3 * 3.6e6, r1 = Math.max(...runs) + 3 * 3.6e6;
  const ticks = niceRange(Math.min(...all.map((p) => p.v)) * 0.95, Math.max(...all.map((p) => p.v)) * 1.05, 4);
  const lo = ticks[0], hi = ticks[ticks.length - 1];
  const x = (ms: number) => padL + ((ms - r0) / (r1 - r0)) * (width - padL - padR);
  const y = (v: number) => padT + (1 - (v - lo) / (hi - lo || 1)) * (height - padT - padB);
  const runFmt = new Intl.DateTimeFormat("en-GB", { day: "numeric", month: "short", hour: "2-digit", hourCycle: "h23", timeZone: "UTC" });
  const uniqueRuns = [...new Set(runs)].sort((a, b) => a - b);
  const cur = hover ? series[hover.m]![hover.i] : null;

  return (
    <div ref={ref} className="relative w-full">
      <svg width={width} height={height} role="img" aria-label={`Forecast energy for ${date} by model run`} className="block overflow-visible">
        {ticks.map((v) => (
          <g key={v}>
            <line x1={padL} x2={width - padR} y1={y(v)} y2={y(v)} stroke={v === lo ? "var(--axis)" : "var(--grid)"} />
            <text x={padL - 6} y={y(v)} textAnchor="end" dominantBaseline="middle" className="tabular fill-[var(--text-muted)] text-[10.5px]">{fmt(v, v % 1 ? 1 : 0)}</text>
          </g>
        ))}
        <text x={padL - 6} y={padT - 6} textAnchor="end" className="fill-[var(--text-muted)] text-[10px]">{unit}</text>
        {uniqueRuns.filter((_, i, a) => a.length <= 6 || i % Math.ceil(a.length / 6) === 0).map((r) => (
          <text key={r} x={x(r)} y={height - 8} textAnchor="middle" className="tabular fill-[var(--text-muted)] text-[10px]">{runFmt.format(r)}Z</text>
        ))}
        {MODEL_KEYS.map((m) => series[m] && (
          <g key={m}>
            <path d={"M" + series[m]!.map((p) => `${x(p.run).toFixed(1)} ${y(p.v).toFixed(1)}`).join("L")} fill="none" stroke={COLOUR_VAR[m]} strokeWidth={2} />
            {series[m]!.map((p, i) => (
              <g key={i}>
                <circle cx={x(p.run)} cy={y(p.v)} r={4.5} fill={COLOUR_VAR[m]} stroke="var(--surface)" strokeWidth={2} />
                <circle cx={x(p.run)} cy={y(p.v)} r={12} fill="transparent" tabIndex={0} role="button" aria-label={`${LABELS[m]} run ${runFmt.format(p.run)} UTC: ${fmt(p.v, 2)} ${unit}`}
                  onPointerEnter={() => setHover({ m, i })} onPointerLeave={() => setHover(null)} onFocus={() => setHover({ m, i })} onBlur={() => setHover(null)} className="cursor-pointer outline-none" />
              </g>
            ))}
          </g>
        ))}
      </svg>
      {hover && cur && (
        <div className="pointer-events-none absolute z-20 rounded-lg border border-line bg-surface px-2.5 py-1.5 text-[12px] shadow-elevated"
          style={{ left: clamp(x(cur.run) - 70, 0, width - 160), top: y(cur.v) + 10 }}>
          <p className="tabular font-semibold text-ink">{fmt(cur.v, 2)} {unit}</p>
          <p className="text-muted">{LABELS[hover.m]} · run {runFmt.format(cur.run)} UTC</p>
        </div>
      )}
    </div>
  );
}
