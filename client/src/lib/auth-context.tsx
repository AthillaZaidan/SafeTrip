"use client";

import React, {
  createContext,
  useContext,
  useCallback,
  useSyncExternalStore,
} from "react";
import { useRouter } from "next/navigation";

export type Role = "commuter" | "officer";

export interface User {
  email: string;
  name: string;
  role: Role;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, role: Role) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = "safetrip_user";

/* ------------------------------------------------------------------ */
/* Tiny external store over localStorage (hydration-safe, no effects)  */
/* ------------------------------------------------------------------ */

const listeners = new Set<() => void>();

function subscribe(callback: () => void) {
  listeners.add(callback);
  window.addEventListener("storage", callback);
  return () => {
    listeners.delete(callback);
    window.removeEventListener("storage", callback);
  };
}

function emitChange() {
  for (const callback of listeners) callback();
}

function getSnapshot() {
  return window.localStorage.getItem(STORAGE_KEY);
}

function getServerSnapshot() {
  return null;
}

/** Hydration-safe mounted flag. */
function useMounted() {
  return useSyncExternalStore(
    useCallback(() => () => {}, []),
    () => true,
    () => false
  );
}

/* ------------------------------------------------------------------ */

/** Where each role lands after sign-in. */
export function homeForRole(role: Role): string {
  return role === "officer" ? "/dashboard" : "/app";
}

/** Derive a friendly display name from an email address. */
function nameFromEmail(email: string): string {
  const local = email.split("@")[0] ?? "";
  const cleaned = local.replace(/[._-]+/g, " ").trim();
  if (!cleaned) return "User";
  return cleaned
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const stored = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const mounted = useMounted();
  const user: User | null = stored ? (JSON.parse(stored) as User) : null;

  const login = useCallback((email: string, role: Role) => {
    const newUser = { email, name: nameFromEmail(email), role };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(newUser));
    emitChange();
  }, []);

  const logout = useCallback(() => {
    window.localStorage.removeItem(STORAGE_KEY);
    emitChange();
  }, []);

  if (!mounted) return null; // Avoid hydration mismatch

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

/**
 * Client-side role guard for the demo.
 * Returns the user only when signed in with `role`;
 * otherwise redirects to the correct home for the session (or /login).
 */
export function useRoleGuard(role: Role) {
  const { user } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!user) {
      router.replace("/login");
    } else if (user.role !== role) {
      router.replace(homeForRole(user.role));
    }
  }, [user, role, router]);

  return user && user.role === role ? user : null;
}
// Force Turbopack rebuild 2
