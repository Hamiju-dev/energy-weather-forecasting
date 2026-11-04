import { motion, useReducedMotion } from "framer-motion";
import { Wrench } from "lucide-react";
import { useState } from "react";
import { Card } from "../components/ui/card";
import { Segmented } from "../components/ui/segmented";
import { Tip } from "../components/ui/tooltip";
import { fmt, pct } from "../lib/format";
import { dayShort, hhmm } from "../lib/time";
import type { PlantView } from "./view";

/* Best daylight windows for maintenance: the stops that lose the least forecast energy.
   "Worst case" uses the highest model, so a team can see how much the choice depends on the models. */
export function WindowsCard({ v }: { v: PlantView }) {
  const reduce = useReducedMotion();
  const options = Object.keys(v.r.windows).sort((a, b) => +a - +b);
  const [hours, setHours] = useState(options.includes("4") ? "4" : options[0]);
  const list = (v.r.windows[hours] ?? []).slice(0, 4);
  const max = Math.max(1e-9, ...list.map((w) => w.energy_kwh_worst));
  const { scale } = v;
  return (
    <Card title="Maintenance" meta="lowest-loss slots" info="Daylight stops with the least lost energy, from now on. The light bar is the worst case over the models."
      actions={<Segmented size="sm" label="Window length" value={hours} onChange={setHours} options={options.map((h) => ({ value: h, label: `${h} h` }))} />}>
      {list.length === 0 ? (
        <p className="py-6 text-center text-[13px] text-muted">No {hours}-hour daylight window left in the forecast.</p>
      ) : (
        <ol className="space-y-2">
          {list.map((w, i) => (
            <motion.li key={w.start_utc} initial={reduce ? false : { opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.04 }}
              className="flex items-center gap-3 rounded-xl border border-line px-3 py-2">
              <span className={`grid size-7 shrink-0 place-items-center rounded-lg text-[12px] font-semibold ${i === 0 ? "bg-accent text-white" : "bg-surface-raised text-ink-2"}`}>{i === 0 ? <Wrench className="size-3.5" /> : i + 1}</span>
              <span className="min-w-0 flex-1">
                <span className="block text-[13px] font-medium text-ink">{dayShort(w.start_utc, v.tz)}, {hhmm(w.start_utc, v.tz)}–{hhmm(w.end_utc, v.tz)}</span>
                <span className="mt-1 flex items-center gap-2">
                  <Tip content={`Blend ${fmt(w.energy_kwh / scale.div, 2)}, highest model ${fmt(w.energy_kwh_worst / scale.div, 2)} ${scale.energy}`}>
                    <span className="relative block h-1.5 w-28 overflow-hidden rounded-full bg-surface-raised sm:w-40">
                      <span className="absolute inset-y-0 left-0 rounded-full bg-[var(--band)]" style={{ width: `${(w.energy_kwh_worst / max) * 100}%` }} />
                      <span className="absolute inset-y-0 left-0 rounded-full bg-blend" style={{ width: `${(w.energy_kwh / max) * 100}%` }} />
                    </span>
                  </Tip>
                  <span className="tabular text-[11.5px] text-muted">{pct(w.share_of_day * 100)} of day</span>
                </span>
              </span>
              <span className="tabular shrink-0 text-right text-[13px] font-medium text-ink">{fmt(w.energy_kwh / scale.div, 2)}<span className="block text-[11px] font-normal text-muted">{scale.energy}</span></span>
            </motion.li>
          ))}
        </ol>
      )}
    </Card>
  );
}
