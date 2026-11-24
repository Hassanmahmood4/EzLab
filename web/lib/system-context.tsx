"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api } from "./api";
import type { Health, StudentProfile, University } from "./types";

const HEALTH_POLL_MS = 15_000;

export type ConnectionState = "connecting" | "connected" | "unreachable";

interface SystemContextValue {
  connection: ConnectionState;
  health: Health | null;
  universities: University[];
  profile: StudentProfile | null;
  profileLoaded: boolean;
  saveProfile: (profile: StudentProfile) => Promise<StudentProfile>;
  refreshHealth: () => Promise<void>;
  lastStats: { tokensPerSecond: number; seconds: number; peakRssGb: number } | null;
  setLastStats: (stats: SystemContextValue["lastStats"]) => void;
}

const SystemContext = createContext<SystemContextValue | null>(null);

export function SystemProvider({ children }: { children: React.ReactNode }) {
  const [connection, setConnection] = useState<ConnectionState>("connecting");
  const [health, setHealth] = useState<Health | null>(null);
  const [universities, setUniversities] = useState<University[]>([]);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [profileLoaded, setProfileLoaded] = useState(false);
  const [lastStats, setLastStats] = useState<SystemContextValue["lastStats"]>(null);

  const refreshHealth = useCallback(async () => {
    try {
      setHealth(await api.health());
      setConnection("connected");
    } catch {
      setConnection("unreachable");
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      await refreshHealth();
      try {
        const [unis, saved] = await Promise.all([api.universities(), api.profile()]);
        if (cancelled) return;
        setUniversities(unis);
        setProfile(saved);
      } catch {
        /* connection state already reflects the failure */
      } finally {
        if (!cancelled) setProfileLoaded(true);
      }
    }
    boot();
    const timer = setInterval(refreshHealth, HEALTH_POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [refreshHealth]);

  // Retry the boot data once the server comes back.
  useEffect(() => {
    if (connection !== "connected" || universities.length > 0) return;
    api.universities().then(setUniversities).catch(() => undefined);
    api
      .profile()
      .then((saved) => {
        setProfile(saved);
        setProfileLoaded(true);
      })
      .catch(() => undefined);
  }, [connection, universities.length]);

  const saveProfile = useCallback(async (next: StudentProfile) => {
    const saved = await api.saveProfile(next);
    setProfile(saved);
    return saved;
  }, []);

  const value = useMemo(
    () => ({
      connection,
      health,
      universities,
      profile,
      profileLoaded,
      saveProfile,
      refreshHealth,
      lastStats,
      setLastStats,
    }),
    [connection, health, universities, profile, profileLoaded, saveProfile, refreshHealth, lastStats],
  );

  return <SystemContext.Provider value={value}>{children}</SystemContext.Provider>;
}

export function useSystem() {
  const ctx = useContext(SystemContext);
  if (!ctx) throw new Error("useSystem must be used inside SystemProvider");
  return ctx;
}

export function universityName(universities: University[], id: string | null | undefined) {
  return universities.find((u) => u.id === id)?.full_name ?? "";
}
