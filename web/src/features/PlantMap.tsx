import { useEffect, useRef } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Plant } from "../lib/api";

/* OpenStreetMap map of the plants. Click to move the selected plant (when onPick is given).
   Tiles: © OpenStreetMap contributors (ODbL), loaded from tile.openstreetmap.org. */
export function PlantMap({ plants, selected = 0, onPick, onSelect, height = 260 }: {
  plants: Pick<Plant, "name" | "latitude" | "longitude" | "capacity_dc_kwp">[]; selected?: number; onPick?: (lat: number, lon: number) => void; onSelect?: (i: number) => void; height?: number;
}) {
  const el = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const layer = useRef<L.LayerGroup | null>(null);
  const pick = useRef(onPick);
  pick.current = onPick;

  useEffect(() => {
    if (!el.current || map.current) return;
    const m = L.map(el.current, { zoomControl: true, attributionControl: true, scrollWheelZoom: false });
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(m);
    m.on("click", (e: L.LeafletMouseEvent) => pick.current?.(+e.latlng.lat.toFixed(4), +e.latlng.lng.toFixed(4)));
    layer.current = L.layerGroup().addTo(m);
    map.current = m;
    return () => { m.remove(); map.current = null; };
  }, []);

  useEffect(() => {
    const m = map.current, g = layer.current;
    if (!m || !g) return;
    g.clearLayers();
    const styles = getComputedStyle(document.documentElement);
    const accent = styles.getPropertyValue("--accent").trim() || "#2a78d6";
    const maxCap = Math.max(...plants.map((p) => p.capacity_dc_kwp), 1);
    plants.forEach((p, i) => {
      const r = 6 + 10 * Math.sqrt(p.capacity_dc_kwp / maxCap);
      L.circleMarker([p.latitude, p.longitude], {
        radius: r, color: "#ffffff", weight: 2, fillColor: accent, fillOpacity: i === selected ? 0.95 : 0.45,
      }).bindTooltip(`${p.name} · ${(p.capacity_dc_kwp / 1000).toFixed(1)} MWp`).on("click", () => onSelect?.(i)).addTo(g);
    });
    if (plants.length === 1) m.setView([plants[0].latitude, plants[0].longitude], onPick ? 9 : 7);
    else if (plants.length > 1) m.fitBounds(L.latLngBounds(plants.map((p) => [p.latitude, p.longitude] as [number, number])).pad(0.3));
  }, [plants, selected, onSelect, onPick]);

  return <div ref={el} style={{ height }} className="relative isolate z-0 w-full overflow-hidden rounded-xl border border-line" aria-label="Map of plant locations" role="application" />;
}
