"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import { Btn, inputStyle, labelStyle } from "@/components/ui";
import LangSwitch from "@/components/LangSwitch";

function ResetPasswordForm() {
  const { t } = useLang();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [password, setPassword] = useState("");
  const [done, setDone] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await API.resetPassword(token, password);
      setDone(true);
    } catch (err) {
      setError(getErrorMessage(err, t("auth.resetPassword.invalid")));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="premium-card" style={{ width: "100%", maxWidth: "460px", padding: "3rem" }}>
      <Link href="/" style={{ fontSize: "1.4rem", fontWeight: "800", display: "block", marginBottom: "2rem" }}>
        <span className="gold-gradient-text">DROPIFY</span>
      </Link>
      <h1 style={{ fontSize: "1.8rem", marginBottom: "2rem" }}>{t("auth.resetPassword.title")}</h1>

      {!token ? (
        <div style={{ padding: "1rem", background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)", borderRadius: "4px", color: "#f87171", fontSize: "0.9rem" }}>
          {t("auth.resetPassword.invalid")}
        </div>
      ) : done ? (
        <div style={{ padding: "1rem", background: "rgba(74,222,128,0.08)", border: "1px solid rgba(74,222,128,0.3)", borderRadius: "4px", color: "#4ade80", fontSize: "0.9rem" }}>
          {t("auth.resetPassword.success")}
        </div>
      ) : (
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div>
            <label style={labelStyle}>{t("auth.resetPassword.new")}</label>
            <input style={inputStyle} type="password" value={password} onChange={(e) => setPassword(e.target.value)} minLength={8} required />
            <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>{t("auth.passwordHint")}</p>
          </div>
          {error && (
            <div style={{ padding: "0.9rem 1rem", background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)", borderRadius: "4px", color: "#f87171", fontSize: "0.85rem" }}>
              {error}
            </div>
          )}
          <Btn type="submit" disabled={loading}>
            {loading ? t("common.loading") : t("auth.resetPassword.submit")}
          </Btn>
        </form>
      )}

      <p style={{ marginTop: "1.5rem", fontSize: "0.85rem" }}>
        <Link href="/login" style={{ color: "var(--accent-gold)", fontWeight: "700" }}>
          {t("auth.backToLogin")}
        </Link>
      </p>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem", background: "radial-gradient(ellipse at top, rgba(197,160,89,0.1) 0%, transparent 60%)" }}>
      <div style={{ position: "absolute", top: "2rem", right: "2rem" }}>
        <LangSwitch />
      </div>
      <Suspense fallback={null}>
        <ResetPasswordForm />
      </Suspense>
    </div>
  );
}
