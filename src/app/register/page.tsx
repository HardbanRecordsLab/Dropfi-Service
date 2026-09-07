"use client";

import { useState } from "react";
import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { getErrorMessage } from "@/lib/api";
import { Btn, inputStyle, labelStyle } from "@/components/ui";
import LangSwitch from "@/components/LangSwitch";

export default function RegisterPage() {
  const { register } = useAuth();
  const { t } = useLang();
  const [form, setForm] = useState({
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    company: "",
    role: "client",
    referral_code: "",
    rodo_consent: false,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 8) {
      setError(t("auth.passwordHint"));
      return;
    }
    if (!form.rodo_consent) {
      setError(t("auth.rodo.required"));
      return;
    }
    setLoading(true);
    try {
      await register(form);
    } catch (err) {
      setError(getErrorMessage(err, t("common.error")));
    } finally {
      setLoading(false);
    }
  };

  const roleCards = [
    { key: "client", label: t("auth.role.client") },
    { key: "freelancer", label: t("auth.role.freelancer") },
  ];

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: "radial-gradient(ellipse at top, rgba(197,160,89,0.1) 0%, transparent 60%)" }}>
      <div style={{ position: "absolute", top: "2rem", right: "2rem" }}>
        <LangSwitch />
      </div>
      <div className="premium-card" style={{ width: "100%", maxWidth: "560px", padding: "3rem" }}>
        <Link href="/" style={{ fontSize: "1.4rem", fontWeight: "800", display: "block", marginBottom: "2rem" }}>
          <span className="gold-gradient-text">DROPIFY</span>
        </Link>
        <h1 style={{ fontSize: "1.8rem", marginBottom: "0.5rem" }}>{t("auth.register.title")}</h1>
        <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "2rem" }}>{t("brand.tagline")}</p>

        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div>
            <label style={labelStyle}>{t("auth.role")}</label>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.8rem" }}>
              {roleCards.map((r) => (
                <button
                  key={r.key}
                  type="button"
                  onClick={() => set("role", r.key)}
                  style={{
                    padding: "1rem",
                    borderRadius: "4px",
                    textAlign: "center",
                    fontSize: "0.8rem",
                    fontWeight: "700",
                    background: form.role === r.key ? "rgba(197,160,89,0.1)" : "transparent",
                    border: form.role === r.key ? "1px solid var(--accent-gold)" : "1px solid var(--border-subtle)",
                    color: form.role === r.key ? "var(--accent-gold)" : "var(--text-secondary)",
                  }}
                >
                  {r.label}
                </button>
              ))}
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
            <div>
              <label style={labelStyle}>{t("auth.firstName")}</label>
              <input style={inputStyle} value={form.first_name} onChange={(e) => set("first_name", e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>{t("auth.lastName")}</label>
              <input style={inputStyle} value={form.last_name} onChange={(e) => set("last_name", e.target.value)} />
            </div>
          </div>

          <div>
            <label style={labelStyle}>{t("auth.company")}</label>
            <input style={inputStyle} value={form.company} onChange={(e) => set("company", e.target.value)} />
          </div>

          <div>
            <label style={labelStyle}>{t("auth.email")}</label>
            <input style={inputStyle} type="email" value={form.email} onChange={(e) => set("email", e.target.value)} required />
          </div>

          <div>
            <label style={labelStyle}>{t("auth.password")}</label>
            <input style={inputStyle} type="password" value={form.password} onChange={(e) => set("password", e.target.value)} required />
            <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>{t("auth.passwordHint")}</div>
          </div>

          <div>
            <label style={labelStyle}>{t("auth.referral")}</label>
            <input style={inputStyle} value={form.referral_code} onChange={(e) => set("referral_code", e.target.value)} />
          </div>

          <label style={{ display: "flex", alignItems: "flex-start", gap: "0.8rem", cursor: "pointer", fontSize: "0.82rem", color: "var(--text-secondary)", lineHeight: "1.5" }}>
            <input
              type="checkbox"
              checked={form.rodo_consent}
              onChange={(e) => set("rodo_consent", String(e.target.checked))}
              style={{ marginTop: "0.2rem", accentColor: "var(--accent-gold)", width: "16px", height: "16px", flexShrink: 0 }}
            />
            <span>
              {t("auth.rodo.consent")}{" "}
              <Link href="/privacy" style={{ color: "var(--accent-gold)", textDecoration: "underline" }}>
                {t("auth.rodo.privacyLink")}
              </Link>{" "}
              {t("auth.rodo.and")}{" "}
              <Link href="/terms" style={{ color: "var(--accent-gold)", textDecoration: "underline" }}>
                {t("auth.rodo.termsLink")}
              </Link>.
            </span>
          </label>

          {error && (
            <div style={{ padding: "0.9rem 1rem", background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)", borderRadius: "4px", color: "#f87171", fontSize: "0.85rem" }}>
              {error}
            </div>
          )}

          <Btn type="submit" disabled={loading}>
            {loading ? t("common.loading") : t("auth.register.btn")}
          </Btn>
        </form>

        <p style={{ marginTop: "1.5rem", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          {t("auth.hasAccount")}{" "}
          <Link href="/login" style={{ color: "var(--accent-gold)", fontWeight: "700" }}>
            {t("auth.login.title")}
          </Link>
        </p>
      </div>
    </div>
  );
}
