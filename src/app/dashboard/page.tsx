"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashShell from "@/components/DashShell";
import { StatCard, Loading, Badge, Btn } from "@/components/ui";
import JobCard from "@/components/JobCard";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API } from "@/lib/api";
import type { Analytics, JobListItem, Match, Contract } from "@/lib/types";

export default function DashboardPage() {
  const { user, loading: authLoading } = useAuth();
  const { t } = useLang();
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [myJobs, setMyJobs] = useState<JobListItem[]>([]);
  const [recommended, setRecommended] = useState<JobListItem[]>([]);
  const [myMatches, setMyMatches] = useState<Match[]>([]);
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      try {
        const [stats, jobs, rec, matches, cons] = await Promise.all([
          API.analytics().catch(() => null),
          API.myJobs().catch(() => []),
          user.role === "freelancer" ? API.recommendedJobs().catch(() => []) : Promise.resolve([]),
          user.role === "freelancer" ? API.myMatches().catch(() => []) : Promise.resolve([]),
          API.myContracts().catch(() => []),
        ]);
        if (active) {
          setAnalytics(stats as Analytics | null);
          setMyJobs((jobs || []) as JobListItem[]);
          setRecommended((rec || []) as JobListItem[]);
          setMyMatches((matches || []) as Match[]);
          setContracts((cons || []) as Contract[]);
        }
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [user]);

  if (authLoading || loading) return <DashShell><Loading /></DashShell>;
  if (!user) return null;

  const isClient = user.role === "client";
  const isAdmin = user.role === "admin";

  return (
    <DashShell>
      <header style={{ marginBottom: "3rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          {t("dash.title")}
        </div>
        <h1 style={{ fontSize: "2.6rem", fontFamily: "var(--font-playfair)", lineHeight: "1.1" }}>
          {t("dash.welcome")}, {user.first_name || user.email.split("@")[0]}
        </h1>
        <p style={{ color: "var(--text-secondary)", marginTop: "0.5rem", fontWeight: "300" }}>
          {isClient ? t("dash.client") : t("dash.freelancer")}
        </p>
      </header>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "1.8rem", marginBottom: "3.5rem" }}>
        {isClient ? (
          <>
            <StatCard icon="📋" label={t("dash.stat.jobs")} value={analytics?.total_jobs ?? 0} sub={`${analytics?.active_jobs ?? 0} ${t("dash.stat.active")}`} />
            <StatCard icon="✓" label={t("dash.stat.completed")} value={analytics?.completed_jobs ?? 0} sub={`${analytics?.jobs_this_month ?? 0} ${t("dash.stat.month")}`} />
            <StatCard icon="💸" label={t("dash.stat.spent")} value={`${(analytics?.total_spent ?? 0).toLocaleString()} ${t("common.currency")}`} />
            <StatCard icon="🤝" label={t("dash.stat.matches")} value={analytics?.match_count ?? 0} sub={`${analytics?.pending_matches ?? 0} ${t("dash.stat.pending")}`} />
          </>
        ) : (
          <>
            <StatCard icon="🤝" label={t("dash.stat.matches")} value={analytics?.match_count ?? 0} sub={`${analytics?.pending_matches ?? 0} ${t("dash.stat.pending")}`} />
            <StatCard icon="💶" label={t("dash.stat.earned")} value={`${(analytics?.total_earned ?? 0).toLocaleString()} ${t("common.currency")}`} />
            <StatCard icon="✓" label={t("dash.stat.completed")} value={analytics?.completed_jobs ?? 0} />
            <StatCard icon="★" label={t("dash.stat.rating")} value={analytics?.rating ?? user.rating ?? 5.0} />
          </>
        )}
      </div>

      {/* Feature #18: AI pipeline metrics for clients */}
      {isClient && (
        <div
          className="premium-card"
          style={{
            marginBottom: "3.5rem",
            padding: "2rem",
            background: "linear-gradient(135deg, rgba(197,160,89,0.08) 0%, rgba(5,5,5,0) 60%)",
            border: "1px dashed var(--border-gold)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem", flexWrap: "wrap", gap: "1rem" }}>
            <div>
              <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "2px", marginBottom: "0.4rem" }}>
                {t("dash.aiPipeline")}
              </div>
              <h2 style={{ fontSize: "1.3rem", fontFamily: "var(--font-playfair)" }}>{t("dash.pipelineDesc")}</h2>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", background: "rgba(74,222,128,0.1)", border: "1px solid rgba(74,222,128,0.3)", borderRadius: "20px", padding: "0.4rem 1rem" }}>
              <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#4ade80", boxShadow: "0 0 8px #4ade80" }} />
              <span style={{ fontSize: "0.75rem", fontWeight: "700", color: "#4ade80" }}>{t("dash.pipelineLive")}</span>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1.5rem" }}>
            <div>
              <div style={{ fontSize: "2rem", fontWeight: "800" }} className="gold-gradient-text">
                {analytics?.avg_match_time_seconds != null ? `${analytics.avg_match_time_seconds}s` : "—"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t("dash.stat.matchTime")}</div>
            </div>
            <div>
              <div style={{ fontSize: "2rem", fontWeight: "800" }} className="gold-gradient-text">
                {analytics?.instant_matches ?? 0}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t("dash.stat.instant")}</div>
            </div>
            <div>
              <div style={{ fontSize: "2rem", fontWeight: "800" }} className="gold-gradient-text">
                {analytics?.avg_time_to_hire_hours != null ? `${analytics.avg_time_to_hire_hours}h` : "—"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t("dash.stat.hireTime")}</div>
            </div>
            <div>
              <div style={{ fontSize: "2rem", fontWeight: "800" }} className="gold-gradient-text">
                {analytics?.total_jobs ?? 0}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{t("dash.stat.jobs")}</div>
            </div>
          </div>
          {(analytics?.total_jobs ?? 0) === 0 && (
            <p style={{ marginTop: "1.2rem", fontSize: "0.85rem", color: "var(--text-muted)" }}>{t("dash.noData")}</p>
          )}
        </div>
      )}

      {/* Main content */}
      <div style={{ display: "grid", gridTemplateColumns: isClient ? "1.6fr 1fr" : "1.6fr 1fr", gap: "3rem", alignItems: "start" }}>
        {/* Left column */}
        <div>
          {isClient && (
            <section style={{ marginBottom: "3rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
                <h2 style={{ fontSize: "1.4rem", fontFamily: "var(--font-playfair)" }}>{t("dash.myJobs")}</h2>
                <Link href="/dashboard/jobs/new">
                  <Btn>{t("nav.createJob")}</Btn>
                </Link>
              </div>
              {myJobs.length === 0 ? (
                <div className="premium-card" style={{ textAlign: "center", padding: "3rem" }}>
                  <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>📋</div>
                  <p style={{ color: "var(--text-secondary)" }}>{t("dash.emptyJobs")}</p>
                  <div style={{ marginTop: "1.5rem" }}>
                    <Link href="/dashboard/jobs/new">
                      <Btn>{t("dash.createFirst")}</Btn>
                    </Link>
                  </div>
                </div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1.5rem" }}>
                  {myJobs.slice(0, 4).map((j) => (
                    <JobCard key={j.id} job={j} />
                  ))}
                </div>
              )}
            </section>
          )}

          {!isClient && !isAdmin && (
            <section style={{ marginBottom: "3rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
                <h2 style={{ fontSize: "1.4rem", fontFamily: "var(--font-playfair)" }}>{t("dash.recommended")}</h2>
                <Link href="/dashboard/jobs" style={{ fontSize: "0.8rem", color: "var(--accent-gold)", fontWeight: "600" }}>
                  {t("common.view")} →
                </Link>
              </div>
              {recommended.length === 0 ? (
                <div className="premium-card" style={{ textAlign: "center", padding: "3rem" }}>
                  <p style={{ color: "var(--text-secondary)" }}>{t("dash.emptyJobs")}</p>
                </div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "1.5rem" }}>
                  {recommended.slice(0, 4).map((j) => (
                    <JobCard key={j.id} job={j} />
                  ))}
                </div>
              )}
            </section>
          )}

          {isAdmin && (
            <div className="premium-card" style={{ textAlign: "center", padding: "4rem" }}>
              <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>🛠️</div>
              <h2 style={{ fontSize: "1.4rem", marginBottom: "0.5rem" }}>{t("admin.title")}</h2>
              <p style={{ color: "var(--text-secondary)", marginBottom: "1.5rem" }}>{t("dash.revenue")}</p>
              <Link href="/admin">
                <Btn>Admin</Btn>
              </Link>
            </div>
          )}
        </div>

        {/* Right column */}
        <div>
          {!isClient && !isAdmin && (
            <section style={{ marginBottom: "2.5rem" }}>
              <h2 style={{ fontSize: "1.4rem", fontFamily: "var(--font-playfair)", marginBottom: "1.5rem" }}>{t("dash.myMatches")}</h2>
              {myMatches.length === 0 ? (
                <div className="premium-card" style={{ textAlign: "center", padding: "2rem" }}>
                  <p style={{ color: "var(--text-secondary)" }}>{t("dash.emptyMatches")}</p>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                  {myMatches.slice(0, 5).map((m) => (
                    <Link key={m.id} href="/dashboard/matches" style={{ textDecoration: "none", color: "inherit" }}>
                      <div className="premium-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1.2rem" }}>
                        <div>
                          <div style={{ fontWeight: "700", fontSize: "0.9rem" }}>{m.job?.title}</div>
                          <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            {m.job?.budget?.toLocaleString()} {t("common.currency")}
                          </div>
                        </div>
                        <div style={{ textAlign: "right" }}>
                          <Badge color="var(--accent-gold)">{Math.round(m.score * 100)}%</Badge>
                          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
                            {t(`match.${m.status}`)}
                          </div>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </section>
          )}

          <section>
            <h2 style={{ fontSize: "1.4rem", fontFamily: "var(--font-playfair)", marginBottom: "1.5rem" }}>{t("nav.contracts")}</h2>
            {contracts.length === 0 ? (
              <div className="premium-card" style={{ textAlign: "center", padding: "2rem" }}>
                <p style={{ color: "var(--text-secondary)" }}>{t("contracts.none")}</p>
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {contracts.slice(0, 5).map((c) => (
                  <div key={c.id} className="premium-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "1.2rem" }}>
                    <div>
                      <div style={{ fontWeight: "700", fontSize: "0.9rem" }}>{c.job?.title}</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{c.job_id}</div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontWeight: "800", fontSize: "1rem" }} className="gold-gradient-text">
                        {c.amount.toLocaleString()} {t("common.currency")}
                      </div>
                      <Badge color={c.status === "completed" ? "#4ade80" : "var(--accent-gold)"}>
                        {t(`contracts.status.${c.status}`)}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </DashShell>
  );
}
