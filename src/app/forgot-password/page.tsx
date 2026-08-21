"use client";

import { useState } from "react";
import Link from "next/link";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import { Btn, inputStyle, labelStyle } from "@/components/ui";
import LangSwitch from "@/components/LangSwitch";

export default function ForgotPasswordPage() {
  const { t } = useLang();
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await API.forgotPassword(email);
      setSent(true);
    } catch (err) {
      setError(getErrorMessage(err, t("common.error")));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: "radial-gradient(ellipse at top, rgba(197,160,89,0.1) 0%, transparent 60%)" }}>
      <div style={{ position: "absolute", top: "2rem", right: "2rem" }}>
        <LangSwitch />
      </div>
      <div className="premium-card" style={{ width: "100%", maxWidth: "460px", padding: "3rem" }}>
        <Link href="/" style={{ fontSize: "1.4rem", fontWeight: "800", display: "block", marginBottom: "2rem" }}>
          <span className="gold-gradient-text">DROPIFY</span>
        </Link>
        <h1 style={{ fontSize: "1.8rem", marginBottom: "0.5rem" }}>{t("auth.forgotPassword.title")}</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "2rem" }}>{t("auth.forgotPassword.desc")}</p>

        {sent ? (
          <div style={{ padding: "1rem", background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.3)", borderRadius: "4px", color: "#4ade80", fontSize: "0.9rem" }}>
            {t("auth.forgotPassword.sent")}
          </div>
        ) : (
          <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            <div>
              <label style={labelStyle}>{t("auth.email")}</label>
              <input style={inputStyle} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            {error && (
              <div style={{ padding: "0.9rem 1rem", background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)", borderRadius: "4px", color: "#f87171", fontSize: "0.85rem" }}>
                {error}
              </div>
            )}
            <Btn type="submit" disabled={loading}>
              {loading ? t("common.loading") : t("auth.forgotPassword.submit")}
            </Btn>
          </form>
        )}

        <p style={{ marginTop: "1.5rem", fontSize: "0.85rem" }}>
          <Link href="/login" style={{ color: "var(--accent-gold)", fontWeight: "700" }}>
            {t("auth.backToLogin")}
          </Link>
        </p>
      </div>
    </div>
  );
}
