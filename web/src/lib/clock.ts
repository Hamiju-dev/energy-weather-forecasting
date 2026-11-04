import { SNAPSHOT } from "./snapshot";

/** The current time; in a snapshot build, the time the snapshot was made, so "today" and "now" stay true to it. */
export const nowMs = () => (SNAPSHOT ? Date.parse(SNAPSHOT.created_utc) : Date.now());
