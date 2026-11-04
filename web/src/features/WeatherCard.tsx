import { nowMs } from "../lib/clock";
import { useState } from "react";
import { Card } from "../components/ui/card";
import { Segmented } from "../components/ui/segmented";
import { TimeChart, type Series } from "../components/charts/TimeChart";
import { COLOUR_VAR, LABELS } from "../lib/api";
import type { PlantView } from "./view";

/* The weather behind the forecast. Irradiance per model with the clear sky as a dashed reference;
   the other quantities are model means. One measure per chart, one axis. */
type Tab = "ghi" | "cloud" | "temp" | "wind";

export function WeatherCard({ v }: { v: PlantView }) {
  const [tab, setTab] = useState<Tab>("ghi");
  const s = v.r.series;
  let series: Series[], unit: string, digits = 0, text: string;
  if (tab === "ghi") {
    series = [
      { key: "clearsky", label: "Clear sky", color: "var(--text-muted)", values: s.ghi.clearsky ?? [], dashed: true, width: 1.25 },
      ...v.models.map((m) => ({ key: m, label: LABELS[m], color: COLOUR_VAR[m], values: s.ghi[m] ?? [] })),
    ];
    unit = "W/m²";
    text = "Global horizontal irradiance. Where models sit far below the clear sky they expect clouds; where they disagree, the power forecast is uncertain.";
  } else if (tab === "cloud") {
    series = [{ key: "cloud", label: "Cloud cover (model mean)", color: "var(--m-blend)", values: s.cloud_cover_pct, width: 2 }];
    unit = "%";
    text = "Total cloud cover, mean of the models.";
  } else if (tab === "temp") {
    series = [
      { key: "air", label: "Air temperature", color: "var(--m-blend)", values: s.temp_air_c, width: 2 },
      { key: "cell", label: "Module temperature (daytime, model mean)", color: "var(--text-muted)", values: s.cell_temp_c, width: 1.5 },
    ];
    unit = "°C"; digits = 1;
    text = "Hot modules lose power: about 0.35 % per kelvin above 25 °C for crystalline silicon.";
  } else {
    series = [{ key: "wind", label: "Wind speed at 10 m", color: "var(--m-blend)", values: s.wind_speed_ms, width: 2 }];
    unit = "m/s"; digits = 1;
    text = "Wind cools the modules (Faiman model).";
  }
  return (
    <Card title="Weather behind the forecast" subtitle={text}
      actions={<Segmented size="sm" label="Quantity" value={tab} onChange={setTab} options={[{ value: "ghi", label: "Irradiance" }, { value: "cloud", label: "Clouds" }, { value: "temp", label: "Temperature" }, { value: "wind", label: "Wind" }]} />}>
      <TimeChart key={tab} t={s.t} series={series} tz={v.tz} unit={unit} digits={digits} height={220} shadeNight={s.ghi.clearsky} nowMs={nowMs()} minY0={tab !== "temp"}
        ariaLabel={`Weather: ${tab}`} />
    </Card>
  );
}
