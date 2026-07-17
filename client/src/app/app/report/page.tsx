"use client";

import { FakeMap } from "@/components/fake-map";
import { Download, TrainFront } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const STEPS = ["Reporting", "Accepted", "Reporting Process", "Resolved", "Submit"];
const CURRENT_STEP = 4; // Step 4 – Resolved (1-indexed)

export default function ReportPage() {
  return (
    <div className="flex flex-col gap-5">
      {/* Current location */}
      <section>
        <h1 className="mb-2 text-xl font-bold text-ink">You&apos;re now here</h1>
        <div className="overflow-hidden rounded-[24px] bg-white border border-hairline shadow-sm">
          <div className="flex items-center gap-3 p-4">
            <span className="flex h-11 w-11 items-center justify-center rounded-full bg-surface-strong text-primary">
              <TrainFront className="h-6 w-6" />
            </span>
            <p className="text-sm font-bold text-ink">
              MRT Jakarta – Lebak Bulus Station
            </p>
          </div>
          <FakeMap route className="h-44 w-full rounded-none" />
        </div>
      </section>

      {/* Progress */}
      <section>
        <h2 className="mb-3 text-xl font-bold text-ink">
          Step {CURRENT_STEP} – Resolved
        </h2>
        <ol className="flex items-start">
          {STEPS.map((label, i) => {
            const stepNo = i + 1;
            const done = stepNo <= CURRENT_STEP;
            return (
              <li key={label} className="flex flex-1 flex-col items-center">
                <div className="flex w-full items-center">
                  <div
                    className={cn(
                      "h-0.5 flex-1",
                      i === 0 ? "bg-transparent" : done ? "bg-primary" : "bg-slate-300"
                    )}
                  />
                  <span
                    className={cn(
                      "h-4 w-4 shrink-0 rounded-full",
                      done ? "bg-primary" : "bg-slate-300"
                    )}
                  />
                  <div
                    className={cn(
                      "h-0.5 flex-1",
                      i === STEPS.length - 1
                        ? "bg-transparent"
                        : stepNo < CURRENT_STEP
                          ? "bg-primary"
                          : "bg-slate-300"
                    )}
                  />
                </div>
                <span
                  className={cn(
                    "mt-1.5 px-0.5 text-center text-[10px] leading-tight",
                    done ? "font-bold text-primary" : "text-muted"
                  )}
                >
                  {label}
                </span>
              </li>
            );
          })}
        </ol>
      </section>

      {/* Incident card */}
      <article className="flex flex-col gap-3 rounded-[24px] bg-white border border-hairline shadow-sm p-5">
        <div className="flex items-start justify-between gap-3">
          <h3 className="text-base font-bold text-ink">
            Incident #ST-101
          </h3>
          <button
            title="Download report"
            className="rounded-full bg-surface-strong p-1.5 text-ink transition-colors hover:bg-slate-200"
          >
            <Download className="h-4 w-4" />
          </button>
        </div>
        <p className="line-clamp-2 text-sm leading-relaxed text-muted">
          Report about sexual harassment in Exit D, happens at Tuesday, 16th
          June 2026 when a passenger was waiting.
        </p>
        <div className="rounded-xl bg-surface-strong px-4 py-3">
          <p className="text-sm font-bold text-ink">Resolved by</p>
          <div className="mt-1 flex items-center justify-between">
            <span className="flex items-center gap-2 text-sm font-medium text-ink">
              <span className="h-2.5 w-2.5 rounded-full bg-signal" />
              Adit
            </span>
            <span className="text-sm font-medium text-muted">19 June 2026</span>
          </div>
        </div>
      </article>

      {/* Carousel dots */}
      <div className="flex items-center justify-center gap-2">
        {[0, 1, 2, 3].map((i) => (
          <span
            key={i}
            className={cn(
              "h-2 w-2 rounded-full",
              i === 3 ? "bg-primary" : "bg-slate-300"
            )}
          />
        ))}
      </div>

      <button className="w-full rounded-full bg-primary py-3.5 text-base font-bold text-white shadow-sm transition-colors hover:bg-primary-active active:scale-[0.99]">
        Continue
      </button>
    </div>
  );
}
