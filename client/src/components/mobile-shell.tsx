"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Navigation, TriangleAlert, User } from "lucide-react";
import { useRoleGuard } from "@/lib/auth-context";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const NAV_ITEMS = [
  { href: "/app", label: "Home", icon: Home },
  { href: "/app/track", label: "Track", icon: Navigation },
  { href: "/app/report", label: "Report", icon: TriangleAlert },
  { href: "/app/profile", label: "Profile", icon: User },
];

/**
 * Phone-framed commuter shell: navy header with centered
 * wordmark + floating bottom navigation. docs/DESIGN.md §5.
 */
export function MobileShell({ children }: { children: React.ReactNode }) {
  const user = useRoleGuard("commuter");
  const pathname = usePathname();

  if (!user) return null;

  return (
    <div className="flex min-h-screen justify-center bg-cloud">
      <div className="relative flex min-h-screen w-full max-w-[420px] flex-col border-x border-hairline bg-cloud shadow-sm">
        {/* Header */}
        <header className="flex h-16 items-center justify-center bg-white border-b border-hairline">
          <span className="text-lg font-extrabold tracking-tight text-primary">
            Safe Trip
          </span>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-y-auto px-4 pb-28 pt-5">
          {children}
        </main>

        {/* Bottom nav */}
        <nav className="fixed bottom-4 left-1/2 z-30 w-[min(420px,100%-2rem)] -translate-x-1/2 rounded-full bg-white border border-hairline shadow-md px-2 py-2">
          <ul className="flex items-center justify-around">
            {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
              const active = pathname === href;
              return (
                <li key={href}>
                  <Link
                    href={href}
                    className={cn(
                      "flex w-16 flex-col items-center gap-0.5 rounded-full py-1.5 transition-colors",
                      active ? "text-primary" : "text-muted hover:text-ink"
                    )}
                  >
                    <Icon className="h-5 w-5" />
                    <span className="text-[11px] font-medium">{label}</span>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
      </div>
    </div>
  );
}
// Force Turbopack rebuild 2
