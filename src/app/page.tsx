"use client";

import Link from "next/link";
import PortalNav from "@/components/PortalNav";
import Footer from "@/components/Footer";
import { useLang } from "@/lib/i18n";
import { Btn } from "@/components/ui";
import { CATEGORIES } from "@/lib/categories";

export default function Home() {
  const { t } = useLang();

  const features = [
    { icon: "🤖", title: t("features.ai.title"), desc: t("features.ai.desc") },
    { icon: "💰", title: t("features.fee.title"), desc: t("features.fee.desc") },
    { icon: "⚡", title: t("features.auto.title"), desc: t("features.auto.desc") },
    { icon: "🌍", title: t("features.bilingual.title"), desc: t("features.bilingual.desc") },
    { icon: "🖥️", title: t("features.saas.title"), desc: t("features.saas.desc") },
    { icon: "🔒", title: t("features.escrow.title"), desc: t("features.escrow.desc") },
  ];

  const steps = [
    { n: "01", title: t("how.s1.title"), desc: t("how.s1.desc") },
    { n: "02", title: t("how.s2.title"), desc: t("how.s2.desc") },
    { n: "03", title: t("how.s3.title"), desc: t("how.s3.desc") },
    { n: "04", title: t("how.s4.title"), desc: t("how.s4.desc") },
  ];

  const plans = [
    { name: "FREE", price: "0", jobs: t("pricing.free.jobs"), features: [t("pricing.feature.matching")], cta: t("pricing.cta.free") },
    { name: "STARTER", price: "49", jobs: t("pricing.starter.jobs"), features: [t("pricing.feature.matching"), t("pricing.feature.analytics"), t("pricing.feature.support")], cta: t("pricing.cta.starter"), popular: false },
    { name: "PRO", price: "149", jobs: t("pricing.pro.jobs"), features: [t("pricing.feature.matching"), t("pricing.feature.priority"), t("pricing.feature.analytics"), t("pricing.feature.slack")], cta: t("pricing.cta.pro"), popular: true },
  ];

  return (
    <main>
      <PortalNav />

      {/* Hero */}
      <section
        style={{
          padding: "8rem 2rem 6rem",
          textAlign: "center",
          background:
            "radial-gradient(ellipse at top, rgba(197,160,89,0.12) 0%, transparent 60%)",
        }}
      >
        <div style={{ maxWidth: "900px", margin: "0 auto" }}>
          <div
            style={{
              fontSize: "0.8rem",
              letterSpacing: "3px",
              color: "var(--accent-gold)",
              fontWeight: "700",
              marginBottom: "1.5rem",
            }}
          >
            AI · AUTOMATION · GLOBAL · PL/EN
          </div>
          <h1 style={{ fontSize: "clamp(2.6rem, 6vw, 4.5rem)", lineHeight: "1.1", marginBottom: "1.5rem" }}>
            <span className="gold-gradient-text">{t("hero.title1")}</span>
            <br />
            {t("hero.title2")}
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "1.15rem", maxWidth: "650px", margin: "0 auto 2.5rem", fontWeight: "300" }}>
            {t("hero.subtitle")}
          </p>
          <div style={{ display: "flex", gap: "1rem", justifyContent: "center", flexWrap: "wrap" }}>
            <Link href="/register">
              <Btn>{t("hero.cta.start")}</Btn>
            </Link>
            <Link href="#how">
              <Btn variant="outline">{t("hero.cta.learn")}</Btn>
            </Link>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "center",
              gap: "3rem",
              marginTop: "4rem",
              flexWrap: "wrap",
            }}
          >
            {[
              { value: "30s", label: t("how.s2.title") },
              { value: "8%", label: t("hero.stat.fee") },
              { value: "24/7", label: t("features.auto.title") },
              { value: "PL · EN", label: t("features.bilingual.title") },
            ].map((s) => (
              <div key={s.value} style={{ textAlign: "center" }}>
                <div style={{ fontSize: "2.2rem", fontWeight: "800" }} className="gold-gradient-text">
                  {s.value}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Categories */}
      <section style={{ padding: "3rem 2rem", borderTop: "1px solid var(--border-subtle)", borderBottom: "1px solid var(--border-subtle)" }}>
        <div style={{ maxWidth: "1300px", margin: "0 auto", display: "flex", flexWrap: "wrap", gap: "0.8rem", justifyContent: "center" }}>
          {CATEGORIES.map((c) => (
            <span key={c} className="glass" style={{ padding: "0.7rem 1.4rem", borderRadius: "30px", fontSize: "0.85rem", fontWeight: "600", color: "var(--text-secondary)" }}>
              {c}
            </span>
          ))}
        </div>
      </section>

      {/* Features */}
      <section id="features" style={{ padding: "7rem 2rem" }}>
        <div style={{ maxWidth: "1300px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", marginBottom: "1rem" }}>
              PLATFORM
            </div>
            <h2 style={{ fontSize: "clamp(2rem, 4vw, 3rem)" }}>{t("features.title")}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "2rem" }}>
            {features.map((f) => (
              <div key={f.title} className="premium-card">
                <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>{f.icon}</div>
                <h3 style={{ fontSize: "1.15rem", marginBottom: "0.6rem" }}>{f.title}</h3>
                <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", fontWeight: "300" }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how" style={{ padding: "7rem 2rem", background: "var(--bg-secondary)" }}>
        <div style={{ maxWidth: "1300px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", marginBottom: "1rem" }}>
              PROCESS
            </div>
            <h2 style={{ fontSize: "clamp(2rem, 4vw, 3rem)" }}>{t("how.title")}</h2>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "2rem" }}>
            {steps.map((s) => (
              <div key={s.n} style={{ position: "relative" }}>
                <div style={{ fontSize: "3.5rem", fontWeight: "900", opacity: 0.06, position: "absolute", top: "-1.5rem", right: "1rem" }}>
                  {s.n}
                </div>
                <h3 style={{ fontSize: "1.1rem", marginBottom: "0.6rem" }}>{s.title}</h3>
                <p style={{ fontSize: "0.9rem", color: "var(--text-secondary)", fontWeight: "300" }}>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" style={{ padding: "7rem 2rem" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto" }}>
          <div style={{ textAlign: "center", marginBottom: "4rem" }}>
            <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", marginBottom: "1rem" }}>
              PRICING
            </div>
            <h2 style={{ fontSize: "clamp(2rem, 4vw, 3rem)" }}>{t("pricing.title")}</h2>
            <p style={{ color: "var(--text-secondary)", marginTop: "0.8rem" }}>{t("pricing.subtitle")}</p>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "2rem" }}>
            {plans.map((p) => (
              <div
                key={p.name}
                className="premium-card"
                style={{
                  ...(p.popular
                    ? { border: "1px solid var(--border-gold)", boxShadow: "0 0 40px rgba(197,160,89,0.1)" }
                    : {}),
                  position: "relative",
                  display: "flex",
                  flexDirection: "column",
                }}
              >
                {p.popular && (
                  <div
                    style={{
                      position: "absolute",
                      top: "-0.8rem",
                      left: "50%",
                      transform: "translateX(-50%)",
                      background: "var(--accent-gold)",
                      color: "#000",
                      fontSize: "0.65rem",
                      fontWeight: "800",
                      padding: "0.3rem 1rem",
                      borderRadius: "20px",
                      letterSpacing: "1px",
                    }}
                  >
                    {t("pricing.popular")}
                  </div>
                )}
                <div style={{ fontSize: "0.85rem", fontWeight: "800", letterSpacing: "2px", marginBottom: "1rem" }}>
                  {p.name}
                </div>
                <div style={{ display: "flex", alignItems: "baseline", gap: "0.3rem", marginBottom: "1rem" }}>
                  <span style={{ fontSize: "2.8rem", fontWeight: "800" }} className="gold-gradient-text">
                    {p.price}
                  </span>
                  <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{t("pricing.month")}</span>
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1.5rem" }}>{p.jobs}</div>
                <ul style={{ display: "flex", flexDirection: "column", gap: "0.6rem", marginBottom: "2rem", flex: 1 }}>
                  {p.features.map((f) => (
                    <li key={f} style={{ fontSize: "0.85rem", color: "var(--text-secondary)", display: "flex", gap: "0.6rem", alignItems: "center" }}>
                      <span style={{ color: "var(--accent-gold)" }}>✓</span> {f}
                    </li>
                  ))}
                </ul>
                <Link href="/register">
                  <Btn variant={p.popular ? "primary" : "outline"} style={{ width: "100%" }}>
                    {p.cta}
                  </Btn>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section style={{ padding: "6rem 2rem", textAlign: "center", background: "var(--bg-secondary)", borderTop: "1px solid var(--border-subtle)" }}>
        <h2 style={{ fontSize: "clamp(1.8rem, 4vw, 2.8rem)", marginBottom: "1rem" }}>{t("cta.title")}</h2>
        <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>{t("cta.desc")}</p>
        <Link href="/register">
          <Btn>{t("cta.button")}</Btn>
        </Link>
      </section>

      <Footer />
    </main>
  );
}
