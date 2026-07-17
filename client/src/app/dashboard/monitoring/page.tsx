"use client";

import { CctvTile, type BoundingBox } from "@/components/cctv-tile";
import { Calendar, MapPin, Search, Filter } from "lucide-react";

const crowdFlags: BoundingBox[] = [
  { x: 8, y: 18, w: 16, h: 42, kind: "flag" },
  { x: 30, y: 10, w: 14, h: 38, kind: "flag" },
  { x: 52, y: 22, w: 15, h: 45, kind: "flag" },
  { x: 74, y: 14, w: 14, h: 40, kind: "flag" },
];

const mixedBoxes: BoundingBox[] = [
  { x: 10, y: 20, w: 13, h: 40, kind: "track" },
  { x: 28, y: 26, w: 13, h: 42, kind: "track" },
  { x: 47, y: 15, w: 12, h: 36, kind: "flag" },
  { x: 64, y: 24, w: 13, h: 44, kind: "track" },
  { x: 82, y: 18, w: 12, h: 40, kind: "flag" },
];

const calmBoxes: BoundingBox[] = [
  { x: 14, y: 24, w: 14, h: 44, kind: "track" },
  { x: 42, y: 18, w: 13, h: 40, kind: "track" },
  { x: 70, y: 26, w: 14, h: 42, kind: "track" },
];

const URGENT_FEEDS = [
  { label: "Stasiun Lebak Bulus, Camera 1", boxes: crowdFlags, alert: true },
  { label: "Kereta MRT 07, Gerbong 2", boxes: mixedBoxes, alert: false },
  { label: "Kereta MRT 07, Gerbong 2", boxes: mixedBoxes, alert: false },
];

const CCTV_FEEDS = [
  { label: "Stasiun Lebak Bulus, Camera 1", boxes: crowdFlags },
  { label: "Stasiun Lebak Bulus, Camera 2", boxes: calmBoxes },
  { label: "Stasiun Lebak Bulus, Camera 3", boxes: calmBoxes },
  { label: "Kereta MRT 07", boxes: mixedBoxes },
  { label: "Kereta MRT 07, Gerbong 2", boxes: mixedBoxes },
  { label: "Kereta MRT 07, Gerbong 2", boxes: crowdFlags },
];

export default function LiveMonitoringPage() {
  return (
    <div className="flex flex-col gap-8">
      {/* Control bar */}
      <div className="flex flex-col gap-3 lg:flex-row">
        <div className="flex items-center gap-2.5 rounded-full bg-surface-strong px-4 py-2.5 text-sm font-bold text-ink">
          <Calendar className="h-4 w-4 shrink-0 text-muted" />
          17/07/2026, 04:47:40
        </div>
        <div className="flex items-center gap-2.5 rounded-full bg-surface-strong px-4 py-2.5 text-sm font-bold text-ink">
          <MapPin className="h-4 w-4 shrink-0 text-muted" />
          Stasiun MRT Lebak Bulus, Jakarta
        </div>
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="filter by Exit"
            className="w-full rounded-full border border-slate-300 bg-white py-2.5 pl-10 pr-10 text-sm text-ink placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <Filter className="absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        </div>
      </div>

      {/* Urgent Overview */}
      <section>
        <h1 className="mb-4 text-xl font-bold text-ink">Urgent Overview</h1>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {URGENT_FEEDS.map((feed, i) => (
            <CctvTile
              key={i}
              label={feed.label}
              boxes={feed.boxes}
              alert={feed.alert}
            />
          ))}
        </div>
      </section>

      {/* CCTV Overview */}
      <section>
        <h2 className="mb-4 text-xl font-bold text-ink">CCTV Overview</h2>
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {CCTV_FEEDS.map((feed, i) => (
            <CctvTile key={i} label={feed.label} boxes={feed.boxes} />
          ))}
        </div>
      </section>
    </div>
  );
}
