"use client";

import { useState } from "react";
import Link from "next/link";
import PortalNav from "@/components/PortalNav";
import Footer from "@/components/Footer";
import { useLang } from "@/lib/i18n";
import { Btn, inputStyle } from "@/components/ui";

export default function FeesPage() {
  const { t } = useLang();
  const [amount, setAmount] = useState(5000);

  const platforms = [
    {
      name: "DROPIFY",
      rate: 0.08,
      color: "var(--accent-gold)",
      tag: t("fees.dropify"),
      highlight: true,
    },
    { name: "Upwork", rate: 0.19, color: "#6da93e", tag: t("fees.upwork"), highlight: false },
    { name: "Fiverr", rate: 0.277, color: "#1dbf73", tag: t("fees.fiverr"), highlight: false },
  ];

  const best = platforms.reduce((a, b) => (a.rate < b.rate ? a : b));

  return (
    <main style={{ minHeight: "100vh" }}>
      <PortalNav />

      <section
        style={{
          padding: "6rem 2rem 4rem",
          textAlign: "center",
          background: "radial-gradient(ellipse at top, rgba(197,160,89,0.12) 0%, transparent 60%)",
        }}
      >
        <div style={{ maxWidth: "900px", margin: "0 auto" }}>
          <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", marginBottom: "1rem" }}>
            TRANSPARENCY
          </div>
          <h1 style={{ fontSize: "clamp(2.2rem, 5vw, 3.6rem)", marginBottom: "1rem" }} className="gold-gradient-text">
            {t("fees.title")}
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "1.05rem" }}>{t("fees.subtitle")}</p>
        </div>
      </section>

      <section style={{ padding: "2rem 2rem 6rem" }}>
        <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
          {/* Calculator */}
          <div className="premium-card" style={{ padding: "3rem", marginBottom: "3rem" }}>
            <label style={{ display: "block", fontSize: "0.8rem", fontWeight: "700", textTransform: "uppercase", letterSpacing: "1px", color: "var(--text-muted)", marginBottom: "0.8rem" }}>
              {t("fees.label")}
            </label>
            <input
              type="number"
              min={100}
              step={100}
              value={amount}
              onChange={(e) => setAmount(Math.max(0, parseFloat(e.target.value) || 0))}
              style={{ ...inputStyle, maxWidth: "280px", fontSize: "1.3rem", fontWeight: "800" }}
            />

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1.8rem", marginTop: "2.5rem" }}>
              {platforms.map((p) => {
                const fee = amount * p.rate;
                const freelancerGets = amount - fee;
                const savings = best.rate < p.rate ? amount * (p.rate - best.rate) : 0;
                return (
                  <div
                    key={p.name}
                    className="premium-card"
                    style={{
                      ...(p.highlight ? { border: "1px solid var(--border-gold)", boxShadow: "0 0 40px rgba(197,160,89,0.12)" } : { opacity: 0.85 }),
                      textAlign: "center",
                    }}
                  >
                    <div style={{ fontSize: "0.9rem", fontWeight: "800", letterSpacing: "1px", marginBottom: "0.4rem", color: p.color }}>
                      {p.name}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "1.5rem" }}>{p.tag}</div>

                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.3rem" }}>
                      {t("fees.clientPays")}
                    </div>
                    <div style={{ fontSize: "1.8rem", fontWeight: "800" }}>
                      {amount.toLocaleString()} {t("common.currency")}
                    </div>

                    <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginTop: "1.2rem", marginBottom: "0.3rem" }}>
                      {t("fees.freelancerGets")}
                    </div>
                    <div style={{ fontSize: "1.8rem", fontWeight: "800", color: p.highlight ? "var(--accent-gold)" : "var(--text-primary)" }}>
                      {freelancerGets.toLocaleString()} {t("common.currency")}
                    </div>

                    <div style={{ marginTop: "1.2rem", paddingTop: "1rem", borderTop: "1px solid var(--border-subtle)" }}>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                        {t("fees.combined")}: <b style={{ color: "#f87171" }}>{fee.toLocaleString()} {t("common.currency")} ({(p.rate * 100).toFixed(p.rate === 0.277 ? 1 : 0)}%)</b>
                      </div>
                      {savings > 0 && p.highlight && (
                        <div style={{ fontSize: "0.85rem", fontWeight: "800", color: "#4ade80", marginTop: "0.5rem" }}>
                          ✓ {t("fees.save")}: {(fee - amount * best.rate).toLocaleString()} {t("common.currency")}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            <div style={{ marginTop: "2rem", padding: "1.2rem 1.5rem", background: "rgba(197,160,89,0.06)", border: "1px dashed var(--border-gold)", borderRadius: "4px", fontSize: "0.88rem", color: "var(--text-secondary)" }}>
              ⭐ {t("fees.dynamic")}
            </div>

            <div style={{ textAlign: "center", marginTop: "2.5rem" }}>
              <Link href="/register">
                <Btn>{t("fees.cta")}</Btn>
              </Link>
            </div>
          </div>

          <p style={{ fontSize: "0.72rem", color: "var(--text-muted)", textAlign: "center" }}>{t("fees.source")}</p>
        </div>
      </section>

      <Footer />
    </main>
  );
}
