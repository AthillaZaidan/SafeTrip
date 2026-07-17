export const API_BASE = "http://127.0.0.1:8000/api/v1";

export async function fetchIncidents(status?: string, severity?: string) {
  const params = new URLSearchParams();
  if (status) params.append("status", status);
  if (severity) params.append("severity", severity);
  
  const qs = params.toString();
  const url = `${API_BASE}/incidents${qs ? `?${qs}` : ""}`;
  
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch incidents");
  return res.json();
}

export async function fetchIncident(id: string) {
  const res = await fetch(`${API_BASE}/incidents/${id}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch incident");
  return res.json();
}

export async function createIncident(data: any) {
  const res = await fetch(`${API_BASE}/incidents`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to create incident");
  return res.json();
}

export async function updateIncident(id: string, data: any) {
  const res = await fetch(`${API_BASE}/incidents/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to update incident");
  return res.json();
}

export async function submitReport(data: any) {
  const res = await fetch(`${API_BASE}/reports`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("Failed to submit report");
  return res.json();
}

export async function fetchCameras() {
  const res = await fetch(`${API_BASE}/cameras`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to fetch cameras");
  return res.json();
}

export async function searchEvidence(query: string) {
  const res = await fetch(`${API_BASE}/investigations/search?query=${encodeURIComponent(query)}`, { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to search evidence");
  return res.json();
}
