"use client";

import { useLang } from "@/lib/i18n";
import Link from "next/link";

export default function Footer() {
  const { t } = useLang();
  return (
    <footer
      style={{
        padding: "4rem 2rem",
        background: "#000",
        borderTop: "1px solid var(--border-subtle)",
      }}
    >
      <div
        style={{
          maxWidth: "1300px",
          margin: "0 auto",
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "3rem",
        }}
      >
        <div>
          <div style={{ fontSize: "1.3rem", fontWeight: "800", marginBottom: "1rem" }}>
            <span className="gold-gradient-text">DROPIFY</span>
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>
            {t("brand.tagline")}. © 2026 DROPIFY by HardbanRecords Lab. {t("footer.rights")}
          </p>
          <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
            Wiercień, Polska · <a href="mailto:dropify@hardbanrecordslab.online" style={{ color: "var(--gold)" }}>dropify@hardbanrecordslab.online</a>
          </p>
        </div>
        <div>
          <h4 style={{ color: "var(--text-primary)", marginBottom: "1.2rem", fontSize: "0.85rem", textTransform: "uppercase" }}>
            {t("footer.platform")}
          </h4>
          <ul style={{ display: "flex", flexDirection: "column", gap: "0.7rem", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
            <li><Link href="/dashboard">{t("nav.dashboard")}</Link></li>
            <li><Link href="/register">{t("nav.register")}</Link></li>
            <li><Link href="/#pricing">{t("nav.pricing")}</Link></li>
          </ul>
        </div>
        <div>
          <h4 style={{ color: "var(--text-primary)", marginBottom: "1.2rem", fontSize: "0.85rem", textTransform: "uppercase" }}>
            {t("footer.legal")}
          </h4>
          <ul style={{ display: "flex", flexDirection: "column", gap: "0.7rem", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
            <li><Link href="/terms">{t("footer.regulamin")}</Link></li>
            <li><Link href="/privacy">{t("footer.privacy")}</Link></li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
