"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { Match } from "@/lib/types";

export default function MatchesPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");
  const [answers, setAnswers] = useState<Record<string, string[]>>({});
  const [prices, setPrices] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      const data = (await API.myMatches().catch(() => [])) as Match[];
      if (active) setMatches(data);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, [user]);

  const reload = async () => {
    setMatches((await API.myMatches()) as Match[]);
  };

  const act = async (matchId: string, action: "accept" | "reject") => {
    try {
      if (action === "accept") await API.acceptMatch(matchId);
      else await API.rejectMatch(matchId);
      setMsg(action === "accept" ? "Contract created!" : "Match declined");
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    }
  };

  const submitInterview = async (match: Match) => {
    const a = answers[match.id] || [];
    if (a.some((x) => !x.trim())) {
      setMsg("Answer all questions");
      return;
    }
    try {
      await API.submitInterview(match.id, a);
      setMsg("Interview submitted — AI scored your answers!");
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    }
  };

  const submitPrice = async (match: Match) => {
    const amount = parseFloat(prices[match.id] || "");
    if (!amount || amount <= 0) {
      setMsg("Enter a valid price");
      return;
    }
    try {
      await API.proposePrice(match.id, amount);
      setMsg("Price proposal sent to the client");
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    }
  };

  if (loading) return <DashShell><Loading /></DashShell>;

  return (
    <DashShell>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          AI MATCHING
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("nav.matches")}</h1>
      </header>

      {matches.length === 0 ? (
        <div className="premium-card" style={{ textAlign: "center", padding: "4rem" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>🤝</div>
          <p style={{ color: "var(--text-secondary)" }}>{t("dash.emptyMatches")}</p>
          <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "0.5rem" }}>
            {t("dash.recommended")}:{" "}
            <Link href="/dashboard/jobs" style={{ color: "var(--accent-gold)" }}>
              {t("jobs.browse")}
            </Link>
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
          {matches.map((m) => (
            <div key={m.id} className="premium-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "2rem", flexWrap: "wrap" }}>
                <div style={{ flex: 1, minWidth: "260px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.8rem", marginBottom: "0.5rem", flexWrap: "wrap" }}>
                    <Link href={`/dashboard/jobs/${m.job_id}`} style={{ fontWeight: "800", fontSize: "1.1rem", color: "var(--text-primary)" }}>
                      {m.job?.title}
                    </Link>
                    <Badge color={m.status === "accepted" ? "#4ade80" : m.status === "rejected" ? "#f87171" : "var(--accent-gold)"}>
                      {t(`match.${m.status}`)}
                    </Badge>
                  </div>
                  <div style={{ display: "flex", gap: "1.5rem", fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "0.8rem", flexWrap: "wrap" }}>
                    <span>{t("match.budget")}: <b>{m.job?.budget?.toLocaleString()} {t("common.currency")}</b></span>
                    <span>{t("match.deadline")}: <b>{m.job?.deadline}</b></span>
                    <span>{t("match.location")}: <b>{m.job?.location || t("common.remote")}</b></span>
                  </div>
                  <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", fontWeight: "300", lineHeight: "1.6" }}>
                    {m.job?.description}
                  </p>
                </div>

                <div style={{ textAlign: "center", minWidth: "160px" }}>
                  <div style={{ fontSize: "2rem", fontWeight: "800" }} className="gold-gradient-text">
                    {Math.round(m.score * 100)}%
                  </div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>
                    {t("match.score")}
                  </div>
                </div>
              </div>

              {m.status === "pending" && (
                <div style={{ marginTop: "1.2rem", paddingTop: "1.2rem", borderTop: "1px solid var(--border-subtle)", display: "flex", flexDirection: "column", gap: "1rem" }}>
                  {/* #1: interview */}
                  {m.job?.interview_questions && m.job.interview_questions.length > 0 && m.interview_score == null && (
                    <div>
                      <div style={{ fontSize: "0.75rem", fontWeight: "800", textTransform: "uppercase", letterSpacing: "1px", color: "var(--accent-gold)", marginBottom: "0.6rem" }}>
                        🎙️ {t("interview.title")}
                      </div>
                      <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem", marginBottom: "0.8rem" }}>
                        {m.job.interview_questions.map((q, i) => (
                          <div key={i}>
                            <div style={{ fontSize: "0.8rem", fontWeight: "700", marginBottom: "0.3rem" }}>{i + 1}. {q}</div>
                            <textarea
                              style={{
                                width: "100%",
                                background: "var(--bg-tertiary)",
                                border: "1px solid var(--border-subtle)",
                                padding: "0.7rem 0.9rem",
                                color: "#fff",
                                borderRadius: "4px",
                                fontSize: "0.85rem",
                                fontFamily: "inherit",
                                minHeight: "55px",
                                resize: "vertical",
                              }}
                              value={(answers[m.id] || [])[i] || ""}
                              onChange={(e) => {
                                const next = [...(answers[m.id] || [])];
                                next[i] = e.target.value;
                                setAnswers((a) => ({ ...a, [m.id]: next }));
                              }}
                            />
                          </div>
                        ))}
                      </div>
                      <Btn variant="outline" onClick={() => submitInterview(m)}>{t("interview.submit")}</Btn>
                    </div>
                  )}
                  {m.interview_score != null && (
                    <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                      🎙️ {t("interview.title")}: <b className="gold-gradient-text">{m.interview_score}/100</b>
                    </div>
                  )}

                  {/* #3: price negotiation */}
                  {m.price_status === "none" ? (
                    <div style={{ display: "flex", gap: "0.8rem", alignItems: "center", flexWrap: "wrap" }}>
                      <input
                        type="number"
                        placeholder={`${t("nego.amount")} (${m.job?.budget} ${t("common.currency")})`}
                        value={prices[m.id] || ""}
                        onChange={(e) => setPrices((p) => ({ ...p, [m.id]: e.target.value }))}
                        style={{
                          flex: 1,
                          minWidth: "180px",
                          background: "var(--bg-tertiary)",
                          border: "1px solid var(--border-subtle)",
                          padding: "0.7rem 0.9rem",
                          color: "#fff",
                          borderRadius: "4px",
                          fontSize: "0.85rem",
                          fontFamily: "inherit",
                        }}
                      />
                      <Btn variant="outline" onClick={() => submitPrice(m)}>{t("nego.propose")}</Btn>
                    </div>
                  ) : (
                    <div style={{ fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                      💬 {t(`nego.${m.price_status === "declined" ? "declined" : "proposed"}`)}
                      {m.price_proposal ? `: ${m.price_proposal.toLocaleString()} ${t("common.currency")}` : ""}
                    </div>
                  )}

                  <div style={{ display: "flex", gap: "0.8rem" }}>
                    <Btn onClick={() => act(m.id, "accept")}>{t("match.accept")}</Btn>
                    <Btn variant="outline" onClick={() => act(m.id, "reject")}>{t("match.reject")}</Btn>
                  </div>
                </div>
              )}
            </div>
          ))}
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
