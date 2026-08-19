"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Loading, StatCard } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { AdminStats } from "@/lib/types";

interface AdminUserRow {
  id: string;
  email: string;
  role: string;
  plan: string;
  rating: number;
  total_jobs: number;
  is_active: boolean;
  created_at: string;
}

export default function AdminPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUserRow[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      try {
        const s = await API.adminStats();
        const u = await API.adminUsers();
        if (active) {
          setStats(s as AdminStats);
          setUsers(u as AdminUserRow[]);
        }
      } catch (err) {
        if (active) setError(getErrorMessage(err));
      }
    })();
    return () => {
      active = false;
    };
  }, [user]);

  if (user && user.role !== "admin") {
    return (
      <DashShell>
        <div className="premium-card" style={{ textAlign: "center", padding: "4rem" }}>
          <p style={{ color: "var(--text-secondary)" }}>Forbidden.</p>
        </div>
      </DashShell>
    );
  }

  if (!stats) return <DashShell><Loading /></DashShell>;

  return (
    <DashShell>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          CONTROL ROOM
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("admin.title")}</h1>
        {error && <p style={{ color: "#f87171", marginTop: "0.5rem" }}>{error}</p>}
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1.8rem", marginBottom: "3rem" }}>
        <StatCard icon="👥" label={t("admin.users")} value={stats.users} />
        <StatCard icon="🎨" label={t("admin.freelancers")} value={stats.freelancers} />
        <StatCard icon="🏢" label={t("admin.clients")} value={stats.clients} />
        <StatCard icon="📋" label={t("admin.jobs")} value={stats.jobs} sub={`${stats.open_jobs} ${t("admin.openJobs")}`} />
        <StatCard icon="🤝" label={t("admin.matches")} value={stats.matches} />
        <StatCard icon="📄" label={t("admin.contracts")} value={stats.contracts} />
        <StatCard icon="💰" label={t("admin.revenue")} value={`${stats.revenue.toLocaleString()} ${t("common.currency")}`} />
        <StatCard icon="✓" label={t("dash.stat.completed")} value={stats.completed_jobs} />
      </div>

      <div className="premium-card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{ padding: "1.5rem 2rem", borderBottom: "1px solid var(--border-subtle)" }}>
          <h2 style={{ fontSize: "1.2rem", fontFamily: "var(--font-playfair)" }}>Users</h2>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", textAlign: "left" }}>
          <thead>
            <tr style={{ background: "rgba(255,255,255,0.03)", borderBottom: "1px solid var(--border-subtle)" }}>
              <th style={{ padding: "1rem 2rem", fontSize: "0.72rem", textTransform: "uppercase", color: "var(--text-muted)" }}>Email</th>
              <th style={{ padding: "1rem 2rem", fontSize: "0.72rem", textTransform: "uppercase", color: "var(--text-muted)" }}>Role</th>
              <th style={{ padding: "1rem 2rem", fontSize: "0.72rem", textTransform: "uppercase", color: "var(--text-muted)" }}>Plan</th>
              <th style={{ padding: "1rem 2rem", fontSize: "0.72rem", textTransform: "uppercase", color: "var(--text-muted)" }}>Rating</th>
              <th style={{ padding: "1rem 2rem", fontSize: "0.72rem", textTransform: "uppercase", color: "var(--text-muted)" }}>Joined</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <td style={{ padding: "1rem 2rem", fontWeight: "600" }}>{u.email}</td>
                <td style={{ padding: "1rem 2rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>{u.role}</td>
                <td style={{ padding: "1rem 2rem", fontSize: "0.85rem" }}>
                  <span style={{ color: u.plan === "pro" ? "var(--accent-gold)" : "var(--text-secondary)", fontWeight: "700" }}>
                    {u.plan?.toUpperCase()}
                  </span>
                </td>
                <td style={{ padding: "1rem 2rem", fontSize: "0.85rem" }}>⭐ {u.rating}</td>
                <td style={{ padding: "1rem 2rem", fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  {u.created_at?.slice(0, 10)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </DashShell>
  );
}
