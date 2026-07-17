import { Maximize2, ShieldAlert } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface BoundingBox {
  /** percentages */
  x: number;
  y: number;
  w: number;
  h: number;
  kind: "flag" | "track";
}

/**
 * A CCTV feed placeholder tile: live dot + camera label,
 * expand affordance, and mock detection bounding boxes.
 */
export function CctvTile({
  label,
  boxes,
  alert = false,
}: {
  label: string;
  boxes: BoundingBox[];
  alert?: boolean;
}) {
  return (
    <figure className="relative overflow-hidden rounded-xl bg-gradient-to-br from-slate-500 via-slate-400 to-slate-600 aspect-video">
      {/* Fake scene texture */}
      <div className="absolute inset-0 opacity-20 bg-[repeating-linear-gradient(90deg,transparent,transparent_46px,rgba(255,255,255,0.35)_47px),repeating-linear-gradient(0deg,transparent,transparent_46px,rgba(255,255,255,0.25)_47px)]" />

      {/* Detection boxes */}
      {boxes.map((b, i) => (
        <span
          key={i}
          aria-hidden
          className={cn(
            "absolute rounded-[3px] border-[3px]",
            b.kind === "flag" ? "border-alert" : "border-signal"
          )}
          style={{
            left: `${b.x}%`,
            top: `${b.y}%`,
            width: `${b.w}%`,
            height: `${b.h}%`,
          }}
        />
      ))}

      {/* Urgent overlay (Dark scrim only for urgent) */}
      {alert && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-ink/70">
          <ShieldAlert className="h-10 w-10 text-alert animate-pulse" />
          <span className="rounded-full bg-alert px-3 py-1 text-xs font-bold text-white uppercase tracking-wider">
            Alert Security
          </span>
        </div>
      )}

      {/* Camera label */}
      <figcaption className="absolute bottom-2 left-2 flex items-center gap-1.5 text-[11px] font-medium text-white drop-shadow">
        <span className="h-2 w-2 rounded-full bg-alert" aria-hidden />
        {label}
      </figcaption>
      <Maximize2 className="absolute bottom-2 right-2 h-4 w-4 text-white/90 drop-shadow" />
    </figure>
  );
}
