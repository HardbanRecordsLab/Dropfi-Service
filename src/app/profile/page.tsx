"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Btn, Loading, inputStyle, labelStyle, Badge } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API } from "@/lib/api";

interface ProfileForm {
  first_name: string;
  last_name: string;
  company: string;
  bio: string;
  location: string;
  country: string;
  languages: string[];
  skills: string[];
  hourly_rate: number | string | null;
  availability: string;
  auto_accept_enabled: boolean;
  auto_accept_min_budget: number | string | null;
  auto_accept_min_score: number | string | null;
  payout_method: string;
  payout_address: string;
}

const EMPTY_FORM: ProfileForm = {
  first_name: "",
  last_name: "",
  company: "",
  bio: "",
  location: "",
  country: "",
  languages: [],
  skills: [],
  hourly_rate: "",
  availability: "available",
  auto_accept_enabled: false,
  auto_accept_min_budget: "",
  auto_accept_min_score: "",
  payout_method: "bank",
  payout_address: "",
};

interface ReferralData {
  total_earned: number;
  pending: number;
  referred_count: number;
  rate_l1: number;
  rate_l2: number;
  window_months: number;
  commissions: {
    id: string;
    level: number;
    rate: number;
    amount: number;
    status: string;
    contract_id: string;
    referred_name: string;
    created_at: string;
  }[];
}

export default function ProfilePage() {
  const { user, refresh } = useAuth();
  const { t } = useLang();
  const [form, setForm] = useState<ProfileForm>(EMPTY_FORM);
  const [refData, setRefData] = useState<ReferralData | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [verifyMsg, setVerifyMsg] = useState("");

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      if (active)
        setForm({
          first_name: user.first_name,
          last_name: user.last_name,
          company: user.company,
          bio: user.bio,
          location: user.location,
          country: user.country,
          languages: user.languages,
          skills: user.skills,
          hourly_rate: user.hourly_rate || "",
          availability: user.availability,
          auto_accept_enabled: user.auto_accept_enabled,
          auto_accept_min_budget: user.auto_accept_min_budget || "",
          auto_accept_min_score: user.auto_accept_min_score || "",
          payout_method: user.payout_method,
          payout_address: user.payout_address || "",
        });
    })();
    return () => {
      active = false;
    };
  }, [user]);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      const data = (await API.referrals().catch(() => null)) as ReferralData | null;
      if (active) setRefData(data);
    })();
    return () => {
      active = false;
    };
  }, [user]);

  if (!user) return <DashShell><Loading /></DashShell>;

  const set = <K extends keyof ProfileForm>(k: K, v: ProfileForm[K]) => {
    setForm((f) => ({ ...f, [k]: v }));
    setSaved(false);
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const payload: ProfileForm = { ...form };
      payload.hourly_rate = payload.hourly_rate ? parseFloat(String(payload.hourly_rate)) : null;
      payload.auto_accept_min_budget = payload.auto_accept_min_budget
        ? parseFloat(String(payload.auto_accept_min_budget))
        : null;
      payload.auto_accept_min_score = payload.auto_accept_min_score
        ? parseFloat(String(payload.auto_accept_min_score))
        : null;
      payload.languages = (payload.languages || []).map((s: string) => s.trim()).filter(Boolean);
      payload.skills = (payload.skills || []).map((s: string) => s.trim()).filter(Boolean);
      await API.updateProfile(payload as unknown as Record<string, unknown>);
      setSaved(true);
      refresh();
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashShell>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          {t("profile.title")}
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("profile.title")}</h1>
      </header>

      {!user.email_verified && (
        <div
          style={{
            marginBottom: "2rem", padding: "1rem 1.5rem", background: "rgba(248,113,113,0.08)",
            border: "1px solid rgba(248,113,113,0.25)", borderRadius: "4px",
            display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "1rem",
          }}
        >
          <span style={{ fontSize: "0.85rem", color: "#f87171" }}>
            ⚠️ {verifyMsg || t("auth.verifyEmail.notVerified")}
          </span>
          <Btn
            variant="outline"
            onClick={async () => {
              try {
                await API.sendVerification();
                setVerifyMsg(t("auth.verifyEmail.resent"));
              } catch {
                // best-effort, ignore
              }
            }}
          >
            {t("auth.verifyEmail.resend")}
          </Btn>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: "3rem", alignItems: "start" }}>
        <form onSubmit={save} className="premium-card" style={{ padding: "3rem", display: "flex", flexDirection: "column", gap: "1.8rem" }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            <div>
              <label style={labelStyle}>{t("auth.firstName")}</label>
              <input style={inputStyle} value={form.first_name || ""} onChange={(e) => set("first_name", e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>{t("auth.lastName")}</label>
              <input style={inputStyle} value={form.last_name || ""} onChange={(e) => set("last_name", e.target.value)} />
            </div>
          </div>

          <div>
            <label style={labelStyle}>{t("auth.company")}</label>
            <input style={inputStyle} value={form.company || ""} onChange={(e) => set("company", e.target.value)} />
          </div>

          <div>
            <label style={labelStyle}>{t("profile.bio")}</label>
            <textarea
              style={{ ...inputStyle, resize: "vertical", minHeight: "120px" }}
              value={form.bio || ""}
              onChange={(e) => set("bio", e.target.value)}
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
            <div>
              <label style={labelStyle}>{t("jobs.location")}</label>
              <input style={inputStyle} value={form.location || ""} onChange={(e) => set("location", e.target.value)} />
            </div>
            <div>
              <label style={labelStyle}>Country</label>
              <input style={inputStyle} value={form.country || ""} onChange={(e) => set("country", e.target.value)} />
            </div>
          </div>

          {user.role === "freelancer" && (
            <>
              <div>
                <label style={labelStyle}>{t("profile.languages")}</label>
                <input style={inputStyle} value={(form.languages || []).join(", ")} onChange={(e) => set("languages", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))} placeholder="Polish, English" />
              </div>
              <div>
                <label style={labelStyle}>{t("profile.skills")}</label>
                <input style={inputStyle} value={(form.skills || []).join(", ")} onChange={(e) => set("skills", e.target.value.split(",").map((s) => s.trim()).filter(Boolean))} placeholder={t("jobs.skillsHint")} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem" }}>
                <div>
                  <label style={labelStyle}>{t("profile.hourlyRate")}</label>
                  <input style={inputStyle} type="number" min={0} value={form.hourly_rate || ""} onChange={(e) => set("hourly_rate", e.target.value)} />
                </div>
                <div>
                  <label style={labelStyle}>{t("profile.availability")}</label>
                  <select style={inputStyle} value={form.availability || "available"} onChange={(e) => set("availability", e.target.value)}>
                    <option value="available">{t("profile.available")}</option>
                    <option value="busy">{t("profile.busy")}</option>
                  </select>
                </div>
              </div>

              {/* #13: AI Proposal Autopilot */}
              <div style={{ marginTop: "1rem", padding: "1.2rem", background: "rgba(197,160,89,0.05)", border: "1px dashed var(--border-gold)", borderRadius: "4px" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem", marginBottom: "0.6rem" }}>
                  <div>
                    <h4 style={{ fontSize: "0.95rem", fontWeight: "800" }}>🤖 {t("auto.title")}</h4>
                    <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{t("auto.desc")}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => set("auto_accept_enabled", !form.auto_accept_enabled)}
                    style={{
                      minWidth: "64px",
                      padding: "0.5rem 0.9rem",
                      borderRadius: "20px",
                      fontWeight: "800",
                      fontSize: "0.72rem",
                      background: form.auto_accept_enabled ? "rgba(74,222,128,0.15)" : "rgba(255,255,255,0.05)",
                      border: form.auto_accept_enabled ? "1px solid #4ade80" : "1px solid var(--border-subtle)",
                      color: form.auto_accept_enabled ? "#4ade80" : "var(--text-muted)",
                    }}
                  >
                    {form.auto_accept_enabled ? "ON" : "OFF"}
                  </button>
                </div>
                {form.auto_accept_enabled && (
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginTop: "0.8rem" }}>
                    <div>
                      <label style={labelStyle}>{t("auto.minScore")}</label>
                      <input style={inputStyle} type="number" min={0} max={1} step={0.05} value={form.auto_accept_min_score || ""} onChange={(e) => set("auto_accept_min_score", e.target.value)} />
                    </div>
                    <div>
                      <label style={labelStyle}>{t("auto.minBudget")}</label>
                      <input style={inputStyle} type="number" min={0} value={form.auto_accept_min_budget || ""} onChange={(e) => set("auto_accept_min_budget", e.target.value)} />
                    </div>
                  </div>
                )}
              </div>

              {/* #6: Stablecoin payouts */}
              <div style={{ marginTop: "1rem", padding: "1.2rem", background: "rgba(96,165,250,0.04)", border: "1px dashed rgba(96,165,250,0.25)", borderRadius: "4px" }}>
                <h4 style={{ fontSize: "0.95rem", fontWeight: "800", marginBottom: "0.2rem" }}>💸 {t("payout.title")}</h4>
                <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.8rem" }}>{t("payout.note")}</p>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  <div>
                    <label style={labelStyle}>{t("payout.method")}</label>
                    <select style={inputStyle} value={form.payout_method || "bank"} onChange={(e) => set("payout_method", e.target.value)}>
                      <option value="bank">{t("payout.bank")}</option>
                      <option value="stablecoin">{t("payout.stablecoin")}</option>
                    </select>
                  </div>
                  {form.payout_method === "stablecoin" && (
                    <div>
                      <label style={labelStyle}>{t("payout.address")}</label>
                      <input style={inputStyle} value={form.payout_address || ""} onChange={(e) => set("payout_address", e.target.value)} placeholder="0x… / T… / 0xUSDT…" />
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <Btn type="submit" disabled={saving}>
              {saving ? t("common.loading") : t("profile.save")}
            </Btn>
            {saved && <span style={{ color: "#4ade80", fontSize: "0.85rem", fontWeight: "700" }}>✓ {t("profile.saved")}</span>}
          </div>
        </form>

        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          <div className="premium-card">
            <h3 style={{ fontSize: "1.1rem", marginBottom: "1rem" }}>{t("profile.rating")}</h3>
            <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
              <div style={{ fontSize: "3rem", fontWeight: "800" }} className="gold-gradient-text">
                {user.rating?.toFixed(1)}
              </div>
              <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                ⭐⭐⭐⭐⭐<br />{user.rating_count} reviews
              </div>
            </div>
          </div>

          <div className="premium-card" style={{ background: "rgba(197,160,89,0.05)", border: "1px dashed var(--border-gold)" }}>
            <h3 style={{ fontSize: "1.1rem", marginBottom: "0.5rem" }}>{t("profile.referral")}</h3>
            <div style={{ fontSize: "1.4rem", fontWeight: "800", letterSpacing: "1px" }} className="gold-gradient-text">
              {user.referral_code || "—"}
            </div>
            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
              Share this code — friends get free PRO trial.
            </p>
          </div>

          {/* Feature #15: Earn Forever referral program */}
          <div className="premium-card">
            <h3 style={{ fontSize: "1.1rem", marginBottom: "0.8rem" }}>{t("profile.referralTitle")}</h3>
            <p style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "1.2rem" }}>
              {t("profile.referralRate")}
            </p>
            {refData === null ? (
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{t("common.loading")}</p>
            ) : (
              <>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem", marginBottom: "1.2rem" }}>
                  <div style={{ background: "rgba(74,222,128,0.06)", border: "1px solid rgba(74,222,128,0.2)", borderRadius: "4px", padding: "1rem" }}>
                    <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("profile.referralEarned")}</div>
                    <div style={{ fontSize: "1.4rem", fontWeight: "800", color: "#4ade80" }}>
                      {refData.total_earned.toLocaleString()} {t("common.currency")}
                    </div>
                  </div>
                  <div style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--border-subtle)", borderRadius: "4px", padding: "1rem" }}>
                    <div style={{ fontSize: "0.68rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("profile.referralReferred")}</div>
                    <div style={{ fontSize: "1.4rem", fontWeight: "800" }}>{refData.referred_count}</div>
                  </div>
                </div>
                {refData.commissions.length > 0 ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", maxHeight: "200px", overflowY: "auto" }}>
                    {refData.commissions.slice(0, 6).map((c) => (
                      <div key={c.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: "0.8rem", padding: "0.5rem 0.8rem", background: "rgba(255,255,255,0.03)", borderRadius: "4px" }}>
                        <span style={{ color: "var(--text-secondary)" }}>
                          L{c.level} · {c.referred_name || c.contract_id.slice(0, 8)}
                        </span>
                        <span style={{ fontWeight: "800", color: "#4ade80" }}>
                          +{c.amount.toLocaleString()} {t("common.currency")}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>{t("profile.referralNone")}</p>
                )}
              </>
            )}
          </div>

          <div className="premium-card">
            <h3 style={{ fontSize: "1.1rem", marginBottom: "0.8rem" }}>{t("profile.plan")}</h3>
            <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem" }}>
              <Badge color="var(--accent-gold)">{user.plan?.toUpperCase()}</Badge>
              <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{user.email}</span>
            </div>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              {["free", "starter", "pro"].map((p) => (
                <button
                  key={p}
                  onClick={async () => {
                    try {
                      await API.subscribe(p);
                      refresh();
                    } catch {}
                  }}
                  style={{
                    padding: "0.5rem 1rem",
                    borderRadius: "4px",
                    fontSize: "0.7rem",
                    fontWeight: "700",
                    textTransform: "uppercase",
                    background: user.plan === p ? "var(--accent-gold)" : "transparent",
                    color: user.plan === p ? "#000" : "var(--text-secondary)",
                    border: "1px solid var(--border-subtle)",
                  }}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </DashShell>
  );
}
