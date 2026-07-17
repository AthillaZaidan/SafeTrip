"use client";

import { useAuth } from "@/lib/auth-context";
import { Siren, Navigation, ShieldCheck, Shield, MapPin, ChevronRight } from "lucide-react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { motion, type Variants } from "framer-motion";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const containerVariants: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 },
  },
};

const itemVariants: Variants = {
  hidden: { opacity: 0, y: 15 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.22, 1, 0.36, 1] } },
};

import Link from "next/link";

const QUICK_ACTIONS = [
  { label: "Report Incident", icon: Siren, color: "text-alert", bg: "bg-alert/10", href: "/app/report" },
  { label: "Share Live Loc", icon: Navigation, color: "text-primary", bg: "bg-primary/10", href: "/app" },
  { label: "Nearest Security", icon: ShieldCheck, color: "text-teal", bg: "bg-teal/10", href: "/app" },
  { label: "Safe Tracking", icon: Shield, color: "text-signal", bg: "bg-signal/10", href: "/app" },
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
    <motion.div variants={containerVariants} initial="hidden" animate="visible" className="flex flex-col gap-6 pt-2 md:gap-8 md:pt-4">
      {/* Welcome card */}
      <motion.section variants={itemVariants} className="relative overflow-hidden flex items-center justify-between gap-5 rounded-[24px] bg-white p-6 md:p-8 shadow-sm border border-hairline">
        <div className="absolute top-0 right-0 h-full w-32 md:w-64 bg-gradient-to-l from-primary/5 to-transparent pointer-events-none" />
        <div className="min-w-0 relative z-10">
          <h1 className="truncate text-xl md:text-2xl font-extrabold text-ink tracking-tight">
            Welcome, {user?.name ?? "XXX"}!
          </h1>
          <div className="mt-3 md:mt-4 flex h-2.5 w-36 md:w-48 overflow-hidden rounded-full bg-teal/20">
            <div className="h-full w-3/4 rounded-full bg-teal" />
          </div>
        </div>
        <span
          aria-hidden
          className="flex h-14 w-14 md:h-16 md:w-16 shrink-0 items-center justify-center rounded-full bg-amber-soft text-2xl md:text-3xl font-bold text-white shadow-sm"
        >
          {(user?.name ?? "X").charAt(0)}
        </span>
      </motion.section>

      {/* Quick actions */}
      <motion.section variants={itemVariants}>
        <h2 className="mb-3 md:mb-4 text-[17px] md:text-lg font-bold text-ink tracking-tight">Quick Actions</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-5">
          {QUICK_ACTIONS.map(({ label, icon: Icon, color, bg, href }) => (
            <Link
              key={label}
              href={href}
              className="group flex flex-col items-center justify-center gap-3 rounded-[24px] bg-white border border-hairline shadow-sm px-2 py-5 md:py-6 transition-all hover:border-primary/20 hover:shadow-md active:scale-95"
            >
              <div className={cn("flex h-14 w-14 md:h-16 md:w-16 items-center justify-center rounded-[18px] transition-transform duration-300 group-hover:scale-105 group-hover:-translate-y-1", bg)}>
                <Icon className={cn("h-7 w-7 md:h-8 md:w-8", color)} strokeWidth={2} />
              </div>
              <span className="text-[13px] md:text-[14px] font-bold text-ink tracking-tight">{label}</span>
            </Link>
          ))}
        </div>
      </motion.section>

      {/* Recent trips */}
      <motion.section variants={itemVariants}>
        <h2 className="mb-3 md:mb-4 text-[17px] md:text-lg font-bold text-ink tracking-tight">Recent Trips</h2>
        <div className="flex flex-col divide-y divide-hairline rounded-[24px] bg-white shadow-sm border border-hairline overflow-hidden">
          {RECENT_TRIPS.map((trip, i) => (
            <div key={i} className="group flex items-center gap-3.5 md:gap-5 px-4 md:px-6 py-4 md:py-5 cursor-pointer hover:bg-cloud/40 transition-colors">
              <div className="w-14 shrink-0">
                <p className="text-[14px] font-black leading-tight text-ink">
                  {trip.date}
                </p>
                <p className="text-[11px] font-bold text-muted uppercase tracking-wider mt-0.5">{trip.time}</p>
              </div>
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-cloud group-hover:bg-white group-hover:shadow-sm transition-all border border-transparent group-hover:border-hairline">
                <MapPin className="h-5 w-5 text-muted" />
              </div>
              <p className="min-w-0 flex-1 truncate text-[14px] font-bold text-ink">
                {trip.route}
              </p>
              <span
                className={cn(
                  "shrink-0 rounded-full px-2.5 py-1 text-[11px] font-extrabold tracking-wide uppercase",
                  trip.status === "On Board" ? "bg-alert/10 text-alert" : "bg-signal/10 text-signal"
                )}
              >
                {trip.status}
              </span>
              <ChevronRight className="h-4 w-4 shrink-0 text-hairline group-hover:text-muted transition-colors ml-1" />
            </div>
          ))}
        </div>
      </motion.section>
    </motion.div>
  );
}
