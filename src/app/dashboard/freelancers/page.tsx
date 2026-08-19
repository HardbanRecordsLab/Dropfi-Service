"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Badge, Loading, inputStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API } from "@/lib/api";
import type { Freelancer, RiskScore } from "@/lib/types";

const RISK_COLOR: Record<string, string> = { low: "#4ade80", medium: "var(--accent-gold)", high: "#f87171" };

function RiskBadge({ userId }: { userId: string }) {
  const { t } = useLang();
  const [risk, setRisk] = useState<RiskScore | null>(null);

  useEffect(() => {
    let active = true;
    API.riskScore(userId)
      .then((r) => active && setRisk(r as RiskScore))
      .catch(() => {});
    return () => {
      active = false;
    };
  }, [userId]);

  if (!risk) return null;
  return (
    <Badge color={RISK_COLOR[risk.level]}>
      🛡️ {risk.score}/100 · {t(`risk.${risk.level}`)}
    </Badge>
  );
}

export default function FreelancersPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const [freelancers, setFreelancers] = useState<Freelancer[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      try {
        const params = search
          ? `?skill=${encodeURIComponent(search.split(" ")[0])}`
          : "";
        const data = (await API.getFreelancers(params)) as Freelancer[];
        if (active) setFreelancers(data);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [user, search]);

  if (loading) return <DashShell><Loading /></DashShell>;

  return (
    <DashShell>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          TALENT POOL
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("nav.matches")}</h1>
      </header>

      <input
        style={{ ...inputStyle, maxWidth: "360px", marginBottom: "2.5rem" }}
        placeholder="Szukaj po umiejętnościach…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      {freelancers.length === 0 ? (
        <div className="premium-card" style={{ textAlign: "center", padding: "4rem" }}>
          <p style={{ color: "var(--text-secondary)" }}>No freelancers found.</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.8rem" }}>
          {freelancers.map((f) => (
            <div key={f.id} className="premium-card">
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.8rem" }}>
                <div>
                  <div style={{ fontWeight: "800", fontSize: "1.05rem" }}>
                    {f.first_name} {f.last_name}
                  </div>
                  <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {f.location || t("common.remote")} · ⭐ {f.rating} ({f.rating_count})
                  </div>
                </div>
                <Badge color={f.availability === "available" ? "#4ade80" : "#f87171"}>
                  {f.availability === "available" ? t("profile.available") : t("profile.busy")}
                </Badge>
              </div>

              <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: "300", marginBottom: "1rem", minHeight: "40px" }}>
                {f.bio}
              </p>

              <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginBottom: "1rem" }}>
                {(f.skills || []).slice(0, 5).map((s) => (
                  <Badge key={s}>{s}</Badge>
                ))}
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <RiskBadge userId={f.id} />
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", paddingTop: "1rem", borderTop: "1px solid var(--border-subtle)" }}>
                <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  {f.hourly_rate ? `${f.hourly_rate} ${t("common.currency")}/h` : "—"}
                </span>
                <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {f.completed_jobs} {t("hero.stat.jobs").toLowerCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashShell>
  );
}
