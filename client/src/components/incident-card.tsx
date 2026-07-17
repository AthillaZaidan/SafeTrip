"use client";

import { Download, Loader2 } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { createInvestigation } from "@/lib/api";
import jsPDF from "jspdf";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export interface Incident {
  id: string; // Used for UI display, e.g. ST-123456
  fullId?: string; // The real UUID required for API calls
  description: string;
  resolvedBy?: string;
  resolvedAt?: string;
  status: string;
}

export function IncidentCard({
  incident,
  actionLabel,
  onStatusChange,
}: {
  incident: Incident;
  actionLabel?: string;
  onStatusChange?: (status: string) => void;
}) {
  const router = useRouter();
  const [analyzing, setAnalyzing] = useState(false);
  const isResolved = incident.status === "resolved";

  const handleAnalyze = async () => {
    if (!incident.fullId) {
      // Fallback for demo incidents without a real ID
      router.push(`/dashboard/investigation?id=${incident.id}`);
      return;
    }
    
    setAnalyzing(true);
    try {
      const inv = await createInvestigation(incident.fullId);
      router.push(`/dashboard/investigation?inv=${inv.investigation_id}`);
    } catch (err) {
      console.error("Failed to create investigation:", err);
      // Fallback to error or just redirect anyway
      alert("Failed to start investigation. The report might already have one.");
    } finally {
      setAnalyzing(false);
    }
  };

  const handleExportPDF = () => {
    const doc = new jsPDF();
    doc.setFont("helvetica");
    
    // Header
    doc.setFontSize(22);
    doc.setTextColor(20, 30, 50); // navy
    doc.text(`Incident Report: ${incident.id}`, 20, 30);
    
    // Separator
    doc.setDrawColor(200, 200, 200);
    doc.line(20, 35, 190, 35);
    
    // Details
    doc.setFontSize(12);
    doc.setTextColor(80, 80, 80);
    doc.text(`Status: Resolved`, 20, 50);
    doc.text(`Handled by: ${incident.resolvedBy ?? "Unknown"}`, 20, 60);
    doc.text(`Resolved at: ${incident.resolvedAt ?? "Unknown time"}`, 20, 70);
    
    // Description Box
    doc.setFontSize(14);
    doc.setTextColor(20, 30, 50);
    doc.text("Incident Description", 20, 90);
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    const splitDesc = doc.splitTextToSize(incident.description, 170);
    doc.text(splitDesc, 20, 100);
    
    // Resolution Box
    const resY = 100 + (splitDesc.length * 7) + 10;
    doc.setFontSize(14);
    doc.setTextColor(20, 30, 50);
    doc.text("Resolution Feedback", 20, resY);
    
    doc.setFontSize(11);
    doc.setTextColor(100, 100, 100);
    const splitRes = doc.splitTextToSize("Investigation completed — evidence confirmed. Officer on site handled the situation according to standard operating procedures. Subject was identified and escorted out of the premises. All clear.", 170);
    doc.text(splitRes, 20, resY + 10);
    
    // Footer
    doc.setFontSize(9);
    doc.setTextColor(150, 150, 150);
    doc.text("SafeTrip AI Automated Report System", 20, 280);
    
    doc.save(`SafeTrip_Incident_${incident.id}.pdf`);
  };
  
  return (
    <article className="flex flex-col gap-4 rounded-[24px] bg-white border border-hairline shadow-sm p-5">
      <div className="flex items-start justify-between">
        <h3 className="text-base font-bold text-ink">Incident #{incident.id}</h3>
        {isResolved && (
          <button 
            onClick={handleExportPDF}
            title="Export PDF"
            className="rounded-full p-1 text-muted transition-colors hover:bg-surface-strong hover:text-ink"
          >
            <Download className="h-4 w-4" />
          </button>
        )}
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
        {!isResolved && (
          <button 
            onClick={handleAnalyze}
            disabled={analyzing}
            className="flex flex-1 items-center justify-center gap-2 rounded-full border border-hairline py-2.5 text-sm font-bold text-ink transition-colors hover:bg-surface-strong disabled:opacity-60"
          >
            {analyzing && <Loader2 className="h-4 w-4 animate-spin" />}
            Analyze
          </button>
        )}

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
        {actionLabel && !onStatusChange && !isResolved && (
          <button className="flex-1 rounded-full bg-primary py-2.5 text-sm font-bold text-white transition-colors hover:bg-primary-active">
            {actionLabel}
          </button>
        )}
      </div>
    </article>
  );
}
