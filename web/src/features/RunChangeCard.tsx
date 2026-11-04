import { History } from "lucide-react";
import { useState } from "react";
import { Card } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Segmented } from "../components/ui/segmented";
import { RunChanges } from "../components/charts/RunChanges";
import { COLOUR_VAR, LABELS } from "../lib/api";
import { dateLabel } from "../lib/time";
import type { App } from "./store";
import { SNAPSHOT } from "../lib/snapshot";
import type { PlantView } from "./view";

/* How stable is the forecast? Energy for one day from each model run seen so far. */
export function RunChangeCard({ v, app }: { v: PlantView; app: App }) {
  const dates = [...new Set(app.history.flatMap((e) => Object.keys(e.energy_kwh)))].sort().filter((d) => d >= v.today);
  const [date, setDate] = useState<string | null>(null);
  const d = date && dates.includes(date) ? date : dates.includes(v.tomorrow) ? v.tomorrow : dates[0];
  // the chart needs at least one model with two runs for the chosen day
  const runs = Math.max(0, ...v.models.map((m) => app.history.filter((e) => e.model === m && d && e.energy_kwh[d] != null).length));
  return (
    <Card title="Run to run" meta={v.scale.energy} info="Energy for one day from each model run seen so far. Large jumps between runs mean an uncertain day."
      actions={dates.length > 0 && <Segmented size="sm" label="Day" value={d} onChange={setDate} options={dates.slice(0, 6).map((x) => ({ value: x, label: dateLabel(x).split(" ")[0] }))} />}>
      {d && runs > 1 ? (
        <>
          <RunChanges history={app.history} date={d} unit={v.scale.energy} div={v.scale.div} models={v.models} />
          <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-[12px] text-ink-2">
            {v.models.map((m) => <span key={m} className="flex items-center gap-1.5"><span className="inline-block size-2 rounded-full" style={{ background: COLOUR_VAR[m] }} />{LABELS[m]}</span>)}
          </div>
        </>
      ) : (
        <div className="flex flex-col items-center gap-3 py-6 text-center">
          <span className="grid size-10 place-items-center rounded-xl bg-surface-raised text-muted"><History className="size-5" /></span>
          <p className="text-[13px] text-ink-2">One run so far.</p>
          <Button variant="secondary" size="sm" disabled={!!SNAPSHOT} loading={app.prevStatus === "running"} onClick={app.runPrevious}>Load previous runs</Button>
          {app.prevStatus === "error" && <p className="text-[12px] text-critical">The previous runs could not be loaded.</p>}
        </div>
      )}
      {d && runs > 1 && (
        <div className="mt-3 flex justify-end">
          {!SNAPSHOT && <Button variant="ghost" size="sm" loading={app.prevStatus === "running"} onClick={app.runPrevious}>Add the runs before</Button>}
        </div>
      )}
    </Card>
  );
}
