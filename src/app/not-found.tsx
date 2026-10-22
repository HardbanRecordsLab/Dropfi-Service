"use client";

import Link from "next/link";
import PortalNav from "@/components/PortalNav";
import Footer from "@/components/Footer";
import { Btn } from "@/components/ui";
import { useLang } from "@/lib/i18n";

export default function NotFound() {
  const { t } = useLang();
  return (
    <main style={{ minHeight: "100vh" }}>
      <PortalNav />

      <section
        style={{
          padding: "8rem 2rem",
          textAlign: "center",
          background: "radial-gradient(ellipse at top, rgba(197,160,89,0.08) 0%, transparent 60%)",
        }}
      >
        <div style={{ maxWidth: "600px", margin: "0 auto" }}>
          <div
            style={{
              fontSize: "6rem",
              fontWeight: "900",
              lineHeight: "1",
              marginBottom: "1rem",
            }}
            className="gold-gradient-text"
          >
            404
          </div>
          <h1 style={{ fontSize: "1.8rem", marginBottom: "1rem" }}>
            {t("nf.title")}
          </h1>
          <p style={{ color: "var(--text-secondary)", fontSize: "1rem", marginBottom: "2.5rem" }}>
            {t("nf.desc")}
          </p>
          <Link href="/">
            <Btn>{t("nf.back")}</Btn>
          </Link>
        </div>
      </section>

      <Footer />
    </main>
  );
}
