"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { CheckoutResult, Contract, Milestone } from "@/lib/types";

export default function ContractsPage() {
  const { user } = useAuth();
  const { t, lang } = useLang();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      const data = (await API.myContracts().catch(() => [])) as Contract[];
      if (active) setContracts(data);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, [user]);

  const reload = async () => {
    setContracts((await API.myContracts()) as Contract[]);
  };

  const act = async (fn: () => Promise<unknown>, okMsg: string) => {
    try {
      await fn();
      setMsg(okMsg);
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    }
  };

  const pay = async (contractId: string, milestoneId: string) => {
    try {
      const res = (await API.checkoutMilestone(contractId, milestoneId)) as CheckoutResult;
      if (res.mode === "stripe" && res.checkout_url) {
        setMsg(t("pay.redirecting"));
        window.location.href = res.checkout_url;
      } else {
        setMsg(res.message || t("pay.demoNote"));
      }
    } catch (err) {
      setMsg(getErrorMessage(err));
    }
  };

  const downloadAgreement = async (contractId: string) => {
    try {
      const res = (await API.contractAgreement(contractId, lang)) as { agreement: string };
      const blob = new Blob([res.agreement], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `dropify-agreement-${contractId.slice(0, 8)}.txt`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setMsg(getErrorMessage(err));
    }
  };

  const msStatus: Record<string, { label: string; color: string }> = {
    pending: { label: t("ms.pending"), color: "var(--text-muted)" },
    in_review: { label: t("ms.in_review"), color: "var(--accent-gold)" },
    released: { label: t("ms.released"), color: "#4ade80" },
    rejected: { label: "✕", color: "#f87171" },
  };

  if (loading) return <DashShell><Loading /></DashShell>;

  return (
    <DashShell>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          ESCROW · MILESTONES
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("nav.contracts")}</h1>
        <p style={{ color: "var(--text-secondary)", fontWeight: "300", marginTop: "0.5rem" }}>{t("ms.desc")}</p>
      </header>

      {contracts.length === 0 ? (
        <div className="premium-card" style={{ textAlign: "center", padding: "4rem" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>📄</div>
          <p style={{ color: "var(--text-secondary)" }}>{t("contracts.none")}</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
          {contracts.map((c) => {
            const ms = c.milestones || [];
            const pct = c.amount > 0 ? Math.min(100, Math.round((c.released_amount / c.amount) * 100)) : 0;
            const allReleased = ms.length > 0 && ms.every((m) => m.status === "released");
            return (
              <div key={c.id} className="premium-card" style={{ padding: "2rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "2rem", flexWrap: "wrap" }}>
                  <div style={{ flex: 1, minWidth: "240px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.8rem", marginBottom: "0.5rem", flexWrap: "wrap" }}>
                      <span style={{ fontWeight: "800", fontSize: "1.05rem" }}>{c.job?.title || c.job_id}</span>
                      <Badge color={c.status === "completed" ? "#4ade80" : c.status === "cancelled" ? "#f87171" : "var(--accent-gold)"}>
                        {t(`contracts.status.${c.status}`)}
                      </Badge>
                      {c.fee_rate !== 0.08 && (
                        <span style={{ fontSize: "0.68rem", color: "var(--accent-gold)", fontWeight: "700" }}>
                          ⚡ {t("contracts.feeTier")} ({(c.fee_rate * 100).toFixed(0)}%)
                        </span>
                      )}
                    </div>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                      {user?.role === "client"
                        ? `${c.freelancer?.first_name} ${c.freelancer?.last_name}`
                        : `ID: ${c.client_id.slice(0, 8)}`} · {c.job_id.slice(0, 8)}
                    </div>

                    {/* Progress */}
                    <div style={{ marginTop: "1.2rem" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: "0.4rem" }}>
                        <span>{t("ms.progress")}: {pct}%</span>
                        <span className="gold-gradient-text" style={{ fontWeight: "800" }}>
                          {c.released_amount.toLocaleString()} / {c.amount.toLocaleString()} {t("common.currency")}
                        </span>
                      </div>
                      <div style={{ height: "8px", background: "var(--bg-tertiary)", borderRadius: "4px", overflow: "hidden" }}>
                        <div
                          style={{
                            height: "100%",
                            width: `${pct}%`,
                            background: "linear-gradient(90deg, var(--accent-gold), #e8c97f)",
                            borderRadius: "4px",
                            transition: "width 0.4s",
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: "1.4rem", fontWeight: "800" }} className="gold-gradient-text">
                      {c.amount.toLocaleString()} {t("common.currency")}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {t("contracts.fee")}: {c.platform_fee.toLocaleString()} {t("common.currency")}
                    </div>
                    <button
                      onClick={() => downloadAgreement(c.id)}
                      style={{ marginTop: "0.6rem", fontSize: "0.72rem", color: "var(--accent-gold)", fontWeight: "700" }}
                    >
                      📄 {t("agreement.download")}
                    </button>
                  </div>
                </div>

                {/* Milestones */}
                {ms.length > 0 && (
                  <div style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "0.8rem" }}>
                    {ms.map((m: Milestone) => {
                      const st = msStatus[m.status] || msStatus.pending;
                      return (
                        <div
                          key={m.id}
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "center",
                            gap: "1rem",
                            flexWrap: "wrap",
                            padding: "0.9rem 1.2rem",
                            background: "rgba(255,255,255,0.02)",
                            border: "1px solid var(--border-subtle)",
                            borderRadius: "4px",
                          }}
                        >
                          <div style={{ display: "flex", alignItems: "center", gap: "1rem", flex: 1, minWidth: "200px" }}>
                            <span
                              style={{
                                width: "26px",
                                height: "26px",
                                borderRadius: "50%",
                                background: m.status === "released" ? "rgba(74,222,128,0.15)" : "var(--bg-tertiary)",
                                color: m.status === "released" ? "#4ade80" : "var(--text-muted)",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontSize: "0.75rem",
                                fontWeight: "800",
                                border: m.status === "released" ? "1px solid #4ade80" : "1px solid var(--border-subtle)",
                              }}
                            >
                              {m.status === "released" ? "✓" : m.order_index + 1}
                            </span>
                            <div>
                              <div style={{ fontWeight: "700", fontSize: "0.9rem" }}>{m.title}</div>
                              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                                {m.amount.toLocaleString()} {t("common.currency")}
                                {m.status === "in_review" && ` · ${t("ms.autoHint")}`}
                              </div>
                            </div>
                          </div>
                          <div style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
                            <Badge color={st.color}>{st.label}</Badge>
                            {user?.role === "freelancer" && m.status === "pending" && (
                              <Btn variant="outline" onClick={() => act(() => API.submitMilestone(c.id, m.id), "Milestone submitted")}>
                                {t("ms.submit")}
                              </Btn>
                            )}
                            {user?.role === "client" && m.status === "in_review" && (
                              <>
                                <Btn onClick={() => pay(c.id, m.id)}>
                                  💳 {t("pay.stripe")}
                                </Btn>
                                <Btn variant="outline" onClick={() => act(() => API.releaseMilestone(c.id, m.id), "Payment released")}>
                                  {t("ms.release")}
                                </Btn>
                              </>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}

                {allReleased && c.status === "completed" && (
                  <div style={{ marginTop: "1.2rem", fontSize: "0.85rem", color: "#4ade80", fontWeight: "700" }}>
                    🎉 {t("ms.completed")}
                  </div>
                )}

                {/* #7: Refund guarantee (client) */}
                {user?.role === "client" && c.status === "in_progress" && (
                  <div
                    style={{
                      marginTop: "1.5rem",
                      padding: "1.2rem",
                      background: "rgba(96,165,250,0.05)",
                      border: "1px dashed rgba(96,165,250,0.3)",
                      borderRadius: "4px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      gap: "1rem",
                      flexWrap: "wrap",
                    }}
                  >
                    <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", flex: 1, minWidth: "220px" }}>
                      🛡️ <b>{t("refund.title")}</b>
                      <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
                        {c.refund_eligible ? (
                          <span style={{ color: "#4ade80", fontWeight: "700" }}>✓ {t("refund.eligible")} — {t("refund.desc")}</span>
                        ) : (
                          t("refund.desc")
                        )}
                        {c.refund_reason && <div style={{ marginTop: "0.3rem" }}>{t("refund.reason")}: {c.refund_reason}</div>}
                      </div>
                    </div>
                    {c.refund_eligible && (
                      <Btn
                        variant="outline"
                        onClick={() => act(() => API.requestRefund(c.id), "Refund issued")}
                      >
                        {t("refund.request")}
                      </Btn>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {msg && (
        <div style={{ position: "fixed", bottom: "2rem", left: "50%", transform: "translateX(-50%)", background: "var(--accent-gold)", color: "#000", fontWeight: "700", padding: "1rem 2rem", borderRadius: "6px", zIndex: 999 }}>
          {msg}
        </div>
      )}
    </DashShell>
  );
}
