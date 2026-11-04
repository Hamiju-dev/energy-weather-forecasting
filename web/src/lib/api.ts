/** Types and calls for the ewf API (src/ewf/api.py). */

export type ModelKey = "ifs" | "aifs" | "gfs";
export type SeriesKey = ModelKey | "blend";
export const MODEL_KEYS: ModelKey[] = ["ifs", "aifs", "gfs"];
export const LABELS: Record<SeriesKey, string> = { ifs: "ECMWF IFS", aifs: "ECMWF AIFS", gfs: "NOAA GFS", blend: "Blend" };
export const SHORT: Record<SeriesKey, string> = { ifs: "IFS", aifs: "AIFS", gfs: "GFS", blend: "Blend" };
export const COLOUR_VAR: Record<SeriesKey, string> = { ifs: "var(--m-ifs)", aifs: "var(--m-aifs)", gfs: "var(--m-gfs)", blend: "var(--m-blend)" };

export interface Plant {
  name: string;
  latitude: number;
  longitude: number;
  capacity_dc_kwp: number;
  capacity_ac_kw: number | null;
  altitude_m: number;
  tracking: "fixed" | "single_axis";
  tilt_deg: number;
  azimuth_deg: number;
  axis_azimuth_deg: number;
  max_angle_deg: number;
  gcr: number;
  backtrack: boolean;
  gamma_pdc_per_k: number;
  system_losses_pct: number;
  inverter_efficiency: number;
  albedo: number;
  temp_u0: number;
  temp_u1: number;
  export_limit_kw: number | null;
  timezone: string;
}

export interface Run {
  model: ModelKey;
  label: string;
  run_utc: string;
  last_step_h: number;
  steps: number;
  source: string;
  licence: string;
  attribution: string;
}

export interface DailyRow {
  date: string;
  complete: boolean;
  energy_kwh: Partial<Record<SeriesKey, number | null>>;
  specific_yield_kwh_per_kwp: number | null;
}

export interface Window {
  start_utc: string;
  end_utc: string;
  energy_kwh: number;
  energy_kwh_worst: number;
  share_of_day: number;
}

export interface PlantResult {
  plant: Plant;
  key: string;
  ac_limit_kw: number | null;
  series: {
    t: number[];
    power: Partial<Record<SeriesKey | "min" | "max", (number | null)[]>>;
    ghi: Partial<Record<SeriesKey | "clearsky", (number | null)[]>>;
    poa: (number | null)[];
    cell_temp_c: (number | null)[];
    temp_air_c: (number | null)[];
    wind_speed_ms: (number | null)[];
    cloud_cover_pct: (number | null)[];
  };
  daily: DailyRow[];
  peak_kw: number | null;
  peak_utc: string | null;
  windows: Record<string, Window[]>;      // keyed by window length in hours: "1", "2", "4", "8"
  clipping: { limit_kw: number | null; hours: Partial<Record<SeriesKey, number>>; first_utc: string | null; last_utc: string | null };
}

export interface ForecastResult {
  created_utc: string;
  window_utc: [string, string];
  models: ModelKey[];
  runs: Run[];
  problems: string[];
  plants: PlantResult[];
  note: string;
}

export interface JobState {
  job: string;
  status: "running" | "done" | "error";
  messages: { t: number; text: string }[];
  error: string | null;
  result?: ForecastResult;
}

export interface HistoryEntry {
  model: ModelKey;
  run_utc: string;
  created_utc: string;
  energy_kwh: Record<string, number>;
}

export interface Actuals {
  resolution_min: number;
  periods: number;
  first_utc: string | null;
  last_utc: string | null;
  column: string;
  measured_from_utc: string;
  measured_to_utc: string;
  metrics: Partial<Record<SeriesKey, { n: number; mae_kw: number; rmse_kw: number; bias_kw: number; nmae_pct_of_dc: number; energy_forecast_kwh: number; energy_actual_kwh: number }>>;
  series: { t: number[]; actual_kw: (number | null)[] } & Partial<Record<SeriesKey, (number | null)[]>>;
}

async function check<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`;
    try {
      const body = await r.json();
      msg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail ?? body);
    } catch { /* keep the status text */ }
    throw new Error(msg);
  }
  return r.json() as Promise<T>;
}

export interface ForecastRequest {
  plants: Partial<Plant>[];
  hours: number;
  models: ModelKey[];
  use_cache?: boolean;
  previous_run?: boolean;
  window_hours?: number;
}

export const api = {
  examplePlant: () => fetch("/api/example-plant").then((r) => check<Plant>(r)),
  startForecast: (req: ForecastRequest) =>
    fetch("/api/forecast", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(req) }).then((r) => check<{ job: string }>(r)),
  job: (id: string, since = 0) => fetch(`/api/jobs/${id}?since=${since}`).then((r) => check<JobState>(r)),
  parsePlants: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return fetch("/api/plants/parse", { method: "POST", body: fd }).then((r) => check<Plant[]>(r));
  },
  history: (plant: Plant) =>
    fetch("/api/history", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ plant }) }).then((r) => check<HistoryEntry[]>(r)),
  actuals: (job: string, plant: string, file: File, timezone: string) => {
    const fd = new FormData();
    fd.append("plant", plant);
    fd.append("file", file);
    fd.append("timezone", timezone);
    return fetch(`/api/jobs/${job}/actuals`, { method: "POST", body: fd }).then((r) => check<Actuals>(r));
  },
  downloadUrl: (job: string, plant: string, kind: "csv" | "daily" | "json" | "html" | "zip") =>
    `/api/jobs/${job}/download?plant=${encodeURIComponent(plant)}&kind=${kind}`,
};

/** Poll a job until it finishes; onProgress gets each new message. */
export async function waitForJob(id: string, onProgress: (text: string) => void, signal?: AbortSignal): Promise<ForecastResult> {
  let seen = 0;
  for (;;) {
    if (signal?.aborted) throw new Error("cancelled");
    const s = await api.job(id, seen);
    seen += s.messages.length;
    s.messages.forEach((m) => onProgress(m.text));
    if (s.status === "done" && s.result) return s.result;
    if (s.status === "error") throw new Error(s.error ?? "forecast failed");
    await new Promise((r) => setTimeout(r, 700));
  }
}
