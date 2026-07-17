"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Home,
  Cctv,
  TriangleAlert,
  Search,
  ChevronLeft,
  LogOut,
  ChevronRight,
} from "lucide-react";
import { useRoleGuard, useAuth } from "@/lib/auth-context";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: Home },
  { href: "/dashboard/monitoring", label: "Live Monitoring", icon: Cctv },
  { href: "/dashboard/incidents", label: "Incident Report", icon: TriangleAlert },
  { href: "/dashboard/investigation", label: "Investigation", icon: Search },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const user = useRoleGuard("officer");
  const { logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();

  if (!user) return null;

  return (
    <div className="min-h-screen bg-cloud text-ink flex flex-col">
      {/* Top Header */}
      <header className="sticky top-0 z-30 flex h-16 items-center justify-between bg-white border-b border-hairline px-6 lg:px-10">
        <div className="flex items-center gap-4">
          <Link href="/dashboard" className="text-lg font-extrabold tracking-tight text-primary">
            Safe Trip
          </Link>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-signal" />
            <span className="text-xs font-semibold text-muted">Admin Online</span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-ink">Role: {user.role}</span>
          <button
            onClick={logout}
            title="Sign out"
            className="rounded-full p-2 text-muted transition-colors hover:bg-surface-strong hover:text-ink"
          >
            <LogOut className="h-5 w-5" />
          </button>
        </div>
      </header>

      <div className="flex flex-1 items-start">
        {/* Left Sidebar */}
        <aside className="sticky top-16 flex h-[calc(100vh-4rem)] w-16 shrink-0 flex-col gap-1 bg-white border-r border-hairline py-4 md:w-60 md:px-3">
          {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "group flex items-center justify-center gap-3 rounded-full py-3 transition-colors md:justify-start md:px-4",
                  active
                    ? "bg-primary text-white"
                    : "text-muted hover:bg-surface-strong hover:text-ink"
                )}
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span className="hidden text-sm font-semibold md:block">{label}</span>
                {active && (
                  <ChevronRight className="ml-auto hidden h-4 w-4 md:block opacity-70" />
                )}
              </Link>
            );
          })}
        </aside>

        {/* Content */}
        <main className="min-w-0 flex-1 p-6 lg:p-10">{children}</main>
      </div>
    </div>
  );
}
