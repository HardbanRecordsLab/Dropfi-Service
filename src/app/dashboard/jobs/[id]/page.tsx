"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading, inputStyle, labelStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { CopilotMessage, Job, Match, ScheduleSuggestion } from "@/lib/types";

export default function JobDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { user } = useAuth();
  const { t, lang } = useLang();
  const [job, setJob] = useState<Job | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  // Sprint 2 state
  const [interviewAnswers, setInterviewAnswers] = useState<string[]>([]);
  const [priceProposal, setPriceProposal] = useState("");
  const [fairPrice, setFairPrice] = useState<{ range_min: number; range_max: number; rationale: string } | null>(null);
  const [deliverDesc, setDeliverDesc] = useState("");
  const [deliverUrl, setDeliverUrl] = useState("");

  // #F5 AI Co-Pilot
  const [copilotHistory, setCopilotHistory] = useState<CopilotMessage[]>([]);
  const [copilotQuestion, setCopilotQuestion] = useState("");
  const [copilotBusy, setCopilotBusy] = useState(false);

  // #F7 Global Talent Time-Zone Auto-Scheduler
  const [schedules, setSchedules] = useState<Record<string, ScheduleSuggestion>>({});

  const jobId = params.id as string;

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      try {
        const [j, m] = await Promise.all([
          API.getJob(jobId),
          API.jobMatches(jobId).catch(() => []),
        ]);
        if (active) {
          setJob(j as Job);
          setMatches(m as Match[]);
        }
      } catch (err) {
        if (active) setMsg(getErrorMessage(err));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [jobId, user]);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      const hist = (await API.copilotHistory(jobId).catch(() => [])) as CopilotMessage[];
      if (active) setCopilotHistory(hist);
    })();
    return () => {
      active = false;
    };
  }, [jobId, user]);

  const reload = async () => {
    try {
      const [j, m] = await Promise.all([
        API.getJob(jobId),
        API.jobMatches(jobId).catch(() => []),
      ]);
      setJob(j as Job);
      setMatches(m as Match[]);
    } catch (err) {
      setMsg(getErrorMessage(err));
    }
  };

  if (loading) return <DashShell><Loading /></DashShell>;
  if (!job) return <DashShell><div className="premium-card"><p>{msg}</p></div></DashShell>;

  const isOwner = user?.id === job.client_id;
  const myMatch = user && user.role === "freelancer" ? matches.find((m) => m.freelancer_id === user.id) : null;
  const interviewed = myMatch?.interview_score != null;
  const hasContract = matches.some((m) => m.status === "accepted");
  const iAmFreelancerOnJob = myMatch != null;

  const statusColor: Record<string, string> = {
    open: "#4ade80",
    matched: "var(--accent-gold)",
    in_progress: "#60a5fa",
    completed: "var(--text-muted)",
    cancelled: "#f87171",
  };

  const handleMatchAction = async (matchId: string, action: "accept" | "reject") => {
    setBusy(true);
    try {
      if (action === "accept") {
        await API.acceptMatch(matchId);
        setMsg("Contract created!");
      } else {
        await API.rejectMatch(matchId);
        setMsg("Match declined");
      }
      setTimeout(() => router.push(action === "accept" ? "/dashboard/contracts" : "/dashboard/matches"), 700);
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const handleComplete = async () => {
    setBusy(true);
    try {
      const updated = (await API.completeJob(job.id)) as Job;
      setJob(updated);
      setMsg("Job completed");
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const submitInterview = async () => {
    if (!myMatch) return;
    if (interviewAnswers.some((a) => !a.trim())) {
      setMsg("Answer all questions");
      return;
    }
    setBusy(true);
    try {
      await API.submitInterview(myMatch.id, interviewAnswers);
      setMsg("Interview submitted — AI scored your answers!");
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const submitPrice = async () => {
    if (!myMatch) return;
    const amount = parseFloat(priceProposal);
    if (!amount || amount <= 0) {
      setMsg("Enter a valid price");
      return;
    }
    setBusy(true);
    try {
      await API.proposePrice(myMatch.id, amount);
      setMsg("Price proposal sent to the client");
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const askCopilot = async () => {
    if (!copilotQuestion.trim() || !job) return;
    setCopilotBusy(true);
    try {
      const res = (await API.askCopilot(job.id, copilotQuestion, lang)) as { answer: string };
      setCopilotHistory((h) => [...h, { question: copilotQuestion, answer: res.answer, created_at: new Date().toISOString() }]);
      setCopilotQuestion("");
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setCopilotBusy(false);
    }
  };

  const loadSchedule = async (matchId: string) => {
    if (schedules[matchId]) return;
    try {
      const res = (await API.matchSchedule(matchId)) as ScheduleSuggestion;
      setSchedules((s) => ({ ...s, [matchId]: res }));
    } catch {
      // non-critical, ignore
    }
  };

  const submitDeliverables = async () => {
    if (!deliverDesc.trim()) {
      setMsg("Describe the delivered work");
      return;
    }
    setBusy(true);
    try {
      const updated = (await API.submitDeliverables(job.id, deliverDesc, deliverUrl)) as Job;
      setJob(updated);
      setMsg(`AI QA report: ${updated.deliverable_report?.score ?? 0}/100`);
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <DashShell>
      <button
        onClick={() => router.back()}
        style={{ color: "var(--text-muted)", fontSize: "0.8rem", fontWeight: "600", marginBottom: "1.5rem" }}
      >
        ← {t("common.back")}
      </button>

      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: "3rem", alignItems: "start" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
            <h1 style={{ fontSize: "2.2rem", fontFamily: "var(--font-playfair)", lineHeight: "1.2" }}>{job.title}</h1>
            <Badge color={statusColor[job.status] || "var(--text-muted)"}>{t(`jobs.status.${job.status}`)}</Badge>
          </div>

          <div className="premium-card" style={{ marginBottom: "2rem" }}>
            <p style={{ color: "var(--text-secondary)", lineHeight: "1.7", fontWeight: "300", whiteSpace: "pre-wrap" }}>
              {job.description}
            </p>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "1.5rem", marginTop: "2rem", paddingTop: "1.5rem", borderTop: "1px solid var(--border-subtle)" }}>
              <div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("jobs.budget")}</div>
                <div style={{ fontSize: "1.4rem", fontWeight: "800" }} className="gold-gradient-text">
                  {job.budget.toLocaleString()} {t("common.currency")}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("jobs.deadline")}</div>
                <div style={{ fontSize: "1.1rem", fontWeight: "700" }}>{job.deadline}</div>
              </div>
              <div>
                <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("jobs.location")}</div>
                <div style={{ fontSize: "1.1rem", fontWeight: "700" }}>{job.location || t("common.remote")}</div>
              </div>
            </div>

            <div style={{ marginTop: "1.5rem" }}>
              <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.6rem" }}>
                {t("jobs.skills")}
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
                {(job.required_skills || []).map((s) => (
                  <Badge key={s}>{s}</Badge>
                ))}
                {(!job.required_skills || job.required_skills.length === 0) && <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>AI…</span>}
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          {job.ai_analysis && (
            <div className="premium-card" style={{ background: "rgba(197,160,89,0.04)", border: "1px dashed var(--border-gold)", marginBottom: "2rem" }}>
              <div style={{ fontSize: "0.75rem", fontWeight: "800", letterSpacing: "2px", color: "var(--accent-gold)", marginBottom: "1rem" }}>
                🤖 AI ANALYSIS {job.ai_analysis.model === "claude" ? "· CLAUDE" : "· RULES"}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1.2rem" }}>
                <div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>{t("jobs.category")}</div>
                  <div style={{ fontWeight: "700" }}>{job.ai_analysis.category} / {job.ai_analysis.subcategory}</div>
                </div>
                <div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Urgency</div>
                  <div style={{ fontWeight: "700" }}>{job.ai_analysis.urgency}</div>
                </div>
                <div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Fair price</div>
                  <div style={{ fontWeight: "700" }}>{job.ai_analysis.fair_price?.toLocaleString()} {t("common.currency")}</div>
                </div>
                <div>
                  <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>Experience</div>
                  <div style={{ fontWeight: "700" }}>{job.ai_analysis.experience_level}</div>
                </div>
              </div>
            </div>
          )}

          {/* #3: AI fair price + negotiation (freelancer) */}
          {iAmFreelancerOnJob && myMatch?.status === "pending" && (
            <div className="premium-card" style={{ marginBottom: "2rem" }}>
              <h3 style={{ fontSize: "1.15rem", fontFamily: "var(--font-playfair)", marginBottom: "0.8rem" }}>🤝 {t("nego.title")}</h3>

              {fairPrice ? (
                <div style={{ marginBottom: "1.2rem", padding: "1rem", background: "rgba(197,160,89,0.05)", border: "1px dashed var(--border-gold)", borderRadius: "4px", fontSize: "0.85rem" }}>
                  <b>{t("nego.range")}: {fairPrice.range_min.toLocaleString()}–{fairPrice.range_max.toLocaleString()} {t("common.currency")}</b>
                  <p style={{ color: "var(--text-secondary)", marginTop: "0.4rem" }}>{fairPrice.rationale}</p>
                </div>
              ) : (
                <Btn
                  variant="outline"
                  onClick={async () => {
                    try {
                      setFairPrice((await API.fairPrice(job.id)) as { range_min: number; range_max: number; rationale: string });
                    } catch (err) {
                      setMsg(getErrorMessage(err));
                    }
                  }}
                >
                  💡 {t("nego.fairPrice")}
                </Btn>
              )}

              {myMatch.price_status === "none" && (
                <div style={{ display: "flex", gap: "1rem", alignItems: "flex-end", marginTop: "1rem", flexWrap: "wrap" }}>
                  <div style={{ flex: 1, minWidth: "180px" }}>
                    <label style={labelStyle}>{t("nego.amount")}</label>
                    <input
                      style={inputStyle}
                      type="number"
                      value={priceProposal}
                      onChange={(e) => setPriceProposal(e.target.value)}
                      placeholder={String(job.budget)}
                    />
                  </div>
                  <Btn onClick={submitPrice} disabled={busy}>{t("nego.propose")}</Btn>
                </div>
              )}
              {myMatch.price_status === "proposed" && (
                <Badge color="var(--accent-gold)">{t("nego.proposed")}: {myMatch.price_proposal} {t("common.currency")}</Badge>
              )}
              {myMatch.price_status === "accepted" && (
                <Badge color="#4ade80">{t("nego.accepted")}: {myMatch.agreed_price} {t("common.currency")}</Badge>
              )}
              {myMatch.price_status === "declined" && <Badge color="#f87171">{t("nego.declined")}</Badge>}
            </div>
          )}

          {/* #1: AI Instant Interview (freelancer) */}
          {iAmFreelancerOnJob && myMatch?.status === "pending" && !interviewed && (job.interview_questions || []).length > 0 && (
            <div className="premium-card" style={{ marginBottom: "2rem" }}>
              <h3 style={{ fontSize: "1.15rem", fontFamily: "var(--font-playfair)", marginBottom: "0.4rem" }}>🎙️ {t("interview.title")}</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1.2rem" }}>{t("interview.desc")}</p>
              <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
                {(job.interview_questions || []).map((q, i) => (
                  <div key={i}>
                    <label style={labelStyle}>{i + 1}. {q}</label>
                    <textarea
                      style={{ ...inputStyle, resize: "vertical", minHeight: "70px" }}
                      value={interviewAnswers[i] || ""}
                      onChange={(e) => {
                        const next = [...interviewAnswers];
                        next[i] = e.target.value;
                        setInterviewAnswers(next);
                      }}
                    />
                  </div>
                ))}
                <div>
                  <Btn onClick={submitInterview} disabled={busy}>{t("interview.submit")}</Btn>
                </div>
              </div>
            </div>
          )}

          {iAmFreelancerOnJob && interviewed && (
            <div className="premium-card" style={{ marginBottom: "2rem", border: "1px solid rgba(74,222,128,0.3)" }}>
              <h3 style={{ fontSize: "1.15rem", fontFamily: "var(--font-playfair)", marginBottom: "0.6rem" }}>🎙️ {t("interview.title")} — {t("interview.done")}</h3>
              <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                <div style={{ fontSize: "2.4rem", fontWeight: "800" }} className="gold-gradient-text">
                  {myMatch?.interview_score}/100
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{t("interview.score")}</div>
              </div>
              {myMatch?.interview_feedback && (
                <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: "0.8rem" }}>{myMatch.interview_feedback}</p>
              )}
            </div>
          )}

          {/* #2: Deliverables + AI QA */}
          {hasContract && (
            <div className="premium-card" style={{ marginBottom: "2rem" }}>
              <h3 style={{ fontSize: "1.15rem", fontFamily: "var(--font-playfair)", marginBottom: "0.4rem" }}>📦 {t("deliver.title")}</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1.2rem" }}>{t("deliver.desc")}</p>

              {job.deliverable_report ? (
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "1.2rem", marginBottom: "1rem", flexWrap: "wrap" }}>
                    <div style={{ fontSize: "2.2rem", fontWeight: "800" }} className="gold-gradient-text">
                      {job.deliverable_report.score}/100
                    </div>
                    <div>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("deliver.recommendation")}</div>
                      <Badge color={job.deliverable_report.recommendation === "approve" ? "#4ade80" : job.deliverable_report.recommendation === "revisions" ? "var(--accent-gold)" : "#f87171"}>
                        {t(`deliver.${job.deliverable_report.recommendation}`)}
                      </Badge>
                    </div>
                  </div>
                  {job.deliverable_report.summary && (
                    <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{job.deliverable_report.summary}</p>
                  )}
                  {(job.deliverable_report.issues || []).length > 0 && (
                    <div style={{ marginTop: "0.8rem" }}>
                      <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.4rem" }}>{t("deliver.issues")}</div>
                      {job.deliverable_report.issues.map((issue, i) => (
                        <div key={i} style={{ fontSize: "0.8rem", color: "#f87171", marginBottom: "0.2rem" }}>• {issue}</div>
                      ))}
                    </div>
                  )}
                  {job.deliverable_url && (
                    <a href={job.deliverable_url} target="_blank" rel="noreferrer" style={{ fontSize: "0.82rem", color: "var(--accent-gold)" }}>
                      {job.deliverable_url}
                    </a>
                  )}
                </div>
              ) : (
                <div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                    <div>
                      <label style={labelStyle}>{t("deliver.description")}</label>
                      <textarea
                        style={{ ...inputStyle, resize: "vertical", minHeight: "90px" }}
                        value={deliverDesc}
                        onChange={(e) => setDeliverDesc(e.target.value)}
                      />
                    </div>
                    <div>
                      <label style={labelStyle}>{t("deliver.url")}</label>
                      <input style={inputStyle} value={deliverUrl} onChange={(e) => setDeliverUrl(e.target.value)} />
                    </div>
                  </div>
                  <div style={{ marginTop: "1rem" }}>
                    <Btn onClick={submitDeliverables} disabled={busy}>{t("deliver.submit")}</Btn>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* #F5: AI Co-Pilot (participants only) */}
          {(isOwner || iAmFreelancerOnJob) && (
            <div className="premium-card" style={{ marginBottom: "2rem" }}>
              <h3 style={{ fontSize: "1.15rem", fontFamily: "var(--font-playfair)", marginBottom: "0.4rem" }}>🧭 {t("copilot.title")}</h3>
              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "1.2rem" }}>{t("copilot.desc")}</p>

              {copilotHistory.length === 0 ? (
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{t("copilot.empty")}</p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem", marginBottom: "1.2rem", maxHeight: "260px", overflowY: "auto" }}>
                  {copilotHistory.map((m, i) => (
                    <div key={i}>
                      <div style={{ fontSize: "0.82rem", fontWeight: "700", color: "var(--text-secondary)" }}>❓ {m.question}</div>
                      <div style={{ fontSize: "0.85rem", color: "var(--text-primary)", marginTop: "0.2rem" }}>🤖 {m.answer}</div>
                    </div>
                  ))}
                </div>
              )}

              <div style={{ display: "flex", gap: "0.8rem", flexWrap: "wrap" }}>
                <input
                  style={{ ...inputStyle, flex: 1, minWidth: "220px" }}
                  value={copilotQuestion}
                  onChange={(e) => setCopilotQuestion(e.target.value)}
                  placeholder={t("copilot.placeholder")}
                  onKeyDown={(e) => e.key === "Enter" && askCopilot()}
                />
                <Btn onClick={askCopilot} disabled={copilotBusy}>{t("copilot.ask")}</Btn>
              </div>
            </div>
          )}

          {isOwner && job.status !== "completed" && job.status !== "cancelled" && (
            <Btn variant="outline" onClick={handleComplete} disabled={busy}>
              {t("jobs.complete")}
            </Btn>
          )}
        </div>

        {/* Right column: matches */}
        <div>
          <h2 style={{ fontSize: "1.4rem", fontFamily: "var(--font-playfair)", marginBottom: "1.5rem" }}>
            {t("jobs.matches")} ({matches.length})
          </h2>

          {matches.length === 0 ? (
            <div className="premium-card" style={{ textAlign: "center", padding: "3rem" }}>
              <div style={{ fontSize: "2rem", marginBottom: "1rem" }}>🤖</div>
              <p style={{ color: "var(--text-secondary)" }}>{t("jobs.noMatches")}</p>
              {isOwner && (
                <div style={{ marginTop: "1.5rem" }}>
                  <Btn
                    variant="outline"
                    onClick={async () => {
                      try {
                        const res = await API.jobMatches(job.id);
                        if (res) router.refresh();
                      } catch {}
                    }}
                  >
                    {t("jobs.retrigger")}
                  </Btn>
                </div>
              )}
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "1.2rem" }}>
              {matches.map((m) => (
                <div key={m.id} className="premium-card" style={{ padding: "1.5rem" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.8rem" }}>
                    <div>
                      <div style={{ fontWeight: "700", fontSize: "1rem" }}>
                        {m.freelancer?.first_name} {m.freelancer?.last_name}
                      </div>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                        {m.freelancer?.location || ""} · ⭐ {m.freelancer?.rating ?? "—"} ({m.freelancer?.rating_count ?? 0})
                      </div>
                    </div>
                    <Badge color={m.status === "accepted" ? "#4ade80" : m.status === "rejected" ? "#f87171" : "var(--accent-gold)"}>
                      {t(`match.${m.status}`)}
                    </Badge>
                  </div>

                  <div style={{ fontSize: "1.6rem", fontWeight: "800", marginBottom: "0.5rem" }} className="gold-gradient-text">
                    {Math.round(m.score * 100)}% {t("match.score").toLowerCase()}
                  </div>

                  {(m.freelancer?.skills || []).slice(0, 4).map((s) => (
                    <Badge key={s}>{s}</Badge>
                  ))}

                  {/* #F7: Global Talent Time-Zone Auto-Scheduler (client view) */}
                  {isOwner && (
                    schedules[m.id] ? (
                      <div style={{ marginTop: "0.8rem", padding: "0.7rem 0.9rem", background: "rgba(96,165,250,0.05)", border: "1px dashed rgba(96,165,250,0.25)", borderRadius: "4px", fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                        🕐 {schedules[m.id].overlap_hours}h {t("sched.overlap")} · {schedules[m.id].hours_apart}h {t("sched.apart")}
                        <div style={{ marginTop: "0.2rem", color: "var(--text-muted)" }}>
                          {schedules[m.id].mode === "live-overlap" && t("sched.live")}
                          {schedules[m.id].mode === "handoff" && t("sched.handoff")}
                          {schedules[m.id].mode === "async-24-7" && t("sched.async")}
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => loadSchedule(m.id)}
                        style={{ marginTop: "0.6rem", fontSize: "0.72rem", color: "var(--accent-gold)", fontWeight: "700" }}
                      >
                        🕐 {t("sched.title")}
                      </button>
                    )
                  )}

                  {/* #1: interview result (client view) */}
                  {isOwner && m.interview_score != null && (
                    <div style={{ marginTop: "0.8rem", padding: "0.8rem", background: "rgba(197,160,89,0.05)", border: "1px dashed var(--border-gold)", borderRadius: "4px" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>
                          {t("interview.title")} · {t("interview.score")}
                        </span>
                        <span style={{ fontWeight: "800", fontSize: "1.1rem" }} className="gold-gradient-text">
                          {m.interview_score}/100
                        </span>
                      </div>
                      {m.interview_feedback && (
                        <p style={{ fontSize: "0.78rem", color: "var(--text-secondary)", marginTop: "0.4rem" }}>{m.interview_feedback}</p>
                      )}
                      {(m.interview_answers || []).length > 0 && (
                        <details style={{ marginTop: "0.5rem" }}>
                          <summary style={{ fontSize: "0.75rem", color: "var(--accent-gold)", cursor: "pointer", fontWeight: "700" }}>
                            {t("interview.answers")}
                          </summary>
                          <div style={{ marginTop: "0.5rem", display: "flex", flexDirection: "column", gap: "0.4rem" }}>
                            {m.interview_answers!.map((a, i) => (
                              <div key={i} style={{ fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                                <b>{i + 1}.</b> {a}
                              </div>
                            ))}
                          </div>
                        </details>
                      )}
                    </div>
                  )}

                  {/* #3: negotiation (client view) */}
                  {isOwner && m.price_status === "proposed" && m.price_proposal != null && (
                    <div style={{ marginTop: "0.8rem", padding: "0.8rem", background: "rgba(96,165,250,0.06)", border: "1px solid rgba(96,165,250,0.25)", borderRadius: "4px" }}>
                      <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.5rem" }}>
                        {t("nego.proposed")}: <b className="gold-gradient-text">{m.price_proposal.toLocaleString()} {t("common.currency")}</b>{" "}
                        (budżet: {job.budget.toLocaleString()} {t("common.currency")})
                      </div>
                      <div style={{ display: "flex", gap: "0.6rem" }}>
                        <Btn onClick={async () => { try { await API.confirmPrice(m.id); await reload(); } catch (err) { setMsg(getErrorMessage(err)); } }} disabled={busy}>
                          {t("nego.accept")}
                        </Btn>
                        <Btn variant="outline" onClick={async () => { try { await API.declinePrice(m.id); await reload(); } catch (err) { setMsg(getErrorMessage(err)); } }} disabled={busy}>
                          {t("nego.decline")}
                        </Btn>
                      </div>
                    </div>
                  )}
                  {isOwner && m.price_status === "accepted" && (
                    <Badge color="#4ade80">{t("nego.accepted")}: {m.agreed_price} {t("common.currency")}</Badge>
                  )}

                  <div style={{ marginTop: "1rem", display: "flex", gap: "1.5rem", fontSize: "0.82rem", color: "var(--text-secondary)" }}>
                    {m.freelancer?.hourly_rate ? (
                      <span>{m.freelancer.hourly_rate} {t("common.currency")}/h</span>
                    ) : null}
                    <span>{m.freelancer?.completed_jobs ?? 0} {t("hero.stat.jobs").toLowerCase()}</span>
                  </div>

                  {user?.role === "freelancer" && m.freelancer_id === user.id && m.status === "pending" && (
                    <div style={{ display: "flex", gap: "0.8rem", marginTop: "1.2rem" }}>
                      <Btn disabled={busy} onClick={() => handleMatchAction(m.id, "accept")}>
                        {t("match.accept")}
                      </Btn>
                      <Btn variant="outline" disabled={busy} onClick={() => handleMatchAction(m.id, "reject")}>
                        {t("match.reject")}
                      </Btn>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {msg && (
        <div style={{ position: "fixed", bottom: "2rem", left: "50%", transform: "translateX(-50%)", background: "var(--accent-gold)", color: "#000", fontWeight: "700", padding: "1rem 2rem", borderRadius: "6px", zIndex: 999 }}>
          {msg}
        </div>
      )}
    </DashShell>
  );
}
