// ---------------------------------------------------------------------------
// SafeTrip API Client
// Base: http://127.0.0.1:8000/api/v1
// ---------------------------------------------------------------------------

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    let detail: unknown;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const message =
      typeof detail === "object" && detail !== null && "detail" in detail
        ? String((detail as { detail: unknown }).detail)
        : `HTTP ${res.status}`;
    throw new ApiError(res.status, message, detail);
  }

  // 204 No Content
  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

// ---------------------------------------------------------------------------
// Shared types (mirror backend Pydantic schemas)
// ---------------------------------------------------------------------------

export interface Camera {
  camera_id: string;
  name: string;
  location: string;
  stream_source: string;
  status: string;
}

export interface Zone {
  zone_id: string;
  zone_type: string;
  polygon: unknown;
  capacity: number | null;
  risk_multiplier: number;
  danger_direction: unknown;
}

export interface CameraDetail extends Camera {
  zones: Zone[];
}

export interface EvidenceClip {
  camera_id: string;
  start_time: number;
  end_time: number;
  url: string;
  snapshot_url: string;
}

export interface TimelineEvent {
  event_type: string;
  description: string;
  actor: string;
  timestamp: string;
  details: Record<string, unknown>;
}

export interface Assignment {
  assignment_id: string;
  officer_name: string;
  officer_id: string;
  status: string;
  notes: string;
  assigned_at: string | null;
  acknowledged_at: string | null;
  arrived_at: string | null;
  resolved_at: string | null;
}

export interface IncidentList {
  incident_id: string;
  incident_type: string;
  severity: string;
  risk_score: number;
  status: string;
  location: string;
  camera_id: string;
  timestamp: string | null;
  created_at: string | null;
}

export interface IncidentDetail extends IncidentList {
  zone_id: string;
  description: string;
  indicators: Record<string, unknown>;
  evidence: Record<string, unknown>;
  source_mode: string;
  resolution_notes: string;
  updated_at: string | null;
  assignments: Assignment[];
  evidence_clips: EvidenceClip[];
  timeline_events: TimelineEvent[];
}

export interface IncidentCreate {
  incident_type: string;
  camera_id?: string;
  zone_id?: string;
  severity?: string;
  risk_score?: number;
  location?: string;
  description?: string;
  indicators?: Record<string, unknown>;
  evidence?: Record<string, unknown>;
  source_mode?: string;
}

export interface IncidentUpdate {
  severity?: string;
  status?: string;
  description?: string;
  resolution_notes?: string;
}

export interface Officer {
  officer_id: string;
  name: string;
  role: string;
  location: string;
  status: string;
}

export interface ReportList {
  report_id: string;
  reporter_type: string;
  location: string;
  description: string;
  status: string;
  created_at: string | null;
}

export interface ReportDetail extends ReportList {
  time_window_start: string | null;
  time_window_end: string | null;
  direction: string;
  attributes: Record<string, unknown>;
  image_url: string;
}

export interface ReportCreate {
  reporter_type?: string;
  time_window_start?: string | null;
  time_window_end?: string | null;
  location?: string;
  description: string;
  direction?: string;
  image_url?: string;
}

export interface VLMResult {
  supported_attributes: string[];
  contradicted_attributes: string[];
  uncertainties: string[];
  relevant_start_seconds: number | null;
  relevant_end_seconds: number | null;
  match_recommendation: "likely_match" | "possible_match" | "unlikely_match";
  source: "gemini" | "cached" | "fallback";
}

export interface CandidateClip {
  candidate_id: string;
  clip_id: string;
  score: number;
  explanation: string;
  url: string | null;
  snapshot_url: string | null;
  camera_id: string;
  location: string;
  clip_metadata: Record<string, unknown>;
  vlm_result: VLMResult | null;
  media_available: boolean;
  timestamp: string | null;
  verification_status: string;
}

export interface TimelineEntry {
  id: number;
  camera_id: string;
  location: string;
  timestamp: string | null;
  note: string;
  sort_order: number;
  human_verified: boolean;
}

export interface InvestigationDetail {
  investigation_id: string;
  report_id: string;
  status: string;
  search_filters: Record<string, unknown>;
  candidate_clips: CandidateClip[];
  timeline_entries: TimelineEntry[];
}

// ---------------------------------------------------------------------------
// Camera endpoints
// ---------------------------------------------------------------------------

export function fetchCameras(): Promise<Camera[]> {
  return request("/cameras");
}

export function fetchCamera(cameraId: string): Promise<CameraDetail> {
  return request(`/cameras/${encodeURIComponent(cameraId)}`);
}

// ---------------------------------------------------------------------------
// Incident endpoints
// ---------------------------------------------------------------------------

export function fetchIncidents(params?: {
  status?: string;
  severity?: string;
}): Promise<IncidentList[]> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set("status", params.status);
  if (params?.severity) qs.set("severity", params.severity);
  const q = qs.toString();
  return request(`/incidents${q ? `?${q}` : ""}`);
}

export function fetchIncident(incidentId: string): Promise<IncidentDetail> {
  return request(`/incidents/${encodeURIComponent(incidentId)}`);
}

export function createIncident(data: IncidentCreate): Promise<IncidentDetail> {
  return request("/incidents", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateIncident(
  incidentId: string,
  data: IncidentUpdate,
): Promise<IncidentDetail> {
  return request(`/incidents/${encodeURIComponent(incidentId)}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export function assignOfficer(
  incidentId: string,
  officerId: string,
): Promise<unknown> {
  return request(`/incidents/${encodeURIComponent(incidentId)}/assignments`, {
    method: "POST",
    body: JSON.stringify({ officer_id: officerId }),
  });
}

export function approvePlaybook(
  incidentId: string,
  playbookId: number,
): Promise<unknown> {
  return request(`/incidents/${encodeURIComponent(incidentId)}/playbook`, {
    method: "POST",
    body: JSON.stringify({ playbook_id: playbookId }),
  });
}

// ---------------------------------------------------------------------------
// Officer endpoints
// ---------------------------------------------------------------------------

export function fetchOfficers(status?: string): Promise<Officer[]> {
  const q = status ? `?status=${encodeURIComponent(status)}` : "";
  return request(`/officers${q}`);
}

export function fetchOfficer(officerId: string): Promise<Officer> {
  return request(`/officers/${encodeURIComponent(officerId)}`);
}

// ---------------------------------------------------------------------------
// Report endpoints
// ---------------------------------------------------------------------------

export function fetchReports(): Promise<ReportList[]> {
  return request("/reports");
}

export function fetchReport(reportId: string): Promise<ReportDetail> {
  return request(`/reports/${encodeURIComponent(reportId)}`);
}

export function submitReport(data: ReportCreate): Promise<ReportDetail> {
  return request("/reports", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function extractReportAttributes(
  reportId: string,
): Promise<{ report_id: string; attributes: Record<string, unknown> }> {
  return request(`/reports/${encodeURIComponent(reportId)}/extract`, {
    method: "POST",
  });
}

// ---------------------------------------------------------------------------
// Investigation endpoints
// ---------------------------------------------------------------------------

export function createInvestigation(
  reportId: string,
): Promise<InvestigationDetail> {
  return request("/investigations", {
    method: "POST",
    body: JSON.stringify({ report_id: reportId }),
  });
}

export function fetchInvestigation(
  investigationId: string,
): Promise<InvestigationDetail> {
  return request(`/investigations/${encodeURIComponent(investigationId)}`);
}

export function fetchCandidates(
  investigationId: string,
): Promise<CandidateClip[]> {
  return request(
    `/investigations/${encodeURIComponent(investigationId)}/candidates`,
  );
}

export function updateCandidate(
  investigationId: string,
  candidateId: string,
  verificationStatus: "confirmed" | "rejected",
  note?: string,
): Promise<CandidateClip> {
  return request(
    `/investigations/${encodeURIComponent(investigationId)}/candidates/${encodeURIComponent(candidateId)}`,
    {
      method: "PATCH",
      body: JSON.stringify({ verification_status: verificationStatus, note }),
    },
  );
}

export function fetchInvestigationTimeline(
  investigationId: string,
): Promise<TimelineEntry[]> {
  return request(
    `/investigations/${encodeURIComponent(investigationId)}/timeline`,
  );
}

// ---------------------------------------------------------------------------
// Legacy alias (kept for dashboard/page.tsx compatibility)
// ---------------------------------------------------------------------------

/** @deprecated use fetchIncidents() */
export { fetchIncidents as default };
