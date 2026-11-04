import { useEffect, useState } from "react";
import { Play, Plus, Trash2 } from "lucide-react";
import { Sheet } from "../components/ui/sheet";
import { Stepper, StepPanels } from "../components/ui/stepper";
import { NumberField, TextField } from "../components/ui/field";
import { Select } from "../components/ui/select";
import { Switch } from "../components/ui/switch";
import { Button } from "../components/ui/button";
import { FileDrop } from "../components/ui/file-drop";
import { Segmented } from "../components/ui/segmented";
import { Alert } from "../components/ui/alert";
import { api, COLOUR_VAR, LABELS, MODEL_KEYS, type Plant } from "../lib/api";
import { DEFAULT_PLANT, type App } from "./store";
import { PlantMap } from "./PlantMap";

const STEPS = [{ title: "Location" }, { title: "Modules" }, { title: "Inverter" }, { title: "Forecast" }];
const ZONES = ["Europe/Berlin", "Europe/Vienna", "Europe/Zurich", "Europe/Paris", "Europe/Madrid", "Europe/Rome", "Europe/Amsterdam", "Europe/Warsaw", "Europe/Prague", "Europe/London", "Europe/Athens", "UTC"];

/* Plant set-up as a four-step wizard in a side sheet (EasyUI sheet + stepper). */
export function PlantSheet({ app, open, onClose }: { app: App; open: boolean; onClose: () => void }) {
  const [step, setStep] = useState(0);
  const [plants, setPlants] = useState<Plant[]>(app.plants);
  const [idx, setIdx] = useState(app.selected);
  const [settings, setSettings] = useState(app.settings);
  const [fileError, setFileError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => { if (open) { setPlants(app.plants); setIdx(app.selected); setSettings(app.settings); setStep(0); setFileError(null); } }, [open]); // eslint-disable-line react-hooks/exhaustive-deps

  const p = plants[idx] ?? plants[0];
  const set = (patch: Partial<Plant>) => setPlants((ps) => ps.map((x, i) => (i === idx ? { ...x, ...patch } : x)));
  const names = plants.map((x) => x.name);
  const problems = [
    !p.name.trim() && "Give the plant a name.",
    new Set(names).size !== names.length && "Plant names must be unique.",
    !(p.latitude >= -90 && p.latitude <= 90) && "Latitude must be between −90 and 90.",
    !(p.longitude >= -180 && p.longitude <= 360) && "Longitude must be between −180 and 360.",
    !(p.capacity_dc_kwp > 0) && "DC capacity must be positive.",
    settings.models.length === 0 && "Choose at least one weather model.",
  ].filter(Boolean) as string[];

  const apply = (andRun: boolean) => {
    app.setPlants(plants);
    app.setSelected(idx);
    app.setSettings(settings);
    onClose();
    if (andRun) app.run({ plants, settings });
  };

  return (
    <Sheet open={open} onClose={onClose} title="Plant and forecast" description="Describe the PV plant; the forecast uses its location and design."
      footer={
        <div className="flex items-center justify-between gap-2">
          <Button variant="ghost" onClick={() => (step ? setStep(step - 1) : onClose())}>{step ? "Back" : "Cancel"}</Button>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => apply(false)} disabled={problems.length > 0}>Save</Button>
            {step < STEPS.length - 1 ? (
              <Button variant="primary" onClick={() => setStep(step + 1)}>Next</Button>
            ) : (
              <Button variant="primary" onClick={() => apply(true)} disabled={problems.length > 0}><Play className="size-3.5" />Run forecast</Button>
            )}
          </div>
        </div>
      }>
      <div className="mb-4 flex items-center gap-2">
        <div className="min-w-0 flex-1">
          <Select label="Plant" value={String(idx)} onChange={(v) => setIdx(Number(v))}
            options={plants.map((x, i) => ({ value: String(i), label: x.name || `Plant ${i + 1}`, description: `${(x.capacity_dc_kwp / 1000).toFixed(1)} MWp · ${x.latitude.toFixed(2)}, ${x.longitude.toFixed(2)}` }))} />
        </div>
        <Button size="icon" variant="secondary" className="mt-6" aria-label="Add a plant" title="Add a plant"
          onClick={() => { setPlants((ps) => [...ps, { ...DEFAULT_PLANT, name: `Plant ${ps.length + 1}` }]); setIdx(plants.length); setStep(0); }}><Plus className="size-4" /></Button>
        <Button size="icon" variant="secondary" className="mt-6" aria-label="Remove this plant" title="Remove this plant" disabled={plants.length < 2}
          onClick={() => { setPlants((ps) => ps.filter((_, i) => i !== idx)); setIdx(0); }}><Trash2 className="size-4" /></Button>
      </div>
      <div className="mb-5"><Stepper steps={STEPS} current={step} onStepChange={setStep} /></div>
      {problems.length > 0 && <div className="mb-4"><Alert tone="warning" title="Check the plant">{problems.join(" ")}</Alert></div>}

      <StepPanels current={step}>
        <div className="space-y-4">
          <TextField label="Name" value={p.name} onChange={(v) => set({ name: v })} />
          <div className="grid grid-cols-2 gap-3">
            <NumberField label="Latitude" value={p.latitude} onChange={(v) => set({ latitude: v ?? 0 })} unit="°N" min={-90} max={90} step={0.0001} />
            <NumberField label="Longitude" value={p.longitude} onChange={(v) => set({ longitude: v ?? 0 })} unit="°E" min={-180} max={360} step={0.0001} />
          </div>
          <PlantMap plants={[p]} onPick={(lat, lon) => set({ latitude: lat, longitude: lon })} height={220} />
          <p className="-mt-2 text-[11.5px] text-muted">Click the map to place the plant.</p>
          <div className="grid grid-cols-2 gap-3">
            <NumberField label="Altitude" value={p.altitude_m} onChange={(v) => set({ altitude_m: v ?? 0 })} unit="m" />
            <Select label="Time zone" value={p.timezone} onChange={(v) => set({ timezone: v })} options={[...new Set([p.timezone, ...ZONES])].map((z) => ({ value: z, label: z }))} />
          </div>
          <div className="pt-2">
            <p className="mb-1.5 text-[12px] font-medium text-ink-2">Or load a plant file</p>
            <FileDrop compact accept={[".yaml", ".yml", ".json"]} maxBytes={1024 * 1024} busy={busy} title="Drop a YAML or JSON plant file" subtitle="Same format as `ewf example-plant`; several plants allowed"
              onFile={async (f) => {
                setBusy(true);
                try { const ps = await api.parsePlants(f); setPlants(ps); setIdx(0); setFileError(null); }
                catch (e) { setFileError(e instanceof Error ? e.message : String(e)); }
                finally { setBusy(false); }
              }} />
            {fileError && <div className="mt-2"><Alert tone="critical" title="Could not read the plant file">{fileError}</Alert></div>}
          </div>
        </div>

        <div className="space-y-4">
          <NumberField label="DC capacity" value={p.capacity_dc_kwp} onChange={(v) => set({ capacity_dc_kwp: v ?? 0 })} unit="kWp" min={0.1} hint="Sum of module STC ratings" />
          <Select label="Mounting" value={p.tracking} onChange={(v) => set({ tracking: v })} options={[
            { value: "fixed", label: "Fixed tilt", description: "Modules at a fixed tilt and azimuth" },
            { value: "single_axis", label: "Single-axis tracker", description: "Rotating around one axis, with backtracking" },
          ]} />
          {p.tracking === "fixed" ? (
            <div className="grid grid-cols-2 gap-3">
              <NumberField label="Tilt" value={p.tilt_deg} onChange={(v) => set({ tilt_deg: v ?? 0 })} unit="°" min={0} max={90} hint="0 = flat" />
              <NumberField label="Azimuth" value={p.azimuth_deg} onChange={(v) => set({ azimuth_deg: v ?? 180 })} unit="°" min={0} max={360} hint="180 = south, 90 = east" />
            </div>
          ) : (
            <div className="grid grid-cols-3 gap-3">
              <NumberField label="Axis azimuth" value={p.axis_azimuth_deg} onChange={(v) => set({ axis_azimuth_deg: v ?? 180 })} unit="°" hint="180 = N–S axis" />
              <NumberField label="Max angle" value={p.max_angle_deg} onChange={(v) => set({ max_angle_deg: v ?? 60 })} unit="°" min={0} max={90} />
              <NumberField label="GCR" value={p.gcr} onChange={(v) => set({ gcr: v ?? 0.4 })} min={0.05} max={1} step={0.01} />
            </div>
          )}
          <div className="grid grid-cols-2 gap-3">
            <NumberField label="Temperature coefficient" value={+(p.gamma_pdc_per_k * 100).toFixed(3)} onChange={(v) => set({ gamma_pdc_per_k: (v ?? -0.35) / 100 })} unit="%/K" step={0.01} />
            <NumberField label="Albedo" value={p.albedo} onChange={(v) => set({ albedo: v ?? 0.2 })} min={0} max={1} step={0.01} hint="Ground reflectance" />
          </div>
        </div>

        <div className="space-y-4">
          <NumberField label="Inverter AC capacity" value={p.capacity_ac_kw} optional onChange={(v) => set({ capacity_ac_kw: v })} unit="kW" min={0.1} hint={p.capacity_ac_kw ? `DC/AC ratio ${(p.capacity_dc_kwp / p.capacity_ac_kw).toFixed(2)}` : "Empty means no clipping"} />
          <NumberField label="Grid export limit" value={p.export_limit_kw} optional onChange={(v) => set({ export_limit_kw: v })} unit="kW" min={0.1} hint="If the grid connection is smaller than the inverters" />
          <div className="grid grid-cols-2 gap-3">
            <NumberField label="System losses" value={p.system_losses_pct} onChange={(v) => set({ system_losses_pct: v ?? 10 })} unit="%" min={0} max={99} hint="Soiling, mismatch, wiring" />
            <NumberField label="Inverter efficiency" value={+(p.inverter_efficiency * 100).toFixed(2)} onChange={(v) => set({ inverter_efficiency: (v ?? 98) / 100 })} unit="%" min={50} max={100} />
          </div>
        </div>

        <div className="space-y-5">
          <div>
            <p className="mb-2 text-[12px] font-medium text-ink-2">Horizon</p>
            <Segmented label="Forecast horizon" value={String(settings.hours)} onChange={(v) => setSettings({ ...settings, hours: Number(v) })}
              options={[48, 72, 120, 168, 240].map((h) => ({ value: String(h), label: h % 24 ? `${h} h` : `${h / 24} d` }))} />
            <p className="mt-1.5 text-[11.5px] text-muted">From now. Beyond 5 days the IFS and GFS steps get coarser.</p>
          </div>
          <div className="space-y-3">
            <p className="text-[12px] font-medium text-ink-2">Weather models</p>
            {MODEL_KEYS.map((m) => (
              <Switch key={m} color={COLOUR_VAR[m]} checked={settings.models.includes(m)} label={LABELS[m]}
                description={{ ifs: "Physics-based, 0.25°, the reference global model", aifs: "Machine-learning model by ECMWF, 0.25°, 6-hourly", gfs: "Physics-based, 0.25°, hourly radiation to 120 h" }[m]}
                onChange={(on) => setSettings({ ...settings, models: on ? MODEL_KEYS.filter((k) => k === m || settings.models.includes(k)) : settings.models.filter((k) => k !== m) })} />
            ))}
          </div>
          <div className="rounded-xl border border-line bg-surface-raised p-3 text-[12.5px] text-ink-2">
            <p className="font-medium text-ink">{p.name}</p>
            <p className="mt-0.5">{p.capacity_dc_kwp.toLocaleString("en-GB")} kWp DC{p.capacity_ac_kw ? `, ${p.capacity_ac_kw.toLocaleString("en-GB")} kW AC` : ", no AC limit"} · {p.tracking === "fixed" ? `fixed ${p.tilt_deg}° / ${p.azimuth_deg}°` : "single-axis tracker"} · {p.latitude.toFixed(3)}, {p.longitude.toFixed(3)}</p>
            {plants.length > 1 && <p className="mt-1 text-muted">All {plants.length} plants are forecast in one run.</p>}
          </div>
        </div>
      </StepPanels>
    </Sheet>
  );
}
