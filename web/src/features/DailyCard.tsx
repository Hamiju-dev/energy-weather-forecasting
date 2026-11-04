import { motion, useReducedMotion } from "framer-motion";
import { useMemo, useState } from "react";
import { Card } from "../components/ui/card";
import { Segmented } from "../components/ui/segmented";
import { AnimatedNumber } from "../components/ui/animated-number";
import { Badge } from "../components/ui/badge";
import { COLOUR_VAR, LABELS, SHORT, type SeriesKey } from "../lib/api";
import { autoDigits, fmt, signed } from "../lib/format";
import { dateLabel, hhmm } from "../lib/time";
import { monotonePath, useElementWidth } from "../lib/chart";
import { clamp } from "../lib/utils";
import { EASE_OUT } from "../lib/motion";
import type { PlantView } from "./view";

/* Daily energy card, adapted from EasyUI "earnings": a day switcher, a counting total, a scrubbable
   blend curve for that day, the spread between models, and one row per model with its energy and
   its difference to the blend. Models are alternatives, not parts of a whole, so the original split
   bar became a range bar. */
const SPARK_H = 72;

export function DailyCard({ v }: { v: PlantView }) {
  const reduce = useReducedMotion();
  const { r, scale } = v;
  const days = r.daily.map((d) => d.date);
  const [date, setDate] = useState(days.includes(v.tomorrow) ? v.tomorrow : days[0]);
  const [scrub, setScrub] = useState<number | null>(null);
  const [focusKey, setFocusKey] = useState<SeriesKey | null>(null);
  const [ref, width] = useElementWidth<HTMLDivElement>(420);
  const row = r.daily.find((d) => d.date === date)!;
  const [a, b] = v.dayIndex.get(date) ?? [0, 0];
  const t = r.series.t.slice(a, b);
  const key: SeriesKey = focusKey ?? "blend";
  const curve = (r.series.power[key] ?? []).slice(a, b).map((x) => (x ?? 0) / scale.div);
  const max = Math.max(1e-9, ...(r.series.power.max ?? []).slice(a, b).map((x) => (x ?? 0) / scale.div));
  const pts = useMemo(() => curve.map((y, i) => [2 + (i / Math.max(1, curve.length - 1)) * (width - 4), 6 + (1 - y / max) * (SPARK_H - 10)] as [number, number]), [curve, width, max]);
  const line = monotonePath(pts);
  const area = pts.length > 1 ? `${line}L${pts[pts.length - 1][0]} ${SPARK_H}L${pts[0][0]} ${SPARK_H}Z` : "";

  const total = (row.energy_kwh[key] ?? 0) / scale.div;
  const blend = (row.energy_kwh.blend ?? 0) / scale.div;
  const vals = v.models.map((m) => (row.energy_kwh[m] ?? 0) / scale.div);
  const lo = Math.min(...vals), hi = Math.max(...vals);
  const barMax = hi * 1.08 || 1;
  const readout = scrub != null && t[scrub] != null
    ? { label: `${hhmm(t[scrub], v.tz)}–${hhmm(t[scrub] + 9e5, v.tz)}, ${LABELS[key]}`, value: curve[scrub], unit: scale.power, digits: 2 }
    : { label: `${LABELS[key]}, ${dateLabel(date)}`, value: total, unit: scale.energy, digits: autoDigits(total) };

  return (
    <Card title="Daily energy" meta={row.complete ? `${fmt(row.specific_yield_kwh_per_kwp, 2)} kWh/kWp` : "partial day"}
      actions={<Segmented size="sm" label="Day" value={date} onChange={(d) => { setDate(d); setScrub(null); }} options={days.map((d) => ({ value: d, label: dateLabel(d).split(" ")[0] }))} className="max-w-full overflow-x-auto scrollbar-none" />}>
      <div aria-live="polite">
        <p className="h-[18px] truncate text-[12.5px] text-muted">{readout.label}</p>
        <p className="mt-1 text-[36px] leading-none font-semibold tracking-[-0.04em] text-ink">
          <AnimatedNumber value={readout.value} format={(n) => fmt(n, readout.digits)} duration={scrub != null ? 0.2 : 0.8} />
          <span className="ml-1.5 text-[15px] font-medium tracking-normal text-muted">{readout.unit}</span>
        </p>
        <p className="mt-2 flex min-h-[24px] flex-wrap items-center gap-2 text-[12.5px] text-muted">
          {!row.complete && <Badge tone="warning" dot>Partial day</Badge>}
          <span className="tabular">Range {fmt(lo, autoDigits(hi))}–{fmt(hi, autoDigits(hi))} {scale.energy}</span>
        </p>
      </div>

      <div ref={ref} className="mt-3" style={{ height: SPARK_H }}>
        {pts.length > 1 && (
          <svg width={width} height={SPARK_H} role="img" tabIndex={0} aria-label={`Power curve on ${dateLabel(date)}. Arrow keys read values.`}
            className="block touch-pan-y overflow-visible rounded-md outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent-ring)]"
            onPointerMove={(e) => { const bx = e.currentTarget.getBoundingClientRect(); setScrub(clamp(Math.round(((e.clientX - bx.left) / width) * (curve.length - 1)), 0, curve.length - 1)); }}
            onPointerLeave={() => setScrub(null)} onBlur={() => setScrub(null)}
            onKeyDown={(e) => {
              if (e.key === "ArrowRight") setScrub((s) => clamp((s ?? -1) + 1, 0, curve.length - 1));
              else if (e.key === "ArrowLeft") setScrub((s) => clamp((s ?? curve.length) - 1, 0, curve.length - 1));
              else if (e.key === "Escape") setScrub(null);
              else return;
              e.preventDefault();
            }}>
            <defs>
              <linearGradient id="dc-fill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor={COLOUR_VAR[key]} stopOpacity="0.22" />
                <stop offset="1" stopColor={COLOUR_VAR[key]} stopOpacity="0" />
              </linearGradient>
            </defs>
            <motion.path d={area} fill="url(#dc-fill)" initial={false} animate={{ d: area }} transition={reduce ? { duration: 0 } : { type: "spring", duration: 0.6, bounce: 0 }} />
            <motion.path d={line} fill="none" stroke={COLOUR_VAR[key]} strokeWidth={2} strokeLinecap="round" initial={false} animate={{ d: line }} transition={reduce ? { duration: 0 } : { type: "spring", duration: 0.6, bounce: 0 }} />
            {scrub != null && pts[scrub] && (
              <g pointerEvents="none">
                <line x1={pts[scrub][0]} x2={pts[scrub][0]} y1={0} y2={SPARK_H} stroke="var(--text-muted)" strokeDasharray="2 3" />
                <circle cx={pts[scrub][0]} cy={pts[scrub][1]} r={4.5} fill={COLOUR_VAR[key]} stroke="var(--surface)" strokeWidth={2} />
              </g>
            )}
          </svg>
        )}
      </div>

      <ul className="mt-4 space-y-1" aria-label="Energy by model">
        {[...v.models, "blend" as const].map((k, i) => {
          const e = (row.energy_kwh[k] ?? 0) / scale.div;
          const diff = blend ? ((e - blend) / blend) * 100 : 0;
          const on = focusKey === k;
          return (
            <li key={k}>
              <button type="button" aria-pressed={on} onClick={() => setFocusKey(on ? null : k)} onMouseEnter={() => setFocusKey(k)} onMouseLeave={() => setFocusKey(null)} onFocus={() => setFocusKey(k)} onBlur={() => setFocusKey(null)}
                className={`focus-ring flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-[background-color,opacity] ${on ? "bg-surface-hover" : "hover:bg-surface-hover"} ${focusKey && !on ? "opacity-55" : ""}`}>
                <span className="min-w-0 flex-1">
                  <span className="flex items-baseline justify-between gap-3 text-[13px]">
                    <span className={k === "blend" ? "font-semibold text-ink" : "text-ink"}>{SHORT[k]}</span>
                    <span className="tabular font-medium text-ink">{fmt(e, autoDigits(e))} {scale.energy}</span>
                  </span>
                  <span className="mt-1.5 flex items-center gap-3">
                    <span className="relative h-1 flex-1 overflow-hidden rounded-full bg-surface-raised">
                      <motion.span className="absolute inset-y-0 left-0 w-full origin-left rounded-full" style={{ background: COLOUR_VAR[k] }}
                        initial={reduce ? false : { scaleX: 0 }} animate={{ scaleX: e / barMax }} transition={{ duration: 0.8, ease: EASE_OUT, delay: i * 0.05 }} />
                    </span>
                    <span className="tabular w-16 shrink-0 text-right text-[11.5px] text-muted">{k === "blend" ? "mean" : `${signed(diff, 0)} %`}</span>
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
