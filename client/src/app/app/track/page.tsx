"use client";

import { FakeMap } from "@/components/fake-map";
import { TrainFront } from "lucide-react";

const COMMUTE_MODES = ["MRT", "LRT", "KAI", "TJ"];

export default function TrackPage() {
  return (
    <div className="flex flex-col gap-5">
      {/* Origin / destination */}
      <section className="flex flex-col gap-4 rounded-[24px] bg-white border border-hairline p-5 shadow-sm">
        <div className="flex items-center gap-3">
          <span className="h-3.5 w-3.5 shrink-0 rounded-full border-[3px] border-signal" />
          <p className="flex-1 text-sm font-semibold text-ink">
            Jl. Titik Awal No. 12
          </p>
        </div>
        <div className="ml-1.5 h-4 w-px bg-slate-300" />
        <div className="flex items-center gap-3">
          <span className="h-3.5 w-3.5 shrink-0 rounded-full border-[3px] border-alert" />
          <p className="flex-1 text-sm font-semibold text-ink">
            Jl. Tujuan Akhir No. 47
          </p>
        </div>
      </section>

      {/* Commute mode picker */}
      <section>
        <h1 className="mb-3 text-lg font-bold text-ink">
          Choose How You Commute
        </h1>
        <div className="flex items-center justify-between rounded-full bg-surface-strong px-5 py-3.5 border border-hairline shadow-sm">
          {COMMUTE_MODES.map((mode) => (
            <button
              key={mode}
              title={mode}
              className="flex h-12 w-12 items-center justify-center rounded-full bg-white transition-transform hover:scale-105 active:scale-95 shadow-sm border border-hairline"
            >
              <span className="text-[11px] font-extrabold tracking-tight text-primary">
                {mode}
              </span>
            </button>
          ))}
        </div>
      </section>

      {/* Map */}
      <FakeMap route className="h-72 w-full rounded-[24px] overflow-hidden border border-hairline shadow-sm" />

      {/* Current location */}
      <section>
        <h2 className="mb-2 text-base font-bold text-ink">You&apos;re Now Here</h2>
        <div className="flex items-center gap-3 rounded-[24px] bg-white border border-hairline p-4 shadow-sm">
          <span className="flex h-11 w-11 items-center justify-center rounded-full bg-surface-strong text-primary">
            <TrainFront className="h-6 w-6" />
          </span>
          <p className="text-sm font-bold text-ink">
            MRT Jakarta – Lebak Bulus Station
          </p>
        </div>
      </section>
    </div>
  );
}
