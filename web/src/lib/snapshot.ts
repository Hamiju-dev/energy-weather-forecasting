import type { ForecastResult, HistoryEntry, Plant } from "./api";

/* Snapshot mode: a build of the dashboard with one real forecast embedded, for viewing without the
   server (see scripts/build-snapshot.mjs). In the normal build __SNAPSHOT__ is null. */
export interface Snapshot { result: ForecastResult; history: HistoryEntry[]; plant: Plant; created_utc: string }
declare const __SNAPSHOT__: Snapshot | null;
export const SNAPSHOT: Snapshot | null = __SNAPSHOT__;
