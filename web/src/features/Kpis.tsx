import { ArrowDownRight, ArrowUpRight, Gauge, Sun, Sunrise, SunMedium } from "lucide-react";
import type { ReactNode } from "react";
import { AnimatedNumber } from "../components/ui/animated-number";
import { Tip } from "../components/ui/tooltip";
import { Badge } from "../components/ui/badge";
import { autoDigits, fmt, signed } from "../lib/format";
import { dateLabel, dayShort, hhmm } from "../lib/time";
import type { HistoryEntry } from "../lib/api";
import type { PlantView } from "./view";

/* Headline numbers: energy today, tomorrow, the day after, and the peak. Each energy tile shows
   the range between models, and tomorrow shows the change against the previous model runs. */
function Tile({ icon, label, value, unit, digits, sub, extra, tip }: { icon: ReactNode; label: string; value: number | null; unit: string; digits: number; sub?: ReactNode; extra?: ReactNode; tip: string }) {
  return (
    <div className="min-w-0 rounded-2xl border border-line bg-surface p-4 shadow-card">
      <div className="flex flex-wrap items-center justify-between gap-x-2 gap-y-1">
        <Tip content={tip} side="bottom" wide><span className="flex cursor-help items-center gap-1.5 text-[12.5px] text-muted [&>svg]:size-3.5">{icon}{label}</span></Tip>
        {extra}
      </div>
      <p className="mt-2 text-[28px] leading-none font-semibold tracking-[-0.03em] text-ink sm:text-[32px]">
        {value == null ? "–" : <AnimatedNumber value={value} format={(n) => fmt(n, digits)} />}
        <span className="ml-1 text-[14px] font-medium tracking-normal text-muted">{unit}</span>
      </p>
      <div className="mt-2 min-h-[18px] text-[12px] text-muted">{sub}</div>
    </div>
  );
}

/** Change of tomorrow's energy between the latest and the previous run, per model, averaged. */
function runDelta(history: HistoryEntry[], date: string, models: string[]): number | null {
  const changes: number[] = [];
  for (const m of models) {
    const runs = history.filter((e) => e.model === m && e.energy_kwh[date] != null).sort((a, b) => a.run_utc.localeCompare(b.run_utc));
    if (runs.length >= 2) {
      const a = runs[runs.length - 2].energy_kwh[date], b = runs[runs.length - 1].energy_kwh[date];
      if (a > 0) changes.push(((b - a) / a) * 100);
    }
  }
  return changes.length ? changes.reduce((s, x) => s + x, 0) / changes.length : null;
}

export function Kpis({ v, history }: { v: PlantView; history: HistoryEntry[] }) {
  const { scale, r } = v;
  const after = [...v.dayIndex.keys()].find((d) => d > v.tomorrow) ?? null;
  const tile = (date: string | null) => {
    const e = date ? v.energy(date, "blend") : null;
    return e == null ? null : e / scale.div;
  };
  const range = (date: string | null) => {
    const s = date ? v.spread(date) : null;
    return s ? `models ${fmt(s[0] / scale.div, autoDigits(s[1] / scale.div))}–${fmt(s[1] / scale.div, autoDigits(s[1] / scale.div))}` : null;
  };
  const complete = (date: string | null) => r.daily.find((d) => d.date === date)?.complete ?? false;
  const delta = runDelta(history, v.tomorrow, v.models);
  const today = tile(v.today), tomorrow = tile(v.tomorrow), dayAfter = tile(after);
  const digits = (x: number | null) => (x == null ? 1 : autoDigits(x));
  return (
    <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      <Tile icon={<Sunrise />} label="Today" value={today} unit={scale.energy} digits={digits(today)} tip="Blend energy for the whole local day. If the forecast starts after sunrise, the day is partial and says so."
        sub={complete(v.today) ? range(v.today) : <span>partial day · {range(v.today)}</span>} />
      <Tile icon={<Sun />} label={`Tomorrow, ${dateLabel(v.tomorrow).split(" ")[0]}`} value={tomorrow} unit={scale.energy} digits={digits(tomorrow)}
        tip="Blend energy for tomorrow. The badge compares the latest model runs with the runs before them (average over models)." sub={range(v.tomorrow)}
        extra={delta != null && (
          <Badge tone={Math.abs(delta) < 5 ? "neutral" : "accent"} title="Change against the previous model runs">
            {Math.round(delta) > 0 ? <ArrowUpRight className="size-3" /> : Math.round(delta) < 0 ? <ArrowDownRight className="size-3" /> : null}
            {signed(delta, 0)} %<span className="hidden sm:inline"> vs last run</span>
          </Badge>
        )} />
      <Tile icon={<SunMedium />} label={after ? dateLabel(after) : "Day after"} value={dayAfter} unit={scale.energy} digits={digits(dayAfter)} tip="Blend energy for the day after tomorrow." sub={after && !complete(after) ? "partial day" : range(after)} />
      <Tile icon={<Gauge />} label="Peak power" value={r.peak_kw == null ? null : r.peak_kw / scale.div} unit={scale.power} digits={2}
        tip="Highest 15-minute mean of the blend in the forecast window." sub={r.peak_utc ? `${dayShort(r.peak_utc, v.tz)}, ${hhmm(r.peak_utc, v.tz)}` : null} />
    </div>
  );
}
