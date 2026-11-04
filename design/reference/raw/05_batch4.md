oh no wonder it was complete one of the batch like this one i accidentally copied before it was done here is batch 4 again:

Date-picker imports `./calendar`, so I’m fetching that file too, then the remaining BATCH 4 components.
BATCH 4 of 6
Spring Select (spring-select)

* Category / priority: FORMS / high (simple labelled dropdown with description lines and error state)
* Page: https://easyui.site/components/spring-select
* Licence shown on page: none shown
* Description: Select dropdown whose menu slides down with a small spring overshoot while the chevron rotates slightly past 180° before settling.
* Dependencies: react, framer-motion, lucide-react (ChevronDown, Check), `../../lib/utils` (cn), `../../lib/motion-tokens` (`springSnappy`), `.focus-ring` (G1). Uses site CSS variables `--text-primary`, `--text-muted`, `--text-secondary`, `--surface`, `--surface-raised`, `--border`, `--border-hover` (all in G3) and `--shadow-elevated` (NOT confirmed in G3; define it yourself). Uses Tailwind `rose-500/400` for the error state.
* Visual notes: 40px-high trigger, 12px text, optional label above, popover list with rounded items, option description in small muted text, check mark on the selected item, red border and message in the error state. Follows the site light/dark tokens.
* Interaction notes: Trigger opens on ArrowDown / Enter / Space. Outside mousedown and Escape close it (Escape returns focus). Arrow keys and Enter work only if the list itself has focus; the list is not focused automatically when it opens, so keyboard navigation inside the list is unreliable. Disabled options are skipped on click only, not by arrow keys.
* Props: options (SpringSelectOption: value, label, disabled?, description?), value, defaultValue, placeholder (‘Select…’), onChange(value), label, disabled, error, className.

src/components/ui/spring-select.tsx
tsx

```tsx
'use client';

import React, { useState, useRef, useEffect, useId } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Check } from 'lucide-react';
import { cn } from '../../lib/utils';
import { motionTransitions } from '../../lib/motion-tokens';

export interface SpringSelectOption {
value: string;
label: string;
disabled?: boolean;
description?: string;
}

export interface SpringSelectProps {
/** Option list */
options: SpringSelectOption[];
/** Currently selected value (controlled) */
value?: string;
/** Default selected value (uncontrolled) */
defaultValue?: string;
/** Placeholder when no value is selected */
placeholder?: string;
/** Change handler */
onChange?: (value: string) => void;
/** Visible label */
label?: string;
/** Disabled state */
disabled?: boolean;
/** Error message */
error?: string;
/** Custom class name for the root */
className?: string;
}

/**
* SpringSelect — The dropdown menu follows the trigger with a tiny spring.
* On open, the menu slides down with a slight overshoot; the chevron rotates
* a hair past 180° before settling. Closing is a smooth ease-back.
*/
export const SpringSelect: React.FC<SpringSelectProps> = ({
options,
value,
defaultValue,
placeholder = 'Select…',
onChange,
label,
disabled = false,
error,
className,
}) => {
const generatedId = useId();
const rootId = `spring-select-${generatedId}`;
const [open, setOpen] = useState(false);
const [internalValue, setInternalValue] = useState<string | undefined>(defaultValue);
const [activeIndex, setActiveIndex] = useState<number>(-1);
const rootRef = useRef<HTMLDivElement>(null);
const triggerRef = useRef<HTMLButtonElement>(null);

const isControlled = value !== undefined;
const current = isControlled ? value : internalValue;
const currentOption = options.find((o) => o.value === current);

useEffect(() => {
if (!open) return;
const onDocClick = (e: MouseEvent) => {
if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
setOpen(false);
}
};
const onKey = (e: KeyboardEvent) => {
if (e.key === 'Escape') {
setOpen(false);
triggerRef.current?.focus();
}
};
document.addEventListener('mousedown', onDocClick);
document.addEventListener('keydown', onKey);
return () => {
document.removeEventListener('mousedown', onDocClick);
document.removeEventListener('keydown', onKey);
};
}, [open]);

const handleSelect = (opt: SpringSelectOption, idx: number) => {
if (opt.disabled) return;
if (!isControlled) setInternalValue(opt.value);
onChange?.(opt.value);
setOpen(false);
setActiveIndex(idx);
triggerRef.current?.focus();
};

const handleTriggerKey = (e: React.KeyboardEvent) => {
if (disabled) return;
if (e.key === 'ArrowDown' || e.key === 'Enter' || e.key === ' ') {
e.preventDefault();
setOpen(true);
setActiveIndex((i) => (i < 0 ? options.findIndex((o) => o.value === current) : i));
}
};

const handleListKey = (e: React.KeyboardEvent) => {
if (e.key === 'ArrowDown') {
e.preventDefault();
setActiveIndex((i) => Math.min(options.length - 1, i + 1));
} else if (e.key === 'ArrowUp') {
e.preventDefault();
setActiveIndex((i) => Math.max(0, i - 1));
} else if (e.key === 'Enter' && activeIndex >= 0) {
e.preventDefault();
handleSelect(options[activeIndex], activeIndex);
}
};

return (
<div ref={rootRef} className={cn('relative w-full', className)} id={rootId}>
{label && (
<label
htmlFor={`${rootId}-trigger`}
className="block text-xs font-medium text-[var(--text-primary)] tracking-tight mb-1.5 select-none"
>
{label}
</label>
)}

<button
ref={triggerRef}
id={`${rootId}-trigger`}
type="button"
disabled={disabled}
aria-haspopup="listbox"
aria-expanded={open}
onClick={() => !disabled && setOpen((o) => !o)}
onKeyDown={handleTriggerKey}
className={cn(
'relative w-full h-10 px-3.5 pr-9 text-xs rounded-lg border outline-none text-left flex items-center justify-between transition-colors duration-150 focus-ring',
'bg-[var(--surface-raised)]',
open
? 'border-[var(--border-hover)]'
: error
? 'border-rose-500/50 hover:border-rose-500/70'
: 'border-[var(--border)] hover:border-[var(--border-hover)]',
disabled && 'opacity-30 cursor-not-allowed',
currentOption ? 'text-[var(--text-primary)]' : 'text-[var(--text-muted)]'
)}
>
<span className="truncate">{currentOption?.label ?? placeholder}</span>

<motion.div
animate={{
rotate: open ? 192 : 0, // 192° gives a tiny past-180° before settle
}}
transition={motionTransitions.springSnappy}
className="absolute right-3 text-[var(--text-secondary)]"
>
<ChevronDown className="w-3.5 h-3.5" />
</motion.div>
</button>

<AnimatePresence>
{open && (
<motion.ul
role="listbox"
tabIndex={-1}
onKeyDown={handleListKey}
initial={{ opacity: 0, y: -6, scale: 0.98 }}
animate={{ opacity: 1, y: 0, scale: 1 }}
exit={{ opacity: 0, y: -4, scale: 0.98 }}
transition={motionTransitions.springSnappy}
// The container itself rides the spring: a tiny upward slide that
// "settles" with the snappy spring, plus a slight overshoot via the
// scale: 0.98 -> 1 motion.
className="absolute z-50 left-0 right-0 mt-1.5 max-h-60 overflow-auto py-1 rounded-lg border border-[var(--border)] bg-[var(--surface)] shadow-[var(--shadow-elevated)] focus:outline-none"
>
{options.map((opt, idx) => {
const selected = opt.value === current;
return (
<li
key={opt.value}
role="option"
aria-selected={selected}
aria-disabled={opt.disabled}
onMouseEnter={() => setActiveIndex(idx)}
onClick={() => handleSelect(opt, idx)}
className={cn(
'relative px-3 py-2 mx-1 rounded-md text-xs cursor-pointer flex items-center justify-between gap-2',
selected ? 'text-[var(--text-primary)]' : 'text-[var(--text-secondary)]',
opt.disabled && 'opacity-30 cursor-not-allowed',
activeIndex === idx && !opt.disabled && 'bg-[var(--surface-raised)]'
)}
>
<span className="flex flex-col">
<span className="leading-tight">{opt.label}</span>
{opt.description && (
<span className="text-[10px] text-[var(--text-muted)] mt-0.5">
{opt.description}
</span>
)}
</span>
{selected && <Check className="w-3.5 h-3.5 text-[var(--text-primary)] shrink-0" />}
</li>
);
})}
</motion.ul>
)}
</AnimatePresence>

{error && (
<motion.p
initial={{ opacity: 0, y: -2 }}
animate={{ opacity: 1, y: 0 }}
transition={motionTransitions.springSnappy}
className="text-[11px] text-rose-400 font-medium mt-1.5"
role="alert"
>
{error}
</motion.p>
)}
</div>
);
};
```

Usage example (from the site):
tsx

```tsx
import { SpringSelect } from "@/components/ui/spring-select";

export function Demo() {
return (
<div className="max-w-sm">
<SpringSelect
label="Workspace"
placeholder="Choose a workspace"
defaultValue="design"
options={[
{ value: "design", label: "Design Team", description: "12 members" },
{ value: "eng", label: "Engineering", description: "34 members" },
{ value: "ops", label: "Operations", description: "8 members" },
{ value: "labs", label: "R&D Labs", description: "5 members", disabled: true },
]}
/>
</div>
);
}
```

* Completeness: complete for the component file. `lib/utils`, `lib/motion-tokens` and the `--shadow-elevated` variable are not shown on the site. Compared with Combobox it is simpler but has weaker keyboard support.

Date Picker (date-picker)

* Category / priority: FORMS / high (forecast date and date-range selection)
* Page: https://easyui.site/components/date-picker
* Licence shown on page: none shown
* Description: Date picker and date range picker; popover opens with a spring, flips above when there is no room, and returns focus to the trigger after selection.
* Dependencies: react, framer-motion, lucide-react (CalendarDays), `../../lib/utils` (cn), and `./calendar` (Calendar, CalendarOptions, DateRange), which is included below as “dependency of date-picker”. Contains its own `useControllableState` and `usePopover`. Tailwind `neutral-*` with `dark:` variants; no site tokens, no `focus-ring`.
* Visual notes: 40px trigger (w-64 for single, w-72 for range) with a calendar icon and either the formatted date (`Intl.DateTimeFormat`, dateStyle medium) or the placeholder; popover is a rounded-xl bordered panel containing the Calendar.
* Interaction notes: Single mode closes 160 ms after a pick. Range mode closes once both ends are chosen. Escape returns focus to the trigger; outside pointer-down closes. `side` can be ‘auto’ (flip up only on desktop, when there is under 340px below and at least 340px above), ‘top’ or ‘bottom’. The `timer` delay keeps the selection pill animation visible.
* Props: DatePicker (value Date | null, defaultValue, onChange(date | null), placeholder ‘Pick a date’, align ‘start’ | ‘end’, side ‘bottom’ | ‘top’ | ‘auto’, disabled, className, plus all CalendarOptions: defaultMonth, minDate, maxDate, isDateDisabled, weekStartsOn, locale). DateRangePicker (value DateRange, defaultValue {from:null,to:null}, onChange(range), placeholder ‘Pick a range’, same other props).

src/components/ui/date-picker.tsx
tsx

```tsx
"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CalendarDays } from "lucide-react";
import { cn } from "../../lib/utils";
import { Calendar, type CalendarOptions, type DateRange } from "./calendar";

function useControllableState<T>(
value: T | undefined,
defaultValue: T,
onChange?: (value: T) => void
): [T, (next: T) => void] {
const [internal, setInternal] = React.useState<T>(defaultValue);
const controlled = value !== undefined;
const current = controlled ? (value as T) : internal;

const onChangeRef = React.useRef(onChange);
React.useEffect(() => {
onChangeRef.current = onChange;
});

const set = React.useCallback(
(next: T) => {
if (!controlled) setInternal(next);
onChangeRef.current?.(next);
},
[controlled]
);

return [current, set];
}

type Side = "bottom" | "top";
type CloseReason = "escape" | "outside";

function usePopover({
open,
onClose,
rootRef,
height = 340,
side: preferredSide = "auto",
}: {
open: boolean;
onClose: (reason: CloseReason) => void;
rootRef: React.RefObject<HTMLElement | null>;
height?: number;
side?: Side | "auto";
}) {
const [side, setSide] = React.useState<Side>("bottom");

React.useLayoutEffect(() => {
if (!open || !rootRef.current) return;
if (preferredSide && preferredSide !== "auto") {
setSide(preferredSide);
return;
}
// Always open downward on mobile viewports (< 640px)
const isMobile = typeof window !== "undefined" && window.innerWidth < 640;
if (isMobile) {
setSide("bottom");
return;
}
const rect = rootRef.current.getBoundingClientRect();
const below = window.innerHeight - rect.bottom;
// On desktop, only flip upward if space below is tight AND there is sufficient space above
setSide(below < height && rect.top >= height ? "top" : "bottom");
}, [open, height, rootRef, preferredSide]);

React.useEffect(() => {
if (!open) return;
const onDown = (e: PointerEvent) => {
if (!rootRef.current?.contains(e.target as Node)) onClose("outside");
};
const onKey = (e: KeyboardEvent) => {
if (e.key === "Escape") onClose("escape");
};
document.addEventListener("pointerdown", onDown);
document.addEventListener("keydown", onKey);
return () => {
document.removeEventListener("pointerdown", onDown);
document.removeEventListener("keydown", onKey);
};
}, [open, onClose, rootRef]);

return side;
}

const popoverMotion = (side: Side, align: "start" | "end" = "start") =>
({
initial: { opacity: 0, scale: 0.96 },
animate: { opacity: 1, scale: 1 },
exit: { opacity: 0, scale: 0.97, transition: { duration: 0.1 } },
transition: { type: "spring", stiffness: 520, damping: 38, mass: 0.7 },
style: {
transformOrigin: `${side === "top" ? "bottom" : "top"} ${align === "end" ? "right" : "left"}`,
},
}) as const;

const fmt = (d: Date, locale?: string) => new Intl.DateTimeFormat(locale, { dateStyle: "medium" }).format(d);

/* ───────────── shell: trigger + animated popover ───────────── */

function PickerShell({
text,
placeholder,
align = "start",
side: preferredSide = "auto",
disabled,
className,
children,
}: {
text: string | null;
placeholder: string;
align?: "start" | "end";
side?: Side | "auto";
disabled?: boolean;
className?: string;
children: (api: { close: () => void }) => React.ReactNode;
}) {
const [open, setOpen] = React.useState(false);
const rootRef = React.useRef<HTMLDivElement>(null);
const triggerRef = React.useRef<HTMLButtonElement>(null);
const timer = React.useRef<number | undefined>(undefined);

const side = usePopover({
open,
rootRef,
height: 340,
side: preferredSide,
onClose: (reason) => {
setOpen(false);
if (reason === "escape") triggerRef.current?.focus();
},
});

// brief beat so the selection pill lands before the popover closes
const close = React.useCallback(() => {
window.clearTimeout(timer.current);
timer.current = window.setTimeout(() => {
const a = document.activeElement;
setOpen(false);
// only hand focus back if it hasn't moved elsewhere in the meantime
if (!a || a === document.body || rootRef.current?.contains(a)) triggerRef.current?.focus();
}, 160);
}, []);
React.useEffect(() => () => window.clearTimeout(timer.current), []);

return (
<div ref={rootRef} className={cn("relative inline-block w-64 max-w-full", className)}>
<button
ref={triggerRef}
type="button"
disabled={disabled}
aria-haspopup="dialog"
aria-expanded={open}
onClick={() => setOpen((o) => !o)}
className={cn(
"flex h-10 w-full items-center gap-2.5 rounded-lg border border-neutral-200 bg-white px-3 text-sm outline-none transition-colors hover:border-neutral-300 focus-visible:ring-2 focus-visible:ring-neutral-400/40 disabled:pointer-events-none disabled:opacity-50 dark:border-neutral-800 dark:bg-neutral-950 dark:hover:border-neutral-700 dark:focus-visible:ring-neutral-600/50",
open && "border-neutral-400 hover:border-neutral-400 dark:border-neutral-600 dark:hover:border-neutral-600"
)}
>
<CalendarDays className="size-4 shrink-0 text-neutral-400" />
<span
className={cn(
"truncate",
text ? "text-neutral-900 dark:text-neutral-100" : "text-neutral-400 dark:text-neutral-500"
)}
>
{text ?? placeholder}
</span>
</button>

<AnimatePresence>
{open && (
<motion.div
role="dialog"
aria-label="Choose date"
{...popoverMotion(side, align)}
className={cn(
"absolute z-50 w-max max-w-[calc(100vw-2rem)] rounded-xl border border-neutral-200 bg-white shadow-lg shadow-neutral-900/5 dark:border-neutral-800 dark:bg-neutral-950 dark:shadow-black/40",
side === "top" ? "bottom-full mb-2" : "top-full mt-2",
align === "end" ? "right-0" : "left-0"
)}
>
{children({ close })}
</motion.div>
)}
</AnimatePresence>
</div>
);
}

/* ───────────── single date ───────────── */

export interface DatePickerProps extends CalendarOptions {
value?: Date | null;
defaultValue?: Date | null;
onChange?: (date: Date | null) => void;
placeholder?: string;
align?: "start" | "end";
side?: Side | "auto";
disabled?: boolean;
className?: string;
}

export function DatePicker({
value,
defaultValue = null,
onChange,
placeholder = "Pick a date",
align,
side,
disabled,
className,
...calendar
}: DatePickerProps) {
const [date, setDate] = useControllableState<Date | null>(value, defaultValue, onChange);

return (
<PickerShell
text={date ? fmt(date, calendar.locale) : null}
placeholder={placeholder}
align={align}
side={side}
disabled={disabled}
className={className}
>
{({ close }) => (
<Calendar
mode="single"
value={date}
onChange={(d) => {
setDate(d);
close();
}}
{...calendar}
/>
)}
</PickerShell>
);
}

/* ───────────── date range ───────────── */

export interface DateRangePickerProps extends CalendarOptions {
value?: DateRange;
defaultValue?: DateRange;
onChange?: (range: DateRange) => void;
placeholder?: string;
align?: "start" | "end";
side?: Side | "auto";
disabled?: boolean;
className?: string;
}

export function DateRangePicker({
value,
defaultValue = { from: null, to: null },
onChange,
placeholder = "Pick a range",
align,
side,
disabled,
className,
...calendar
}: DateRangePickerProps) {
const [range, setRange] = useControllableState<DateRange>(value, defaultValue, onChange);
const text = range.from
? `${fmt(range.from, calendar.locale)} – ${range.to ? fmt(range.to, calendar.locale) : "…"}`
: null;

return (
<PickerShell
text={text}
placeholder={placeholder}
align={align}
side={side}
disabled={disabled}
className={cn("w-72", className)}
>
{({ close }) => (
<Calendar
mode="range"
value={range}
onChange={(r) => {
setRange(r);
if (r.from && r.to) close();
}}
{...calendar}
/>
)}
</PickerShell>
);
}
```

Usage example (from the site):
tsx

```tsx
import { DatePicker, DateRangePicker } from "@/components/ui/date-picker";

<DatePicker value={date} onChange={setDate} placeholder="Due date" minDate={new Date()} />

<DateRangePicker value={range} onChange={setRange} />
```

* Completeness: complete for this file; requires `calendar.tsx` below and `lib/utils` (not shown on the site). Time of day is not supported (dates only).

Calendar (calendar) — dependency of date-picker

* Category / priority: FORMS / dependency (also useful alone)
* Page: https://easyui.site/components/calendar
* Licence shown on page: none shown
* Description: Dependency-free calendar with a gliding selected-day pill, range mode with a live hover preview band, and month slide animation in the direction of navigation.
* Dependencies: react, framer-motion (AnimatePresence, motion, Variants), lucide-react (ChevronLeft, ChevronRight), `../../lib/utils` (cn). Own `useControllableState` and date helpers (no date library). Tailwind `neutral-*` with `dark:` variants.
* Visual notes: Compact w-fit card with 36px cells, month title header with prev/next buttons, narrow weekday row, fixed 216px grid (6 rows), today shown as a small dot, selected day as a filled pill (neutral-900 / white in dark), range band in neutral-100 / neutral-800.
* Interaction notes: Full keyboard grid navigation (Arrows, Home/End, PageUp/PageDown, Shift+PageUp/Down for a year), roving tabindex, range hover preview, min/max/disabled predicate, `weekStartsOn` 0 or 1, `locale` for month, weekday and aria labels. Selection pill uses shared `layoutId` per instance.
* Props: mode (‘single’ | ‘range’), value, defaultValue, onChange, defaultMonth, minDate, maxDate, isDateDisabled, weekStartsOn (0), locale, className. Exports types DateRange, CalendarOptions, CalendarProps, CalendarSingleProps, CalendarRangeProps.

src/components/ui/calendar.tsx
tsx

```tsx
"use client";

import * as React from "react";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "../../lib/utils";

function useControllableState<T>(
value: T | undefined,
defaultValue: T,
onChange?: (value: T) => void
): [T, (next: T) => void] {
const [internal, setInternal] = React.useState<T>(defaultValue);
const controlled = value !== undefined;
const current = controlled ? (value as T) : internal;

const onChangeRef = React.useRef(onChange);
React.useEffect(() => {
onChangeRef.current = onChange;
});

const set = React.useCallback(
(next: T) => {
if (!controlled) setInternal(next);
onChangeRef.current?.(next);
},
[controlled]
);

return [current, set];
}

const spring = { type: "spring", stiffness: 460, damping: 38, mass: 0.7 } as const;

const slide: Variants = {
enter: (d: number) => ({ x: d * 24, opacity: 0 }),
center: { x: 0, opacity: 1 },
exit: (d: number) => ({ x: d * -24, opacity: 0 }),
};

export type DateRange = { from: Date | null; to: Date | null };

interface CalendarBase {
defaultMonth?: Date;
minDate?: Date;
maxDate?: Date;
isDateDisabled?: (date: Date) => boolean;
weekStartsOn?: 0 | 1;
locale?: string;
className?: string;
}
export type CalendarOptions = Omit<CalendarBase, "className">;

export interface CalendarSingleProps extends CalendarBase {
mode?: "single";
value?: Date | null;
defaultValue?: Date | null;
onChange?: (date: Date | null) => void;
}
export interface CalendarRangeProps extends CalendarBase {
mode: "range";
value?: DateRange;
defaultValue?: DateRange;
onChange?: (range: DateRange) => void;
}
export type CalendarProps = CalendarSingleProps | CalendarRangeProps;

/* ── date helpers (no dependencies) ── */
const startOfDay = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
const addDays = (d: Date, n: number) => new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
const addMonths = (d: Date, n: number) => {
const first = new Date(d.getFullYear(), d.getMonth() + n, 1);
const last = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
return new Date(first.getFullYear(), first.getMonth(), Math.min(d.getDate(), last));
};
const isSameDay = (a?: Date | null, b?: Date | null) =>
!!a && !!b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
const isSameMonth = (a: Date, b: Date) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth();
const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;

const EMPTY: DateRange = { from: null, to: null };
const toRange = (v: Date | null | DateRange | undefined): DateRange | undefined =>
v === undefined ? undefined : v === null ? EMPTY : v instanceof Date ? { from: v, to: null } : v;

export function Calendar(props: CalendarProps) {
const { defaultMonth, minDate, maxDate, isDateDisabled, weekStartsOn = 0, locale, className } = props;
const isRange = props.mode === "range";
const uid = React.useId();

const [selected, setSelected] = useControllableState<DateRange>(
toRange(props.value),
toRange(props.defaultValue) ?? EMPTY,
(next) => {
if (props.mode === "range") props.onChange?.(next);
else props.onChange?.(next.from);
}
);
const { from, to } = selected;

const today = React.useMemo(() => startOfDay(new Date()), []);
const [view, setView] = React.useState(() => {
const base = defaultMonth ?? from ?? today;
return new Date(base.getFullYear(), base.getMonth(), 1);
});
const [dir, setDir] = React.useState(1);
const [focus, setFocus] = React.useState<Date>(from ?? today);
const [hover, setHover] = React.useState<Date | null>(null);
const gridRef = React.useRef<HTMLDivElement>(null);
const shouldFocus = React.useRef(false);

const min = minDate ? startOfDay(minDate) : null;
const max = maxDate ? startOfDay(maxDate) : null;
const disabled = (d: Date) => (!!min && d < min) || (!!max && d > max) || !!isDateDisabled?.(d);

const y = view.getFullYear();
const m = view.getMonth();
const canPrev = !min || new Date(y, m, 0) >= min;
const canNext = !max || new Date(y, m + 1, 1) <= max;

const go = (target: Date, direction?: number) => {
setDir(direction ?? (target > view ? 1 : -1));
setView(new Date(target.getFullYear(), target.getMonth(), 1));
};

const monthFmt = React.useMemo(() => new Intl.DateTimeFormat(locale, { month: "long", year: "numeric" }), [locale]);
const dayFmt = React.useMemo(() => new Intl.DateTimeFormat(locale, { dateStyle: "full" }), [locale]);
const weekdays = React.useMemo(() => {
const f = new Intl.DateTimeFormat(locale, { weekday: "narrow" });
// 1 Aug 2021 is a Sunday
return Array.from({ length: 7 }, (_, i) => f.format(new Date(2021, 7, 1 + ((weekStartsOn + i) % 7))));
}, [locale, weekStartsOn]);

const dim = new Date(y, m + 1, 0).getDate();
const offset = (new Date(y, m, 1).getDay() - weekStartsOn + 7) % 7;
const cells = Array.from({ length: 42 }, (_, i) => {
const n = i - offset + 1;
return n < 1 || n > dim ? null : new Date(y, m, n);
});
const tabDate = isSameMonth(focus, view) ? focus : new Date(y, m, 1);

const pick = (d: Date) => {
if (disabled(d)) return;
setFocus(d);
if (!isRange) setSelected({ from: d, to: null });
else if (!from || to || d < from) setSelected({ from: d, to: null });
else setSelected({ from, to: d });
};

const rangeEnd = isRange && from ? (to ?? (hover && hover > from ? hover : null)) : null;

const onKeyDown = (e: React.KeyboardEvent) => {
const el = (e.target as HTMLElement).closest<HTMLElement>("[data-date]");
if (!el) return;
const [yy, mm, dd] = el.dataset.date!.split("-").map(Number);
const cur = new Date(yy, mm - 1, dd);
const col = (cur.getDay() - weekStartsOn + 7) % 7;
let next: Date | null = null;
if (e.key === "ArrowLeft") next = addDays(cur, -1);
else if (e.key === "ArrowRight") next = addDays(cur, 1);
else if (e.key === "ArrowUp") next = addDays(cur, -7);
else if (e.key === "ArrowDown") next = addDays(cur, 7);
else if (e.key === "Home") next = addDays(cur, -col);
else if (e.key === "End") next = addDays(cur, 6 - col);
else if (e.key === "PageUp") next = addMonths(cur, e.shiftKey ? -12 : -1);
else if (e.key === "PageDown") next = addMonths(cur, e.shiftKey ? 12 : 1);
if (!next) return;
e.preventDefault();
if (min && next < min) next = min;
if (max && next > max) next = max;
shouldFocus.current = true;
setFocus(next);
if (!isSameMonth(next, view)) go(next);
};

React.useEffect(() => {
if (!shouldFocus.current) return;
shouldFocus.current = false;
gridRef.current?.querySelector<HTMLElement>(`[data-date="${dayKey(focus)}"]`)?.focus();
}, [focus, view]);

return (
<div className={cn("w-fit select-none p-3", className)}>
{/* header */}
<div className="mb-2 flex h-8 items-center gap-1">
<NavButton label="Previous month" disabled={!canPrev} onClick={() => go(addMonths(view, -1), -1)}>
<ChevronLeft className="size-4" />
</NavButton>
<div className="relative h-5 flex-1 overflow-hidden text-center text-sm font-medium text-neutral-900 dark:text-neutral-100">
<AnimatePresence initial={false} custom={dir}>
<motion.span
key={y * 12 + m}
custom={dir}
variants={slide}
initial="enter"
animate="center"
exit="exit"
transition={spring}
aria-live="polite"
className="absolute inset-0"
>
{monthFmt.format(view)}
</motion.span>
</AnimatePresence>
</div>
<NavButton label="Next month" disabled={!canNext} onClick={() => go(addMonths(view, 1), 1)}>
<ChevronRight className="size-4" />
</NavButton>
</div>

{/* weekdays */}
<div className="flex" aria-hidden>
{weekdays.map((w, i) => (
<div key={i} className="grid h-8 w-9 place-items-center text-xs text-neutral-400 dark:text-neutral-500">
{w}
</div>
))}
</div>

{/* days */}
<div className="-m-1 overflow-hidden p-1">
<div
ref={gridRef}
role="grid"
aria-label={monthFmt.format(view)}
onKeyDown={onKeyDown}
onMouseLeave={() => setHover(null)}
className="relative h-[216px]"
>
<AnimatePresence initial={false} custom={dir}>
<motion.div
key={y * 12 + m}
custom={dir}
variants={slide}
initial="enter"
animate="center"
exit="exit"
transition={spring}
className="absolute inset-0"
>
{Array.from({ length: 6 }, (_, r) => (
<div key={r} role="row" className="flex">
{cells.slice(r * 7, r * 7 + 7).map((d, col) => {
if (!d) return <div key={col} role="gridcell" className="h-9 w-9" />;

const isStart = isSameDay(d, from);
const isEnd = !isStart && isRange && isSameDay(d, to);
const picked = isStart || isEnd;
const inBand =
isRange && !!from && !!rangeEnd && !isSameDay(from, rangeEnd) && d >= from && d <= rangeEnd;
const off = disabled(d);
const isToday = isSameDay(d, today);

return (
<div
key={col}
role="gridcell"
aria-selected={picked || inBand}
className={cn(
"relative h-9 w-9",
inBand && "bg-neutral-100 dark:bg-neutral-800/70",
inBand && (isSameDay(d, from) || col === 0 || d.getDate() === 1) && "rounded-l-lg",
inBand && (isSameDay(d, rangeEnd) || col === 6 || d.getDate() === dim) && "rounded-r-lg"
)}
>
<button
type="button"
data-date={dayKey(d)}
tabIndex={isSameDay(d, tabDate) ? 0 : -1}
aria-label={dayFmt.format(d)}
aria-disabled={off || undefined}
aria-current={isToday ? "date" : undefined}
onClick={() => pick(d)}
onMouseEnter={() => setHover(d)}
className={cn(
"group relative grid size-9 place-items-center rounded-lg text-sm tabular-nums outline-none transition-colors focus-visible:ring-2 focus-visible:ring-neutral-400/60 dark:focus-visible:ring-neutral-600",
picked ? "text-white dark:text-neutral-900" : "text-neutral-900 dark:text-neutral-100",
!picked &&
!off &&
(inBand
? "hover:bg-neutral-200/80 dark:hover:bg-neutral-700/60"
: "hover:bg-neutral-100 dark:hover:bg-neutral-800"),
off && "cursor-not-allowed opacity-30"
)}
>
{picked && (
<motion.span
layoutId={isRange ? `${uid}-${isStart ? "start" : "end"}` : `${uid}-sel`}
transition={spring}
className="absolute inset-0 rounded-lg bg-neutral-900 dark:bg-white"
/>
)}
<span className="relative transition-transform duration-150 group-active:scale-90">
{d.getDate()}
</span>
{isToday && !picked && (
<span className="absolute bottom-1 size-1 rounded-full bg-neutral-400 dark:bg-neutral-500" />
)}
</button>
</div>
);
})}
</div>
))}
</motion.div>
</AnimatePresence>
</div>
</div>
</div>
);
}

function NavButton({
label,
disabled,
onClick,
children,
}: {
label: string;
disabled?: boolean;
onClick: () => void;
children: React.ReactNode;
}) {
return (
<button
type="button"
aria-label={label}
disabled={disabled}
onClick={onClick}
className="grid size-8 place-items-center rounded-lg text-neutral-500 outline-none transition hover:bg-neutral-100 hover:text-neutral-900 focus-visible:ring-2 focus-visible:ring-neutral-400/60 active:scale-95 disabled:pointer-events-none disabled:opacity-30 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white dark:focus-visible:ring-neutral-600"
>
{children}
</button>
);
}
```

Usage example (from the site):
tsx

```tsx
import { Calendar, type DateRange } from "@/components/ui/calendar";

// single
const [date, setDate] = React.useState<Date | null>(null);
<Calendar value={date} onChange={setDate} />

// range
const [range, setRange] = React.useState<DateRange>({ from: null, to: null });
<Calendar mode="range" value={range} onChange={setRange} />

// limits
<Calendar minDate={new Date()} isDateDisabled={(d) => d.getDay() === 0} weekStartsOn={1} />
```

* Completeness: complete for the component file. Only `lib/utils` (cn) is not shown on the site. Dates are local-time `Date` objects, with no time-zone handling.

 <!-- CONTINUES IN NEXT MESSAGE -->
<!-- CONTINUED: BATCH 4 of 6, components stretch-switch, animated-file-upload and stepper -->
Stretch Switch (stretch-switch)

* Category / priority: FORMS / medium (toggles for layer or model visibility)
* Page: https://easyui.site/components/stretch-switch
* Licence shown on page: none shown
* Description: Toggle switch whose thumb stretches slightly while pressed, then snaps to its destination with a snappy spring.
* Dependencies: react, framer-motion (motion, useMotionValue, useTransform, animate), `../../lib/utils` (cn), `../../lib/motion-tokens` (`springSnappy`), `.focus-ring` (G1). Uses site CSS variables `--text-primary`, `--text-muted`, `--text-secondary`, `--surface-raised`, `--border`, `--bg` (G3).
* Visual notes: 36×20px track with a 14px thumb; on = filled with the primary text colour, off = raised surface with a border. Optional label and description text on the left (12px / 11px).
* Interaction notes: Click or tap toggles; `role="switch"` with `aria-checked`. Pressing scales the thumb to 1.18 × 0.86. Clicking the label text also toggles. No keyboard handling beyond the native button (Space/Enter work). The thumb is not actually draggable despite the description saying “dragging”.
* Props: checked, defaultChecked (false), disabled, onChange(checked), label, description, className.

src/components/ui/stretch-switch.tsx
tsx

```tsx
'use client';

import React, { useState } from 'react';
import { motion, useMotionValue, useTransform, animate } from 'framer-motion';
import { cn } from '../../lib/utils';
import { motionTransitions } from '../../lib/motion-tokens';

export interface StretchSwitchProps {
checked?: boolean;
defaultChecked?: boolean;
disabled?: boolean;
onChange?: (checked: boolean) => void;
label?: React.ReactNode;
description?: string;
className?: string;
}

const TRACK_WIDTH = 36; // px (w-9)
const THUMB_SIZE = 14; // px (h-3.5 w-3.5)
const TRACK_PADDING = 2; // px-0.5
const TRAVEL = TRACK_WIDTH - THUMB_SIZE - TRACK_PADDING * 2;

/**
* StretchSwitch — Thumb stretches slightly while dragging/pressing,
* then snaps naturally to its destination.
*
* Implementation: while pressing, the thumb is allowed to grow horizontally
* (scaleX > 1) and slightly vertically (scaleY < 1) so it looks "stretched".
* On release, the spring (springSnappy) handles the snap to the new x.
*/
export const StretchSwitch: React.FC<StretchSwitchProps> = ({
checked,
defaultChecked = false,
disabled = false,
onChange,
label,
description,
className,
}) => {
const [isOn, setIsOn] = useState(defaultChecked);
const isControlled = checked !== undefined;
const current = isControlled ? checked : isOn;

const x = useMotionValue(current ? TRAVEL : 0);
const [isPressed, setIsPressed] = useState(false);

// Animate to the new x whenever current changes
React.useEffect(() => {
animate(x, current ? TRAVEL : 0, motionTransitions.springSnappy);
}, [current, x]);

// Stretch the thumb: while pressed, scaleX -> 1.18, scaleY -> 0.86 — looks stretched.
const scaleX = useTransform(x, () => (isPressed ? 1.18 : 1));
const scaleY = useTransform(x, () => (isPressed ? 0.86 : 1));

const handleToggle = () => {
if (disabled) return;
const next = !current;
if (!isControlled) setIsOn(next);
onChange?.(next);
};

return (
<div
className={cn(
'flex items-center justify-between gap-4 select-none',
disabled && 'opacity-30 cursor-not-allowed',
className
)}
>
{(label || description) && (
<div
className={cn('text-left cursor-pointer', disabled && 'cursor-not-allowed')}
onClick={handleToggle}
>
{label && (
<div className="text-xs font-medium text-[var(--text-primary)] leading-tight">{label}</div>
)}
{description && (
<div className="text-[11px] text-[var(--text-muted)] mt-0.5 leading-relaxed">
{description}
</div>
)}
</div>
)}

<button
type="button"
role="switch"
aria-checked={current}
disabled={disabled}
onPointerDown={() => !disabled && setIsPressed(true)}
onPointerUp={() => setIsPressed(false)}
onPointerCancel={() => setIsPressed(false)}
onPointerLeave={() => setIsPressed(false)}
onClick={handleToggle}
className={cn(
'relative inline-flex h-5 w-9 shrink-0 rounded-full border transition-colors duration-200 focus-ring',
current
? 'bg-[var(--text-primary)] border-[var(--text-primary)]'
: 'bg-[var(--surface-raised)] border-[var(--border)]',
disabled && 'cursor-not-allowed'
)}
style={{ paddingInline: TRACK_PADDING }}
>
<motion.span
style={{ x, scaleX, scaleY, width: THUMB_SIZE, height: THUMB_SIZE }}
className={cn(
'pointer-events-none block my-auto rounded-full shadow-xs origin-center',
current ? 'bg-[var(--bg)]' : 'bg-[var(--text-secondary)]'
)}
/>
</button>
</div>
);
};
```

Usage example (from the site):
tsx

```tsx
import { StretchSwitch } from "@/components/ui/stretch-switch";

export function Demo() {
return (
<div className="space-y-3 max-w-sm">
<StretchSwitch
label="Reduce motion"
description="Disables parallax and large translations across the app."
defaultChecked
/>
<StretchSwitch
label="Show pre-release features"
description="Toggle to preview experiments in the dashboard."
/>
</div>
);
}
```

* Completeness: complete for the component file. `lib/utils` and `lib/motion-tokens` not shown on the site.

Animated File Upload (animated-file-upload)

* Category / priority: FORMS / low (only if the dashboard accepts uploads such as CSV or weather files)
* Page: https://easyui.site/components/animated-file-upload
* Licence shown on page: none shown
* Description: Drag-and-drop uploader with a drop reaction, per-file progress that morphs through uploading, processing and complete states, error and retry handling.
* Dependencies: react, framer-motion, lucide-react (Upload, File as FileIcon, Check, AlertCircle, X, RotateCcw, FileText, Image as ImageIcon, Film, Music, Archive, Code), `../../lib/utils` (cn), `../../lib/motion-tokens` (`springSnappy`, `springGentle`), `.focus-ring` (G1). All colours are hard-coded dark hex values (dark-only), plus Tailwind rose/emerald accents.
* Visual notes: Dashed drop zone (min-h 180px, or 120px in the compact variant) with an upload icon tile, title, subtitle and size limit; below it a “Files (n)” list with per-file cards: icon tile by file type, name, size, status line (Uploading n% / Processing... / Ready / error text), retry and remove buttons, and a 2px progress bar along the bottom edge. Complete cards are tinted green, error cards red.
* Interaction notes: Click, Enter or Space opens the file picker; drag over scales the zone and lifts the icon. Max size check produces an error card. When no `uploadHandler` is given, the upload is only SIMULATED with a timer (setInterval, random progress steps); no network request is made. A custom `uploadHandler(file, onProgress)` returns a promise. “Clear Completed” removes finished items. Note: the `accept` prop only goes to the hidden input, so dropped files are not type-checked; `maxFiles` only slices the list; the `group-hover:text-white` class has no `group` parent so it does nothing.
* Props: multiple (true), accept (string | string[]), maxSize (25 MB), maxFiles (10), dropTitle, dropSubtitle, variant (‘standard’ | ‘compact’), disabled, initialFiles, onFilesSelected(files), onUploadComplete(file), uploadHandler, className. Also exports types FileUploadStatus and UploadFileItem.

src/components/ui/animated-file-upload.tsx
tsx

```tsx
'use client';

import React, { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
Upload,
File as FileIcon,
Check,
AlertCircle,
X,
RotateCcw,
FileText,
Image as ImageIcon,
Film,
Music,
Archive,
Code
} from 'lucide-react';
import { cn } from '../../lib/utils';
import { motionTransitions } from '../../lib/motion-tokens';

export type FileUploadStatus = 'queued' | 'uploading' | 'processing' | 'complete' | 'error';

export interface UploadFileItem {
id: string;
name: string;
size: number;
type: string;
progress: number;
status: FileUploadStatus;
errorMessage?: string;
rawFile?: File;
}

export interface AnimatedFileUploadProps {
/** Allow multiple files selection and upload */
multiple?: boolean;
/** Accepted MIME types or extensions (e.g., "image/*,application/pdf" or [".png", ".jpg"]) */
accept?: string | string[];
/** Maximum file size in bytes (e.g., 10 * 1024 * 1024 for 10MB) */
maxSize?: number;
/** Maximum number of files allowed when multiple is true */
maxFiles?: number;
/** Custom label for primary drop title */
dropTitle?: string;
/** Custom label for secondary browse action */
dropSubtitle?: string;
/** Layout mode: standard full-size or compact inline */
variant?: 'standard' | 'compact';
/** Disabled state */
disabled?: boolean;
/** Initial files list for controlled or default showcase */
initialFiles?: UploadFileItem[];
/** Callback fired when files are dropped or selected */
onFilesSelected?: (files: File[]) => void;
/** Callback fired when a file upload completes */
onUploadComplete?: (file: UploadFileItem) => void;
/** Custom upload simulation or upload handler returning a promise */
uploadHandler?: (
file: UploadFileItem,
onProgress: (progress: number) => void
) => Promise<void>;
/** Custom class name */
className?: string;
}

const formatFileSize = (bytes: number): string => {
if (bytes === 0) return '0 B';
const k = 1024;
const sizes = ['B', 'KB', 'MB', 'GB'];
const i = Math.floor(Math.log(bytes) / Math.log(k));
return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
};

const getFileIcon = (fileName: string, mimeType: string) => {
const ext = fileName.split('.').pop()?.toLowerCase() || '';
if (mimeType.startsWith('image/') || ['jpg', 'jpeg', 'png', 'svg', 'webp', 'gif'].includes(ext)) {
return ImageIcon;
}
if (mimeType.startsWith('video/') || ['mp4', 'mov', 'webm', 'mkv'].includes(ext)) {
return Film;
}
if (mimeType.startsWith('audio/') || ['mp3', 'wav', 'ogg', 'flac'].includes(ext)) {
return Music;
}
if (['zip', 'rar', 'tar', 'gz', '7z'].includes(ext)) {
return Archive;
}
if (['ts', 'tsx', 'js', 'jsx', 'json', 'html', 'css', 'py', 'rs', 'go'].includes(ext)) {
return Code;
}
if (['pdf', 'doc', 'docx', 'txt', 'md'].includes(ext)) {
return FileText;
}
return FileIcon;
};

export const AnimatedFileUpload: React.FC<AnimatedFileUploadProps> = ({
multiple = true,
accept,
maxSize = 25 * 1024 * 1024, // 25MB default
maxFiles = 10,
dropTitle = 'Drop files here',
dropSubtitle = 'or browse from your device',
variant = 'standard',
disabled = false,
initialFiles,
onFilesSelected,
onUploadComplete,
uploadHandler,
className,
}) => {
const [isDragOver, setIsDragOver] = useState(false);
const [files, setFiles] = useState<UploadFileItem[]>(initialFiles || []);
const inputRef = useRef<HTMLInputElement>(null);

const acceptString = Array.isArray(accept) ? accept.join(',') : accept;

const simulateUpload = useCallback(
(fileItem: UploadFileItem) => {
let currentProgress = 0;
const interval = setInterval(() => {
currentProgress += Math.floor(Math.random() * 18) + 12;
if (currentProgress >= 90 && currentProgress < 100) {
setFiles((prev) =>
prev.map((f) =>
f.id === fileItem.id
? { ...f, progress: 92, status: 'processing' }
: f
)
);
} else if (currentProgress >= 100) {
clearInterval(interval);
setFiles((prev) =>
prev.map((f) => {
if (f.id === fileItem.id) {
const updated = { ...f, progress: 100, status: 'complete' as const };
onUploadComplete?.(updated);
return updated;
}
return f;
})
);
} else {
setFiles((prev) =>
prev.map((f) =>
f.id === fileItem.id
? { ...f, progress: currentProgress, status: 'uploading' }
: f
)
);
}
}, 180);
},
[onUploadComplete]
);

const processIncomingFiles = useCallback(
(incoming: File[]) => {
if (disabled) return;
const validFiles: UploadFileItem[] = [];

incoming.forEach((file) => {
const id = `${file.name}-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;
const isOverSize = maxSize && file.size > maxSize;

if (isOverSize) {
validFiles.push({
id,
name: file.name,
size: file.size,
type: file.type,
progress: 0,
status: 'error',
errorMessage: `File exceeds maximum allowed size (${formatFileSize(maxSize)})`,
rawFile: file,
});
} else {
const item: UploadFileItem = {
id,
name: file.name,
size: file.size,
type: file.type,
progress: 0,
status: 'uploading',
rawFile: file,
};
validFiles.push(item);
}
});

setFiles((prev) => {
const combined = multiple ? [...validFiles, ...prev] : validFiles;
return combined.slice(0, maxFiles);
});

onFilesSelected?.(incoming);

// Start processing/uploading valid files
validFiles.forEach((fileItem) => {
if (fileItem.status !== 'error') {
if (uploadHandler) {
uploadHandler(fileItem, (progress) => {
setFiles((prev) =>
prev.map((f) =>
f.id === fileItem.id ? { ...f, progress } : f
)
);
})
.then(() => {
setFiles((prev) =>
prev.map((f) =>
f.id === fileItem.id
? { ...f, progress: 100, status: 'complete' }
: f
)
);
onUploadComplete?.(fileItem);
})
.catch((err) => {
setFiles((prev) =>
prev.map((f) =>
f.id === fileItem.id
? {
...f,
status: 'error',
errorMessage: err?.message || 'Upload failed',
}
: f
)
);
});
} else {
simulateUpload(fileItem);
}
}
});
},
[disabled, maxSize, multiple, maxFiles, onFilesSelected, onUploadComplete, uploadHandler, simulateUpload]
);

const handleDragOver = (e: React.DragEvent) => {
e.preventDefault();
e.stopPropagation();
if (!disabled && !isDragOver) {
setIsDragOver(true);
}
};

const handleDragLeave = (e: React.DragEvent) => {
e.preventDefault();
e.stopPropagation();
setIsDragOver(false);
};

const handleDrop = (e: React.DragEvent) => {
e.preventDefault();
e.stopPropagation();
setIsDragOver(false);
if (disabled) return;

if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
const droppedFiles = Array.from(e.dataTransfer.files);
processIncomingFiles(multiple ? droppedFiles : [droppedFiles[0]]);
}
};

const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
if (e.target.files && e.target.files.length > 0) {
const selected = Array.from(e.target.files);
processIncomingFiles(multiple ? selected : [selected[0]]);
if (inputRef.current) {
inputRef.current.value = '';
}
}
};

const handleRemoveFile = (id: string) => {
setFiles((prev) => prev.filter((f) => f.id !== id));
};

const handleRetryFile = (fileItem: UploadFileItem) => {
setFiles((prev) =>
prev.map((f) =>
f.id === fileItem.id
? { ...f, progress: 0, status: 'uploading', errorMessage: undefined }
: f
)
);
if (uploadHandler) {
uploadHandler(fileItem, (progress) => {
setFiles((prev) =>
prev.map((f) => (f.id === fileItem.id ? { ...f, progress } : f))
);
})
.then(() => {
setFiles((prev) =>
prev.map((f) =>
f.id === fileItem.id
? { ...f, progress: 100, status: 'complete' }
: f
)
);
})
.catch((err) => {
setFiles((prev) =>
prev.map((f) =>
f.id === fileItem.id
? { ...f, status: 'error', errorMessage: err?.message || 'Upload failed' }
: f
)
);
});
} else {
simulateUpload(fileItem);
}
};

const isCompact = variant === 'compact';

return (
<div className={cn('w-full select-none font-sans', className)}>
<input
ref={inputRef}
type="file"
multiple={multiple}
accept={acceptString}
onChange={handleFileInputChange}
disabled={disabled}
className="hidden"
aria-label="Upload files"
/>

{/* Drop Zone Box */}
<motion.div
onDragOver={handleDragOver}
onDragLeave={handleDragLeave}
onDrop={handleDrop}
onClick={() => !disabled && inputRef.current?.click()}
onKeyDown={(e) => {
if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
e.preventDefault();
inputRef.current?.click();
}
}}
tabIndex={disabled ? -1 : 0}
role="button"
aria-disabled={disabled}
whileHover={disabled ? undefined : { borderColor: '#4A4A4A' }}
animate={{
scale: isDragOver ? 1.01 : 1,
borderColor: isDragOver ? '#4A4A4A' : '#1F1F1F',
backgroundColor: isDragOver ? '#141414' : '#0E0E0E',
}}
transition={motionTransitions.springSnappy}
className={cn(
'relative flex flex-col items-center justify-center text-center cursor-pointer border border-dashed rounded-xl transition-colors focus-ring',
isCompact ? 'p-5 sm:p-6 min-h-[120px]' : 'p-8 sm:p-10 min-h-[180px]',
disabled && 'opacity-40 cursor-not-allowed border-solid'
)}
>
<motion.div
animate={{
y: isDragOver ? -3 : 0,
scale: isDragOver ? 1.08 : 1,
}}
transition={motionTransitions.springSnappy}
className="w-10 h-10 rounded-lg bg-[#141414] border border-[#1F1F1F] flex items-center justify-center text-[#A1A1A1] mb-3 group-hover:text-white"
>
<Upload className={cn('w-5 h-5 transition-colors', isDragOver ? 'text-white' : 'text-[#525252]')} />
</motion.div>

<div className="space-y-1">
<p className="text-sm font-medium text-[#FAFAFA]">{dropTitle}</p>
<p className="text-xs text-[#A1A1A1]">
{dropSubtitle}{' '}
{maxSize && (
<span className="text-[#6B6B6B]">
(up to {formatFileSize(maxSize)})
</span>
)}
</p>
</div>
</motion.div>

{/* Uploading / Uploaded Files List */}
<AnimatePresence mode="popLayout">
{files.length > 0 && (
<motion.div
initial={{ opacity: 0, y: 8 }}
animate={{ opacity: 1, y: 0 }}
exit={{ opacity: 0, y: 8 }}
transition={motionTransitions.springGentle}
className="mt-4 space-y-2"
>
<div className="flex items-center justify-between px-1 text-[11px] font-mono text-[#6B6B6B] uppercase tracking-wider">
<span>Files ({files.length})</span>
{files.some((f) => f.status === 'complete') && (
<button
type="button"
onClick={() => setFiles((prev) => prev.filter((f) => f.status !== 'complete'))}
className="hover:text-[#A1A1A1] transition-colors focus-ring rounded cursor-pointer"
>
Clear Completed
</button>
)}
</div>

<div className="space-y-2">
{files.map((file) => {
const IconComponent = getFileIcon(file.name, file.type);
const isComplete = file.status === 'complete';
const isError = file.status === 'error';
const isProcessing = file.status === 'processing';
const isUploading = file.status === 'uploading';

return (
<motion.div
key={file.id}
layout
initial={{ opacity: 0, y: 10, scale: 0.98 }}
animate={{ opacity: 1, y: 0, scale: 1 }}
exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.15 } }}
transition={motionTransitions.springGentle}
className={cn(
'relative overflow-hidden rounded-xl border p-3 sm:p-3.5 bg-[#0E0E0E] transition-colors',
isError
? 'border-rose-500/30 bg-rose-500/5'
: isComplete
? 'border-emerald-500/30 bg-emerald-500/5'
: 'border-[#1F1F1F]'
)}
>
<div className="flex items-center gap-3 relative z-10">
{/* File Type Icon */}
<div
className={cn(
'w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border',
isError
? 'bg-rose-500/10 border-rose-500/30 text-rose-400'
: isComplete
? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
: 'bg-[#141414] border-[#1F1F1F] text-[#A1A1A1]'
)}
>
<IconComponent className="w-4 h-4" />
</div>

{/* File Metadata */}
<div className="flex-1 min-w-0">
<div className="flex items-center justify-between gap-2">
<p className="text-xs font-medium text-[#FAFAFA] truncate">
{file.name}
</p>
<span className="text-[10px] font-mono text-[#6B6B6B] shrink-0">
{formatFileSize(file.size)}
</span>
</div>

{/* Status line */}
<div className="flex items-center justify-between text-[11px] mt-1">
{isError ? (
<span className="text-rose-400 flex items-center gap-1">
<AlertCircle className="w-3 h-3 shrink-0" />
<span className="truncate">{file.errorMessage || 'Upload failed'}</span>
</span>
) : isComplete ? (
<span className="text-emerald-400 flex items-center gap-1">
<Check className="w-3 h-3 shrink-0" />
<span>Ready</span>
</span>
) : isProcessing ? (
<span className="text-[#A1A1A1] flex items-center gap-1.5 font-mono text-[10px]">
<span className="w-1.5 h-1.5 rounded-full bg-white/70 animate-pulse" />
Processing...
</span>
) : (
<span className="text-[#6B6B6B] font-mono text-[10px]">
Uploading {file.progress}%
</span>
)}
</div>
</div>

{/* Action buttons */}
<div className="flex items-center gap-1 shrink-0">
{isError && (
<button
type="button"
onClick={() => handleRetryFile(file)}
className="p-1 rounded-md text-[#525252] hover:text-white hover:bg-[#141414] transition-colors focus-ring cursor-pointer"
title="Retry upload"
aria-label={`Retry uploading ${file.name}`}
>
<RotateCcw className="w-3.5 h-3.5" />
</button>
)}
<button
type="button"
onClick={() => handleRemoveFile(file.id)}
className="p-1 rounded-md text-[#525252] hover:text-[#FAFAFA] hover:bg-[#141414] transition-colors focus-ring cursor-pointer"
title="Remove file"
aria-label={`Remove ${file.name}`}
>
<X className="w-3.5 h-3.5" />
</button>
</div>
</div>

{/* Progress Bar (at the bottom) */}
{(isUploading || isProcessing) && (
<div className="absolute bottom-0 left-0 right-0 h-[2px] bg-[#141414]">
<motion.div
className="h-full bg-[#FAFAFA]"
initial={{ width: '0%' }}
animate={{ width: `${file.progress}%` }}
transition={{ duration: 0.15, ease: 'easeOut' }}
/>
</div>
)}
</motion.div>
);
})}
</div>
</motion.div>
)}
</AnimatePresence>
</div>
);
};
```

Usage example (from the site):
tsx

```tsx
import { AnimatedFileUpload } from "@/components/ui/animated-file-upload";

export function Demo() {
return (
<div className="max-w-md mx-auto p-4">
<AnimatedFileUpload
multiple
maxSize={10 * 1024 * 1024}
accept="image/*,application/pdf"
onFilesSelected={(files) => console.log('Selected:', files)}
onUploadComplete={(file) => console.log('Uploaded:', file.name)}
/>
</div>
);
}
```

* Completeness: complete for the component file. `lib/utils` and `lib/motion-tokens` not shown on the site.

Stepper (stepper)

* Category / priority: NAVIGATION / medium (multi-step setup or wizard flows)
* Page: https://easyui.site/components/stepper
* Licence shown on page: none shown
* Description: Multi-step progress indicator with line fills, a gliding active ring, drawn check marks, and direction-aware sliding step panels.
* Dependencies: react, framer-motion (AnimatePresence, motion, Variants), `../../lib/utils` (cn). Does not use `lib/motion-tokens` or `focus-ring`. Tailwind `neutral-*` with `dark:` variants.
* Visual notes: Numbered circles (28px) joined by thin lines; completed steps are filled with a check that draws itself; the current step has an outer ring that glides to the next step; upcoming steps are muted. Horizontal layout hides labels of non-current steps below the sm breakpoint. Vertical layout stacks the steps with a left line.
* Interaction notes: Completed steps become buttons when `onStepChange` is given (jump back only). Lines fill with a scale animation. `StepPanels` renders only the current child and slides it in the direction of travel (24px, 0.18s, `mode="wait"`). `aria-current="step"` on the current item, screen-reader “(completed)” text. The component does not move between steps by itself; you control `current`.
* Props: Stepper (steps: Step[] {title, description?}, current, onStepChange, orientation ‘horizontal’ | ‘vertical’, className). StepPanels (current, children, className).

src/components/ui/stepper.tsx
tsx

```tsx
"use client";

import * as React from "react";
import { AnimatePresence, motion, type Variants } from "framer-motion";
import { cn } from "../../lib/utils";

const spring = { type: "spring", stiffness: 420, damping: 34, mass: 0.8 } as const;
const fill = { duration: 0.35, ease: [0.32, 0.72, 0, 1] } as const;

export interface Step {
title: string;
description?: string;
}

export interface StepperProps {
steps: Step[];
/** Zero-based index of the active step. */
current: number;
/** Makes completed steps clickable (jump back). */
onStepChange?: (index: number) => void;
orientation?: "horizontal" | "vertical";
className?: string;
}

export function Stepper({ steps, current, onStepChange, orientation = "horizontal", className }: StepperProps) {
const uid = React.useId();
const vertical = orientation === "vertical";
const last = steps.length - 1;

// don't replay the check-draw for steps that are already done on first paint
const ready = React.useRef(false);
React.useEffect(() => {
ready.current = true;
}, []);

return (
<ol aria-label="Progress" className={cn(vertical ? "flex flex-col" : "flex w-full items-center", className)}>
{steps.map((step, i) => {
const state = i < current ? "complete" : i === current ? "current" : "upcoming";
const clickable = !!onStepChange && state === "complete";

const indicator = (
<span
className={cn(
"relative grid size-7 shrink-0 place-items-center rounded-full border text-xs font-medium tabular-nums transition-colors duration-300",
state === "complete" &&
"border-neutral-900 bg-neutral-900 text-white dark:border-white dark:bg-white dark:text-neutral-900",
state === "current" && "border-neutral-900 text-neutral-900 dark:border-white dark:text-white",
state === "upcoming" && "border-neutral-200 text-neutral-400 dark:border-neutral-800 dark:text-neutral-500"
)}
>
{state === "current" && (
<motion.span
layoutId={`${uid}-ring`}
transition={spring}
className="absolute -inset-[5px] rounded-full border border-neutral-300 dark:border-neutral-700"
/>
)}
{state === "complete" ? (
<svg
viewBox="0 0 24 24"
className="size-3.5"
fill="none"
stroke="currentColor"
strokeWidth={3}
strokeLinecap="round"
strokeLinejoin="round"
aria-hidden
>
<motion.path
d="M5 12.5l4.5 4.5L19 7.5"
initial={ready.current ? { pathLength: 0 } : false}
animate={{ pathLength: 1 }}
transition={{ duration: 0.3, delay: 0.08, ease: "easeOut" }}
/>
</svg>
) : (
i + 1
)}
</span>
);

const label = (
<span
className={cn(
"flex min-w-0 flex-col text-left",
!vertical && state !== "current" && "hidden sm:flex"
)}
>
<span
className={cn(
"truncate text-sm transition-colors duration-300",
state === "upcoming" ? "text-neutral-400 dark:text-neutral-500" : "font-medium text-neutral-900 dark:text-neutral-100"
)}
>
{step.title}
{state === "complete" && <span className="sr-only"> (completed)</span>}
</span>
{step.description && (
<span className="truncate text-xs text-neutral-400 dark:text-neutral-500">{step.description}</span>
)}
</span>
);

const row = clickable ? (
<button
type="button"
onClick={() => onStepChange!(i)}
className={cn(
"flex gap-3 rounded-lg text-left outline-none focus-visible:ring-2 focus-visible:ring-neutral-400/50 dark:focus-visible:ring-neutral-600/60",
vertical ? "items-start" : "items-center"
)}
>
{indicator}
{label}
</button>
) : (
<div className={cn("flex gap-3", vertical ? "items-start" : "items-center")}>
{indicator}
{label}
</div>
);

return (
<li
key={i}
aria-current={state === "current" ? "step" : undefined}
className={cn(
vertical ? "relative pb-7 last:pb-0" : "flex items-center",
!vertical && i < last && "flex-1"
)}
>
{row}

{i < last && (
<span
aria-hidden
className={cn(
"overflow-hidden bg-neutral-200 dark:bg-neutral-800",
vertical ? "absolute bottom-1 left-[13.5px] top-[34px] w-px" : "relative mx-3 h-px flex-1"
)}
>
<motion.span
initial={false}
animate={vertical ? { scaleY: i < current ? 1 : 0 } : { scaleX: i < current ? 1 : 0 }}
transition={fill}
className={cn(
"absolute inset-0 bg-neutral-900 dark:bg-white",
vertical ? "origin-top" : "origin-left"
)}
/>
</span>
)}
</li>
);
})}
</ol>
);
}

/* ───────────── panels: slide in the direction you're travelling ───────────── */

const slide: Variants = {
enter: (d: number) => ({ x: d * 24, opacity: 0 }),
center: { x: 0, opacity: 1 },
exit: (d: number) => ({ x: d * -24, opacity: 0 }),
};

export interface StepPanelsProps {
current: number;
/** One child per step, in order. */
children: React.ReactNode;
className?: string;
}

export function StepPanels({
current,
children,
className,
}: StepPanelsProps) {
const panels = React.Children.toArray(children);
const prev = React.useRef(current);
const dir = current >= prev.current ? 1 : -1;
React.useEffect(() => {
prev.current = current;
}, [current]);

return (
<div className={className}>
<AnimatePresence mode="wait" initial={false} custom={dir}>
<motion.div
key={current}
custom={dir}
variants={slide}
initial="enter"
animate="center"
exit="exit"
transition={{ duration: 0.18, ease: [0.32, 0.72, 0, 1] }}
>
{panels[current]}
</motion.div>
</AnimatePresence>
</div>
);
}
```

Usage example (from the site):
tsx

```tsx
import { Stepper, StepPanels, type Step } from "@/components/ui/stepper";

const steps: Step[] = [
{ title: "Account", description: "Your details" },
{ title: "Workspace", description: "Name it" },
{ title: "Invite", description: "Optional" },
{ title: "Done" },
];

const [current, setCurrent] = React.useState(0);

<Stepper steps={steps} current={current} onStepChange={setCurrent} />
<StepPanels current={current}>
<div>Step 1 content</div>
<div>Step 2 content</div>
<div>Step 3 content</div>
<div>Step 4 content</div>
</StepPanels>
```

* Completeness: complete for the component file. Only `lib/utils` (cn) is not shown on the site.

Reply “continue” for BATCH 5.
BATCH 4 is sent: spring-select, date-picker, calendar, stretch-switch, animated-file-upload and stepper.

* Calendar added: date-picker imports `./calendar`, so I included that file as “dependency of date-picker”.
* Missing token: spring-select uses the CSS variable `--shadow-elevated`, which isn’t in the G3 tokens I gave you earlier, so you’ll need to define it.
* Safe default upload: animated-file-upload only simulates uploads with a timer unless you pass your own handler, so it makes no network calls.
* Suspicious text: I found nothing new in this batch.

Reply “continue” for BATCH 5.