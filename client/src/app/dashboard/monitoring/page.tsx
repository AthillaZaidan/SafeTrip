"use client";

import { useEffect, useState } from "react";
import { CctvTile, type BoundingBox } from "@/components/cctv-tile";
import { Calendar, MapPin, Search, Filter, Loader2, AlertTriangle, Radio } from "lucide-react";
import { fetchCameras, type Camera, ApiError } from "@/lib/api";

// Rotating demo bounding boxes — visual only, no live stream
const DEMO_BOXES: BoundingBox[][] = [
  [
    { x: 8, y: 18, w: 16, h: 42, kind: "flag" },
    { x: 30, y: 10, w: 14, h: 38, kind: "flag" },
    { x: 52, y: 22, w: 15, h: 45, kind: "flag" },
    { x: 74, y: 14, w: 14, h: 40, kind: "flag" },
  ],
  [
    { x: 10, y: 20, w: 13, h: 40, kind: "track" },
    { x: 28, y: 26, w: 13, h: 42, kind: "track" },
    { x: 47, y: 15, w: 12, h: 36, kind: "flag" },
    { x: 64, y: 24, w: 13, h: 44, kind: "track" },
    { x: 82, y: 18, w: 12, h: 40, kind: "flag" },
  ],
  [
    { x: 14, y: 24, w: 14, h: 44, kind: "track" },
    { x: 42, y: 18, w: 13, h: 40, kind: "track" },
    { x: 70, y: 26, w: 14, h: 42, kind: "track" },
  ],
];

const DEMO_VIDEOS = [
  "/videos/feature-1/Adult_falls_on_floor_202607171330.mp4",
  "/videos/feature-1/Adult_walks_along_platform_202607171208.mp4",
  "/videos/feature-1/Dense_crowd_on_platform_202607171216.mp4",
  "/videos/feature-1/Indonesian_commuters_walking_through_ticket_gates_202607171431.mp4",
  "/videos/feature-1/Indonesian_commuters_walking_through_ticket_gates_202607171435.mp4",
  "/videos/feature-1/Passenger_falls_in_corridor_202607171243.mp4",
];

function boxesForCamera(index: number): BoundingBox[] {
  return DEMO_BOXES[index % DEMO_BOXES.length];
}

function videoForCamera(index: number): string {
  return DEMO_VIDEOS[index % DEMO_VIDEOS.length];
}

function isAlert(cam: Camera): boolean {
  return cam.status === "alert" || cam.status === "critical";
}

export default function LiveMonitoringPage() {
  const [cameras, setCameras] = useState<Camera[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const tick = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(tick);
  }, []);

  useEffect(() => {
    let mounted = true;

    async function load() {
      try {
        setLoading(true);
        const data = await fetchCameras();
        if (mounted) {
          setCameras(data);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          const msg =
            err instanceof ApiError
              ? `API Error ${err.status}: ${err.message}`
              : "Failed to load cameras.";
          setError(msg);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    const interval = setInterval(load, 10_000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  const filtered = cameras.filter(
    (c) =>
      filter === "" ||
      c.name.toLowerCase().includes(filter.toLowerCase()) ||
      c.location.toLowerCase().includes(filter.toLowerCase()),
  );

  const isUrgent = (cam: Camera) =>
    isAlert(cam) ||
    cam.name.toLowerCase().includes("platform") ||
    cam.name.toLowerCase().includes("gate");

  const urgentCams = filtered.filter(isUrgent);
  const otherCams = filtered.filter((cam) => !isUrgent(cam));

  return (
    <div className="flex flex-col gap-8">
      {/* Control bar */}
      <div className="flex flex-col gap-3 lg:flex-row">
        <div className="flex items-center gap-2.5 rounded-full bg-surface-strong px-4 py-2.5 text-sm font-bold text-ink">
          <Calendar className="h-4 w-4 shrink-0 text-muted" />
          {now.toLocaleString("en-GB", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          })}
        </div>
        <div className="flex items-center gap-2.5 rounded-full bg-surface-strong px-4 py-2.5 text-sm font-bold text-ink">
          <MapPin className="h-4 w-4 shrink-0 text-muted" />
          {cameras.length > 0
            ? `${cameras.length} camera${cameras.length !== 1 ? "s" : ""} online`
            : "Loading cameras…"}
        </div>
        <div className="relative flex-1">
          <Search className="absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
          <input
            type="text"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter by name or location"
            className="w-full rounded-full border border-slate-300 bg-white py-2.5 pl-10 pr-10 text-sm text-ink placeholder:text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
          />
          <Filter className="absolute right-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted" />
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-3 rounded-2xl border border-alert/30 bg-alert/10 p-4 text-sm text-alert">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          {error} — make sure the Python API is running.
        </div>
      )}

      {loading && cameras.length === 0 ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-primary/50" />
        </div>
      ) : (
        <>
          {/* Section 1: Priority Surveillance */}
          <section>
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold text-ink">Priority Surveillance</h2>
                {urgentCams.some(isAlert) && (
                  <span className="flex items-center gap-1.5 rounded-full bg-alert/10 px-3 py-1 text-xs font-bold text-alert animate-pulse">
                    <Radio className="h-3 w-3" /> Urgent Activity Detected
                  </span>
                )}
              </div>
            </div>
            
            {urgentCams.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-2 rounded-[24px] border border-dashed border-slate-300 bg-surface-strong p-12 text-center">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-signal/10 text-signal">
                  <Radio className="h-6 w-6" />
                </span>
                <p className="font-bold text-ink">All Clear</p>
                <p className="text-sm text-muted">No high density or urgent activity detected at priority locations.</p>
              </div>
            ) : (
              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {urgentCams.map((cam, i) => (
                    <CctvTile
                      key={cam.camera_id}
                      label={`${cam.name} · ${cam.location}`}
                      boxes={boxesForCamera(i)}
                      videoSrc={videoForCamera(i)}
                      alert={isAlert(cam)}
                    />
                ))}
              </div>
            )}
          </section>

          {/* Section 2: Station & Train Coverage */}
          <section>
            <div className="mb-4 flex items-center justify-between flex-wrap gap-4">
              <h2 className="text-xl font-bold text-ink">Station & Train Coverage</h2>
              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 border-2 border-signal rounded-sm"></span>
                  <span className="text-muted">Tracked Person</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="h-3 w-3 border-2 border-primary rounded-sm"></span>
                  <span className="text-muted">Normal Movement</span>
                </div>
                <div className="flex items-center gap-1.5 font-semibold text-signal ml-2">
                  <Radio className="h-3.5 w-3.5" />
                  Live
                </div>
              </div>
            </div>
            
            {otherCams.length === 0 ? (
              <p className="py-12 text-center text-muted">
                {filter
                  ? "No cameras match your filter."
                  : "No cameras found. Make sure the database is seeded."}
              </p>
            ) : (
              <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {otherCams.map((cam, i) => (
                    <CctvTile
                      key={cam.camera_id}
                      label={`${cam.name} · ${cam.location}`}
                      boxes={boxesForCamera(i + urgentCams.length)}
                      videoSrc={videoForCamera(i + urgentCams.length)}
                      alert={isAlert(cam)}
                    />
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}
