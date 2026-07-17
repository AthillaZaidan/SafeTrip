"use client";

import { useEffect, useState } from "react";
import { 
  fetchIncidents, 
  fetchReports, 
  fetchCameras,
  type IncidentList,
  type ReportList,
  type Camera 
} from "@/lib/api";
import { CctvTile } from "@/components/cctv-tile";
import { Loader2, AlertTriangle, ArrowRight, Activity, ShieldAlert, FileText, CheckCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function DashboardPage() {
  const router = useRouter();
  const [incidents, setIncidents] = useState<IncidentList[]>([]);
  const [reports, setReports] = useState<ReportList[]>([]);
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    
    async function loadData() {
      try {
        setLoading(true);
        const [incRes, repRes, camRes] = await Promise.all([
          fetchIncidents(),
          fetchReports(),
          fetchCameras()
        ]);
        if (mounted) {
          setIncidents(incRes);
          setReports(repRes);
          setCameras(camRes);
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
    const interval = setInterval(loadData, 10000); // 10s poll
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const openIncidents = incidents.filter(i => i.status !== "resolved");
  const openReports = reports.filter(r => r.status !== "resolved");
  const urgentCams = cameras.filter(c => c.status === "alert" || c.status === "critical");
  const resolvedToday = incidents.filter(i => i.status === "resolved").length;

  return (
    <div className="flex flex-col gap-10">
      {error && (
        <div className="rounded-lg bg-alert/10 p-4 border border-alert/20 text-alert flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            <p className="font-medium">{error} Make sure the Python API is running.</p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink">Dashboard Overview</h1>
      </div>

      {loading && incidents.length === 0 ? (
        <div className="flex justify-center p-12"><Loader2 className="w-8 h-8 animate-spin text-primary/50" /></div>
      ) : (
        <>
          {/* KPI Cards */}
          <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-[24px] border border-hairline bg-white p-5 shadow-sm">
              <div className="flex items-center gap-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-alert/10 text-alert">
                  <Activity className="h-6 w-6" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-muted">Open Incidents</p>
                  <p className="text-2xl font-bold text-ink">{openIncidents.length}</p>
                </div>
              </div>
            </div>
            <div className="rounded-[24px] border border-hairline bg-white p-5 shadow-sm">
              <div className="flex items-center gap-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary">
                  <FileText className="h-6 w-6" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-muted">Passenger Reports</p>
                  <p className="text-2xl font-bold text-ink">{openReports.length}</p>
                </div>
              </div>
            </div>
            <div className="rounded-[24px] border border-hairline bg-white p-5 shadow-sm">
              <div className="flex items-center gap-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-orange-100 text-orange-600">
                  <ShieldAlert className="h-6 w-6" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-muted">Urgent Cameras</p>
                  <p className="text-2xl font-bold text-ink">{urgentCams.length}</p>
                </div>
              </div>
            </div>
            <div className="rounded-[24px] border border-hairline bg-white p-5 shadow-sm">
              <div className="flex items-center gap-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-signal/10 text-signal">
                  <CheckCircle className="h-6 w-6" />
                </span>
                <div>
                  <p className="text-sm font-semibold text-muted">Resolved Today</p>
                  <p className="text-2xl font-bold text-ink">{resolvedToday}</p>
                </div>
              </div>
            </div>
          </section>

          <div className="grid gap-10 xl:grid-cols-2">
            {/* Urgent Cameras */}
            <section className="flex flex-col gap-4 rounded-[24px] border border-hairline bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-ink">Urgent Activity</h2>
                <Link href="/dashboard/monitoring" className="text-sm font-bold text-primary hover:underline flex items-center gap-1">
                  View All <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
              {urgentCams.length === 0 ? (
                <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-hairline bg-surface-strong p-8 text-center text-muted">
                  All clear! No urgent activity detected.
                </div>
              ) : (
                <div className="grid gap-4 sm:grid-cols-2">
                  {urgentCams.slice(0, 2).map((cam, i) => (
                    <CctvTile
                      key={cam.camera_id}
                      label={cam.name}
                      boxes={[{ x: 40, y: 30, w: 20, h: 40, kind: "flag" }]}
                      videoSrc="/videos/feature-1/Adult_falls_on_floor_202607171330.mp4"
                      alert
                    />
                  ))}
                </div>
              )}
            </section>

            {/* Open Reports */}
            <section className="flex flex-col gap-4 rounded-[24px] border border-hairline bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-ink">Open Reports</h2>
                <Link href="/dashboard/investigation" className="text-sm font-bold text-primary hover:underline flex items-center gap-1">
                  Investigate <ArrowRight className="h-4 w-4" />
                </Link>
              </div>
              {openReports.length === 0 ? (
                <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-hairline bg-surface-strong p-8 text-center text-muted">
                  No open passenger reports.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-hairline text-muted">
                        <th className="pb-3 font-semibold">ID</th>
                        <th className="pb-3 font-semibold">Location</th>
                        <th className="pb-3 font-semibold">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-hairline">
                      {openReports.slice(0, 4).map(report => (
                        <tr key={report.report_id} className="text-ink transition-colors hover:bg-surface-strong cursor-pointer" onClick={() => router.push(`/dashboard/investigation?report=${report.report_id}`)}>
                          <td className="py-3 font-semibold text-primary">#{report.report_id.substring(0, 6).toUpperCase()}</td>
                          <td className="py-3">{report.location || "Unknown"}</td>
                          <td className="py-3 max-w-[200px] truncate">{report.description}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>

          {/* Recent Incidents Table */}
          <section className="flex flex-col gap-4 rounded-[24px] border border-hairline bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-ink">Recent System Incidents</h2>
              <Link href="/dashboard/incidents" className="text-sm font-bold text-primary hover:underline flex items-center gap-1">
                View All <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="bg-surface-strong font-bold text-ink">
                    <th className="rounded-l-xl px-4 py-3">Incident ID</th>
                    <th className="px-4 py-3">Date & Time</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Location</th>
                    <th className="px-4 py-3">Status</th>
                    <th className="rounded-r-xl px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-hairline">
                  {incidents.slice(0, 5).map(incident => {
                    const d = incident.created_at ? new Date(incident.created_at) : new Date();
                    return (
                      <tr key={incident.incident_id} className="text-ink hover:bg-slate-50 transition-colors">
                        <td className="px-4 py-4 font-semibold text-primary">#{incident.incident_id.substring(0, 8).toUpperCase()}</td>
                        <td className="px-4 py-4">{d.toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</td>
                        <td className="px-4 py-4 capitalize">{incident.incident_type.replace(/_/g, " ")}</td>
                        <td className="px-4 py-4">{incident.location || "N/A"}</td>
                        <td className="px-4 py-4">
                          <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-bold capitalize ${
                            incident.status === "resolved" ? "bg-signal/10 text-signal" : "bg-alert/10 text-alert"
                          }`}>
                            {incident.status.replace("_", " ")}
                          </span>
                        </td>
                        <td className="px-4 py-4 text-right">
                          <Link href="/dashboard/incidents" className="font-semibold text-primary hover:underline">
                            Manage
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                  {incidents.length === 0 && (
                    <tr><td colSpan={6} className="text-center py-8 text-muted">No incidents recorded.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
