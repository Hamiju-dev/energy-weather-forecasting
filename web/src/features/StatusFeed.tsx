import { nowMs } from "../lib/clock";
import { AnimatePresence, motion } from "framer-motion";
import { CircleAlert, CircleCheck, Info, TriangleAlert, X } from "lucide-react";
import { useMemo, useState } from "react";
import { Card } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import { spring } from "../lib/motion";
import { fmt, pct } from "../lib/format";
import { dateLabel, dayShort, hhmm } from "../lib/time";
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
  for (const p of result.problems) out.push({ id: `p-${p}`, tone: "critical", title: "Model missing", text: p });
  for (const r of result.runs) {
    const h = (nowMs() - Date.parse(r.run_utc)) / 3.6e6;
    if (h > 18) out.push({ id: `old-${r.model}`, tone: "warning", title: `${r.label} run is ${Math.round(h)} h old`, text: "Newer runs do not reach the horizon yet." });
  }
  const c = v.r.clipping;
  if (c.first_utc && (c.hours.blend ?? 0) > 0)
    out.push({ id: "clip", tone: "info", title: `${fmt(c.hours.blend, 1)} h at the ${v.r.plant.export_limit_kw ? "export" : "AC"} limit`, text: `From ${dayShort(c.first_utc, v.tz)} ${hhmm(c.first_utc, v.tz)}` });
  for (const d of v.r.daily) {
    if (!d.complete) continue;
    const s = v.spread(d.date), b = d.energy_kwh.blend;
    if (s && b && (s[1] - s[0]) / b > 0.35)
      out.push({ id: `spread-${d.date}`, tone: "warning", title: `Models disagree, ${dateLabel(d.date)}`, text: `${fmt(s[0] / v.scale.div, 1)}–${fmt(s[1] / v.scale.div, 1)} ${v.scale.energy} (±${pct(((s[1] - s[0]) / b) * 50)})` });
  }
  for (const m of v.models) {
    const runs = history.filter((e) => e.model === m && e.energy_kwh[v.tomorrow] != null).sort((a, b) => a.run_utc.localeCompare(b.run_utc));
    if (runs.length < 2) continue;
    const a = runs[runs.length - 2].energy_kwh[v.tomorrow], b = runs[runs.length - 1].energy_kwh[v.tomorrow];
    if (a > 0 && Math.abs(b - a) / a > 0.15)
      out.push({ id: `jump-${m}`, tone: "warning", title: `${m.toUpperCase()} moved tomorrow ${pct(((b - a) / a) * 100)}`, text: "Against its previous run" });
  }
  if (!out.length) out.push({ id: "ok", tone: "good", title: "Models agree", text: "Within 35 % on every day" });
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
    <Card title="Alerts" actions={urgent > 0 && <Badge tone="warning" dot>{`${urgent} open`}</Badge>}>
      <ul className="divide-y divide-[var(--border)]">
        <AnimatePresence initial={false}>
          {shown.map((e) => {
            const I = icon[e.tone];
            return (
              <motion.li key={e.id} layout initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} exit={{ opacity: 0, height: 0 }} transition={spring.responsive} className="overflow-hidden">
                <div className="flex items-start gap-3 py-2.5">
                  <I className={`mt-0.5 size-4 shrink-0 ${colour[e.tone]}`} aria-hidden />
                  <div className="min-w-0 flex-1 [overflow-wrap:anywhere]">
                    <p className="text-[13px] font-medium text-ink">{e.title}</p>
                    <p className="mt-0.5 text-[12px] leading-snug text-muted">{e.text}</p>
                  </div>
                  <button type="button" aria-label="Dismiss" onClick={() => setGone((g) => [...g, e.id])} className="focus-ring rounded p-0.5 text-muted hover:text-ink"><X className="size-3.5" /></button>
                </div>
              </motion.li>
            );
          })}
        </AnimatePresence>
      </ul>
      {list.length === 0 && <p className="py-4 text-center text-[13px] text-muted">No alerts.</p>}
      <div className="mt-1 flex gap-3 text-[12px]">
        {list.length > 3 && <button type="button" onClick={() => setExpanded(!expanded)} className="focus-ring rounded text-muted hover:text-ink">{expanded ? "Show less" : `Show all ${list.length}`}</button>}
        {gone.length > 0 && <button type="button" onClick={() => setGone([])} className="focus-ring rounded text-muted hover:text-ink">Restore {gone.length}</button>}
      </div>
    </Card>
  );
}
