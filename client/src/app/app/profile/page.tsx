"use client";

import { useAuth } from "@/lib/auth-context";
import { useRouter } from "next/navigation";
import { LogOut, Mail, ShieldCheck } from "lucide-react";

export default function ProfilePage() {
  const { user, logout } = useAuth();
  const router = useRouter();

  return (
    <div className="flex flex-col gap-5">
      {/* Identity card */}
      <section className="flex flex-col items-center gap-3 rounded-2xl bg-white p-6 text-center shadow-[0_1px_6px_rgba(16,24,40,0.06)]">
        <span className="flex h-16 w-16 items-center justify-center rounded-full bg-amber-soft text-3xl font-bold text-white">
          {(user?.name ?? "X").charAt(0)}
        </span>
        <div>
          <h1 className="text-xl font-extrabold text-ink">{user?.name}</h1>
          <p className="mt-0.5 flex items-center justify-center gap-1.5 text-sm text-muted">
            <Mail className="h-3.5 w-3.5" />
            {user?.email}
          </p>
        </div>
        <span className="mt-1 flex items-center gap-1.5 rounded-full bg-signal/10 px-3 py-1 text-xs font-bold text-signal">
          <ShieldCheck className="h-3.5 w-3.5" />
          Commuter Account
        </span>
      </section>

      {/* Sign out */}
      <button
        onClick={() => {
          logout();
          router.push("/login");
        }}
        className="flex w-full items-center justify-center gap-2 rounded-xl bg-alert py-3.5 text-base font-bold text-white transition-colors hover:bg-alert/90 active:scale-[0.99]"
      >
        <LogOut className="h-5 w-5" />
        Sign Out
      </button>
    </div>
  );
}
