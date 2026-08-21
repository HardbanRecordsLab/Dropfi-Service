"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useLang } from "@/lib/i18n";
import { API } from "@/lib/api";
import { Loading } from "@/components/ui";
import LangSwitch from "@/components/LangSwitch";

function VerifyEmailInner() {
  const { t } = useLang();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [status, setStatus] = useState<"loading" | "success" | "error">(token ? "loading" : "error");

  useEffect(() => {
    if (!token) return;
    let active = true;
    API.verifyEmail(token)
      .then(() => active && setStatus("success"))
      .catch(() => active && setStatus("error"));
    return () => {
      active = false;
    };
  }, [token]);

  return (
    <div className="premium-card" style={{ width: "100%", maxWidth: "460px", padding: "3rem", textAlign: "center" }}>
      <Link href="/" style={{ fontSize: "1.4rem", fontWeight: "800", display: "block", marginBottom: "2rem" }}>
        <span className="gold-gradient-text">DROPIFY</span>
      </Link>
      <h1 style={{ fontSize: "1.8rem", marginBottom: "1.5rem" }}>{t("auth.verifyEmail.title")}</h1>

      {status === "loading" && <p style={{ color: "var(--text-secondary)" }}>{t("auth.verifyEmail.verifying")}</p>}
      {status === "success" && (
        <div style={{ padding: "1rem", background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.3)", borderRadius: "4px", color: "#4ade80", fontSize: "0.9rem" }}>
          ✓ {t("auth.verifyEmail.success")}
        </div>
      )}
      {status === "error" && (
        <div style={{ padding: "1rem", background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)", borderRadius: "4px", color: "#f87171", fontSize: "0.9rem" }}>
          {t("auth.verifyEmail.invalid")}
        </div>
      )}

      <p style={{ marginTop: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/dashboard" style={{ color: "var(--accent-gold)", fontWeight: "700" }}>
          {t("nav.dashboard")}
        </Link>
      </p>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: "radial-gradient(ellipse at top, rgba(197,160,89,0.1) 0%, transparent 60%)" }}>
      <div style={{ position: "absolute", top: "2rem", right: "2rem" }}>
        <LangSwitch />
      </div>
      <Suspense fallback={<Loading />}>
        <VerifyEmailInner />
      </Suspense>
    </div>
  );
}
