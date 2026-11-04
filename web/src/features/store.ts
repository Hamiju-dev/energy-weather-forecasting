import { useCallback, useEffect, useRef, useState } from "react";
import { api, waitForJob, type ForecastResult, type HistoryEntry, type ModelKey, type Plant } from "../lib/api";

/* App state: plants (kept in this browser), forecast settings, the running job and its result. */

export const DEFAULT_PLANT: Plant = {
  name: "Leipzig solar park", latitude: 51.42, longitude: 12.24, capacity_dc_kwp: 10000, capacity_ac_kw: 7700, altitude_m: 0,
  tracking: "fixed", tilt_deg: 20, azimuth_deg: 180, axis_azimuth_deg: 180, max_angle_deg: 60, gcr: 0.4, backtrack: true,
  gamma_pdc_per_k: -0.0035, system_losses_pct: 10, inverter_efficiency: 0.98, albedo: 0.2, temp_u0: 25, temp_u1: 6.84,
  export_limit_kw: null, timezone: "Europe/Berlin",
};

export interface Settings { hours: number; models: ModelKey[] }

const load = <T,>(key: string, fallback: T): T => {
  try { const v = localStorage.getItem(key); return v ? (JSON.parse(v) as T) : fallback; } catch { return fallback; }
};
const save = (key: string, v: unknown) => { try { localStorage.setItem(key, JSON.stringify(v)); } catch { /* private mode */ } };

export type Status = "idle" | "running" | "done" | "error";

export function useApp() {
  const [plants, setPlantsState] = useState<Plant[]>(() => load("ewf-plants", [DEFAULT_PLANT]));
  const [selected, setSelected] = useState(0);
  const [settings, setSettingsState] = useState<Settings>(() => load("ewf-settings", { hours: 120, models: ["ifs", "aifs", "gfs"] }));
  const [status, setStatus] = useState<Status>("idle");
  const [messages, setMessages] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ForecastResult | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [prevStatus, setPrevStatus] = useState<Status>("idle");
  const abort = useRef<AbortController | null>(null);

  const setPlants = useCallback((p: Plant[]) => { setPlantsState(p); save("ewf-plants", p); setSelected((s) => Math.min(s, p.length - 1)); }, []);
  const setSettings = useCallback((s: Settings) => { setSettingsState(s); save("ewf-settings", s); }, []);

  const refreshHistory = useCallback(async (p: Plant) => {
    try { setHistory(await api.history(p)); } catch { setHistory([]); }
  }, []);

  const run = useCallback(async (opts?: { plants?: Plant[]; settings?: Settings }) => {
    const ps = opts?.plants ?? plants, st = opts?.settings ?? settings;
    abort.current?.abort();
    const ctrl = new AbortController();
    abort.current = ctrl;
    setStatus("running");
    setMessages([]);
    setError(null);
    try {
      const { job } = await api.startForecast({ plants: ps, hours: st.hours, models: st.models });
      const res = await waitForJob(job, (m) => setMessages((x) => [...x, m]), ctrl.signal);
      setJobId(job);
      setResult(res);
      setStatus("done");
      refreshHistory(ps[Math.min(selected, ps.length - 1)]);
    } catch (e) {
      if (ctrl.signal.aborted) return;
      setError(e instanceof Error ? e.message : String(e));
      setStatus("error");
    }
  }, [plants, settings, selected, refreshHistory]);

  /** Forecast from the runs before the latest ones, so the run-to-run chart has a second point. */
  const runPrevious = useCallback(async () => {
    setPrevStatus("running");
    try {
      const { job } = await api.startForecast({ plants, hours: settings.hours, models: settings.models, previous_run: true });
      await waitForJob(job, () => undefined);
      await refreshHistory(plants[selected]);
      setPrevStatus("done");
    } catch {
      setPrevStatus("error");
    }
  }, [plants, settings, selected, refreshHistory]);

  useEffect(() => { if (result) refreshHistory(plants[selected]); }, [selected]); // eslint-disable-line react-hooks/exhaustive-deps

  return { plants, setPlants, selected, setSelected, settings, setSettings, status, messages, error, result, jobId, run, history, runPrevious, prevStatus };
}

export type App = ReturnType<typeof useApp>;
