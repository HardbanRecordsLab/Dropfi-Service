"use client";
import PortalNav from "@/components/PortalNav";
import Footer from "@/components/Footer";

// Dokumenty prawne są wspólne dla całej platformy HardbanRecords Lab (jedno źródło na
// hardbanrecordslab.online). Tu tylko skrót dla DROPIFY.
const SITE = "https://hardbanrecordslab.online";
const DOCS = [
  { href: `${SITE}/terms/`, label: "Regulamin" },
  { href: `${SITE}/privacy/`, label: "Polityka prywatności" },
  { href: `${SITE}/cookies/`, label: "Polityka cookies" },
];

export default function LegalSummary({ title, points }: { title: string; points: string[] }) {
  return (
    <main style={{ minHeight: "100vh" }}>
      <PortalNav />
      <section style={{ padding: "6rem 2rem 2rem" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto" }}>
          <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: 700, letterSpacing: "3px", marginBottom: "1rem" }}>
            LEGAL
          </div>
          <h1 style={{ fontSize: "clamp(2rem, 4vw, 3rem)", marginBottom: "1rem" }} className="gold-gradient-text">
            {title}
          </h1>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            Obowiązuje od 11 października 2026 r. · Kamil Skomra, HardbanRecords Lab
          </p>
        </div>
      </section>
      <section style={{ padding: "1rem 2rem 6rem" }}>
        <div style={{ maxWidth: "800px", margin: "0 auto", lineHeight: 1.8, color: "var(--text-secondary)" }}>
          <p>DROPIFY jest częścią HardbanRecords Lab. Obowiązują wspólne dokumenty całej platformy. Najważniejsze zasady dotyczące tej aplikacji:</p>
          <ul style={{ paddingLeft: "1.2rem", margin: "1rem 0 2rem" }}>
            {points.map((p) => (
              <li key={p} style={{ marginBottom: "0.5rem" }}>{p}</li>
            ))}
          </ul>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.6rem" }}>
            {DOCS.map((d) => (
              <a
                key={d.href}
                href={d.href}
                target="_blank"
                rel="noopener noreferrer"
                style={{ border: "1px solid var(--accent-gold)", borderRadius: "8px", padding: "0.4rem 0.9rem", color: "var(--accent-gold)", textDecoration: "none" }}
              >
                {d.label} ↗
              </a>
            ))}
          </div>
          <p style={{ marginTop: "2rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>
            Sprawy prawne, reklamacje i dane osobowe: legal@hardbanrecordslab.online
          </p>
        </div>
      </section>
      <Footer />
    </main>
  );
}
