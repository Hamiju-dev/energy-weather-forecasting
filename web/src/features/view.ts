import { nowMs } from "../lib/clock";
import { useMemo } from "react";
import type { ForecastResult, ModelKey, PlantResult, SeriesKey } from "../lib/api";
import { scaleFor, type Scale } from "../lib/format";
import { localDate } from "../lib/time";

/* Derived values for one plant: scaling, per-day slices, today and tomorrow in local time. */
export interface PlantView {
  r: PlantResult;
  tz: string;
  scale: Scale;
  models: ModelKey[];
  dayIndex: Map<string, [number, number]>;   // local date -> [first, last+1] index into the series
  today: string;
  tomorrow: string;
  energy: (date: string, key: SeriesKey) => number | null;
  spread: (date: string) => [number, number] | null;
}

export function usePlantView(result: ForecastResult | null, name: string | undefined): PlantView | null {
  return useMemo(() => {
    if (!result) return null;
    const r = result.plants.find((p) => p.plant.name === name) ?? result.plants[0];
    if (!r) return null;
    const tz = r.plant.timezone;
    const dayIndex = new Map<string, [number, number]>();
    r.series.t.forEach((ms, i) => {
      const d = localDate(ms, tz);
      const cur = dayIndex.get(d);
      dayIndex.set(d, cur ? [cur[0], i + 1] : [i, i + 1]);
    });
    const now = nowMs();
    const today = localDate(now, tz), tomorrow = localDate(now + 864e5, tz);
    const byDate = new Map(r.daily.map((d) => [d.date, d]));
    const energy = (date: string, key: SeriesKey) => byDate.get(date)?.energy_kwh[key] ?? null;
    const spread = (date: string): [number, number] | null => {
      const vals = result.models.map((m) => energy(date, m)).filter((v): v is number => v != null);
      return vals.length ? [Math.min(...vals), Math.max(...vals)] : null;
    };
    return { r, tz, scale: scaleFor(r.plant.capacity_dc_kwp), models: result.models, dayIndex, today, tomorrow, energy, spread };
  }, [result, name]);
}
