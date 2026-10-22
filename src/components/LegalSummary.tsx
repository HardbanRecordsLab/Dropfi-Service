"use client";
import PortalNav from "@/components/PortalNav";
import Footer from "@/components/Footer";
import { useLang } from "@/lib/i18n";
import { wpUrl } from "@/lib/langPref";

// Dokumenty prawne są wspólne dla całej platformy HardbanRecords Lab (jedno źródło na
// hardbanrecordslab.online). Tu tylko skrót dla DROPIFY.
const DOCS = [
  { path: "/terms/", key: "legal.terms" },
  { path: "/privacy/", key: "legal.privacy" },
  { path: "/cookies/", key: "legal.cookies" },
];

export default function LegalSummary({ title, points }: { title: { pl: string; en: string }; points: { pl: string[]; en: string[] } }) {
  const { lang, t } = useLang();
  return (
    <main style={{ minHeight: "100vh" }}>
      <PortalNav />
      <section style={{ padding: "6rem 2rem 2rem" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: 700, letterSpacing: "3px", marginBottom: "1rem" }}>
            LEGAL
          </div>
          <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: "1rem" }} className="gold-gradient-text">
            {title[lang]}
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            {t("legal.effective")}
          </p>
          {lang === "en" && <p style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{t("legal.note")}</p>}
        </div>
      </section>
      <section style={{ padding: "1rem 2rem 6rem" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto", lineHeight: 1.8, color: "var(--text-secondary)" }}>
          <p>{t("legal.intro")}</p>
          <ul style={{ paddingLeft: "1.2rem", margin: "1rem 0 2rem" }}>
            {points[lang].map((p) => (
              <li key={p} style={{ marginBottom: "0.5rem" }}>{p}</li>
            ))}
          </ul>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem" }}>
            {DOCS.map((d) => (
              <a
                key={d.path}
                href={wpUrl(d.path, lang)}
                target="_blank"
                rel="noopener noreferrer"
                style={{ border: "1px solid var(--accent-gold)", borderRadius: "8px", padding: "0.4rem 0.9rem", color: "var(--accent-gold)", textDecoration: "none" }}
              >
                {t(d.key)} ↗
              </a>
            ))}
          </div>
          <p style={{ marginTop: "2rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            {t("legal.contact")}
          </p>
        </div>
      </section>
      <Footer />
    </main>
  );
}
