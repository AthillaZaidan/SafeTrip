"use client";

import { IncidentCard, type Incident } from "@/components/incident-card";

const ALL_INCIDENTS: Incident[] = [
  {
    id: "ST-101",
    description:
      "Report about sexual harassment in Exit D, happens at Tuesday, 16th June 2026 when a passenger was waiting for the train.",
    resolvedBy: "Adit",
    resolvedAt: "19 June 2026",
  },
  {
    id: "ST-187",
    description:
      "Suspicious unattended bag reported near Platform 2 bench. Footage flagged at 13.21.12 WIB, awaiting officer confirmation.",
    resolvedBy: "Rafi",
    resolvedAt: "12 June 2026",
  },
  {
    id: "ST-199",
    description:
      "Crowd compression detected at the concourse gate during morning peak. Flow restored after barrier adjustment.",
    resolvedBy: "Rafi",
    resolvedAt: "12 June 2026",
  },
  {
    id: "ST-204",
    description:
      "Possible person-down event at Level 1 concourse. Officer dispatched and passenger assisted within four minutes.",
    resolvedBy: "Adit",
    resolvedAt: "18 June 2026",
  },
  {
    id: "ST-211",
    description:
      "Restricted-zone intrusion beyond the yellow safety line on Peron 3. Warning broadcast triggered automatically.",
    resolvedBy: "Sinta",
    resolvedAt: "20 June 2026",
  },
  {
    id: "ST-215",
    description:
      "Passenger report of aggressive behavior near Exit B escalator. Evidence clips retrieved for investigator review.",
    resolvedBy: "Adit",
    resolvedAt: "21 June 2026",
  },
];

export default function IncidentReportPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-ink">Incident Report</h1>
        <button className="rounded-full bg-primary px-5 py-2 text-sm font-bold text-white transition-colors hover:bg-primary-active">
          Export
        </button>
      </div>
      <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
        {ALL_INCIDENTS.map((incident) => (
          <IncidentCard key={incident.id} incident={incident} />
        ))}
      </div>
    </div>
  );
}
