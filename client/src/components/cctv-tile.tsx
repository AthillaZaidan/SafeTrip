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
  videoSrc,
}: {
  label: string;
  boxes: BoundingBox[];
  alert?: boolean;
  videoSrc?: string;
}) {
  return (
    <figure className="group relative overflow-hidden rounded-[20px] bg-slate-800 aspect-video shadow-sm transition-transform hover:shadow-md">
      {/* Video or Fallback texture */}
      {videoSrc ? (
        <video
          src={videoSrc}
          autoPlay
          muted
          loop
          playsInline
          className="absolute inset-0 h-full w-full object-cover"
        />
      ) : (
        <div className="absolute inset-0 bg-gradient-to-br from-slate-600 via-slate-500 to-slate-700 opacity-80">
          <div className="absolute inset-0 opacity-10 bg-[repeating-linear-gradient(90deg,transparent,transparent_46px,rgba(255,255,255,0.35)_47px),repeating-linear-gradient(0deg,transparent,transparent_46px,rgba(255,255,255,0.25)_47px)]" />
        </div>
      )}

      {/* Detection boxes */}
      {boxes.map((b, i) => (
        <span
          key={i}
          aria-hidden
          className={cn(
            "absolute rounded-[3px] border-2 md:border-[3px] transition-all",
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

      {/* Urgent overlay */}
      {alert && (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-ink/70 backdrop-blur-[2px] transition-opacity duration-300">
          <ShieldAlert className="h-10 w-10 text-alert animate-pulse" />
          <span className="rounded-full bg-alert px-3 py-1 text-xs font-bold text-white shadow-sm">
            Alert Security
          </span>
        </div>
      )}

      {/* Subtle bottom gradient for readability */}
      <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-ink/60 to-transparent pointer-events-none" />

      {/* Camera label */}
      <figcaption className="absolute bottom-3 left-4 flex items-center gap-2 text-xs font-bold text-white drop-shadow-md">
        <span className="h-2 w-2 rounded-full bg-alert animate-pulse shadow-[0_0_8px_rgba(239,68,68,0.8)]" aria-hidden />
        {label}
      </figcaption>
      
      {/* Expand affordance */}
      <button className="absolute bottom-3 right-4 rounded-full p-1.5 text-white/80 opacity-0 backdrop-blur-md bg-white/10 transition-all hover:bg-white/20 hover:text-white group-hover:opacity-100">
        <Maximize2 className="h-4 w-4 drop-shadow-md" />
      </button>
    </figure>
  );
}
