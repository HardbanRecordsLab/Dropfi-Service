"use client";

import Link from "next/link";
import { useLang } from "@/lib/i18n";
import type { JobListItem } from "@/lib/types";
import { Badge } from "./ui";

export default function JobCard({ job }: { job: JobListItem }) {
  const { t } = useLang();

  const statusColor: Record<string, string> = {
    open: "#4ade80",
    matched: "var(--accent-gold)",
    in_progress: "#60a5fa",
    completed: "var(--text-muted)",
    cancelled: "#f87171",
  };

  return (
    <Link href={`/dashboard/jobs/${job.id}`} style={{ textDecoration: "none", color: "inherit" }}>
      <div className="premium-card" style={{ height: "100%", display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "1rem" }}>
          <h3 style={{ fontSize: "1.1rem", lineHeight: "1.3" }}>{job.title}</h3>
          <Badge color={statusColor[job.status] || "var(--text-muted)"}>
            {t(`jobs.status.${job.status}`)}
          </Badge>
        </div>

        <p
          style={{
            fontSize: "0.85rem",
            color: "var(--text-secondary)",
            display: "-webkit-box",
            WebkitLineClamp: 2,
            WebkitBoxOrient: "vertical",
            overflow: "hidden",
            flex: 1,
          }}
        >
          {job.description}
        </p>

        <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem" }}>
          {(job.required_skills || []).slice(0, 4).map((s) => (
            <Badge key={s}>{s}</Badge>
          ))}
        </div>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            paddingTop: "1rem",
            borderTop: "1px solid var(--border-subtle)",
          }}
        >
          <div>
            <div style={{ fontSize: "1.3rem", fontWeight: "800" }} className="gold-gradient-text">
              {job.budget.toLocaleString()} {t("common.currency")}
            </div>
            <div style={{ fontSize: "0.7rem", color: "var(--text-muted)" }}>
              {job.deadline} · {job.location || t("common.remote")}
            </div>
          </div>
          {job.match_count > 0 && (
            <div style={{ fontSize: "0.75rem", color: "var(--accent-gold)", fontWeight: "700" }}>
              {job.match_count} {t("jobs.matches")}
            </div>
          )}
        </div>
      </div>
    </Link>
  );
}
