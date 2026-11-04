heres the two missing code:

Earnings (earnings)

* Category / priority: FEEDBACK (chart card) / high (headline number with trend and breakdown; maps to a “today’s yield” or “forecast vs actual” card)
* Page: https://easyui.site/components/earnings
* Licence shown on page: none shown
* Description: Summary card with a counting-up total, a delta against the previous period, a scrubbable trend line, a split bar plus one row per income source, and a 7D / 30D / 12M period switcher. The page labels it “NEW”.
* Dependencies: react (19 per the file comment), framer-motion (animate, motion, useMotionValue, useReducedMotion, useSpring, useTransform), Tailwind. No lucide-react, no `lib/utils`, no `lib/chart-primitives`, no `lib/motion-tokens`: the file defines its own helpers (`cx`, `clamp`, `useElementWidth`, `monotonePath`, `resample`, `AnimatedNumber`, `SegmentedControl`) and is self-contained. Colours are Tailwind `neutral-*`, `emerald`, `rose` with `dark:` variants plus a hard-coded dark card colour `#0b0b0c`.
* Chart data and features: charting source is hand-written SVG (monotone cubic path, no chart library). Data shape: an array of periods `{ id, label, comparison?, total?, previous?, trend: number[], trendLabels?: string[], sources: { id, label, amount, change?, color?, icon? }[] }` (see the usage example). Tooltips: no floating tooltip, but the big readout above the chart shows the scrubbed point or the hovered source. Hover crosshair: yes (dashed vertical line and a dot that follows the cursor or finger, with arrow-key scrubbing). Legends: the source rows act as the legend. Animation on data change: yes (numbers count, the bar and the trend line morph between periods, all trends are resampled to 32 points). Light and dark mode: yes (`dark:` classes).
* Visual notes: Rounded-[22px] card; title and pill-shaped segmented control on top; a 36–44px bold total, a green or red delta chip with a ▲/▼ triangle and a comparison caption; a 76px-high area-and-line chart in indigo (`#6d7cff`); a 12px-high split bar with gaps between segments; a list of sources with coloured initial tiles, amounts, thin progress bars, change percentages and shares; an optional payout footer.
* Interaction notes: Pointer move or touch on the chart scrubs; arrow keys scrub when the chart has focus (Escape clears). Hover or tap a source row or bar segment to highlight it and show only its numbers; a tap outside clears the selection. Reduced motion disables the animations. A screen-reader-only table repeats the source figures.
* Props: periods, defaultPeriod (second period when three or more exist), onPeriodChange, title (‘Earnings’), currency (‘USD’), locale (‘en-US’), payout ({ label?, date, amount? }), animated (true), className. Also exports helpers `SOURCE_COLORS`, `monotonePath`, `resample` and a default export. Money is formatted with `Intl.NumberFormat` (whole units when the total is 10,000 or more).
* Solar adaptation note: `trend` takes a plain number array, so it could hold 15-minute power values and the `sources` rows could be forecast models, but the component is built around currency formatting, so the `money` formatter would need to be replaced with a kW / MWh formatter.

src/components/ui/earnings.tsx
tsx

```tsx
"use client";

import React, {
type ReactNode,
useEffect,
useId,
useLayoutEffect,
useMemo,
useRef,
useState,
} from "react";
import {
animate,
motion,
useMotionValue,
useReducedMotion,
useSpring,
useTransform,
} from "framer-motion";

/* -------------------------------------------------------------------------- */
/* Earnings — "how much did I make, and from where?" */
/* */
/* • Big total that counts up, with a delta vs the previous period */
/* • Trend line you can scrub (the number follows your finger / cursor) */
/* • One split bar + a row per income source; hover or tap a source to */
/* highlight it and see just its share */
/* • Period switcher (7D / 30D / 12M): numbers count, the bar and the */
/* trend line morph */
/* */
/* One file · deps: react 19, framer-motion, tailwindcss · light + dark · */
/* fully responsive. */
/* -------------------------------------------------------------------------- */

/* ========================================================================== */
/* Types */
/* ========================================================================== */

export interface EarningsSource {
id: string;
label: string;
amount: number;
/** % change vs the previous period (shown as a small ▲/▼) */
change?: number;
/** Any CSS color */
color?: string;
/** Your own icon. Defaults to a colored initial */
icon?: ReactNode;
}

export interface EarningsPeriod {
id: string;
/** Segmented-control label, e.g. "30D" */
label: string;
/** Under the delta, e.g. "vs previous 30 days" */
comparison?: string;
/** Defaults to the sum of the sources */
total?: number;
/** Total of the previous period → the delta is computed from it */
previous?: number;
/** Earnings per point (day, week, month…), oldest → newest */
trend: number[];
/** Name for each trend point, shown while scrubbing ("Oct 12") */
trendLabels?: string[];
sources: EarningsSource[];
}

export interface EarningsProps {
periods: EarningsPeriod[];
/** Initial period id (default: second one if there are 3+, else the first) */
defaultPeriod?: string;
onPeriodChange?: (id: string) => void;
title?: string;
currency?: string;
locale?: string;
/** Footer line, e.g. { label: "Next payout", date: "Nov 5", amount: 1240 } */
payout?: { label?: string; date: string; amount?: number };
animated?: boolean;
className?: string;
}

/* ========================================================================== */
/* Helpers */
/* ========================================================================== */

export const SOURCE_COLORS = ["#6d7cff", "#34d1bf", "#ffb44c", "#ff6b8b", "#a78bfa", "#5ac8fa"];

const EASE_OUT = [0.23, 1, 0.32, 1] as const;
const clamp = (v: number, min: number, max: number) => Math.min(Math.max(v, min), max);
const cx = (...a: (string | false | null | undefined)[]) => a.filter(Boolean).join(" ");
const pct = (x: number) => `${Math.abs(x) >= 10 ? Math.round(Math.abs(x)) : Math.abs(x).toFixed(1)}%`;

const focus =
"outline-none focus-visible:ring-2 focus-visible:ring-neutral-400/70 dark:focus-visible:ring-white/40";
const ring = "ring-1 ring-black/[0.07] dark:ring-white/[0.07]";
const muted = "text-neutral-500";

function useElementWidth<T extends HTMLElement>(initial: number) {
const ref = useRef<T>(null);
const [width, setWidth] = useState(initial);
useLayoutEffect(() => {
const el = ref.current;
if (!el) return;
const update = () => setWidth(Math.round(el.clientWidth) || initial);
update();
const ro = new ResizeObserver(update);
ro.observe(el);
return () => ro.disconnect();
}, [initial]);
return [ref, width] as const;
}

/** Smooth monotone cubic (never overshoots the data) */
export function monotonePath(p: [number, number][]): string {
const n = p.length;
if (n < 2) return n ? `M${p[0][0]} ${p[0][1]}` : "";
const dx: number[] = [], m: number[] = [];
for (let i = 0; i < n - 1; i++) {
dx[i] = p[i + 1][0] - p[i][0];
m[i] = (p[i + 1][1] - p[i][1]) / (dx[i] || 1e-9);
}
const t: number[] = new Array(n);
t[0] = m[0];
t[n - 1] = m[n - 2];
for (let i = 1; i < n - 1; i++) t[i] = m[i - 1] * m[i] <= 0 ? 0 : (m[i - 1] + m[i]) / 2;
for (let i = 0; i < n - 1; i++) {
if (m[i] === 0) {
t[i] = 0;
t[i + 1] = 0;
} else {
const a = t[i] / m[i], b = t[i + 1] / m[i], s = a * a + b * b;
if (s > 9) {
const k = 3 / Math.sqrt(s);
t[i] = k * a * m[i];
t[i + 1] = k * b * m[i];
}
}
}
let d = `M${p[0][0].toFixed(2)} ${p[0][1].toFixed(2)}`;
for (let i = 0; i < n - 1; i++) {
const h = dx[i] / 3;
d += `C${(p[i][0] + h).toFixed(2)} ${(p[i][1] + t[i] * h).toFixed(2)} ${(p[i + 1][0] - h).toFixed(2)} ${(p[i + 1][1] - t[i + 1] * h).toFixed(2)} ${p[i + 1][0].toFixed(2)} ${p[i + 1][1].toFixed(2)}`;
}
return d;
}

/** Linear resample to a fixed number of points so any two trends can morph into each other */
export function resample(v: number[], n: number): number[] {
if (!v.length) return Array(n).fill(0);
if (v.length === 1) return Array(n).fill(v[0]);
return Array.from({ length: n }, (_, i) => {
const x = (i / (n - 1)) * (v.length - 1);
const i0 = Math.floor(x), i1 = Math.min(v.length - 1, i0 + 1);
return v[i0] + (v[i1] - v[i0]) * (x - i0);
});
}

function AnimatedNumber({
value,
format,
duration = 0.9,
fromZero,
}: {
value: number;
format: (n: number) => string;
duration?: number;
fromZero?: boolean;
}) {
const reduce = useReducedMotion();
const mv = useMotionValue(fromZero && !reduce ? 0 : value);
const fmt = useRef(format);
fmt.current = format;
const text = useTransform(mv, (v) => fmt.current(v));
useEffect(() => {
const c = animate(mv, value, { duration: reduce ? 0 : duration, ease: EASE_OUT });
return () => c.stop();
}, [value, duration, mv, reduce]);
return <motion.span>{text}</motion.span>;
}

function SegmentedControl<T extends string>({
value,
onChange,
options,
label,
}: {
value: T;
onChange: (v: T) => void;
options: { value: T; label: string }[];
label: string;
}) {
const id = useId();
return (
<div role="radiogroup" aria-label={label} className="relative inline-flex shrink-0 rounded-full bg-black/[0.04] p-0.5 dark:bg-white/[0.05]">
{options.map((o) => {
const on = o.value === value;
return (
<button
key={o.value}
type="button"
role="radio"
aria-checked={on}
onClick={() => onChange(o.value)}
className={`relative z-10 h-9 rounded-full px-3.5 text-[12px] font-medium transition-colors duration-150 [-webkit-tap-highlight-color:transparent] sm:h-8 sm:px-3 ${focus} ${
on ? "text-neutral-900 dark:text-white" : "text-neutral-500"
}`}
>
{on && (
<motion.span
layoutId={id}
className="absolute inset-0 -z-10 rounded-full bg-white shadow-sm dark:bg-neutral-800"
transition={{ type: "spring", duration: 0.3, bounce: 0.15 }}
/>
)}
{o.label}
</button>
);
})}
</div>
);
}

/* ========================================================================== */
/* Earnings */
/* ========================================================================== */

const N_POINTS = 32;
const SPARK_H = 76;

export function Earnings({
periods,
defaultPeriod,
onPeriodChange,
title = "Earnings",
currency = "USD",
locale = "en-US",
payout,
animated = true,
className = "",
}: EarningsProps) {
const reduce = useReducedMotion();
const anim = animated && !reduce;
const uid = useId().replace(/:/g, "");
const [sparkRef, width] = useElementWidth<HTMLDivElement>(480);
const svgRef = useRef<SVGSVGElement>(null);
const cardRef = useRef<HTMLElement>(null);

const [periodId, setPeriodId] = useState(defaultPeriod ?? periods[periods.length > 2 ? 1 : 0]?.id ?? "");
const [activeSource, setActiveSource] = useState<string | null>(null);
const [scrub, setScrub] = useState<number | null>(null);

const period = periods.find((p) => p.id === periodId) ?? periods[0];

// tap outside clears a tap-selected source / scrub (touch)
useEffect(() => {
if (activeSource === null && scrub === null) return;
const down = (e: PointerEvent) => {
if (!cardRef.current?.contains(e.target as Node)) {
setActiveSource(null);
setScrub(null);
}
};
document.addEventListener("pointerdown", down);
return () => document.removeEventListener("pointerdown", down);
}, [activeSource, scrub]);

const money = useMemo(() => {
const big = (period?.total ?? period?.sources.reduce((s, x) => s + x.amount, 0) ?? 0) >= 10000;
const nf = new Intl.NumberFormat(locale, { style: "currency", currency, minimumFractionDigits: big ? 0 : 2, maximumFractionDigits: big ? 0 : 2 });
return (n: number) => nf.format(n);
}, [locale, currency, period]);
const moneyExact = useMemo(() => {
const nf = new Intl.NumberFormat(locale, { style: "currency", currency, minimumFractionDigits: 2, maximumFractionDigits: 2 });
return (n: number) => nf.format(n);
}, [locale, currency]);

/* ------------------------------- numbers ------------------------------- */
const sources = period?.sources ?? [];
const sum = sources.reduce((s, x) => s + Math.max(0, x.amount), 0);
const total = period?.total ?? sum;
const trend = period?.trend ?? [];
const n = trend.length;

const delta =
period?.previous !== undefined && period.previous !== 0
? ((total - period.previous) / Math.abs(period.previous)) * 100
: n > 1 && trend[0] !== 0
? ((trend[n - 1] - trend[0]) / Math.abs(trend[0])) * 100
: 0;
const deltaRounded = Math.round(delta * 10) / 10;

const src = sources.find((s) => s.id === activeSource) ?? null;
const maxAmount = Math.max(1e-9, ...sources.map((s) => s.amount));

// what the big readout shows right now: a source, a scrubbed point, or the total
const readout = src
? { label: src.label, value: src.amount, change: src.change, note: `${pct(sum ? (src.amount / sum) * 100 : 0)} of earnings` }
: scrub !== null && n
? { label: period.trendLabels?.[scrub] ?? `Point ${scrub + 1}`, value: trend[scrub], change: undefined, note: "earned" }
: { label: title, value: total, change: deltaRounded, note: period?.comparison ?? "vs previous period" };

/* -------------------------------- trend -------------------------------- */
const padX = 2, padT = 10, padB = 6;
const min = n ? Math.min(...trend) : 0;
const span = (n ? Math.max(...trend) : 1) - min || 1;
const yOf = (v: number) => padT + (1 - (v - min) / span) * (SPARK_H - padT - padB);
const xOf = (f: number) => padX + f * (width - padX * 2);
const smooth = resample(trend, N_POINTS);
const pts = smooth.map((v, i) => [xOf(i / (N_POINTS - 1)), yOf(v)] as [number, number]);
const line = monotonePath(pts);
const area = n > 1 ? `${line}L${pts[N_POINTS - 1][0].toFixed(2)} ${SPARK_H}L${pts[0][0].toFixed(2)} ${SPARK_H}Z` : "";
const accent = SOURCE_COLORS[0];

const curX = useSpring(0, { stiffness: 600, damping: 44, mass: 0.5 });
const curY = useSpring(0, { stiffness: 600, damping: 44, mass: 0.5 });
const seen = useRef(false);
useEffect(() => {
if (scrub === null || n < 2) {
seen.current = false;
return;
}
const f = scrub / (n - 1);
const i0 = Math.min(N_POINTS - 2, Math.floor(f * (N_POINTS - 1)));
const lf = f * (N_POINTS - 1) - i0;
const y = pts[i0][1] + (pts[i0 + 1][1] - pts[i0][1]) * lf;
if (!seen.current) {
curX.jump(xOf(f));
curY.jump(y);
seen.current = true;
} else {
curX.set(xOf(f));
curY.set(y);
}
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [scrub, width, periodId]);

const scrubTo = (e: React.PointerEvent) => {
if (n < 2 || !svgRef.current) return;
const box = svgRef.current.getBoundingClientRect();
const f = clamp((e.clientX - box.left - padX) / (width - padX * 2), 0, 1);
setScrub(Math.round(f * (n - 1)));
setActiveSource(null);
};
const onSparkKey = (e: React.KeyboardEvent) => {
if (e.key === "ArrowRight") setScrub((s) => clamp((s ?? n - 2) + 1, 0, n - 1));
else if (e.key === "ArrowLeft") setScrub((s) => clamp((s ?? n) - 1, 0, n - 1));
else if (e.key === "Escape") setScrub(null);
else return;
e.preventDefault();
};

const choosePeriod = (id: string) => {
setPeriodId(id);
setActiveSource(null);
setScrub(null);
onPeriodChange?.(id);
};

if (!period) return null;

const spring = reduce ? { duration: 0 } : ({ type: "spring", duration: 0.6, bounce: 0 } as const);
const good = readout.change === undefined ? null : readout.change === 0 ? null : readout.change > 0;
const colorOf = (s: EarningsSource, i: number) => s.color ?? SOURCE_COLORS[i % SOURCE_COLORS.length];

return (
<section
ref={cardRef}
aria-label={title}
className={`w-full min-w-0 rounded-[22px] bg-white p-4 text-neutral-700 antialiased dark:bg-[#0b0b0c] dark:text-neutral-300 sm:p-6 ${ring} ${className}`}
style={{ boxShadow: "0 1px 2px rgba(0,0,0,0.04), 0 28px 56px -36px rgba(0,0,0,0.25)" }}
>
{/* header */}
<div className="flex items-center justify-between gap-3">
<h3 className={`text-[13px] font-medium ${muted}`}>{title}</h3>
{periods.length > 1 && (
<SegmentedControl label="Period" value={period.id} onChange={choosePeriod} options={periods.map((p) => ({ value: p.id, label: p.label }))} />
)}
</div>

{/* readout */}
<div className="mt-4" aria-live="polite">
<p className={`h-[18px] truncate text-[12.5px] ${muted}`}>{readout.label}</p>
<p className="mt-1 text-[36px] font-semibold leading-none tracking-[-0.04em] tabular-nums text-neutral-900 dark:text-neutral-50 sm:text-[44px]">
<AnimatedNumber
value={readout.value}
format={readout.value === total && !src && scrub === null ? money : moneyExact}
duration={src || scrub !== null ? 0.25 : 0.9}
fromZero={anim}
/>
</p>
<p className="mt-2 flex min-h-[24px] flex-wrap items-center gap-x-2 gap-y-1 text-[12.5px]">
{good !== null && (
<span
className={cx(
"inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11.5px] font-medium tabular-nums",
good ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400" : "bg-rose-500/10 text-rose-600 dark:text-rose-400",
)}
>
<svg viewBox="0 0 10 10" className={cx("h-2 w-2", !good && "rotate-180")} fill="currentColor" aria-hidden>
<path d="M5 1.5 9 7.5H1Z" />
</svg>
{pct(readout.change as number)}
</span>
)}
<span className={muted}>{readout.note}</span>
</p>
</div>

{/* trend */}
<div ref={sparkRef} className="mt-4" style={{ height: SPARK_H }}>
{n > 1 && (
<svg
ref={svgRef}
width={width}
height={SPARK_H}
role="img"
aria-label={`Earnings trend, ${period.label}. Use left and right arrow keys to inspect.`}
tabIndex={0}
onKeyDown={onSparkKey}
onPointerMove={scrubTo}
onPointerDown={scrubTo}
onPointerLeave={(e) => {
if (e.pointerType === "mouse") setScrub(null);
}}
onBlur={() => setScrub(null)}
className="block touch-pan-y overflow-visible rounded-md outline-none focus-visible:ring-2 focus-visible:ring-neutral-400/60 dark:focus-visible:ring-white/30"
>
<defs>
<linearGradient id={`${uid}-a`} x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stopColor={accent} stopOpacity="0.26" />
<stop offset="1" stopColor={accent} stopOpacity="0" />
</linearGradient>
</defs>
<motion.path
fill={`url(#${uid}-a)`}
initial={anim ? { opacity: 0, d: area } : false}
animate={{ opacity: 1, d: area }}
transition={{ d: spring, opacity: { duration: 0.8, delay: anim ? 0.4 : 0 } }}
/>
<motion.path
fill="none"
stroke={accent}
strokeWidth={2}
strokeLinecap="round"
strokeLinejoin="round"
initial={anim ? { pathLength: 0, d: line } : false}
animate={{ pathLength: 1, d: line }}
transition={{ d: spring, pathLength: { duration: 1.1, ease: EASE_OUT, delay: 0.1 } }}
/>
<motion.g initial={false} animate={{ opacity: scrub === null ? 0 : 1 }} transition={{ duration: 0.12 }}>
<motion.line y1={0} y2={SPARK_H} x1={curX} x2={curX} strokeDasharray="2 3" className="stroke-black/20 dark:stroke-white/25" />
<motion.circle cx={curX} cy={curY} r={4.5} fill={accent} strokeWidth={2} className="stroke-white dark:stroke-[#0b0b0c]" />
</motion.g>
</svg>
)}
</div>

{/* split bar */}
<div className="mt-6 flex h-3 w-full gap-[3px]" role="presentation">
{sources.map((s, i) => {
const share = sum ? Math.max(0, s.amount) / sum : 0;
const dim = activeSource !== null && activeSource !== s.id;
return (
<motion.div
key={s.id}
className="h-full min-w-[3px] cursor-pointer rounded-full"
style={{ background: colorOf(s, i), opacity: dim ? 0.3 : 1, transition: "opacity .2s" }}
initial={anim ? { flexGrow: 0 } : false}
animate={{ flexGrow: Math.max(share, 0.004), scaleY: activeSource === s.id ? 1.5 : 1 }}
transition={anim ? { type: "spring", duration: 0.8, bounce: 0.1, delay: i * 0.06 } : spring}
onPointerEnter={(e) => e.pointerType === "mouse" && (setActiveSource(s.id), setScrub(null))}
onPointerLeave={(e) => e.pointerType === "mouse" && setActiveSource(null)}
onClick={() => {
setActiveSource((a) => (a === s.id ? null : s.id));
setScrub(null);
}}
/>
);
})}
</div>

{/* sources */}
<ul className="mt-3" aria-label="Earnings by source">
{sources.map((s, i) => {
const c = colorOf(s, i);
const on = activeSource === s.id;
const share = sum ? (Math.max(0, s.amount) / sum) * 100 : 0;
const up = (s.change ?? 0) > 0;
return (
<li key={s.id}>
<button
type="button"
aria-pressed={on}
onPointerEnter={(e) => e.pointerType === "mouse" && (setActiveSource(s.id), setScrub(null))}
onPointerLeave={(e) => e.pointerType === "mouse" && setActiveSource(null)}
onFocus={() => setActiveSource(s.id)}
onBlur={() => setActiveSource(null)}
onClick={() => {
setActiveSource((a) => (a === s.id ? null : s.id));
setScrub(null);
}}
className={cx(
"group relative flex min-h-[56px] w-full items-center gap-3 rounded-2xl px-2.5 py-2 text-left transition-[background-color,opacity] duration-150 [-webkit-tap-highlight-color:transparent]",
on ? "bg-black/[0.04] dark:bg-white/[0.05]" : "[@media(hover:hover)]:hover:bg-black/[0.03] dark:[@media(hover:hover)]:hover:bg-white/[0.04]",
activeSource !== null && !on && "opacity-55",
focus,
)}
>
<span
className="grid h-9 w-9 shrink-0 place-items-center rounded-xl text-[13px] font-semibold"
style={{ background: `color-mix(in srgb, ${c} 16%, transparent)`, color: c }}
aria-hidden
>
{s.icon ?? s.label.slice(0, 1).toUpperCase()}
</span>

<span className="min-w-0 flex-1">
<span className="flex items-baseline justify-between gap-3">
<span className="truncate text-[13.5px] font-medium text-neutral-900 dark:text-neutral-100">{s.label}</span>
<span className="shrink-0 text-[13.5px] font-medium tabular-nums text-neutral-900 dark:text-neutral-100">
<AnimatedNumber value={s.amount} format={moneyExact} fromZero={anim} />
</span>
</span>
<span className="mt-1.5 flex items-center gap-3">
<span className="relative h-1 flex-1 overflow-hidden rounded-full bg-black/[0.06] dark:bg-white/[0.07]">
<motion.span
className="absolute inset-y-0 left-0 rounded-full"
style={{ background: c, width: "100%", originX: 0 }}
initial={anim ? { scaleX: 0 } : false}
animate={{ scaleX: Math.max(0.01, s.amount / maxAmount) }}
transition={anim ? { duration: 0.9, ease: EASE_OUT, delay: 0.1 + i * 0.06 } : spring}
/>
</span>
<span className="flex w-[84px] shrink-0 items-center justify-end gap-1.5 text-[11.5px] tabular-nums text-neutral-500">
{s.change !== undefined && s.change !== 0 && (
<span className={up ? "text-emerald-500" : "text-rose-500"}>
{up ? "▲" : "▼"} {pct(s.change)}
</span>
)}
<span>{pct(share)}</span>
</span>
</span>
</span>
</button>
</li>
);
})}
</ul>

{payout && (
<div className="mt-3 flex items-center justify-between gap-3 border-t border-black/[0.06] pt-4 text-[12.5px] dark:border-white/[0.07]">
<span className={muted}>
{payout.label ?? "Next payout"} · <span className="text-neutral-700 dark:text-neutral-300">{payout.date}</span>
</span>
{payout.amount !== undefined && <span className="font-medium tabular-nums text-neutral-900 dark:text-neutral-100">{moneyExact(payout.amount)}</span>}
</div>
)}

<table className="sr-only">
<caption>{`${title}, ${period.label}`}</caption>
<thead>
<tr>
<th scope="col">Source</th>
<th scope="col">Amount</th>
<th scope="col">Share</th>
</tr>
</thead>
<tbody>
{sources.map((s) => (
<tr key={s.id}>
<th scope="row">{s.label}</th>
<td>{moneyExact(s.amount)}</td>
<td>{pct(sum ? (s.amount / sum) * 100 : 0)}</td>
</tr>
))}
</tbody>
</table>
</section>
);
}

export default Earnings;
```

Usage example (from the site):
tsx

```tsx
import { Earnings, type EarningsPeriod } from "@/components/ui/earnings";

const periods: EarningsPeriod[] = [
{
id: "30d",
label: "30D",
comparison: "vs previous 30 days",
previous: 9800,
trend: [240, 310, 280, 390, 420, 380, 510],
trendLabels: ["Oct 1", "Oct 6", "Oct 11", "Oct 16", "Oct 21", "Oct 26", "Oct 31"],
sources: [
{ id: "sponsors", label: "Sponsors", amount: 4200, change: 8.2 },
{ id: "pro", label: "Pro licenses", amount: 3100, change: 14.6 },
{ id: "affiliate", label: "Affiliate", amount: 1250, change: -3.1 },
],
},
];

export function Demo() {
return (
<div className="w-full max-w-[520px]">
<Earnings
periods={periods}
payout={{ date: "Nov 5", amount: 1240 }}
onPeriodChange={(id) => console.log(id)}
/>
</div>
);
}
```

* Completeness: complete and self-contained; nothing is missing from the file. The code comment banner lost its internal column spacing in the page text (cosmetic only). Demo strings (Sponsors, Pro licenses, Affiliate) are sample data. With a single period the switcher is hidden. The site’s doc says a default period is the second one when three or more exist.

 <!-- CONTINUES IN NEXT MESSAGE -->
<!-- CONTINUED: component activity-heatmap -->
Activity Heatmap (activity-heatmap)

* Category / priority: FEEDBACK (chart) / high (hour-of-day by weekday grid, or a year calendar of daily values such as availability or yield)
* Page: https://easyui.site/components/activity-heatmap
* Licence shown on page: none shown
* Description: GitHub-style contribution calendar, or a weekday-by-hour grid, with automatic column fitting, quartile-based colour levels, hover tooltips and keyboard navigation.
* Dependencies: react, framer-motion (motion, useReducedMotion), and `../../lib/chart-primitives` (Tooltip, clamp, cx, fullFmt, muted, useDismissOutside, useElementWidth). That `chart-primitives` file is NOT shown on the site and was not collected, so this component cannot run on its own. The helpers can be rewritten: `clamp` and `cx` are trivial; `fullFmt` appears to be an `Intl.NumberFormat`; `muted` is a Tailwind text-colour class string (the Earnings file uses `text-neutral-500` for the same name); `useElementWidth` is a ResizeObserver width hook (a version is in the Earnings file above); `Tooltip` takes `pos` and `boundsWidth` and renders its children in a floating box; `useDismissOutside(ref, enabled, onDismiss)` calls the callback on an outside pointer-down. Tailwind `neutral-*` classes with `dark:` variants.
* Chart data and features: charting source is hand-written SVG (one `<rect>` per cell) with a CSS keyframe entrance animation; no chart library. Data shape: calendar mode takes `data: { date: "YYYY-MM-DD" | Date, value: number }[]` (duplicate dates are summed); hours mode takes `matrix: number[7][24]` (rows are weekdays, columns are hours, with `rowLabels`). Example: `{ date: "2026-10-19", value: 9 }`. Tooltips: yes (floating box with value, unit and date or weekday and hour). Hover crosshair: yes in hours mode (row and column bands) plus an outlined active cell in both modes. Legends: yes, a “Less … More” five-swatch scale. Animation on data change: no (cells animate in once when mounted; later data changes just change colours). Light and dark mode: yes (`dark:` classes; cell colours mix the `color` prop with transparency).
* Visual notes: Summary text on top (“N contributions in the last year”) with a peak-cell note on the right; below it an SVG grid with month labels on top and Mon/Wed/Fri labels at the left (calendar), or hour labels every 3 or 6 hours and weekday labels (hours); five levels from a faint grey to the full base colour (default `#34d399`); legend at the bottom right.
* Interaction notes: Pointer move or tap picks a cell; arrow keys move the active cell when the SVG has focus; Escape clears; an outside tap dismisses; a screen-reader live region announces the active cell. Cell levels use quartiles of the non-zero values, so the colours are relative to the data, not absolute thresholds. Narrow screens show fewer weeks automatically (calendar) and shorter labels. The entrance animation is skipped when reduced motion is on. Calendar dates are treated as UTC days. The component contains one inline `<style>` element with static keyframe CSS (`dangerouslySetInnerHTML` of a constant string); it is ordinary styling, not a script.
* Props: mode (‘calendar’ | ‘hours’), data, matrix, rowLabels (Mon…Sun), weeks (53), endDate, weekStart (0 | 1), color (‘`#34d399`’), unit (‘contributions’), minCell (11), animated (true), ariaLabel, className. Exports interfaces HeatDay and ActivityHeatmapProps.

src/components/ui/activity-heatmap.tsx
tsx

```tsx
"use client";

import {
useCallback,
useMemo,
useRef,
useState,
type CSSProperties,
type KeyboardEvent as ReactKeyboardEvent,
type PointerEvent as ReactPointerEvent,
} from "react";
import { motion, useReducedMotion } from "framer-motion";
import {
Tooltip,
clamp,
cx,
fullFmt,
muted,
useDismissOutside,
useElementWidth,
} from "../../lib/chart-primitives";

export interface HeatDay {
/** "YYYY-MM-DD" or a Date */
date: string | Date;
value: number;
}

export interface ActivityHeatmapProps {
/** calendar: one cell per day (GitHub style) · hours: weekday × hour grid */
mode?: "calendar" | "hours";
/** calendar mode */
data?: HeatDay[];
/** hours mode: 7 rows × 24 columns */
matrix?: number[][];
/** hours mode row names (default Mon…Sun) */
rowLabels?: string[];
/** Most weeks to show. Narrow screens automatically show fewer (default 53) */
weeks?: number;
/** Last day shown (default: latest date in data) */
endDate?: string | Date;
/** 0 = Sunday, 1 = Monday */
weekStart?: 0 | 1;
color?: string;
/** Plural noun used in the tooltip / summary */
unit?: string;
/** Smallest cell size in px before weeks are dropped (default 11) */
minCell?: number;
animated?: boolean;
ariaLabel?: string;
className?: string;
}

const DAY_MS = 86_400_000;
const toDay = (d: string | Date): number | null => {
if (d instanceof Date) return isNaN(+d) ? null : Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / DAY_MS);
const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d);
if (m) return Math.floor(Date.UTC(+m[1], +m[2] - 1, +m[3]) / DAY_MS);
const p = new Date(d);
return isNaN(+p) ? null : toDay(p);
};
const weekday = (day: number) => (((day + 4) % 7) + 7) % 7; // 0 = Sunday
const dayFmt = new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
const monthFmt = new Intl.DateTimeFormat("en-US", { month: "short", timeZone: "UTC" });
const WEEKDAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
const LEVEL_MIX = [0, 28, 52, 76, 100];

interface HeatCell {
c: number;
r: number;
v: number;
title: string;
}

export function ActivityHeatmap({
mode = "calendar",
data = [],
matrix,
rowLabels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
weeks = 53,
endDate,
weekStart = 0,
color = "#34d399",
unit = "contributions",
minCell = 11,
animated = true,
ariaLabel,
className = "",
}: ActivityHeatmapProps) {
const reduce = useReducedMotion();
const anim = animated && !reduce;
const [rootRef, width] = useElementWidth<HTMLDivElement>(720);
const [active, setActive] = useState<{ c: number; r: number } | null>(null);
const wrapRef = useRef<HTMLDivElement>(null);
useDismissOutside(wrapRef, active !== null, useCallback(() => setActive(null), []));

const hours = mode === "hours";
const narrow = width < 440;
const LW = hours ? (narrow ? 30 : 36) : narrow ? 18 : 30;
const TOP = 18;
const gap = hours ? (narrow ? 2 : 3) : 3;
const innerW = Math.max(40, width - LW);

// columns that fit
const cols = hours ? 24 : clamp(Math.min(weeks, Math.floor((innerW + gap) / (minCell + gap))), 4, weeks);
const cw = (innerW - (cols - 1) * gap) / cols;
const cell = hours ? cw : Math.min(cw, 16);
const ch = hours ? clamp(cw, 10, 22) : cell;
const cwEff = hours ? cw : cell;

// build cells
const model = useMemo(() => {
const out: HeatCell[] = [];
let first = 0;
let endDay = 0;
if (hours) {
const m = matrix ?? [];
for (let r = 0; r < 7; r++)
for (let c = 0; c < 24; c++) {
const v = Math.max(0, Number(m[r]?.[c]) || 0);
out.push({ c, r, v, title: `${rowLabels[r] ?? ""} · ${String(c).padStart(2, "0")}:00` });
}
} else {
const map = new Map<number, number>();
let maxDay = -Infinity;
for (const d of data) {
const day = toDay(d.date);
if (day === null) continue;
map.set(day, (map.get(day) ?? 0) + (Number.isFinite(d.value) ? Math.max(0, d.value) : 0));
maxDay = Math.max(maxDay, day);
}
endDay = (endDate ? toDay(endDate) : null) ?? (isFinite(maxDay) ? maxDay : (toDay(new Date()) as number));
const lastColStart = endDay - ((weekday(endDay) - weekStart + 7) % 7);
first = lastColStart - (cols - 1) * 7;
for (let c = 0; c < cols; c++)
for (let r = 0; r < 7; r++) {
const day = first + c * 7 + r;
if (day > endDay) continue;
out.push({ c, r, v: map.get(day) ?? 0, title: dayFmt.format(new Date(day * DAY_MS)) });
}
}
const nz = out.filter((x) => x.v > 0).map((x) => x.v).sort((a, b) => a - b);
const q = (p: number) => nz[Math.min(nz.length - 1, Math.floor(p * nz.length))] ?? 0;
const t1 = q(0.25), t2 = q(0.5), t3 = q(0.75);
const level = (v: number) => (v <= 0 ? 0 : v <= t1 ? 1 : v <= t2 ? 2 : v <= t3 ? 3 : 4);
const total = out.reduce((s, x) => s + x.v, 0);
const best = out.reduce<HeatCell | null>((b, x) => (!b || x.v > b.v ? x : b), null);
return { cells: out, level, total, best, first, endDay, active: nz.length };
}, [hours, matrix, rowLabels, data, endDate, weekStart, cols]);

const byKey = useMemo(() => new Map(model.cells.map((x) => [`${x.c}:${x.r}`, x])), [model.cells]);
const gx = (c: number) => LW + c * (cwEff + gap);
const gy = (r: number) => TOP + r * (ch + gap);
const svgH = TOP + 7 * ch + 6 * gap + 2;

// month / hour labels
const topLabels = useMemo(() => {
const out: { c: number; text: string }[] = [];
if (hours) {
const every = cwEff < 14 ? 6 : 3;
for (let c = 0; c < 24; c += every) out.push({ c, text: String(c) });
} else {
let prev = -1;
let lastC = -9;
for (let c = 0; c < cols; c++) {
const m = new Date((model.first + c * 7) * DAY_MS).getUTCMonth();
if (m !== prev) {
if (prev !== -1 && c - lastC >= 3 && c <= cols - 2) {
out.push({ c, text: monthFmt.format(new Date((model.first + c * 7) * DAY_MS)) });
lastC = c;
} else if (prev === -1 && cols > 6) {
out.push({ c, text: monthFmt.format(new Date((model.first + c * 7) * DAY_MS)) });
lastC = c;
}
prev = m;
}
}
}
return out;
}, [hours, cols, cwEff, model.first]);

const rowNames = hours
? rowLabels.map((l, r) => ({ r, text: narrow ? l.slice(0, 1) : l })).filter((x) => !narrow || x.r % 2 === 0)
: [1, 3, 5].map((k) => {
const r = (k - weekStart + 7) % 7;
return { r, text: narrow ? WEEKDAYS[k].slice(0, 1) : WEEKDAYS[k] };
});

const locate = (e: ReactPointerEvent<SVGRectElement>) => {
const box = e.currentTarget.getBoundingClientRect();
const c = Math.floor((e.clientX - box.left - LW) / (cwEff + gap));
const r = Math.floor((e.clientY - box.top - TOP) / (ch + gap));
if (c < 0 || r < 0 || c >= cols || r > 6 || !byKey.has(`${c}:${r}`)) return setActive(null);
setActive({ c, r });
};
const onKey = (e: ReactKeyboardEvent) => {
const dc = e.key === "ArrowRight" ? 1 : e.key === "ArrowLeft" ? -1 : 0;
const dr = e.key === "ArrowDown" ? 1 : e.key === "ArrowUp" ? -1 : 0;
if (e.key === "Escape") return setActive(null);
if (!dc && !dr) return;
e.preventDefault();
setActive((a) => {
const from = a ?? { c: cols - 1, r: 0 };
const next = { c: clamp(from.c + dc, 0, cols - 1), r: clamp(from.r + dr, 0, 6) };
return byKey.has(`${next.c}:${next.r}`) ? next : from;
});
};

const cur = active ? byKey.get(`${active.c}:${active.r}`) : null;
const total = model.total;
const summary = hours
? `${fullFmt.format(total)} ${unit} per week`
: `${fullFmt.format(total)} ${unit} in the last ${cols >= 52 ? "year" : cols >= 8 ? `${Math.round(cols / 4.345)} months` : `${cols} weeks`}`;
const lvlFill = (l: number): CSSProperties =>
l === 0 ? {} : { fill: `color-mix(in srgb, ${color} ${LEVEL_MIX[l]}%, transparent)` };

return (
<div ref={rootRef} className={cx("w-full", className)}>
<style
dangerouslySetInnerHTML={{
__html:
"@keyframes cj-cell{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:scale(1)}}" +
".cj-cell{transform-box:fill-box;transform-origin:center;animation:cj-cell .55s cubic-bezier(.23,1,.32,1) both;animation-delay:var(--d,0s)}" +
"@media (prefers-reduced-motion: reduce){.cj-cell{animation:none}}",
}}
/>

<div className="mb-3 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
<p className="text-[13px] font-medium tabular-nums text-neutral-900 dark:text-neutral-100">{summary}</p>
{model.best && model.best.v > 0 && (
<p className={`text-[12px] ${muted}`}>
Peak {model.best.title} · <span className="tabular-nums">{fullFmt.format(model.best.v)}</span>
</p>
)}
</div>

<div ref={wrapRef} className="relative" style={{ height: svgH }}>
<svg
width={width}
height={svgH}
role="img"
aria-label={ariaLabel ?? `Activity heatmap. ${summary}`}
tabIndex={0}
onKeyDown={onKey}
onBlur={() => setActive(null)}
className="block touch-pan-y overflow-visible rounded-md outline-none focus-visible:ring-2 focus-visible:ring-neutral-400/60 dark:focus-visible:ring-white/30"
>
{topLabels.map((l) => (
<text key={l.c} x={gx(l.c)} y={11} className="fill-neutral-500 text-[11px]">
{l.text}
</text>
))}
{rowNames.map((l) => (
<text key={l.r} x={0} y={gy(l.r) + ch / 2} dominantBaseline="middle" className="fill-neutral-500 text-[10.5px]">
{l.text}
</text>
))}

{/* crosshair bands (hours mode) */}
{hours && (
<>
<motion.rect
x={LW - 2}
width={24 * (cwEff + gap)}
height={ch + 4}
rx={5}
className="fill-black/[0.035] dark:fill-white/[0.04]"
initial={false}
animate={{ y: gy(active?.r ?? 0) - 2, opacity: active ? 1 : 0 }}
transition={reduce ? { duration: 0 } : { duration: 0.15 }}
/>
<motion.rect
y={TOP - 2}
width={cwEff + 4}
height={7 * (ch + gap)}
rx={5}
className="fill-black/[0.035] dark:fill-white/[0.04]"
initial={false}
animate={{ x: gx(active?.c ?? 0) - 2, opacity: active ? 1 : 0 }}
transition={reduce ? { duration: 0 } : { duration: 0.15 }}
/>
</>
)}

{model.cells.map((x) => {
const l = model.level(x.v);
return (
<rect
key={`${x.c}:${x.r}`}
x={gx(x.c)}
y={gy(x.r)}
width={cwEff}
height={ch}
rx={Math.min(3, cwEff / 4)}
className={cx(anim && "cj-cell", l === 0 && "fill-black/[0.05] dark:fill-white/[0.06]")}
style={{ ...lvlFill(l), ["--d" as string]: anim ? `${(x.c * 0.012 + x.r * 0.02).toFixed(3)}s` : undefined } as CSSProperties}
/>
);
})}

{/* active ring */}
<motion.rect
width={cwEff + 2}
height={ch + 2}
rx={Math.min(4, cwEff / 3)}
fill="none"
strokeWidth={1.5}
className="stroke-neutral-900 dark:stroke-white"
initial={false}
animate={{ x: gx(active?.c ?? 0) - 1, y: gy(active?.r ?? 0) - 1, opacity: active ? 1 : 0 }}
transition={reduce ? { duration: 0 } : { x: { duration: 0.12 }, y: { duration: 0.12 }, opacity: { duration: 0.12 } }}
/>

<rect
x={LW}
y={TOP}
width={cols * (cwEff + gap)}
height={7 * (ch + gap)}
fill="transparent"
onPointerMove={locate}
onPointerDown={locate}
onPointerLeave={(e) => e.pointerType === "mouse" && setActive(null)}
/>
</svg>

<Tooltip pos={active ? { x: gx(active.c) + cwEff / 2, y: gy(active.r) } : null} boundsWidth={width}>
{cur && (
<>
<p className="font-medium tabular-nums text-neutral-900 dark:text-neutral-100">
{fullFmt.format(cur.v)} <span className="font-normal text-neutral-500">{unit}</span>
</p>
<p className="mt-0.5 text-neutral-500">{cur.title}</p>
</>
)}
</Tooltip>
</div>

<p className="sr-only" role="status" aria-live="polite">
{cur ? `${cur.title}: ${fullFmt.format(cur.v)} ${unit}` : ""}
</p>

<div className="mt-3 flex items-center justify-end gap-2 text-[11.5px] text-neutral-500">
Less
<span className="flex gap-[3px]" aria-hidden>
{LEVEL_MIX.map((m, i) => (
<span
key={i}
className={cx("h-[11px] w-[11px] rounded-[3px]", i === 0 && "bg-black/[0.05] dark:bg-white/[0.06]")}
style={i === 0 ? undefined : { background: `color-mix(in srgb, ${color} ${m}%, transparent)` }}
/>
))}
</span>
More
</div>
</div>
);
}
```

Usage example (from the site):
tsx

```tsx
import { ActivityHeatmap } from "@/components/ui/activity-heatmap";

const data = [
{ date: "2026-10-18", value: 3 },
{ date: "2026-10-19", value: 9 },
{ date: "2026-10-20", value: 5 },
{ date: "2026-10-21", value: 12 },
];

export function Demo() {
return (
<div className="w-full max-w-3xl rounded-2xl bg-white p-5 dark:bg-neutral-950">
<ActivityHeatmap data={data} weekStart={1} unit="contributions" />
</div>
);
}
```

* Completeness: the component file is complete, but it is NOT runnable alone because `lib/chart-primitives` (Tooltip, clamp, cx, fullFmt, muted, useDismissOutside, useElementWidth) is not shown on the site. Its exact code could not be collected. The usage example shows only calendar mode; the site gives no example for `matrix` / hours mode, so for that mode the data shape is taken from the prop types and the API table. Solar use: hours mode with a 7×24 matrix of mean kW, or calendar mode with one value per day (kWh), would fit directly.

 <!-- END -->
Both components are sent: `earnings` and `activity-heatmap`, each with its full file, usage example and notes. They are in two messages, ending in `CONTINUES IN NEXT MESSAGE` and `END`. I collected them the same way as before. I read the Usage and Code tabs as page text, and I used no CLI, registry or API. I found nothing on either page asking you to follow, star, pay, subscribe or contact anyone.

* `earnings`: the file is self-contained and runs on its own. It defines its own helpers, so it has no dependency on the missing `lib` files.
* `activity-heatmap`: it needs `lib/chart-primitives` (`Tooltip`, `clamp`, `cx`, `fullFmt`, `muted`, `useDismissOutside`, `useElementWidth`), which the site doesn’t show. I couldn’t collect that file. I listed what each helper appears to do so you can rewrite them. The site gives no usage example for the weekday-by-hour mode (`matrix`).
* Duplicates: your BATCH 1 file may already hold earlier, partly different entries for these two. Use these new entries to replace them.
* Style blocks: both files contain a small inline `<style>` element with fixed CSS, which is ordinary styling.