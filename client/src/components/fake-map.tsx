import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Lightweight CSS map placeholder: streets texture with an
 * optional drawn route between an origin and destination pin.
 */
export function FakeMap({
  className,
  route = false,
}: {
  className?: string;
  route?: boolean;
}) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-xl bg-[#e8ece4]",
        className
      )}
      aria-label="Map preview"
      role="img"
    >
      {/* Street grid */}
      <div className="absolute inset-0 bg-[repeating-linear-gradient(23deg,transparent,transparent_34px,rgba(255,255,255,0.9)_35px),repeating-linear-gradient(112deg,transparent,transparent_52px,rgba(255,255,255,0.75)_53px),repeating-linear-gradient(78deg,transparent,transparent_90px,rgba(190,200,190,0.5)_91px)]" />
      {/* Water / park hints */}
      <div className="absolute -left-10 top-6 h-24 w-40 rounded-full bg-[#c9ddd6]/70" />
      <div className="absolute right-4 bottom-4 h-20 w-32 rounded-full bg-[#d3e3c8]/70" />

      {route && (
        <>
          {/* Route line */}
          <svg
            className="absolute inset-0 h-full w-full"
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            aria-hidden
          >
            <path
              d="M18 16 C 35 30, 55 34, 58 52 S 70 82, 84 86"
              fill="none"
              stroke="#d92d20"
              strokeWidth="2.6"
              strokeLinecap="round"
            />
          </svg>
          {/* Origin / destination dots */}
          <span className="absolute left-[15%] top-[12%] h-3 w-3 rounded-full border-2 border-white bg-signal shadow" />
          <span className="absolute right-[13%] bottom-[10%] h-3 w-3 rounded-full border-2 border-white bg-alert shadow" />
        </>
      )}
    </div>
  );
}
