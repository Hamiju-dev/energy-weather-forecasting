BATCH 5 of 6
Alert (alert)

* Category / priority: FEEDBACK / high (data-feed warnings, model errors, forecast-outage notices)
* Page: https://easyui.site/components/alert
* Licence shown on page: none shown
* Description: Alert box that collapses in height and opacity when dismissed, with tone-based icons, an action slot and ARIA roles.
* Dependencies: react, framer-motion (AnimatePresence, motion), lucide-react (CircleAlert, CircleCheck, Info, TriangleAlert, X, type LucideIcon), `../../lib/utils` (cn). Tailwind `neutral/sky/emerald/amber/red` colours with `dark:` variants; no site tokens, no `focus-ring`. Needs a recent lucide-react (the `CircleAlert` and `CircleCheck` names).
* Visual notes: Rounded-xl bordered box with a tinted background per tone (neutral, info, success, warning, danger), a 16px tone-coloured icon on the left, content in the middle, optional action on the right, and a small close button.
* Interaction notes: Dismiss collapses height and opacity over 0.25 s; `onDismiss` is called after the animation ends. Dismissal state is internal only (cannot be re-shown by a prop). Role is `alert` for danger and warning, `status` otherwise.
* Props: tone (‘neutral’ default | ‘info’ | ‘success’ | ‘warning’ | ‘danger’), icon (ReactNode | false), dismissible, onDismiss, action, className, plus any div props. Also exports AlertTitle and AlertDescription.

src/components/ui/alert.tsx
tsx

```tsx
"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { CircleAlert, CircleCheck, Info, TriangleAlert, X, type LucideIcon } from "lucide-react";
import { cn } from "../../lib/utils";

export type AlertTone = "neutral" | "info" | "success" | "warning" | "danger";

const tones: Record<AlertTone, { box: string; icon: string; Icon: LucideIcon }> = {
neutral: {
box: "border-neutral-200 bg-neutral-50/70 dark:border-neutral-800 dark:bg-neutral-900/60",
icon: "text-neutral-500 dark:text-neutral-400",
Icon: Info,
},
info: {
box: "border-sky-200 bg-sky-50/70 dark:border-sky-500/30 dark:bg-sky-500/12",
icon: "text-sky-600 dark:text-sky-400",
Icon: Info,
},
success: {
box: "border-emerald-200 bg-emerald-50/70 dark:border-emerald-500/30 dark:bg-emerald-500/12",
icon: "text-emerald-600 dark:text-emerald-400",
Icon: CircleCheck,
},
warning: {
box: "border-amber-200 bg-amber-50/70 dark:border-amber-500/30 dark:bg-amber-500/12",
icon: "text-amber-600 dark:text-amber-400",
Icon: TriangleAlert,
},
danger: {
box: "border-red-200 bg-red-50/70 dark:border-red-500/30 dark:bg-red-500/12",
icon: "text-red-600 dark:text-red-400",
Icon: CircleAlert,
},
};

export interface AlertProps extends Omit<React.ComponentProps<"div">, "title"> {
tone?: AlertTone;
/** Custom icon, or `false` for none. */
icon?: React.ReactNode | false;
dismissible?: boolean;
/** Fires after the collapse animation finishes. */
onDismiss?: () => void;
/** Right-side slot, e.g. a button. */
action?: React.ReactNode;
}

export function Alert({
tone = "neutral",
icon,
dismissible,
onDismiss,
action,
className,
children,
...props
}: AlertProps) {
const [visible, setVisible] = React.useState(true);
const t = tones[tone];

return (
<AnimatePresence initial={false} onExitComplete={onDismiss}>
{visible && (
<motion.div
key="alert"
initial={false}
animate={{ height: "auto", opacity: 1 }}
exit={{ height: 0, opacity: 0 }}
transition={{ duration: 0.25, ease: [0.32, 0.72, 0, 1] }}
className="overflow-hidden"
>
<div
role={tone === "danger" || tone === "warning" ? "alert" : "status"}
className={cn("flex items-start gap-3 rounded-xl border p-4 text-sm", t.box, className)}
{...props}
>
{icon !== false && (
<span className={cn("mt-0.5 shrink-0 [&>svg]:size-4", t.icon)}>{icon ?? <t.Icon />}</span>
)}
<div className="min-w-0 flex-1">{children}</div>
{action && <div className="-my-1 shrink-0">{action}</div>}
{dismissible && (
<button
type="button"
aria-label="Dismiss"
onClick={() => setVisible(false)}
className="-mr-1 -mt-1 grid size-7 shrink-0 place-items-center rounded-lg text-neutral-400 outline-none transition hover:bg-black/5 hover:text-neutral-900 focus-visible:ring-2 focus-visible:ring-neutral-400/50 active:scale-95 dark:hover:bg-white/10 dark:hover:text-white dark:focus-visible:ring-neutral-600/60"
>
<X className="size-4" />
</button>
)}
</div>
</motion.div>
)}
</AnimatePresence>
);
}

export function AlertTitle({ className, ...props }: React.ComponentProps<"p">) {
return <p className={cn("font-medium text-neutral-900 dark:text-neutral-100", className)} {...props} />;
}

export function AlertDescription({ className, ...props }: React.ComponentProps<"p">) {
return <p className={cn("mt-0.5 text-neutral-600 dark:text-neutral-400", className)} {...props} />;
}
```

Usage example (from the site):
tsx

```tsx
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";

<Alert tone="danger" dismissible onDismiss={() => handleDismiss()}>
<AlertTitle>Payment failed</AlertTitle>
<AlertDescription>Your card was declined. Please try another card.</AlertDescription>
</Alert>

<Alert tone="success">
<AlertTitle>Changes saved successfully</AlertTitle>
</Alert>
```

* Completeness: complete for the component file. Only `lib/utils` (cn) is not shown on the site.

Notification Stack (notification-stack)

* Category / priority: FEEDBACK / medium (alarm and event inbox)
* Page: https://easyui.site/components/notification-stack
* Licence shown on page: none shown
* Description: Stacked notification cards with spring elevation, swipe-right-to-dismiss, and a “Simulate” button that adds fake items.
* Dependencies: react, framer-motion, lucide-react (CheckCircle2, AlertCircle, Info, X, Bell), `../../lib/utils` (cn), `../../lib/motion-tokens` (`motionTransitions.springResponsive`, NOT confirmed in the G5 tokens recorded earlier). Hard-coded dark hex colours (dark-only).
* Visual notes: Header row with a bell icon and “Notifications (n)” plus “+ Simulate” and “Expand/Stack” links; below it a pile of cards, each offset by 12px and scaled down by 4% per level (compact view) or listed at 74px steps (expanded). Each card has a type icon, title, relative time, description and a close button.
* Interaction notes: Drag on the x axis; a drag of more than 60px to the right dismisses. Close button also dismisses. Compact view shows `maxVisible` cards. Items live in internal state only (`initialNotifications` is just the initial value, there is no `onDismiss`/`onChange` callback). The default initial items are demo data (deployment, component sync, API limit), and the “+ Simulate” action is demo-only.
* Props: initialNotifications (NotificationItem: id, title, description, type ‘success’ | ‘info’ | ‘warning’, time) with a built-in default of 3 demo items (the site’s API table says default `[]`, which does not match the code), className, maxVisible (3).

src/components/ui/notification-stack.tsx
tsx

```tsx
'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Info, X, Bell } from 'lucide-react';
import { cn } from '../../lib/utils';
import { motionTransitions } from '../../lib/motion-tokens';

export interface NotificationItem {
id: string;
title: string;
description: string;
type?: 'success' | 'info' | 'warning';
time?: string;
}

export interface NotificationStackProps {
initialNotifications?: NotificationItem[];
className?: string;
maxVisible?: number;
}

export const NotificationStack: React.FC<NotificationStackProps> = ({
initialNotifications = [
{
id: '1',
title: 'Deployment Successful',
description: 'Production build v2.4.0 deployed to edge nodes.',
type: 'success',
time: 'Just now',
},
{
id: '2',
title: 'Component Synced',
description: 'magnetic-button synced from EasyUI GitHub registry.',
type: 'info',
time: '2m ago',
},
{
id: '3',
title: 'API Limit Warning',
description: '85% of monthly request quota utilized.',
type: 'warning',
time: '10m ago',
},
],
className,
maxVisible = 3,
}) => {
const [notifications, setNotifications] = useState<NotificationItem[]>(initialNotifications);
const [isExpanded, setIsExpanded] = useState(false);

const dismiss = (id: string) => {
setNotifications((prev) => prev.filter((n) => n.id !== id));
};

const addSampleNotification = () => {
const types: ('success' | 'info' | 'warning')[] = ['success', 'info', 'warning'];
const randomType = types[Math.floor(Math.random() * types.length)];
const newNotif: NotificationItem = {
id: Date.now().toString(),
title: randomType === 'success' ? 'Cache Invalidation Done' : randomType === 'warning' ? 'High Memory Usage' : 'New Webhook Triggered',
description: 'Triggered by automated pipeline workflow #841.',
type: randomType,
time: 'Just now',
};
setNotifications((prev) => [newNotif, ...prev]);
};

const getIcon = (type?: 'success' | 'info' | 'warning') => {
switch (type) {
case 'success':
return <CheckCircle2 className="w-4 h-4 text-white" />;
case 'warning':
return <AlertCircle className="w-4 h-4 text-[#D4D4D4]" />;
default:
return <Info className="w-4 h-4 text-[#ECECEC]" />;
}
};

return (
<div className={cn('flex flex-col gap-3 max-w-sm w-full select-none', className)}>
<div className="flex items-center justify-between px-1">
<div className="flex items-center gap-2 text-xs font-medium text-[#A1A1A1]">
<Bell className="w-3.5 h-3.5 text-[#525252]" />
<span>Notifications ({notifications.length})</span>
</div>
<div className="flex items-center gap-2">
<button
onClick={addSampleNotification}
className="text-[11px] text-[#FAFAFA] hover:text-white font-medium transition-colors cursor-pointer"
>
+ Simulate
</button>
<button
onClick={() => setIsExpanded(!isExpanded)}
className="text-[11px] text-[#6B6B6B] hover:text-[#A1A1A1] transition-colors cursor-pointer"
>
{isExpanded ? 'Stack' : 'Expand'}
</button>
</div>
</div>

<div className="relative min-h-[140px]">
<AnimatePresence mode="popLayout">
{notifications.length === 0 ? (
<motion.div
initial={{ opacity: 0 }}
animate={{ opacity: 1 }}
className="p-6 text-center rounded-xl border border-[#1F1F1F] bg-[#0E0E0E] text-xs text-[#6B6B6B]"
>
No pending notifications
</motion.div>
) : (
notifications.slice(0, isExpanded ? notifications.length : maxVisible).map((item, index) => {
const offset = index * 12;
const scale = 1 - index * 0.04;
const zIndex = notifications.length - index;

return (
<motion.div
key={item.id}
layout
initial={{ opacity: 0, y: -20, scale: 0.95 }}
animate={{
opacity: 1,
y: isExpanded ? index * 74 : offset,
scale: isExpanded ? 1 : scale,
zIndex,
}}
exit={{ opacity: 0, x: 80, scale: 0.9 }}
transition={motionTransitions.springResponsive}
drag="x"
dragConstraints={{ left: 0, right: 100 }}
onDragEnd={(_, info) => {
if (info.offset.x > 60) {
dismiss(item.id);
}
}}
style={{
position: isExpanded ? 'relative' : 'absolute',
top: 0,
left: 0,
right: 0,
}}
className="rounded-xl border border-[#1F1F1F] bg-[#0E0E0E] p-3.5 shadow-md cursor-grab active:cursor-grabbing hover:border-[#4A4A4A] transition-colors"
>
<div className="flex items-start justify-between gap-2">
<div className="flex items-start gap-2.5">
<div className="mt-0.5 shrink-0">{getIcon(item.type)}</div>
<div>
<div className="flex items-center gap-2">
<h4 className="text-xs font-semibold text-[#FAFAFA]">{item.title}</h4>
<span className="text-[10px] text-[#6B6B6B]">{item.time}</span>
</div>
<p className="text-[11px] text-[#A1A1A1] mt-0.5 leading-snug">
{item.description}
</p>
</div>
</div>
<button
onClick={() => dismiss(item.id)}
className="text-[#525252] hover:text-[#FAFAFA] p-0.5 rounded transition-colors cursor-pointer"
aria-label="Dismiss"
>
<X className="w-3.5 h-3.5" />
</button>
</div>
</motion.div>
);
})
)}
</AnimatePresence>
</div>
</div>
);
};
```

Usage example (from the site):
tsx

```tsx
import { NotificationStack } from "@/components/ui/notification-stack";

export function Demo() {
return <NotificationStack maxVisible={3} />;
}
```

* Completeness: complete for the component file. `lib/utils` and `lib/motion-tokens` (including `springResponsive`) not shown on the site. Contains demo strings that mention “EasyUI GitHub registry”; these are plain text, not instructions, and should be replaced when reused.

Skeleton (skeleton)

* Category / priority: FEEDBACK / high (loading placeholders for charts and cards)
* Page: https://easyui.site/components/skeleton
* Licence shown on page: none shown
* Description: Placeholder blocks with a slow light sweep, text and avatar presets, and a `SkeletonReveal` wrapper that fades, lifts and un-blurs the real content in.
* Dependencies: react, framer-motion (AnimatePresence, motion), `../../lib/utils` (cn). Tailwind `neutral-*` with `dark:` variants and an arbitrary CSS variable `--sk` for the sweep colour; no site tokens.
* Visual notes: Rounded-md blocks in neutral-200/70 (neutral-800/70 dark) with a moving soft white highlight (1.6 s loop with a 0.2 s pause). Text preset has 14px lines with varied widths and a last line at 62%.
* Interaction notes: Decorative (`aria-hidden`) blocks; `SkeletonReveal` wraps the skeleton in `role="status" aria-busy="true"`. The sweep animation runs forever and ignores the reduced-motion setting.
* Props: Skeleton (div props, size with className), SkeletonText (lines 3, className), SkeletonAvatar (size 40, className), SkeletonReveal (loading, skeleton, children, className).

src/components/ui/skeleton.tsx
tsx

```tsx
"use client";

import * as React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { cn } from "../../lib/utils";

export interface SkeletonProps extends React.ComponentProps<"div"> {}

/** A quiet block with a slow light sweep. Size it with className. */
export function Skeleton({ className, ...props }: SkeletonProps) {
return (
<div
aria-hidden
className={cn("relative overflow-hidden rounded-md bg-neutral-200/70 dark:bg-neutral-800/70", className)}
{...props}
>
<motion.span
className="absolute inset-0 bg-[linear-gradient(90deg,transparent,var(--sk),transparent)] [--sk:rgb(255_255_255/0.65)] dark:[--sk:rgb(255_255_255/0.07)]"
initial={{ x: "-100%" }}
animate={{ x: "100%" }}
transition={{ duration: 1.6, ease: "easeInOut", repeat: Infinity, repeatDelay: 0.2 }}
/>
</div>
);
}

const WIDTHS = ["100%", "94%", "98%", "88%"];

export interface SkeletonTextProps {
lines?: number;
className?: string;
}

export function SkeletonText({
lines = 3,
className,
}: SkeletonTextProps) {
return (
<div aria-hidden className={cn("space-y-2.5", className)}>
{Array.from({ length: lines }, (_, i) => (
<Skeleton
key={i}
className="h-3.5"
style={{ width: i === lines - 1 && lines > 1 ? "62%" : WIDTHS[i % WIDTHS.length] }}
/>
))}
</div>
);
}

export interface SkeletonAvatarProps {
size?: number;
className?: string;
}

export function SkeletonAvatar({ size = 40, className }: SkeletonAvatarProps) {
return <Skeleton className={cn("shrink-0 rounded-full", className)} style={{ width: size, height: size }} />;
}

export interface SkeletonRevealProps {
loading: boolean;
skeleton: React.ReactNode;
children: React.ReactNode;
className?: string;
}

/**
* Swap a skeleton for real content. Content eases in (fade, rise, un-blur).
* Make the skeleton roughly the same size as the content so nothing jumps.
*/
export function SkeletonReveal({
loading,
skeleton,
children,
className,
}: SkeletonRevealProps) {
return (
<div className={className}>
<AnimatePresence mode="wait" initial={false}>
{loading ? (
<motion.div
key="skeleton"
role="status"
aria-busy="true"
aria-label="Loading"
initial={{ opacity: 0 }}
animate={{ opacity: 1 }}
exit={{ opacity: 0 }}
transition={{ duration: 0.12 }}
>
{skeleton}
</motion.div>
) : (
<motion.div
key="content"
initial={{ opacity: 0, y: 6, filter: "blur(4px)" }}
animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
transition={{ duration: 0.3, ease: [0.32, 0.72, 0, 1] }}
>
{children}
</motion.div>
)}
</AnimatePresence>
</div>
);
}
```

Usage example (from the site):
tsx

```tsx
import { Skeleton, SkeletonAvatar, SkeletonText, SkeletonReveal } from "@/components/ui/skeleton";

<SkeletonReveal
loading={isLoading}
skeleton={
<div className="flex gap-3">
<SkeletonAvatar size={40} />
<div className="flex-1 space-y-2">
<Skeleton className="h-4 w-1/3" />
<SkeletonText lines={2} />
</div>
</div>
}
>
<UserCard user={user} />
</SkeletonReveal>
```

* Completeness: complete for the component file. Only `lib/utils` (cn) is not shown on the site.

 <!-- CONTINUES IN NEXT MESSAGE -->
<!-- CONTINUED: BATCH 5 of 6, components loader and directional-tooltip -->
Loader (loader)

* Category / priority: FEEDBACK / medium (spinner for model or API requests)
* Page: https://easyui.site/components/loader
* Licence shown on page: none shown
* Description: Minimal loading indicator with four calm variants: arc, dots, line and rings.
* Dependencies: react, framer-motion (motion), `../../lib/utils` (cn). The arc variant uses Tailwind `animate-spin`. Hard-coded dark colours (`#FAFAFA` text, `#1F1F1F` track, `#141414` line track), so it is dark-oriented; the colour prop can override the stroke.
* Visual notes: arc = grey ring with a 35% arc rotating slowly (2.5 s per turn); dots = three breathing dots; line = a bar sliding across a 2× width track; rings = two expanding fading rings around a centre dot. The site demo shows the four variants on a near-black card.
* Interaction notes: `role="status"` with `aria-busy` and a screen-reader label. `reduceMotion` swaps the motion for a gentle opacity pulse in dots, line and rings, but does NOT stop the arc spin (the `animate-spin` class is removed, so the arc just stays still). It does not read the system `prefers-reduced-motion` setting itself.
* Props: size (32), variant (‘arc’ | ‘dots’ | ‘line’ | ‘rings’, default ‘arc’), label (‘Loading...’), reduceMotion (false), color (‘currentColor’), className, plus div props.

src/components/ui/loader.tsx
tsx

```tsx
'use client';

import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

export interface LoaderProps extends React.HTMLAttributes<HTMLDivElement> {
/** Size of the loader in pixels. Default is 32. */
size?: number;
/** Visual animation style variant. Default is 'arc'. */
variant?: 'arc' | 'dots' | 'line' | 'rings';
/** Optional accessible text label. */
label?: string;
/** Force reduced motion if true. */
reduceMotion?: boolean;
/** Custom stroke / fill color. Default inherits or neutral. */
color?: string;
}

export const Loader: React.FC<LoaderProps> = ({
size = 32,
variant = 'arc',
label = 'Loading...',
reduceMotion = false,
color = 'currentColor',
className,
...props
}) => {
return (
<div
role="status"
aria-busy="true"
aria-label={label}
className={cn('inline-flex flex-col items-center justify-center gap-2 text-[#FAFAFA]', className)}
{...props}
>
{/* 1. Rotating Arc Variant */}
{variant === 'arc' && (
<div style={{ width: size, height: size }} className="relative flex items-center justify-center">
<svg
className={cn('w-full h-full', !reduceMotion && 'animate-spin')}
style={{ animationDuration: '2.5s' }}
viewBox="0 0 40 40"
fill="none"
xmlns="http://www.w3.org/2000/svg"
>
<circle
cx="20"
cy="20"
r="16"
stroke="#1F1F1F"
strokeWidth="3"
className="opacity-60"
/>
<motion.circle
cx="20"
cy="20"
r="16"
stroke={color}
strokeWidth="3"
strokeLinecap="round"
strokeDasharray="100"
strokeDashoffset="65"
/>
</svg>
</div>
)}

{/* 2. Breathing Dots Variant */}
{variant === 'dots' && (
<div
style={{ width: size * 1.5, height: size * 0.4 }}
className="flex items-center justify-center gap-1.5"
>
{[0, 1, 2].map((i) => (
<motion.span
key={i}
className="rounded-full bg-current"
style={{
width: Math.max(4, size * 0.18),
height: Math.max(4, size * 0.18),
backgroundColor: color !== 'currentColor' ? color : undefined,
}}
animate={
reduceMotion
? { opacity: [0.3, 0.8, 0.3] }
: {
scale: [0.8, 1.25, 0.8],
opacity: [0.3, 1, 0.3],
}
}
transition={{
duration: 1.4,
repeat: Infinity,
delay: i * 0.22,
ease: 'easeInOut',
}}
/>
))}
</div>
)}

{/* 3. Sliding Line Variant */}
{variant === 'line' && (
<div
style={{ width: size * 2, height: Math.max(3, size * 0.08) }}
className="relative rounded-full bg-[#141414] overflow-hidden"
>
<motion.div
className="absolute top-0 bottom-0 rounded-full"
style={{
width: '35%',
backgroundColor: color !== 'currentColor' ? color : '#FAFAFA',
}}
animate={
reduceMotion
? { opacity: [0.4, 1, 0.4] }
: {
left: ['-35%', '100%'],
}
}
transition={{
duration: 1.8,
repeat: Infinity,
ease: [0.4, 0, 0.2, 1],
}}
/>
</div>
)}

{/* 4. Concentric Expanding Rings Variant */}
{variant === 'rings' && (
<div style={{ width: size, height: size }} className="relative flex items-center justify-center">
{[0, 1].map((i) => (
<motion.span
key={i}
className="absolute inset-0 rounded-full border border-current"
style={{
borderColor: color !== 'currentColor' ? color : undefined,
}}
animate={
reduceMotion
? { opacity: [0.2, 0.6, 0.2] }
: {
scale: [0.6, 1.15],
opacity: [0.8, 0],
}
}
transition={{
duration: 2.2,
repeat: Infinity,
delay: i * 0.9,
ease: 'easeOut',
}}
/>
))}
<span
className="rounded-full bg-current"
style={{
width: Math.max(4, size * 0.2),
height: Math.max(4, size * 0.2),
backgroundColor: color !== 'currentColor' ? color : undefined,
}}
/>
</div>
)}

{label && <span className="sr-only">{label}</span>}
</div>
);
};
```

Usage example (from the site):
tsx

```tsx
import { Loader } from "@/components/ui/loader";

export function Demo() {
return (
<div className="flex items-center gap-6 p-8 bg-[#0A0A0A] rounded-2xl border border-[#222222]">
<Loader variant="arc" size={32} />
<Loader variant="dots" size={28} />
<Loader variant="line" size={36} />
<Loader variant="rings" size={32} />
</div>
);
}
```

* Completeness: complete for the component file. Only `lib/utils` (cn) is not shown on the site.

Directional Tooltip (directional-tooltip)

* Category / priority: OVERLAYS / high (chart and KPI hover explanations)
* Page: https://easyui.site/components/directional-tooltip
* Licence shown on page: none shown
* Description: Tooltip that springs in from the side it points to, so it appears to come out of the trigger.
* Dependencies: react, framer-motion, `../../lib/utils` (cn), `../../lib/motion-tokens` (`springSnappy`). Uses site CSS variables `--border`, `--surface`, `--text-primary`, `--shadow-elevated` (the last is NOT confirmed in G3). The site’s usage example also uses `PressButton`, but only as an example trigger, not as an import of the component file.
* Visual notes: Small rounded-md bubble (12px text, no wrapping, max-w-xs) with a border, surface background, elevation shadow and an optional 8px arrow that takes the border colour.
* Interaction notes: Opens on hover or focus after `delayDuration` (150 ms), closes on leave or blur; the trigger must be a single React element that accepts a ref and mouse/focus handlers. Entry offset is 8px from the chosen side. `forceOpen` keeps it open for previews. `aria-describedby` points to the tooltip while open. No automatic flipping despite the code comment (side stays as given), no Escape handling, and no touch support. The `offset` prop is applied as an inline `margin` on all four sides, which overrides the `mb-2` / `mt-2` spacing classes. Align classes are added after side classes, so their `left/top/right/bottom` rules depend on Tailwind’s generated order (check the result when using `align` other than center).
* Props: content, side (‘top’ default | ‘right’ | ‘bottom’ | ‘left’), align (‘start’ | ‘center’ | ‘end’), delayDuration (150), showArrow (true), offset (8), className, forceOpen (false), children (single element).

src/components/ui/directional-tooltip.tsx
tsx

```tsx
'use client';

import React, { useState, useRef, useId } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '../../lib/utils';
import { motionTransitions } from '../../lib/motion-tokens';

export type TooltipSide = 'top' | 'right' | 'bottom' | 'left';
export type TooltipAlign = 'start' | 'center' | 'end';

export interface DirectionalTooltipProps {
/** Trigger element(s) */
children: React.ReactElement;
/** Tooltip content */
content: React.ReactNode;
/** Preferred side; may be flipped if there's no space (auto by default) */
side?: TooltipSide;
/** Alignment along the side */
align?: TooltipAlign;
/** Delay before showing, in ms */
delayDuration?: number;
/** Whether to show an arrow */
showArrow?: boolean;
/** Offset from the trigger in px */
offset?: number;
className?: string;
/** Force the tooltip to always be visible (for design previews) */
forceOpen?: boolean;
}

const sideTransform: Record<TooltipSide, { x: number; y: number }> = {
top: { x: 0, y: 8 },
right: { x: -8, y: 0 },
bottom: { x: 0, y: -8 },
left: { x: 8, y: 0 },
};

const sideStyles: Record<TooltipSide, string> = {
top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
right: 'left-full top-1/2 -translate-y-1/2 ml-2',
bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
left: 'right-full top-1/2 -translate-y-1/2 mr-2',
};

const arrowStyles: Record<TooltipSide, { position: string; borderColorSide: string }> = {
top: {
position: 'top-full left-1/2 -translate-x-1/2 -translate-y-1/2 border-l-transparent border-r-transparent border-b-transparent',
borderColorSide: 'borderTopColor',
},
right: {
position: 'right-full top-1/2 -translate-y-1/2 translate-x-1/2 border-t-transparent border-b-transparent border-l-transparent',
borderColorSide: 'borderRightColor',
},
bottom: {
position: 'bottom-full left-1/2 -translate-x-1/2 translate-y-1/2 border-l-transparent border-r-transparent border-t-transparent',
borderColorSide: 'borderBottomColor',
},
left: {
position: 'left-full top-1/2 -translate-y-1/2 -translate-x-1/2 border-t-transparent border-b-transparent border-r-transparent',
borderColorSide: 'borderLeftColor',
},
};

const alignStyles: Record<TooltipAlign, Record<TooltipSide, string>> = {
start: {
top: 'left-0 translate-x-0',
right: 'top-0 translate-y-0',
bottom: 'left-0 translate-x-0',
left: 'top-0 translate-y-0',
},
center: {
top: 'left-1/2 -translate-x-1/2',
right: 'top-1/2 -translate-y-1/2',
bottom: 'left-1/2 -translate-x-1/2',
left: 'top-1/2 -translate-y-1/2',
},
end: {
top: 'right-0 translate-x-0',
right: 'bottom-0 translate-y-0',
bottom: 'right-0 translate-x-0',
left: 'bottom-0 translate-y-0',
},
};

/**
* DirectionalTooltip — Appears from the direction it originates.
* The tooltip starts a small distance outside the trigger in its preferred
* direction and springs inward, so the user perceives it as materializing
* from the trigger toward the content.
*/
export const DirectionalTooltip: React.FC<DirectionalTooltipProps> = ({
children,
content,
side = 'top',
align = 'center',
delayDuration = 150,
showArrow = true,
offset = 8,
className,
forceOpen = false,
}) => {
const [open, setOpen] = useState(false);
const triggerRef = useRef<HTMLElement | null>(null);
const timeoutRef = useRef<number | null>(null);
const id = useId();

const handleOpen = () => {
if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
timeoutRef.current = window.setTimeout(() => setOpen(true), delayDuration);
};
const handleClose = () => {
if (timeoutRef.current) window.clearTimeout(timeoutRef.current);
setOpen(false);
};

// Clone the trigger and wire ref + hover handlers
const trigger = React.cloneElement(children, {
ref: (node: HTMLElement | null) => {
triggerRef.current = node;
// forward existing ref if any
const existingRef = (children as any).ref;
if (typeof existingRef === 'function') existingRef(node);
else if (existingRef && 'current' in existingRef) {
(existingRef as any).current = node;
}
},
onMouseEnter: (e: React.MouseEvent) => {
handleOpen();
(children.props as any).onMouseEnter?.(e);
},
onMouseLeave: (e: React.MouseEvent) => {
handleClose();
(children.props as any).onMouseLeave?.(e);
},
onFocus: (e: React.FocusEvent) => {
handleOpen();
(children.props as any).onFocus?.(e);
},
onBlur: (e: React.FocusEvent) => {
handleClose();
(children.props as any).onBlur?.(e);
},
'aria-describedby': open ? id : undefined,
} as any);

const isOpen = open || forceOpen;
const offsetT = sideTransform[side];
const applyOffset = (val: number) => val + (Math.sign(val) || 0) * 0; // keep tiny entry; offset handled by CSS spacing

return (
<span className="relative inline-flex">
{trigger}
<AnimatePresence>
{isOpen && (
<motion.div
id={id}
role="tooltip"
initial={{
opacity: 0,
scale: 0.94,
x: applyOffset(offsetT.x),
y: applyOffset(offsetT.y),
}}
animate={{ opacity: 1, scale: 1, x: 0, y: 0 }}
exit={{
opacity: 0,
scale: 0.96,
x: applyOffset(offsetT.x) * 0.5,
y: applyOffset(offsetT.y) * 0.5,
}}
transition={motionTransitions.springSnappy}
className={cn(
'absolute z-50 max-w-xs whitespace-nowrap rounded-md border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] shadow-[var(--shadow-elevated)] px-2.5 py-1.5 text-xs leading-relaxed',
sideStyles[side],
alignStyles[align][side],
className
)}
style={{ margin: offset }}
>
{content}
{showArrow && (
<span
aria-hidden="true"
className={cn('absolute w-2 h-2 border-4', arrowStyles[side].position)}
style={{ [arrowStyles[side].borderColorSide]: 'var(--border)' } as React.CSSProperties}
/>
)}
</motion.div>
)}
</AnimatePresence>
</span>
);
};
```

Usage example (from the site):
tsx

```tsx
import { DirectionalTooltip } from "@/components/ui/directional-tooltip";
import { PressButton } from "@/components/ui/press-button";

export function Demo() {
return (
<div className="flex flex-wrap gap-4">
<DirectionalTooltip content="Save your changes" side="top">
<PressButton>Save</PressButton>
</DirectionalTooltip>
<DirectionalTooltip content="Open command palette ⌘K" side="bottom" align="end">
<PressButton variant="secondary">Search</PressButton>
</DirectionalTooltip>
</div>
);
}
```

* Completeness: complete for the component file. `lib/utils`, `lib/motion-tokens` and the `--shadow-elevated` variable are not shown on the site. The example’s `PressButton` is not part of the requested scope and was not collected here.

Reply “continue” for BATCH 6.
BATCH 5 (alert, notification-stack, skeleton, loader, directional-tooltip) is sent in two messages. Three things to know:

* Another token missing: notification-stack uses `motionTransitions.springResponsive`, which isn’t in the G5 set I gave you. `springMorph` from BATCH 3 is also missing, so the shared motion-token file needs both.
* `--shadow-elevated` again: directional-tooltip uses the same undefined CSS variable as spring-select in BATCH 4.
* Not a prompt injection: notification-stack contains demo text that mentions the “EasyUI GitHub registry”. It’s plain text, so I’m not logging it as suspicious. I flagged it for replacement when you reuse it.

Nothing else suspicious turned up. Reply “continue” for BATCH 6.