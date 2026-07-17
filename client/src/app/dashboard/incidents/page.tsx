"use client";

import { useEffect, useState } from "react";
import { IncidentCard } from "@/components/incident-card";
import { Loader2, AlertTriangle } from "lucide-react";
import { fetchIncidents, updateIncident, type IncidentList, ApiError } from "@/lib/api";

function mapToCard(i: IncidentList) {
  return {
    id: `ST-${i.incident_id.substring(0, 6).toUpperCase()}`,
    description: `${i.incident_type.replace(/_/g, " ")} detected at ${i.location || "unknown location"}`,
    resolvedBy: "—",
    resolvedAt: i.created_at
      ? new Date(i.created_at).toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          year: "numeric",
        })
      : "—",
    status: i.status,
  };
}

export default function IncidentReportPage() {
  const [incidents, setIncidents] = useState<IncidentList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setLoading(true);
      const data = await fetchIncidents();
      setIncidents(data);
      setError(null);
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? `API Error ${err.status}: ${err.message}`
          : "Failed to connect to the backend server.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const handleStatusChange = async (incidentId: string, newStatus: string) => {
    try {
      await updateIncident(incidentId, { status: newStatus });
      await load();
    } catch (err) {
      const msg =
        err instanceof ApiError
          ? `Failed to update: ${err.message}`
          : "Failed to update incident status.";
      setError(msg);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink">Incident Report</h1>
        <button
          onClick={load}
          className="rounded-full bg-primary px-5 py-2 text-sm font-bold text-white transition-colors hover:bg-primary-active"
        >
          Refresh
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-alert/30 bg-alert/10 p-4 text-sm text-alert">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error} — make sure the Python API is running.
        </div>
      )}

      {loading && incidents.length === 0 ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary/50" />
        </div>
      ) : incidents.length === 0 && !error ? (
        <p className="py-12 text-center text-muted">No incidents found.</p>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {incidents.map((incident) => (
            <IncidentCard
              key={incident.incident_id}
              incident={mapToCard(incident)}
              onStatusChange={(status) =>
                handleStatusChange(incident.incident_id, status)
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}
