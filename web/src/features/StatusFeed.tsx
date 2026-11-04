import { AnimatePresence, motion } from "framer-motion";
import { Bell, CircleAlert, CircleCheck, Info, TriangleAlert, X } from "lucide-react";
import { useMemo, useState } from "react";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { spring } from "../lib/motion";
import { fmt, pct } from "../lib/format";
import { dateLabel, dayShort, hhmm, relative } from "../lib/time";
import type { ForecastResult, HistoryEntry } from "../lib/api";
import type { PlantView } from "./view";

/* Events worth a look, computed from the forecast (adapted from EasyUI notification-stack:
   stacked cards, swipe right or press x to dismiss; the demo items and "Simulate" are gone). */
type Tone = "good" | "info" | "warning" | "critical";
interface Event { id: string; tone: Tone; title: string; text: string }
const icon = { good: CircleCheck, info: Info, warning: TriangleAlert, critical: CircleAlert };
const colour = { good: "text-good-text", info: "text-accent", warning: "text-warning-text", critical: "text-critical" };

export function events(v: PlantView, result: ForecastResult, history: HistoryEntry[]): Event[] {
  const out: Event[] = [];
  for (const p of result.problems) out.push({ id: `p-${p}`, tone: "critical", title: "Model left out", text: p });
  for (const r of result.runs) {
    const h = (Date.now() - Date.parse(r.run_utc)) / 3.6e6;
    if (h > 18) out.push({ id: `old-${r.model}`, tone: "warning", title: `${r.label} run is ${Math.round(h)} h old`, text: "A newer run may not have reached the horizon yet. Try again later or shorten the horizon." });
  }
  const c = v.r.clipping;
  if (c.first_utc && (c.hours.blend ?? 0) > 0)
    out.push({ id: "clip", tone: "info", title: `At the ${v.r.plant.export_limit_kw ? "export" : "AC"} limit for ${fmt(c.hours.blend, 1)} h`, text: `First at ${dayShort(c.first_utc, v.tz)} ${hhmm(c.first_utc, v.tz)}. Energy above the limit is clipped.` });
  for (const d of v.r.daily) {
    if (!d.complete) continue;
    const s = v.spread(d.date), b = d.energy_kwh.blend;
    if (s && b && (s[1] - s[0]) / b > 0.35)
      out.push({ id: `spread-${d.date}`, tone: "warning", title: `Models disagree on ${dateLabel(d.date)}`, text: `Range ${fmt(s[0] / v.scale.div, 1)}–${fmt(s[1] / v.scale.div, 1)} ${v.scale.energy}, ${pct(((s[1] - s[0]) / b) * 100)} of the blend. Plan with margin.` });
  }
  for (const m of v.models) {
    const runs = history.filter((e) => e.model === m && e.energy_kwh[v.tomorrow] != null).sort((a, b) => a.run_utc.localeCompare(b.run_utc));
    if (runs.length < 2) continue;
    const a = runs[runs.length - 2].energy_kwh[v.tomorrow], b = runs[runs.length - 1].energy_kwh[v.tomorrow];
    if (a > 0 && Math.abs(b - a) / a > 0.15)
      out.push({ id: `jump-${m}`, tone: "warning", title: `${m.toUpperCase()} changed tomorrow by ${pct(((b - a) / a) * 100)}`, text: "Compared with its previous run. See run-to-run changes." });
  }
  if (!out.length) out.push({ id: "ok", tone: "good", title: "Nothing unusual", text: `All ${result.runs.length} models are current and agree within 35 % per day.` });
  out.push({ id: "fresh", tone: "info", title: "Forecast created", text: `${relative(result.created_utc)} from ${result.runs.map((r) => r.label).join(", ")}.` });
  return out;
}

export function StatusFeed({ v, result, history }: { v: PlantView; result: ForecastResult; history: HistoryEntry[] }) {
  const all = useMemo(() => events(v, result, history), [v, result, history]);
  const [gone, setGone] = useState<string[]>([]);
  const [expanded, setExpanded] = useState(false);
  const list = all.filter((e) => !gone.includes(e.id));
  const shown = expanded ? list : list.slice(0, 3);
  const urgent = list.filter((e) => e.tone === "warning" || e.tone === "critical").length;
  return (
    <Card title={<span className="flex items-center gap-2"><Bell className="size-4 text-muted" />Status</span>}
      actions={<>
        {urgent > 0 && <Badge tone="warning" dot>{`${urgent} to check`}</Badge>}
        {list.length > 3 && <button type="button" onClick={() => setExpanded(!expanded)} className="focus-ring rounded text-[12px] text-muted hover:text-ink">{expanded ? "Stack" : `Show all ${list.length}`}</button>}
      </>}>
      <div className="relative" style={{ minHeight: expanded ? undefined : shown.length ? 96 + Math.min(2, shown.length - 1) * 10 : 60 }}>
        <AnimatePresence mode="popLayout">
          {shown.length === 0 && <motion.p key="none" initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="py-4 text-center text-[13px] text-muted">All read.</motion.p>}
          {shown.map((e, i) => {
            const I = icon[e.tone];
            return (
              <motion.div key={e.id} layout
                initial={{ opacity: 0, y: -12, scale: 0.97 }}
                animate={{ opacity: 1, y: expanded ? 0 : i * 10, scale: expanded ? 1 : 1 - i * 0.04, zIndex: shown.length - i }}
                exit={{ opacity: 0, x: 80, scale: 0.92 }}
                transition={spring.responsive}
                drag="x" dragConstraints={{ left: 0, right: 100 }} dragElastic={0.3}
                onDragEnd={(_, info) => info.offset.x > 60 && setGone((g) => [...g, e.id])}
                style={{ position: expanded ? "relative" : "absolute", top: 0, left: 0, right: 0 }}
                className={`cursor-grab rounded-xl border border-line bg-surface p-3 shadow-card active:cursor-grabbing ${expanded ? "mb-2" : ""}`}>
                <div className="flex items-start gap-2.5">
                  <I className={`mt-0.5 size-4 shrink-0 ${colour[e.tone]}`} aria-hidden />
                  <div className="min-w-0 flex-1">
                    <p className="text-[12.5px] font-semibold text-ink">{e.title}</p>
                    <p className="mt-0.5 text-[12px] leading-snug text-ink-2">{e.text}</p>
                  </div>
                  <button type="button" aria-label="Dismiss" onClick={() => setGone((g) => [...g, e.id])} className="focus-ring rounded p-0.5 text-muted hover:text-ink"><X className="size-3.5" /></button>
                </div>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
      {gone.length > 0 && <button type="button" onClick={() => setGone([])} className="focus-ring mt-2 rounded text-[12px] text-muted hover:text-ink">Show dismissed ({gone.length})</button>}
    </Card>
  );
}
