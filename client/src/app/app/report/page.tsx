"use client";

import { useState } from "react";
import { FakeMap } from "@/components/fake-map";
import { TrainFront, Loader2, AlertTriangle, CheckCircle2, Send } from "lucide-react";
import { submitReport, createInvestigation, type ReportDetail, ApiError } from "@/lib/api";

const STEPS = ["Reporting", "Accepted", "Processing", "Resolved", "Done"];

function StepBar({ current }: { current: number }) {
  return (
    <ol className="flex items-start">
      {STEPS.map((label, i) => {
        const stepNo = i + 1;
        const done = stepNo <= current;
        return (
          <li key={label} className="flex flex-1 flex-col items-center">
            <div className="flex w-full items-center">
              <div
                className={`h-0.5 flex-1 ${
                  i === 0 ? "bg-transparent" : done ? "bg-primary" : "bg-slate-300"
                }`}
              />
              <span
                className={`h-4 w-4 shrink-0 rounded-full ${
                  done ? "bg-primary" : "bg-slate-300"
                }`}
              />
              <div
                className={`h-0.5 flex-1 ${
                  i === STEPS.length - 1
                    ? "bg-transparent"
                    : stepNo < current
                    ? "bg-primary"
                    : "bg-slate-300"
                }`}
              />
            </div>
            <span
              className={`mt-1.5 px-0.5 text-center text-[10px] leading-tight ${
                done ? "font-bold text-primary" : "text-muted"
              }`}
            >
              {label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

type Phase = "form" | "submitting" | "submitted" | "investigating";

export default function ReportPage() {
  const [phase, setPhase] = useState<Phase>("form");
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [invId, setInvId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form fields
  const [description, setDescription] = useState("");
  const [location, setLocation] = useState("");
  const [direction, setDirection] = useState("");

  const validate = () => {
    if (!description.trim()) return "Please describe what happened.";
    if (description.trim().length < 10)
      return "Description must be at least 10 characters.";
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setPhase("submitting");

    try {
      const newReport = await submitReport({
        reporter_type: "passenger",
        description: description.trim(),
        location: location.trim(),
        direction: direction.trim(),
      });
      setReport(newReport);
      setPhase("submitted");
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.status === 422
            ? "Invalid form data — please check your input."
            : `Server error ${err.status}: ${err.message}`
          : "Could not submit report. Is the server running?";
      setError(msg);
      setPhase("form");
    }
  };

  const handleStartInvestigation = async () => {
    if (!report) return;
    setPhase("investigating");
    setError(null);
    try {
      const inv = await createInvestigation(report.report_id);
      setInvId(inv.investigation_id);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? err.status === 409
            ? "Report is still being processed — please wait a moment."
            : `Error ${err.status}: ${err.message}`
          : "Failed to start investigation.";
      setError(msg);
      setPhase("submitted");
    }
  };

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
          {phase === "form"
            ? "Step 1 – Reporting"
            : phase === "submitting"
            ? "Step 1 – Submitting…"
            : phase === "submitted"
            ? "Step 2 – Accepted"
            : "Step 3 – Processing"}
        </h2>
        <StepBar
          current={
            phase === "form" || phase === "submitting"
              ? 1
              : phase === "submitted"
              ? 2
              : 3
          }
        />
      </section>

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-alert/30 bg-alert/10 p-4 text-sm text-alert">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* ── Phase: Form ────────────────────────────────────────────────── */}
      {(phase === "form" || phase === "submitting") && (
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label htmlFor="description" className="text-sm font-semibold text-ink">
              What happened? <span className="text-alert">*</span>
            </label>
            <textarea
              id="description"
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe the incident — include time, appearance, direction…"
              className="w-full rounded-2xl border border-hairline bg-surface-strong px-4 py-3 text-sm text-ink placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary resize-none"
              required
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="location" className="text-sm font-semibold text-ink">
              Location (optional)
            </label>
            <input
              id="location"
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Platform B, near Exit 2"
              className="w-full rounded-full border border-hairline bg-surface-strong px-4 py-2.5 text-sm text-ink placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="direction" className="text-sm font-semibold text-ink">
              Direction of subject (optional)
            </label>
            <input
              id="direction"
              type="text"
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
              placeholder="e.g. Toward Exit 2, northbound"
              className="w-full rounded-full border border-hairline bg-surface-strong px-4 py-2.5 text-sm text-ink placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <button
            type="submit"
            disabled={phase === "submitting"}
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3.5 text-base font-bold text-white shadow-sm transition-colors hover:bg-primary-active active:scale-[0.99] disabled:opacity-60"
          >
            {phase === "submitting" ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting…
              </>
            ) : (
              <>
                <Send className="h-4 w-4" />
                Submit Report
              </>
            )}
          </button>
        </form>
      )}

      {/* ── Phase: Submitted ───────────────────────────────────────────── */}
      {(phase === "submitted" || phase === "investigating") && report && (
        <article className="flex flex-col gap-3 rounded-[24px] bg-white border border-hairline shadow-sm p-5">
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-base font-bold text-ink">
              Report #{report.report_id.substring(0, 8).toUpperCase()}
            </h3>
            <span className="flex items-center gap-1.5 rounded-full bg-signal/15 px-3 py-1 text-xs font-bold text-signal">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Submitted
            </span>
          </div>

          <p className="line-clamp-3 text-sm leading-relaxed text-muted">
            {report.description}
          </p>

          {report.location && (
            <div className="rounded-xl bg-surface-strong px-4 py-3 text-sm">
              <span className="font-semibold text-muted">Location: </span>
              <span className="text-ink">{report.location}</span>
            </div>
          )}

          <div className="rounded-xl bg-surface-strong px-4 py-3">
            <p className="text-sm font-bold text-ink">Status</p>
            <div className="mt-1 flex items-center justify-between">
              <span className="flex items-center gap-2 text-sm font-medium text-ink">
                <span className="h-2.5 w-2.5 rounded-full bg-signal" />
                {report.status.charAt(0).toUpperCase() + report.status.slice(1)}
              </span>
              <span className="text-sm font-medium text-muted">
                {report.created_at
                  ? new Date(report.created_at).toLocaleDateString("en-GB", {
                      day: "numeric",
                      month: "long",
                      year: "numeric",
                    })
                  : "Just now"}
              </span>
            </div>
          </div>

          {invId ? (
            <div className="flex items-center gap-3 rounded-2xl border border-signal/30 bg-signal/5 p-4 text-sm text-signal">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              Investigation started — ID: {invId.substring(0, 8).toUpperCase()}
            </div>
          ) : (
            <button
              onClick={handleStartInvestigation}
              disabled={phase === "investigating"}
              className="mt-1 flex w-full items-center justify-center gap-2 rounded-full bg-primary py-3 text-sm font-bold text-white transition-colors hover:bg-primary-active disabled:opacity-60"
            >
              {phase === "investigating" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Starting investigation…
                </>
              ) : (
                "Start AI Investigation"
              )}
            </button>
          )}
        </article>
      )}
    </div>
  );
}
