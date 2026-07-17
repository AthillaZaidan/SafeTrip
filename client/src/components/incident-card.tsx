import { Download } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface Incident {
  id: string;
  description: string;
  resolvedBy?: string;
  resolvedAt?: string;
  status: string;
}

/**
 * Harbor-navy incident card with the signature white
 * "Resolved by" inner strip. See docs/DESIGN.md §4.
 */
export function IncidentCard({
  incident,
  actionLabel,
  onStatusChange,
}: {
  incident: Incident;
  actionLabel?: string;
  onStatusChange?: (status: string) => void;
}) {
  const isResolved = !!incident.resolvedBy && incident.resolvedBy !== "Unassigned";
  
  return (
    <article className="flex flex-col gap-4 rounded-[24px] bg-white border border-hairline shadow-sm p-5">
      <div className="flex items-start justify-between">
        <h3 className="text-base font-bold text-ink">Incident #{incident.id}</h3>
        <button className="rounded-full p-1 text-muted transition-colors hover:bg-surface-strong hover:text-ink">
          <Download className="h-4 w-4" />
        </button>
      </div>

      <p className="line-clamp-2 text-sm leading-relaxed text-muted">
        {incident.description}
      </p>

      {/* Resolution block */}
      <div className="mt-2 flex items-center justify-between rounded-xl bg-surface-strong px-4 py-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "h-2 w-2 rounded-full",
                isResolved ? "bg-signal" : "bg-alert"
              )}
            />
            <span className="text-xs font-bold text-ink">
              {isResolved ? "Resolved by" : "Handled by"}
            </span>
          </div>
          <span className="text-sm font-semibold text-ink">
            {incident.resolvedBy ?? "Unassigned"}
          </span>
        </div>
        {incident.resolvedAt && (
          <span className="text-sm font-medium text-muted">
            {incident.resolvedAt}
          </span>
        )}
      </div>

      {/* Actions block */}
      <div className="mt-1 flex items-center gap-3">
        <a 
          href={`/dashboard/investigation?id=${incident.id}`}
          className="flex flex-1 items-center justify-center rounded-full border border-hairline py-2.5 text-sm font-bold text-ink transition-colors hover:bg-surface-strong"
        >
          Analyze
        </a>

        {incident.status === "open" && onStatusChange && (
          <button 
            onClick={() => onStatusChange("assigned")}
            className="flex-1 rounded-full bg-primary py-2.5 text-sm font-bold text-white transition-colors hover:bg-primary-active"
          >
            Assign
          </button>
        )}

        {(incident.status === "assigned" || incident.status === "in_progress") && onStatusChange && (
          <button 
            onClick={() => onStatusChange("resolved")}
            className="flex-1 rounded-full bg-signal py-2.5 text-sm font-bold text-white transition-colors hover:bg-signal/80"
          >
            Resolve
          </button>
        )}
        
        {/* Fallback for the original actionLabel prop if needed */}
        {actionLabel && !onStatusChange && (
          <button className="flex-1 rounded-full bg-primary py-2.5 text-sm font-bold text-white transition-colors hover:bg-primary-active">
            {actionLabel}
          </button>
        )}
      </div>
    </article>
  );
}
