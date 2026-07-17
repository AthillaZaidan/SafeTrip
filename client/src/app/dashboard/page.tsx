"use client";

import { useEffect, useState } from "react";
import { IncidentCard, type Incident } from "@/components/incident-card";
import { ChevronDown, Loader2 } from "lucide-react";
import { createIncident, fetchIncidents, updateIncident } from "@/lib/api";

export default function DashboardPage() {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    
    async function loadData() {
      try {
        setLoading(true);
        const data = await fetchIncidents();
        if (mounted) {
          setIncidents(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          console.error(err);
          setError("Failed to connect to the backend server.");
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    
    loadData();
    // Poll every 5 seconds for MVP demo
    const interval = setInterval(loadData, 5000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleStatusChange = async (fullIncidentId: string, newStatus: string) => {
    try {
      await updateIncident(fullIncidentId, { status: newStatus });
      const data = await fetchIncidents();
      setIncidents(data);
    } catch (err) {
      console.error(err);
      setError("Failed to update incident status.");
    }
  };

  const handleTriggerDemo = async () => {
    try {
      await createIncident({
        incident_type: "demo_trigger",
        severity: "medium",
        location: "Concourse B, Gate 4",
        description: "Demo incident manually triggered via dashboard",
        source_mode: "manual_demo"
      });
      const data = await fetchIncidents();
      setIncidents(data);
    } catch (err) {
      console.error(err);
      setError("Failed to create demo incident.");
    }
  };

  // Split incidents by status
  const resolvedIncidents = incidents.filter(i => i.status === "resolved").slice(0, 6);
  const newIncidents = incidents.filter(i => i.status === "open").slice(0, 6);
  const reviewIncidents = incidents.filter(i => i.status === "assigned" || i.status === "in_progress").slice(0, 5);

  // Map backend model to IncidentCard props
  const mapToCard = (i: any): Incident => ({
    id: i.incident_id.substring(0, 8).toUpperCase(),
    description: i.description || `Detected ${i.incident_type} at ${i.location}`,
    resolvedBy: i.assignments?.[0]?.officer_name || "Unassigned",
    resolvedAt: new Date(i.created_at).toLocaleDateString("en-GB", {
      day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit"
    }),
    status: i.status,
  });

  return (
    <div className="flex flex-col gap-10">
      {error && (
        <div className="rounded-lg bg-alert/10 p-4 border border-alert/20 text-alert flex items-center justify-between">
          <p className="font-medium">{error} Make sure the Python API is running.</p>
        </div>
      )}

      {/* Incident Reports */}
      <section>
        <div className="mb-5 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-ink">Incident Reports</h1>
          <div className="flex gap-3">
            <button 
              onClick={handleTriggerDemo}
              className="rounded-full bg-surface-strong px-5 py-2 text-sm font-bold text-ink transition-colors hover:bg-slate-200"
            >
              Trigger Demo
            </button>
            <button className="rounded-full bg-primary px-5 py-2 text-sm font-bold text-white transition-colors hover:bg-primary-active">
              See All
            </button>
          </div>
        </div>
        
        {loading && incidents.length === 0 ? (
          <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-navy/50" /></div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {resolvedIncidents.length > 0 ? (
              resolvedIncidents.map((incident, i) => (
                <IncidentCard key={i} incident={mapToCard(incident)} onStatusChange={(status) => handleStatusChange(incident.incident_id, status)} />
              ))
            ) : (
              <p className="text-muted text-sm col-span-full">No resolved incidents found.</p>
            )}
          </div>
        )}
      </section>

      {/* Incident On Review */}
      <section className="rounded-[24px] border border-hairline bg-white shadow-sm p-5 lg:p-6">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-xl font-bold text-ink">Incident On Review</h2>
          <button className="flex items-center gap-2 rounded-full border border-hairline px-4 py-1.5 text-sm font-medium text-ink transition-colors hover:bg-surface-strong">
            Week
            <ChevronDown className="h-4 w-4" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-separate border-spacing-y-1 text-left">
            <thead>
              <tr className="bg-surface-strong text-sm font-bold text-ink">
                <th className="rounded-l-xl px-4 py-3">Incident</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Location</th>
                <th className="px-4 py-3">Handled by</th>
                <th className="rounded-r-xl px-4 py-3 text-right">Status</th>
              </tr>
            </thead>
            <tbody>
              {reviewIncidents.map((row, i) => {
                const d = new Date(row.created_at);
                return (
                  <tr key={i} className="text-sm text-ink border-b border-hairline">
                    <td className="px-4 py-3.5 font-semibold text-primary">#{row.incident_id.substring(0, 8).toUpperCase()}</td>
                    <td className="px-4 py-3.5">{d.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</td>
                    <td className="px-4 py-3.5">{d.toLocaleTimeString("en-GB")}</td>
                    <td className="px-4 py-3.5">
                      <button className="underline underline-offset-2 hover:text-primary transition-colors">
                        {row.location || "N/A"}
                      </button>
                    </td>
                    <td className="px-4 py-3.5">{row.assignments?.[0]?.officer_name || "Pending"}</td>
                    <td className="px-4 py-3.5 text-right font-bold capitalize">
                      {row.status.replace("_", " ")}
                    </td>
                  </tr>
                );
              })}
              {reviewIncidents.length === 0 && !loading && (
                <tr><td colSpan={6} className="text-center py-8 text-muted">No incidents under review</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* New Incidents */}
      <section>
        <h2 className="mb-5 text-2xl font-bold text-ink">New Incidents</h2>
        {loading && incidents.length === 0 ? (
          <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-navy/50" /></div>
        ) : (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {newIncidents.length > 0 ? (
              newIncidents.map((incident, i) => (
                <IncidentCard key={i} incident={mapToCard(incident)} onStatusChange={(status) => handleStatusChange(incident.incident_id, status)} />
              ))
            ) : (
              <p className="text-muted text-sm col-span-full">No new incidents reported.</p>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
