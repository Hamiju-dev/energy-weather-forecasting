BATCH 2 of 6
stat-card

* Category / priority: Feedback / A (KPI tile, also exports `StatGrid`)
* Page URL: https://easyui.site/components/stat-card
* Licence shown on page: none
* Description (from site): “A KPI tile with a count-up headline number, a direction-aware delta pill, and a scrubable sparkline. Pair several with StatGrid for a responsive metrics row that works from phones to wide dashboards.”
* Dependencies: `react`, `framer-motion` (`animate`, `motion`, `useMotionValue`, `useReducedMotion`, `useSpring`, `useTransform`). It also imports two lib files that are not shown anywhere on the site and were not collected: `../../lib/chart-primitives` (`CHART_COLORS, EASE_OUT, clamp, cx, defaultFormat, focus, muted, ring, useDismissOutside, useElementWidth`) and `../../lib/dashboard-chart-utils` (`monotonePath, pctText`). Note that `earnings.tsx` (BATCH 1) defines its own `monotonePath`, `clamp`, `cx`, `focus`, `muted`, `ring`, `useElementWidth` and `EASE_OUT`, so it shows what several of these helpers look like.
* Charting source: hand-written SVG sparkline (monotone cubic path). No chart library.
* Data prop shape: `trend: number[]` (oldest to newest), `trendLabels?: string[]`, `value: number`, `previous?: number` or `delta?: number` (percent). Example from the demo code:

tsx

```tsx
const revenue = [41200, 42100, 41800, 43600, 44200, 45800, 47100];
<StatCard label="Revenue" value={revenue[revenue.length - 1]} previous={revenue[0]} trend={revenue} period="Last 7 days" />
<StatCard label="Churn" value={2.4} previous={2.9} trend={[2.9, 2.8, 2.7, 2.6, 2.5, 2.4]} goodWhen="down" format={(n) => `${n.toFixed(1)}%`} period="Last 6 weeks" color="#ff6b8b" />
```

* Chart features:
   * Tooltip: no floating tooltip. The headline number and the caption under it switch to the scrubbed point and its label.
   * Hover crosshair: yes (dashed line plus dot, with Left and Right arrows, and Escape to clear).
   * Legend: no.
   * Animation on data change: on mount the number counts up from 0 and the line draws, and the latest point pulses. The headline follows the scrubber with a 0.22 s tween. A new `trend` does not morph, it redraws.
   * Light and dark: yes (`dark:` classes, dark card hard-coded `#0b0b0c`).
   * `goodWhen="down"` flips the green/red meaning, which suits metrics such as error rate or churn.
* Visual notes (dark demo): four tiles side by side in a dark card. Each has a small grey label top left, a small green delta pill top right, a large white number, a grey caption (“Last 14 days”), and a coloured sparkline with a soft gradient fill along the bottom edge. The four demo tiles use blue/indigo, teal, amber and pink lines ($45,896, 10,067, 3.26%, 1.93%).
* Interaction notes: moving across the tile scrubs the sparkline and the number follows. The tile is focusable (`tabIndex=0`) and has a visible hover ring. Tap outside clears it.
* Props / variants: `label`, `value`, `trend`, `trendLabels`, `previous`, `delta`, `goodWhen` (“up” | “down”), `period`, `format`, `color`, `animated`, `className`. `StatGrid` takes `children` and `className`, laid out as `repeat(auto-fit, minmax(min(100%, 210px), 1fr))`.
* Usage example (from site):

tsx

```tsx
import { StatCard, StatGrid } from "@/components/ui/stat-card";

const revenue = [41200, 42100, 41800, 43600, 44200, 45800, 47100];

export function Demo() {
return (
<StatGrid>
<StatCard
label="Revenue"
value={revenue[revenue.length - 1]}
previous={revenue[0]}
trend={revenue}
period="Last 7 days"
/>
<StatCard
label="Churn"
value={2.4}
previous={2.9}
trend={[2.9, 2.8, 2.7, 2.6, 2.5, 2.4]}
goodWhen="down"
format={(n) => `${n.toFixed(1)}%`}
period="Last 6 weeks"
color="#ff6b8b"
/>
</StatGrid>
);
}
```

* Completeness: the file shown is complete (ends after `StatGrid`). Not usable on its own because both lib files are missing. Nothing removed. Suspicious text: none.
* Files:

src/components/ui/stat-card.tsx
tsx

```tsx
"use client";

import React, {
type ReactNode,
useCallback,
useEffect,
useId,
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
import {
CHART_COLORS,
EASE_OUT,
clamp,
cx,
defaultFormat,
focus,
muted,
ring,
useDismissOutside,
useElementWidth,
} from "../../lib/chart-primitives";
import { monotonePath, pctText } from "../../lib/dashboard-chart-utils";

/* -------------------------------------------------------------------------- */
/* StatCard / StatGrid */
/* */
/* KPI tiles with a count-up value, a delta pill, and a scrubable sparkline. */
/* Hand-written SVG · light and dark · measures its own container. */
/* -------------------------------------------------------------------------- */

export interface StatCardProps {
label: string;
/** The headline number (usually the latest point of `trend`) */
value: number;
/** Points for the sparkline, oldest → newest */
trend: number[];
/** Names for each trend point, shown while scrubbing (e.g. "Oct 12") */
trendLabels?: string[];
/** Previous-period value → the delta is computed from it */
previous?: number;
/** …or give the delta in percent directly */
delta?: number;
/** Which direction is good news. Use "down" for churn, latency, costs */
goodWhen?: "up" | "down";
/** Text under the number, e.g. "vs last 30 days" */
period?: string;
format?: (n: number) => string;
color?: string;
animated?: boolean;
className?: string;
}

export function StatCard({
label,
value,
trend,
trendLabels,
previous,
delta,
goodWhen = "up",
period = "vs previous period",
format = defaultFormat,
color = CHART_COLORS[0],
animated = true,
className = "",
}: StatCardProps) {
const reduce = useReducedMotion();
const anim = animated && !reduce;
const uid = useId().replace(/:/g, "");
const [boxRef, width] = useElementWidth<HTMLDivElement>(220);
const svgRef = useRef<SVGSVGElement>(null);
const cardRef = useRef<HTMLDivElement>(null);
const [active, setActive] = useState<number | null>(null);
useDismissOutside(cardRef, active !== null, useCallback(() => setActive(null), []));

const n = trend.length;
const H = 52, padX = 0, padT = 8, padB = 6;
const min = n ? Math.min(...trend) : 0;
const span = (n ? Math.max(...trend) : 1) - min || 1;
const stepX = n > 1 ? (width - padX * 2) / (n - 1) : 0;
const pts = trend.map((v, i) => [padX + i * stepX, padT + (1 - (v - min) / span) * (H - padT - padB)] as [number, number]);
const line = monotonePath(pts);
const area = n > 1 ? `${line}L${pts[n - 1][0].toFixed(2)} ${H}L${pts[0][0].toFixed(2)} ${H}Z` : "";

const pct =
delta ??
(previous !== undefined && previous !== 0
? ((value - previous) / Math.abs(previous)) * 100
: n > 1 && trend[0] !== 0
? ((trend[n - 1] - trend[0]) / Math.abs(trend[0])) * 100
: 0);
const rounded = Math.round(pct * 10) / 10;
const good = rounded === 0 ? null : goodWhen === "up" ? rounded > 0 : rounded < 0;

/* number: counts up on mount, follows the scrubber afterwards */
const fmt = useRef(format);
fmt.current = format;
const shown = useMotionValue(anim ? 0 : value);
const text = useTransform(shown, (v) => fmt.current(v));
const mounted = useRef(false);
useEffect(() => {
const target = active === null ? value : trend[active];
const intro = !mounted.current;
mounted.current = true;
const c = animate(shown, target, { duration: reduce ? 0 : intro ? 1.1 : 0.22, ease: EASE_OUT });
return () => c.stop();
}, [active, value, trend, shown, reduce]);

/* scrub cursor */
const curX = useSpring(0, { stiffness: 600, damping: 44, mass: 0.5 });
const curY = useSpring(0, { stiffness: 600, damping: 44, mass: 0.5 });
const seen = useRef(false);
useEffect(() => {
if (active === null || !pts[active]) {
seen.current = false;
return;
}
const [px, py] = pts[active];
if (!seen.current) {
curX.jump(px);
curY.jump(py);
seen.current = true;
} else {
curX.set(px);
curY.set(py);
}
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [active, width, curX, curY]);

const move = (e: React.PointerEvent) => {
if (n < 2 || !svgRef.current) return;
const box = svgRef.current.getBoundingClientRect();
setActive(clamp(Math.round((e.clientX - box.left - padX) / stepX), 0, n - 1));
};
const onKey = (e: React.KeyboardEvent) => {
if (e.key === "ArrowRight") setActive((a) => clamp((a ?? n - 2) + 1, 0, n - 1));
else if (e.key === "ArrowLeft") setActive((a) => clamp((a ?? n) - 1, 0, n - 1));
else if (e.key === "Escape") setActive(null);
else return;
e.preventDefault();
};

const sub = active === null ? period : (trendLabels?.[active] ?? `Point ${active + 1}`);

return (
<div
ref={cardRef}
tabIndex={0}
role="group"
aria-label={`${label}: ${format(value)}, ${rounded > 0 ? "up" : rounded < 0 ? "down" : "unchanged"} ${pctText(Math.abs(rounded))}`}
onPointerMove={move}
onPointerDown={move}
onPointerLeave={(e) => e.pointerType === "mouse" && setActive(null)}
onKeyDown={onKey}
onBlur={() => setActive(null)}
className={`group relative min-w-0 select-none overflow-hidden rounded-2xl bg-white pt-4 text-neutral-700 transition-[box-shadow] duration-200 dark:bg-[#0b0b0c] dark:text-neutral-300 ${ring} ${focus} [@media(hover:hover)]:hover:ring-black/15 dark:[@media(hover:hover)]:hover:ring-white/15 ${className}`}
style={{ boxShadow: "0 1px 2px rgba(0,0,0,0.04), 0 18px 36px -28px rgba(0,0,0,0.2)" }}
>
<div className="flex items-start justify-between gap-3 px-4">
<p className={`truncate text-[12.5px] ${muted}`}>{label}</p>
<span
className={cx(
"inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[11.5px] font-medium tabular-nums",
good === null && "bg-black/[0.05] text-neutral-500 dark:bg-white/[0.06]",
good === true && "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
good === false && "bg-rose-500/10 text-rose-600 dark:text-rose-400",
)}
>
{rounded !== 0 && (
<svg viewBox="0 0 10 10" className={cx("h-2 w-2", rounded < 0 && "rotate-180")} fill="currentColor" aria-hidden>
<path d="M5 1.5 9 7.5H1Z" />
</svg>
)}
{pctText(Math.abs(rounded))}
</span>
</div>

<p className="mt-1.5 px-4 text-[28px] font-semibold leading-none tracking-[-0.035em] tabular-nums text-neutral-900 dark:text-neutral-50 sm:text-[30px]">
<motion.span>{text}</motion.span>
</p>
<p className={`mt-1.5 truncate px-4 text-[12px] ${muted}`}>{sub}</p>

<div ref={boxRef} className="mt-3" style={{ height: H }}>
{n > 1 && (
<svg
ref={svgRef}
width={width}
height={H}
role="img"
aria-label={`${label} trend from ${format(trend[0])} to ${format(trend[n - 1])}`}
className="block overflow-visible"
>
<defs>
<linearGradient id={`${uid}-g`} x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stopColor={color} stopOpacity="0.28" />
<stop offset="1" stopColor={color} stopOpacity="0" />
</linearGradient>
</defs>
<motion.path
d={area}
fill={`url(#${uid}-g)`}
initial={anim ? { opacity: 0 } : false}
animate={{ opacity: 1 }}
transition={{ duration: 0.8, delay: 0.5 }}
/>
<motion.path
d={line}
fill="none"
stroke={color}
strokeWidth={2}
strokeLinecap="round"
strokeLinejoin="round"
initial={anim ? { pathLength: 0 } : false}
animate={{ pathLength: 1 }}
transition={{ duration: 1.1, ease: EASE_OUT, delay: 0.15 }}
/>
{/* latest point */}
<g style={{ opacity: active === null ? 1 : 0, transition: "opacity .15s" }}>
{anim && (
<motion.circle
cx={pts[n - 1][0]}
cy={pts[n - 1][1]}
r={3.5}
fill={color}
style={{ transformBox: "fill-box", transformOrigin: "center" }}
animate={{ scale: [1, 2.8], opacity: [0.4, 0] }}
transition={{ repeat: Infinity, duration: 1.8, ease: "easeOut" }}
/>
)}
<circle cx={pts[n - 1][0]} cy={pts[n - 1][1]} r={3.5} fill={color} />
</g>
{/* scrubber */}
<motion.g initial={false} animate={{ opacity: active === null ? 0 : 1 }} transition={{ duration: 0.12 }}>
<motion.line y1={0} y2={H} x1={curX} x2={curX} className="stroke-black/15 dark:stroke-white/20" strokeDasharray="2 3" />
<motion.circle cx={curX} cy={curY} r={4.5} fill={color} className="stroke-white dark:stroke-[#0b0b0c]" strokeWidth={2} />
</motion.g>
</svg>
)}
</div>
<p className="sr-only" role="status" aria-live="polite">
{active !== null ? `${trendLabels?.[active] ?? `Point ${active + 1}`}: ${format(trend[active])}` : ""}
</p>
</div>
);
}

export function StatGrid({ children, className = "" }: { children: ReactNode; className?: string }) {
return (
<div
className={`grid gap-3 sm:gap-4 ${className}`}
style={{ gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 210px), 1fr))" }}
>
{children}
</div>
);
}
```

animated-number

* Category / priority: Motion / B (number ticker; the site names it “Animated Number Morph”)
* Page URL: https://easyui.site/components/animated-number
* Licence shown on page: none
* Description (from site): “An Apple-grade smooth rolling digit counter that independently morphs individual numerical columns with physics-based springs, locale commas, currencies, and compact notation.”
* Dependencies: `react`, `framer-motion` (`motion`, `useSpring`, `useTransform`), `../../lib/cn` is not used; it imports `{ cn } from '../../lib/utils'` (not shown on the site, see GLOBALS G4). No other component or lib file.
* Charting source: not a chart. It is DOM: one clipped column of digits 0 to 9 per character, moved with a spring (`y: -value*10%`). No SVG, canvas or library.
* Data prop shape: a single number: `value: number`. Example from the demo code: `const [revenue, setRevenue] = useState(12450); <AnimatedNumber value={revenue} prefix="$" useGrouping />`.
* Chart features: tooltip: no. Hover crosshair: no. Legend: no. Animation on data change: yes, each digit column springs independently when `value` changes (defaults stiffness 170, damping 22, mass 0.6). Light and dark: the text colour is hard-coded `text-[#FAFAFA]` (near white), so it only reads on dark backgrounds unless you pass a `className` that overrides the colour.
* Visual notes (dark demo): a dark card with a tiny uppercase caption above a large monospace “$12,450” in white, and a small green note below it. A second dark panel under it holds buttons labelled “+$1,000”, “-$500”, “Randomize” and “Reset” which change the number.
* Interaction notes: none built in. The number animates whenever the `value` prop changes. Non-digit characters (commas, dots, minus, K/M/B letters) are rendered as plain text. It exposes `aria-label` with the formatted value.
* Props / variants: `value`, `decimals` (0), `prefix`, `suffix`, `stiffness`, `damping`, `mass`, `useGrouping` (true), `compact` (false), `className`.
* Docs mismatch: the Usage tab’s “Import Component” line shows `import { AnimatedNumberMorph } ...`, but the code and the example code export and import `AnimatedNumber`. Use `AnimatedNumber`.
* Usage example (from site):

tsx

```tsx
import { AnimatedNumber } from "@/components/ui/animated-number";

export function Demo() {
const [revenue, setRevenue] = useState(12450);

return (
<div className="text-3xl font-bold">
<AnimatedNumber value={revenue} prefix="$" useGrouping />
</div>
);
}
```

(The site’s example omits the `useState` import.)

* Completeness: complete, ends with the closing of `AnimatedNumber`. Nothing removed. Suspicious text: none.
* Files:

src/components/ui/animated-number.tsx
tsx

```tsx
'use client';

import React, { useEffect } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';
import { cn } from '../../lib/utils';

export interface AnimatedNumberProps {
/** Numeric value to animate to */
value: number;
/** Number of decimal places (default: 0) */
decimals?: number;
/** Prepend text or currency symbol (e.g. "$", "+") */
prefix?: string;
/** Append text (e.g. "%", " users", "ms") */
suffix?: string;
/** Spring physics stiffness */
stiffness?: number;
/** Spring physics damping */
damping?: number;
/** Mass of spring */
mass?: number;
/** Format as locale string (e.g. "1,250") */
useGrouping?: boolean;
/** Compact notation (e.g. 1.2M, 45K) */
compact?: boolean;
/** Custom class name */
className?: string;
}

// Single Digit Rolling Column
const DigitColumn: React.FC<{
digit: string;
stiffness?: number;
damping?: number;
mass?: number;
}> = ({ digit, stiffness = 160, damping = 18, mass = 0.8 }) => {
const isNumber = !isNaN(parseInt(digit, 10));
const numValue = isNumber ? parseInt(digit, 10) : 0;

const spring = useSpring(numValue, {
stiffness,
damping,
mass,
});

const y = useTransform(spring, (current) => `-${current * 10}%`);

useEffect(() => {
spring.set(numValue);
}, [spring, numValue]);

if (!isNumber) {
return <span className="inline-block">{digit}</span>;
}

return (
<div className="inline-block relative overflow-hidden h-[1.15em] leading-[1.15em] w-[0.58em] text-center">
<motion.div
style={{ y }}
className="flex flex-col select-none"
>
{[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => (
<div key={n} className="h-[1.15em] flex items-center justify-center">
{n}
</div>
))}
</motion.div>
</div>
);
};

export const AnimatedNumber: React.FC<AnimatedNumberProps> = ({
value,
decimals = 0,
prefix = '',
suffix = '',
stiffness = 170,
damping = 22,
mass = 0.6,
useGrouping = true,
compact = false,
className,
}) => {
const formatNumber = (val: number): string => {
if (compact) {
const formatter = new Intl.NumberFormat('en-US', {
notation: 'compact',
maximumFractionDigits: decimals,
minimumFractionDigits: decimals,
});
return formatter.format(val);
}

const fixed = Math.abs(val).toFixed(decimals);
const [intPart, decPart] = fixed.split('.');

let formattedInt = intPart;
if (useGrouping) {
formattedInt = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

const sign = val < 0 ? '-' : '';
return decPart !== undefined ? `${sign}${formattedInt}.${decPart}` : `${sign}${formattedInt}`;
};

const formattedStr = formatNumber(value);
const chars = formattedStr.split('');

return (
<span
className={cn(
'inline-flex items-baseline font-mono tracking-tight text-[#FAFAFA] select-none',
className
)}
aria-label={`${prefix}${formattedStr}${suffix}`}
>
{prefix && <span className="mr-0.5">{prefix}</span>}
<span className="inline-flex items-baseline overflow-hidden">
{chars.map((char, index) => (
<DigitColumn
key={`${index}-${char === ',' || char === '.' || char === '-' ? char : 'num'}`}
digit={char}
stiffness={stiffness}
damping={damping}
mass={mass}
/>
))}
</span>
{suffix && <span className="ml-0.5">{suffix}</span>}
</span>
);
};
```

A correction to the Dependencies line above: it contains a stray clause (“`../../lib/cn` is not used”). The component imports only `cn` from `../../lib/utils`, and nothing else.
torque-dial

* Category / priority: Motion / B (gauge or dial; it is also a controlled input)
* Page URL: https://easyui.site/components/torque-dial
* Licence shown on page: none
* Description (from site): “A rotational control dial with realistic physical angular momentum, velocity tracking, and exponential friction deceleration.”
* Dependencies: `react`, `framer-motion` (`motion`), `../../lib/utils` (`cn`), `../../lib/motion-tokens` (`motionTransitions.springSnappy`, see GLOBALS G5). Colours are hard-coded hex (`#1F1F1F`, `#3B82F6`, `#141414`, `#0E0E0E`, `#FAFAFA`, `#6B6B6B`), so it is dark-only.
* Charting source: hand-written SVG: a 270° arc track plus a progress arc drawn with `strokeDasharray` and `strokeDashoffset`, and a rotating knob `div`. No library.
* Data prop shape: a single controlled number: `value`, `min`, `max`, `step`, `onChange(value)`. Example from the demo code: `const [gain, setGain] = useState(48); <TorqueDial value={gain} onChange={setGain} min={0} max={100} unit="%" label="Gain Level" />`.
* Chart features: tooltip: no (the current value is printed under the dial). Hover crosshair: no. Legend: no. Animation on data change: the arc and knob spring with `springSnappy` while not dragging. Light and dark: dark only, hard-coded colours.
* Visual notes (dark demo): a dark rounded card with a round dial about 120 px across. A thin blue arc fills clockwise from the lower left. Inside is a dark knob with a blue notch near the top and a small ring at the centre. Under the dial are the value (“48%” in monospace), the label in small grey text, and a hint line “Click and drag or use mouse wheel to rotate dial with physical momentum”.
* Interaction notes: drag around the centre to rotate, and releasing with velocity (above 0.4°) coasts with 0.92 friction per frame. The mouse wheel changes the value by `step`. Arrow keys change by `step`, Home and End jump to min and max, and double-click resets to the midpoint. It has `role="slider"` with `aria-valuemin`, `aria-valuemax` and `aria-valuenow`.
* Props / variants: `value`, `min` (0), `max` (100), `step` (1), `onChange`, `onChangeEnd`, `label`, `showValue` (true), `size` (120), `disabled`, `momentum` (true), `unit`, `className`.
* Usage example (from site):

tsx

```tsx
import { useState } from "react";
import { TorqueDial } from "@/components/ui/torque-dial";

export function Demo() {
const [gain, setGain] = useState(48);

return (
<div className="p-8 flex items-center justify-center bg-[#090909] rounded-2xl border border-[#1F1F1F]">
<TorqueDial
value={gain}
onChange={setGain}
min={0}
max={100}
unit="%"
label="Gain Level"
/>
</div>
);
}
```

* Completeness: complete, ends with the closing of `TorqueDial`. Nothing removed. Suspicious text: none.
* Files:

src/components/ui/torque-dial.tsx
tsx

```tsx
'use client';

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';
import { motionTransitions } from '../../lib/motion-tokens';

export interface TorqueDialProps {
/** Current numerical value. */
value: number;
/** Minimum selectable value. Default is 0. */
min?: number;
/** Maximum selectable value. Default is 100. */
max?: number;
/** Step increment. Default is 1. */
step?: number;
/** Change callback. */
onChange: (value: number) => void;
/** End of interaction / release callback. */
onChangeEnd?: () => void;
/** Accessible label. Default is 'Dial control'. */
label?: string;
/** Render numeric value at center or below. Default is true. */
showValue?: boolean;
/** Sizing diameter in pixels. Default is 120. */
size?: number;
/** Disables interaction. */
disabled?: boolean;
/** Apply realistic angular release momentum. Default is true. */
momentum?: boolean;
/** Custom unit or suffix (e.g., '°', '%', 'dB'). */
unit?: string;
/** Custom CSS class names. */
className?: string;
}

export const TorqueDial: React.FC<TorqueDialProps> = ({
value,
min = 0,
max = 100,
step = 1,
onChange,
onChangeEnd,
label = 'Dial control',
showValue = true,
size = 120,
disabled = false,
momentum = true,
unit = '',
className,
}) => {
const [isDragging, setIsDragging] = useState(false);
const dialRef = useRef<HTMLDivElement>(null);
const lastAngleRef = useRef<number>(0);
const velocityRef = useRef<number>(0);
const animFrameRef = useRef<number | null>(null);
const valueRef = useRef<number>(value);

// Keep latest value in ref to avoid stale closures during gesture/RAF
useEffect(() => {
valueRef.current = value;
}, [value]);

// Map value to angle (-135deg to +135deg, total 270deg sweep)
const angleRange = 270;
const startAngle = -135;
const normalizedProgress = Math.min(1, Math.max(0, (value - min) / (max - min || 1)));
const currentAngle = startAngle + normalizedProgress * angleRange;

const clampValue = useCallback(
(val: number) => {
const stepped = Math.round((val - min) / step) * step + min;
return Math.min(max, Math.max(min, Number(stepped.toFixed(2))));
},
[min, max, step]
);

const calculateAngleFromEvent = useCallback(
(clientX: number, clientY: number) => {
if (!dialRef.current) return 0;
const rect = dialRef.current.getBoundingClientRect();
const centerX = rect.left + rect.width / 2;
const centerY = rect.top + rect.height / 2;

const rad = Math.atan2(clientY - centerY, clientX - centerX);
let deg = (rad * 180) / Math.PI + 90; // Align 0deg to 12 o'clock
if (deg > 180) deg -= 360;
return deg;
},
[]
);

// Attach non-passive wheel listener directly to DOM to prevent console errors & enable smooth scroll
useEffect(() => {
const el = dialRef.current;
if (!el) return;

const onWheel = (e: WheelEvent) => {
if (disabled) return;
e.preventDefault();
const delta = e.deltaY < 0 ? step : -step;
const updated = clampValue(valueRef.current + delta);
if (updated !== valueRef.current) {
valueRef.current = updated;
onChange(updated);
}
};

el.addEventListener('wheel', onWheel, { passive: false });
return () => el.removeEventListener('wheel', onWheel);
}, [disabled, step, clampValue, onChange]);

const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
if (disabled) return;
if (animFrameRef.current) {
cancelAnimationFrame(animFrameRef.current);
animFrameRef.current = null;
}
setIsDragging(true);

const deg = calculateAngleFromEvent(e.clientX, e.clientY);
lastAngleRef.current = deg;
velocityRef.current = 0;

const handlePointerMove = (moveEvent: PointerEvent) => {
const newAngle = calculateAngleFromEvent(moveEvent.clientX, moveEvent.clientY);
let deltaAngle = newAngle - lastAngleRef.current;

// Prevent 360-degree boundary wrap spikes
if (deltaAngle > 180) deltaAngle -= 360;
if (deltaAngle < -180) deltaAngle += 360;

lastAngleRef.current = newAngle;
velocityRef.current = deltaAngle;

// Value delta proportional to angular movement
const valueDelta = (deltaAngle / angleRange) * (max - min);
const updated = clampValue(valueRef.current + valueDelta);
if (updated !== valueRef.current) {
valueRef.current = updated;
onChange(updated);
}
};

const handlePointerUp = () => {
setIsDragging(false);
window.removeEventListener('pointermove', handlePointerMove);
window.removeEventListener('pointerup', handlePointerUp);

if (momentum && Math.abs(velocityRef.current) > 0.4) {
let currentVel = velocityRef.current;

const applyDecay = () => {
currentVel *= 0.92; // Friction damping factor
if (Math.abs(currentVel) > 0.05) {
const delta = (currentVel / angleRange) * (max - min);
const updated = clampValue(valueRef.current + delta);
if (updated !== valueRef.current) {
valueRef.current = updated;
onChange(updated);
}
animFrameRef.current = requestAnimationFrame(applyDecay);
} else {
animFrameRef.current = null;
onChangeEnd?.();
}
};

animFrameRef.current = requestAnimationFrame(applyDecay);
} else {
onChangeEnd?.();
}
};

window.addEventListener('pointermove', handlePointerMove);
window.addEventListener('pointerup', handlePointerUp);
};

const handleKeyDown = (e: React.KeyboardEvent) => {
if (disabled) return;
if (e.key === 'ArrowRight' || e.key === 'ArrowUp') {
e.preventDefault();
onChange(clampValue(valueRef.current + step));
} else if (e.key === 'ArrowLeft' || e.key === 'ArrowDown') {
e.preventDefault();
onChange(clampValue(valueRef.current - step));
} else if (e.key === 'Home') {
e.preventDefault();
onChange(min);
} else if (e.key === 'End') {
e.preventDefault();
onChange(max);
}
};

const handleDoubleClick = () => {
if (disabled) return;
onChange(clampValue((max + min) / 2));
};

// SVG circular arc geometric constants
const radius = 40;
const circumference = 2 * Math.PI * radius; // ~251.32
const arcLength = circumference * (angleRange / 360); // 270 deg = ~188.49
const strokeOffset = arcLength * (1 - normalizedProgress);

return (
<div className={cn('inline-flex flex-col items-center select-none', className)}>
<div
ref={dialRef}
role="slider"
aria-label={label}
aria-valuemin={min}
aria-valuemax={max}
aria-valuenow={value}
tabIndex={disabled ? -1 : 0}
onPointerDown={handlePointerDown}
onKeyDown={handleKeyDown}
onDoubleClick={handleDoubleClick}
style={{ width: size, height: size, touchAction: 'none' }}
className={cn(
'relative rounded-full flex items-center justify-center cursor-grab active:cursor-grabbing focus:outline-none focus:ring-2 focus:ring-white transition-shadow',
disabled && 'opacity-40 cursor-not-allowed'
)}
>
{/* Outer Circular Gauge Track */}
<svg
style={{ width: size, height: size }}
className="absolute inset-0 pointer-events-none"
viewBox="0 0 100 100"
>
{/* Background Track (270 deg arc starting at 135 deg / bottom-left) */}
<circle
cx="50"
cy="50"
r={radius}
fill="none"
stroke="#1F1F1F"
strokeWidth="5"
strokeDasharray={`${arcLength} ${circumference}`}
strokeDashoffset="0"
strokeLinecap="round"
transform="rotate(135 50 50)"
/>
{/* Active Progress Track */}
<motion.circle
cx="50"
cy="50"
r={radius}
fill="none"
stroke="#3B82F6"
strokeWidth="5"
strokeDasharray={`${arcLength} ${circumference}`}
strokeDashoffset={strokeOffset}
strokeLinecap="round"
transform="rotate(135 50 50)"
transition={isDragging ? { duration: 0 } : motionTransitions.springSnappy}
/>
</svg>

{/* Center Rotating Knob */}
<motion.div
style={{
width: size * 0.65,
height: size * 0.65,
rotate: currentAngle,
}}
transition={isDragging ? { duration: 0 } : motionTransitions.springSnappy}
className={cn(
'relative rounded-full bg-[#141414] border border-[#1F1F1F] shadow-xs flex items-center justify-center',
isDragging && 'border-[#3B82F6]/60 shadow-[0_0_15px_rgba(59,130,246,0.2)]'
)}
>
{/* Top Indicator Pip / Notch */}
<span className="absolute top-2 w-1.5 h-3 rounded-full bg-[#3B82F6] shadow-xs" />
{/* Center tactile metallic ring */}
<div className="w-4 h-4 rounded-full bg-[#0E0E0E] border border-[#1F1F1F]" />
</motion.div>
</div>

{/* Numeric Value Display */}
{showValue && (
<div className="mt-3 text-center">
<div className="text-sm font-mono font-semibold text-[#FAFAFA] tracking-tight">
{value}
{unit}
</div>
<span className="text-[10px] font-mono text-[#6B6B6B]">{label}</span>
</div>
)}
</div>
);
};
```

 <!-- CONTINUES IN NEXT MESSAGE -->