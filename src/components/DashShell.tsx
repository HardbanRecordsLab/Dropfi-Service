"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import LangSwitch from "./LangSwitch";

export default function DashShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const { t } = useLang();
  const pathname = usePathname();

  if (!user) return <>{children}</>;

  const isClient = user.role === "client";
  const isAdmin = user.role === "admin";

  const links: { href: string; label: string }[] = [
    { href: "/dashboard", label: t("nav.dashboard") },
    ...(isClient
      ? [
          { href: "/dashboard/jobs", label: t("nav.jobs") },
          { href: "/dashboard/contracts", label: t("nav.contracts") },
        ]
      : [
          { href: "/dashboard/matches", label: t("nav.matches") },
          { href: "/dashboard/jobs", label: t("jobs.browse") },
        ]),
    ...(isClient ? [{ href: "/dashboard/freelancers", label: t("nav.talent") }] : []),
    ...(isClient ? [{ href: "/dashboard/factory", label: t("nav.factory") }] : []),
    ...(isClient ? [{ href: "/dashboard/integrations", label: t("nav.integrations") }] : []),
    { href: "/dashboard/radar", label: t("nav.radar") },
    { href: "/dashboard/developer", label: t("nav.developer") },
    { href: "/profile", label: t("nav.profile") },
    ...(isAdmin ? [{ href: "/admin", label: t("nav.admin") }] : []),
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "var(--bg-primary)", color: "var(--text-primary)" }}>
      <aside
        style={{
          width: "250px",
          flexShrink: 0,
          background: "#000",
          borderRight: "1px solid var(--border-subtle)",
          padding: "2rem 1.5rem",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          position: "sticky",
          top: 0,
          height: "100vh",
        }}
      >
        <div>
          <Link href="/" style={{ fontSize: "1.3rem", fontWeight: "800", display: "block", marginBottom: "2.5rem" }}>
            <span className="gold-gradient-text">DROPIFY</span>
          </Link>
          <nav style={{ display: "flex", flexDirection: "column", gap: "0.4rem" }}>
            {links.map((l) => {
              const active = pathname === l.href;
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  style={{
                    padding: "0.8rem 1rem",
                    borderRadius: "4px",
                    fontSize: "0.85rem",
                    fontWeight: active ? "700" : "500",
                    background: active ? "var(--accent-gold-muted)" : "transparent",
                    color: active ? "var(--accent-gold)" : "var(--text-secondary)",
                    borderLeft: active ? "2px solid var(--accent-gold)" : "2px solid transparent",
                  }}
                >
                  {l.label}
                </Link>
              );
            })}
            {isClient && (
              <Link href="/dashboard/jobs/new" style={{ marginTop: "1.5rem" }}>
                <button
                  style={{
                    width: "100%",
                    padding: "0.9rem",
                    background: "var(--accent-gold)",
                    color: "#000",
                    fontWeight: "800",
                    borderRadius: "4px",
                    fontSize: "0.78rem",
                    textTransform: "uppercase",
                    letterSpacing: "1px",
                  }}
                >
                  {t("nav.createJob")}
                </button>
              </Link>
            )}
          </nav>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <div>
              <div style={{ fontSize: "0.85rem", fontWeight: "700" }}>
                {user.first_name} {user.last_name}
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase" }}>
                {user.role} · {user.plan}
              </div>
            </div>
            <LangSwitch />
          </div>
          <button
            onClick={logout}
            style={{
              padding: "0.7rem",
              background: "transparent",
              border: "1px solid var(--border-subtle)",
              color: "var(--text-muted)",
              borderRadius: "4px",
              fontSize: "0.75rem",
              fontWeight: "700",
            }}
          >
            {t("nav.logout")}
          </button>
        </div>
      </aside>

      <main style={{ flex: 1, padding: "3rem", minWidth: 0 }}>
        <div style={{ maxWidth: "1200px", margin: "0 auto" }}>{children}</div>
      </main>
    </div>
  );
}
