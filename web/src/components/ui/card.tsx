import type { ReactNode } from "react";
import { cn } from "../../lib/utils";

export function Card({ title, subtitle, actions, children, className, id }: {
  title?: ReactNode; subtitle?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string; id?: string;
}) {
  return (
    <section id={id} className={cn("min-w-0 rounded-2xl border border-line bg-surface p-4 shadow-card sm:p-5", className)} aria-label={typeof title === "string" ? title : undefined}>
      {(title || actions) && (
        <header className="mb-3 flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
          <div className="min-w-0">
            {title && <h2 className="text-[14px] font-semibold tracking-tight text-ink">{title}</h2>}
            {subtitle && <p className="mt-0.5 text-[12.5px] text-muted">{subtitle}</p>}
          </div>
          {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
        </header>
      )}
      {children}
    </section>
  );
}
