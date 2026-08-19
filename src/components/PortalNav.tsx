"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import LangSwitch from "./LangSwitch";

export default function PortalNav() {
  const { user } = useAuth();
  const { t } = useLang();

  const links = [
    { href: "/#how", label: t("nav.how") },
    { href: "/#features", label: t("nav.features") },
    { href: "/fees", label: t("nav.fees") },
    { href: "/#pricing", label: t("nav.pricing") },
  ];

  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 50,
        background: "rgba(5,5,5,0.85)",
        backdropFilter: "blur(12px)",
        borderBottom: "1px solid var(--border-subtle)",
      }}
    >
      <div
        style={{
          maxWidth: "1300px",
          margin: "0 auto",
          padding: "1.2rem 2rem",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Link href="/" style={{ fontSize: "1.3rem", fontWeight: "800" }}>
          <span className="gold-gradient-text">DROPIFY</span>
        </Link>

        <nav style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              style={{ fontSize: "0.82rem", color: "var(--text-secondary)", fontWeight: "600" }}
            >
              {l.label}
            </Link>
          ))}
          <LangSwitch />
          {user ? (
            <Link href="/dashboard">
              <button
                style={{
                  padding: "0.7rem 1.5rem",
                  background: "var(--accent-gold)",
                  color: "#000",
                  fontWeight: "700",
                  borderRadius: "4px",
                  fontSize: "0.78rem",
                  textTransform: "uppercase",
                  letterSpacing: "1px",
                }}
              >
                {t("nav.dashboard")}
              </button>
            </Link>
          ) : (
            <div style={{ display: "flex", gap: "0.8rem" }}>
              <Link href="/login">
                <button
                  style={{
                    padding: "0.7rem 1.5rem",
                    background: "transparent",
                    border: "1px solid var(--border-subtle)",
                    color: "var(--text-primary)",
                    fontWeight: "700",
                    borderRadius: "4px",
                    fontSize: "0.78rem",
                  }}
                >
                  {t("nav.login")}
                </button>
              </Link>
              <Link href="/register">
                <button
                  style={{
                    padding: "0.7rem 1.5rem",
                    background: "var(--accent-gold)",
                    color: "#000",
                    fontWeight: "700",
                    borderRadius: "4px",
                    fontSize: "0.78rem",
                  }}
                >
                  {t("nav.register")}
                </button>
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
