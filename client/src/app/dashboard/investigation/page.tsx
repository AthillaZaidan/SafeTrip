"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";
import { CctvTile } from "@/components/cctv-tile";
import {
  ScanSearch,
  Check,
  FileSearch,
  Loader2,
  AlertTriangle,
  X,
} from "lucide-react";
import {
  fetchInvestigation,
  updateCandidate,
  type InvestigationDetail,
  type CandidateClip,
  ApiError,
} from "@/lib/api";

// ─── helpers ────────────────────────────────────────────────────────────────

function scoreColor(score: number) {
  if (score >= 0.85) return "bg-signal/15 text-signal";
  if (score >= 0.65) return "bg-amber-100 text-amber-700";
  return "bg-surface-strong text-muted";
}

function formatFilters(filters: Record<string, unknown>) {
  const labels: Record<string, string> = {
    time_window_start: "Time from",
    time_window_end: "Time to",
    location: "Location",
    upper_clothing: "Upper clothing",
    lower_clothing: "Lower clothing",
    direction: "Direction",
    event: "Event",
    accessories: "Accessories",
  };
  return Object.entries(filters)
    .filter(([, v]) => {
      if (v === null || v === undefined || v === "") return false;
      if (Array.isArray(v) && v.length === 0) return false;
      return true;
    })
    .map(([k, v]) => ({
      label: labels[k] ?? k,
      value: Array.isArray(v) ? v.join(", ") : String(v),
    }));
}

// ─── main component ─────────────────────────────────────────────────────────

function InvestigationContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const investigationId = searchParams.get("inv");

  const [inv, setInv] = useState<InvestigationDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState<string | null>(null); // candidate_id being updated

  const load = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInvestigation(id);
      setInv(data);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.status === 404
            ? "Investigation not found."
            : `API Error ${err.status}: ${err.message}`
          : "Failed to load investigation.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (investigationId) {
      load(investigationId);
    }
  }, [investigationId, load]);

  const handleConfirm = async (
    candidate: CandidateClip,
    action: "confirmed" | "rejected",
  ) => {
    if (!inv) return;
    setConfirming(candidate.candidate_id);
    try {
      await updateCandidate(
        inv.investigation_id,
        candidate.candidate_id,
        action,
      );
      await load(inv.investigation_id);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? `Failed to update clip: ${err.message}`
          : "Failed to update candidate clip.",
      );
    } finally {
      setConfirming(null);
    }
  };

  // No investigation ID in URL — show prompt
  if (!investigationId) {
    return (
      <div className="flex flex-col gap-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-ink">Investigation</h1>
        </div>
        <div className="flex flex-col items-center gap-4 rounded-[24px] border border-dashed border-hairline bg-white p-12 text-center">
          <span className="rounded-full bg-surface-strong p-4">
            <ScanSearch className="h-8 w-8 text-primary" />
          </span>
          <div>
            <h2 className="font-bold text-ink">No investigation selected</h2>
            <p className="mt-1 text-sm text-muted">
              Start an investigation from a submitted passenger report.
            </p>
          </div>
          <button
            onClick={() => router.push("/dashboard")}
            className="rounded-full bg-primary px-6 py-2.5 text-sm font-bold text-white transition-colors hover:bg-primary-active"
          >
            Go to Reports
          </button>
        </div>
      </div>
    );
  }

  // Loading state
  if (loading && !inv) {
    return (
      <div className="flex flex-col gap-8">
        <h1 className="text-2xl font-bold text-ink">Investigation</h1>
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary/50" />
        </div>
      </div>
    );
  }

  const attributes = inv ? formatFilters(inv.search_filters) : [];
  const confirmed = inv?.candidate_clips.filter(
    (c) => c.verification_status === "confirmed",
  ) ?? [];
  const timeline = inv?.timeline_entries ?? [];

  return (
    <div className="flex flex-col gap-8">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink">Investigation</h1>
        <button
          onClick={() => inv && load(inv.investigation_id)}
          className="flex items-center gap-2 rounded-full bg-primary px-5 py-2 text-sm font-bold text-white transition-colors hover:bg-primary-active"
        >
          <ScanSearch className="h-4 w-4" />
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-alert/30 bg-alert/10 p-4 text-sm text-alert">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {inv && (
        <>
          {/* Status pill */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-semibold text-muted">
              Investigation #{inv.investigation_id.substring(0, 8).toUpperCase()}
            </span>
            <span
              className={`rounded-full px-3 py-0.5 text-xs font-bold uppercase tracking-wide ${
                inv.status === "completed"
                  ? "bg-signal/15 text-signal"
                  : inv.status === "in_progress"
                  ? "bg-primary/10 text-primary"
                  : "bg-surface-strong text-muted"
              }`}
            >
              {inv.status.replace("_", " ")}
            </span>
          </div>

          {/* Extracted search attributes */}
          <section className="rounded-[24px] bg-white border border-hairline shadow-sm p-5 lg:p-6">
            <div className="mb-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-ink">
                Report #{inv.report_id.substring(0, 8).toUpperCase()} — Extracted Attributes
              </h2>
              <span className="rounded-full bg-signal/15 px-3 py-1 text-xs font-bold text-signal">
                AI Extracted
              </span>
            </div>
            {attributes.length === 0 ? (
              <p className="text-sm text-muted">No attributes extracted yet.</p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {attributes.map((attr) => (
                  <div
                    key={attr.label}
                    className="rounded-xl bg-surface-strong px-4 py-3"
                  >
                    <p className="text-sm font-semibold text-muted">
                      {attr.label}
                    </p>
                    <p className="mt-0.5 text-sm font-bold text-ink">
                      {attr.value}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* Candidate clips */}
          <section>
            <h2 className="mb-4 text-lg font-bold text-ink">
              Candidate Evidence Clips{" "}
              <span className="text-base font-normal text-muted">
                ({inv.candidate_clips.length})
              </span>
            </h2>
            {inv.candidate_clips.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted">
                No candidate clips found for this investigation.
              </p>
            ) : (
              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {inv.candidate_clips.map((clip) => {
                  const isConfirmed = clip.verification_status === "confirmed";
                  const isRejected = clip.verification_status === "rejected";
                  const isUpdating = confirming === clip.candidate_id;

                  return (
                    <article
                      key={clip.candidate_id}
                      className={`flex flex-col gap-3 rounded-[24px] border shadow-sm p-4 ${
                        isConfirmed
                          ? "border-signal/40 bg-signal/5"
                          : isRejected
                          ? "border-hairline bg-surface-strong opacity-60"
                          : "border-hairline bg-white"
                      }`}
                    >
                      <CctvTile
                        label={`${clip.camera_id || "Camera"} · ${clip.location || "Unknown"}`}
                        boxes={[{ x: 38, y: 18, w: 16, h: 48, kind: "flag" }]}
                      />
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-bold text-ink">
                          {clip.clip_id || clip.candidate_id.substring(0, 8).toUpperCase()}
                        </span>
                        <span
                          className={`rounded-full px-2 py-0.5 text-xs font-bold ${scoreColor(clip.score)}`}
                        >
                          {(clip.score * 100).toFixed(0)}% match
                        </span>
                      </div>
                      {clip.timestamp && (
                        <p className="text-xs text-muted">
                          {new Date(clip.timestamp).toLocaleString("en-GB")}
                        </p>
                      )}
                      <p className="text-sm leading-relaxed text-muted">
                        {clip.explanation || "No explanation available."}
                      </p>

                      {/* VLM recommendation badge */}
                      {clip.vlm_result && (
                        <span
                          className={`self-start rounded-full px-2 py-0.5 text-[11px] font-bold uppercase tracking-wide ${
                            clip.vlm_result.match_recommendation === "likely_match"
                              ? "bg-signal/15 text-signal"
                              : clip.vlm_result.match_recommendation === "possible_match"
                              ? "bg-amber-100 text-amber-700"
                              : "bg-alert/10 text-alert"
                          }`}
                        >
                          {clip.vlm_result.match_recommendation.replace("_", " ")}
                        </span>
                      )}

                      {/* Action buttons */}
                      {!isRejected && (
                        <div className="mt-auto flex gap-2">
                          <button
                            disabled={isUpdating}
                            onClick={() =>
                              handleConfirm(
                                clip,
                                isConfirmed ? "rejected" : "confirmed",
                              )
                            }
                            className={`flex flex-1 items-center justify-center gap-2 rounded-full py-2 text-sm font-bold transition-colors ${
                              isConfirmed
                                ? "bg-signal text-white hover:bg-signal/80"
                                : "bg-surface-strong text-ink hover:bg-slate-200"
                            }`}
                          >
                            {isUpdating ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Check className="h-4 w-4" />
                            )}
                            {isConfirmed ? "Confirmed" : "Confirm Clip"}
                          </button>
                          {!isConfirmed && (
                            <button
                              disabled={isUpdating}
                              onClick={() => handleConfirm(clip, "rejected")}
                              className="flex items-center justify-center rounded-full bg-surface-strong px-3 py-2 text-ink transition-colors hover:bg-alert/10 hover:text-alert"
                            >
                              <X className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      )}
                    </article>
                  );
                })}
              </div>
            )}
          </section>

          {/* Verified timeline */}
          <section className="flex items-start gap-4 rounded-[24px] border border-dashed border-slate-300 bg-white p-5">
            <span className="rounded-full bg-surface-strong p-3">
              <FileSearch className="h-5 w-5 text-primary" />
            </span>
            <div className="flex-1 min-w-0">
              <h3 className="font-bold text-ink">Verified Timeline</h3>
              {timeline.length > 0 ? (
                <ol className="mt-3 space-y-2">
                  {timeline.map((entry) => (
                    <li key={entry.id} className="flex items-start gap-3 text-sm">
                      <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-signal" />
                      <div>
                        <span className="font-semibold text-ink">
                          {entry.camera_id || "Camera"} · {entry.location || "Unknown"}
                        </span>
                        {entry.timestamp && (
                          <span className="ml-2 text-xs text-muted">
                            {new Date(entry.timestamp).toLocaleTimeString("en-GB")}
                          </span>
                        )}
                        {entry.note && (
                          <p className="mt-0.5 text-muted">{entry.note}</p>
                        )}
                      </div>
                    </li>
                  ))}
                </ol>
              ) : confirmed.length > 0 ? (
                <p className="mt-1 text-sm text-muted">
                  {confirmed.length} clip(s) confirmed — timeline will be
                  reconstructed by the system.
                </p>
              ) : (
                <p className="mt-1 text-sm text-muted">
                  Confirm candidate clips to build the human-verified incident
                  timeline.
                </p>
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}

export default function InvestigationPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary/50" />
        </div>
      }
    >
      <InvestigationContent />
    </Suspense>
  );
}
