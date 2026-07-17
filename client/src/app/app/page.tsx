"use client";

import { useAuth } from "@/lib/auth-context";
import { Siren, Navigation, ShieldCheck, Shield } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const QUICK_ACTIONS = [
  { label: "SOS", icon: Siren, tone: "bg-alert" },
  { label: "Share Live Loc", icon: Navigation, tone: "bg-teal" },
  { label: "Nearest Security", icon: ShieldCheck, tone: "bg-teal" },
  { label: "Safe Tracking", icon: Shield, tone: "bg-alert" },
];

const RECENT_TRIPS = [
  {
    date: "17 July",
    time: "06:30",
    route: "Cipete Raya – Haji Nawi",
    status: "On Board",
  },
  {
    date: "17 July",
    time: "06:30",
    route: "Fatmawati – Cipete Raya",
    status: "Arrived",
  },
  {
    date: "17 July",
    time: "06:30",
    route: "Lebak Bulus – Fatmawati",
    status: "Arrived",
  },
];

export default function CommuterHomePage() {
  const { user } = useAuth();

  return (
    <div className="flex flex-col gap-6">
      {/* Welcome card */}
      <section className="flex items-center justify-between gap-4 rounded-2xl bg-white p-5 shadow-[0_1px_6px_rgba(16,24,40,0.06)]">
        <div className="min-w-0">
          <h1 className="truncate text-2xl font-extrabold text-ink">
            Welcome, {user?.name ?? "XXX"}!
          </h1>
          <div className="mt-3 flex h-2.5 w-36 overflow-hidden rounded-full bg-teal/20">
            <div className="h-full w-3/4 rounded-full bg-teal" />
          </div>
        </div>
        <span
          aria-hidden
          className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-amber-soft text-2xl font-bold text-white"
        >
          {(user?.name ?? "X").charAt(0)}
        </span>
      </section>

      {/* Quick actions */}
      <section>
        <h2 className="mb-3 text-lg font-bold text-ink">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-4">
          {QUICK_ACTIONS.map(({ label, icon: Icon, tone }) => (
            <button
              key={label}
              className={cn(
                "flex flex-col items-center justify-center gap-2 rounded-2xl px-4 py-5 text-white transition-transform active:scale-[0.97]",
                tone
              )}
            >
              <Icon className="h-8 w-8" strokeWidth={1.8} />
              <span className="text-sm font-bold">{label}</span>
            </button>
          ))}
        </div>
      </section>

      {/* Recent trips */}
      <section>
        <h2 className="mb-3 text-lg font-bold text-ink">Recent Trips</h2>
        <div className="flex flex-col divide-y divide-slate-100 rounded-2xl bg-white shadow-[0_1px_6px_rgba(16,24,40,0.06)]">
          {RECENT_TRIPS.map((trip, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-3.5">
              <div className="w-12 shrink-0">
                <p className="text-[13px] font-bold leading-tight text-ink">
                  {trip.date}
                </p>
                <p className="text-[12px] text-muted">{trip.time}</p>
              </div>
              <span
                aria-hidden
                className="h-9 w-9 shrink-0 rounded-md bg-[repeating-linear-gradient(45deg,#d9e1f2,#d9e1f2_4px,#a9b4d0_5px,#a9b4d0_6px)]"
              />
              <p className="min-w-0 flex-1 truncate text-sm font-semibold text-ink">
                {trip.route}
              </p>
              <span
                className={cn(
                  "shrink-0 text-sm font-bold",
                  trip.status === "On Board" ? "text-alert" : "text-signal"
                )}
              >
                {trip.status}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
