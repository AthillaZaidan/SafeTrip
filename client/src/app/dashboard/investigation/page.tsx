"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";
import { CctvTile } from "@/components/cctv-tile";
import { ScanSearch, Check, FileSearch } from "lucide-react";

const EXTRACTED_ATTRIBUTES = [
  { label: "Time window", value: "17:05 – 17:15" },
  { label: "Location", value: "Platform B" },
  { label: "Upper clothing", value: "Grey jacket" },
  { label: "Accessory", value: "Black backpack" },
  { label: "Direction", value: "Toward Exit 2" },
];

const CANDIDATES = [
  {
    id: "REC-888",
    label: "Platform B, Camera 2 — 17:07",
    score: 0.92,
    note: "Grey top + backpack match; movement toward Exit 2.",
  },
  {
    id: "REC-765",
    label: "Concourse L1, Camera 1 — 17:09",
    score: 0.81,
    note: "Partial clothing match; direction consistent.",
  },
  {
    id: "REC-777",
    label: "Exit 2 Gate, Camera 4 — 17:13",
    score: 0.74,
    note: "Backpack match; timestamp within window.",
  },
];

function InvestigationContent() {
  const searchParams = useSearchParams();
  const id = searchParams.get("id") || "ST-101";
  const [confirmed, setConfirmed] = useState<string[]>([]);

  const toggle = (clipId: string) =>
    setConfirmed((prev) =>
      prev.includes(clipId) ? prev.filter((c) => c !== clipId) : [...prev, clipId]
    );

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink">Investigation</h1>
        <button className="flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-sm font-bold text-white transition-colors hover:bg-primary-active">
          <ScanSearch className="h-4 w-4" />
          New Search
        </button>
      </div>

      {/* Extracted attributes */}
      <section className="rounded-[24px] bg-white border border-hairline shadow-sm p-5 lg:p-6">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-ink">
            Report #{id} — Extracted Attributes
          </h2>
          <span className="rounded-full bg-signal/15 px-3 py-1 text-xs font-bold text-signal">
            Human Verified
          </span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {EXTRACTED_ATTRIBUTES.map((attr) => (
            <div key={attr.label} className="rounded-xl bg-surface-strong px-4 py-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                {attr.label}
              </p>
              <p className="mt-0.5 text-sm font-bold text-ink">{attr.value}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Candidate clips */}
      <section>
        <h2 className="mb-4 text-lg font-bold text-ink">
          Candidate Evidence Clips
        </h2>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {CANDIDATES.map((clip) => {
            const isConfirmed = confirmed.includes(clip.id);
            return (
              <article
                key={clip.id}
                className="flex flex-col gap-3 rounded-[24px] bg-white border border-hairline shadow-sm p-4"
              >
                <CctvTile
                  label={clip.label}
                  boxes={[{ x: 38, y: 18, w: 16, h: 48, kind: "flag" }]}
                />
                <div className="flex items-center justify-between">
                  <span className="text-sm font-bold text-ink">
                    {clip.id}
                  </span>
                  <span className="rounded-full bg-surface-strong px-2 py-0.5 text-xs font-bold text-ink">
                    {(clip.score * 100).toFixed(0)}% match
                  </span>
                </div>
                <p className="text-sm leading-relaxed text-muted">
                  {clip.note}
                </p>
                <button
                  onClick={() => toggle(clip.id)}
                  className={
                    isConfirmed
                      ? "mt-auto flex items-center justify-center gap-2 rounded-full bg-signal px-4 py-2 text-sm font-bold text-white transition-colors"
                      : "mt-auto flex items-center justify-center gap-2 rounded-full bg-surface-strong px-4 py-2 text-sm font-bold text-ink transition-colors hover:bg-slate-200"
                  }
                >
                  <Check className="h-4 w-4" />
                  {isConfirmed ? "Confirmed" : "Confirm Clip"}
                </button>
              </article>
            );
          })}
        </div>
      </section>

      {/* Timeline summary */}
      <section className="flex items-start gap-4 rounded-[24px] border border-dashed border-slate-300 bg-white p-5">
        <span className="rounded-full bg-surface-strong p-3">
          <FileSearch className="h-5 w-5 text-primary" />
        </span>
        <div>
          <h3 className="font-bold text-ink">Verified Timeline</h3>
          <p className="mt-1 text-sm text-muted">
            {confirmed.length === 0
              ? "Confirm candidate clips to build the human-verified incident timeline."
              : `${confirmed.length} clip(s) confirmed — timeline entries: ${confirmed
                  .sort()
                  .join(" → ")}.`}
          </p>
        </div>
      </section>
    </div>
  );
}

export default function InvestigationPage() {
  return (
    <Suspense fallback={<div>Loading investigation...</div>}>
      <InvestigationContent />
    </Suspense>
  );
}
