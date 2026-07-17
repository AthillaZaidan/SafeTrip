"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth, homeForRole, type Role } from "@/lib/auth-context";
import { motion } from "framer-motion";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<Role>("commuter");
  const { login } = useAuth();
  const router = useRouter();

  // Handle Alt+C and Alt+O for demo autofill
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && e.key.toLowerCase() === "c") {
        e.preventDefault();
        setEmail("commuter@safetrip.id");
        setRole("commuter");
      } else if (e.altKey && e.key.toLowerCase() === "o") {
        e.preventDefault();
        setEmail("officer@safetrip.id");
        setRole("officer");
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    login(email, role);
    router.push(homeForRole(role));
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative z-10 w-full max-w-[420px] rounded-[24px] border border-hairline bg-white px-8 pb-10 pt-12 shadow-sm"
    >
      <div className="mb-8 text-center">
        <h2 className="text-2xl font-bold text-ink">Welcome back</h2>
        <p className="mt-2 text-sm text-muted">
          Sign in to your account to continue
        </p>
      </div>

      <form className="flex flex-col gap-5" onSubmit={handleSubmit}>
        <div className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-1.5 block text-sm font-medium text-ink">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              placeholder="name@domain.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-ink placeholder:text-slate-400 focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>
          
          <div>
            <label htmlFor="role" className="mb-1.5 block text-sm font-medium text-ink">
              Role
            </label>
            <select
              id="role"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-ink focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            >
              <option value="officer">Control Room Officer</option>
              <option value="commuter">Passenger / Commuter</option>
            </select>
          </div>
        </div>

        <div className="mt-2 flex flex-col gap-3">
          <button
            type="submit"
            className={cn(
              "flex w-full justify-center rounded-full bg-primary py-3 px-4",
              "text-sm font-bold text-white shadow-sm",
              "transition-colors duration-200 hover:bg-primary-active",
              "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            )}
          >
            Sign In
          </button>
          <div className="mt-8 border-t border-slate-100 pt-6">
            <p className="text-center text-xs leading-relaxed text-muted">
              <strong className="text-ink">Demo Shortcuts:</strong>
              <br />
              Press{" "}
              <kbd className="mx-1 rounded bg-cloud px-1.5 py-0.5 font-mono text-ink border border-slate-200">
                Alt+C
              </kbd>{" "}
              for Commuter
              <br />
              Press{" "}
              <kbd className="mx-1 mt-2 rounded bg-cloud px-1.5 py-0.5 font-mono text-ink border border-slate-200">
                Alt+O
              </kbd>{" "}
              for Officer
            </p>
          </div>
        </div>
      </form>
    </motion.div>
  );
}
