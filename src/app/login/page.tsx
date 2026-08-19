"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { getErrorMessage } from "@/lib/api";
import { Btn, inputStyle, labelStyle } from "@/components/ui";
import LangSwitch from "@/components/LangSwitch";

export default function LoginPage() {
  const { login } = useAuth();
  const { t } = useLang();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
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
        <h1 style={{ fontSize: "1.8rem", marginBottom: "0.5rem" }}>{t("auth.login.title")}</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "2rem" }}>{t("brand.tagline")}</p>

        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div>
            <label style={labelStyle}>{t("auth.email")}</label>
            <input style={inputStyle} type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </div>
          <div>
            <label style={labelStyle}>{t("auth.password")}</label>
            <input style={inputStyle} type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          </div>

          {error && (
            <div style={{ padding: "0.9rem 1rem", background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)", borderRadius: "4px", color: "#f87171", fontSize: "0.85rem" }}>
              {error}
            </div>
          )}

          <Btn type="submit" disabled={loading}>
            {loading ? t("common.loading") : t("auth.login.btn")}
          </Btn>
        </form>

        <p style={{ marginTop: "1.5rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          {t("auth.noAccount")}{" "}
          <Link href="/register" style={{ color: "var(--accent-gold)", fontWeight: "700" }}>
            {t("auth.register.title")}
          </Link>
        </p>
      </div>
    </div>
  );
}
