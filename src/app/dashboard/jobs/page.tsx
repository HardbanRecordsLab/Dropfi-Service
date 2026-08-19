"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashShell from "@/components/DashShell";
import JobCard from "@/components/JobCard";
import { Btn, Loading, inputStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API } from "@/lib/api";
import type { JobListItem } from "@/lib/types";
import { CATEGORIES } from "@/lib/categories";

export default function JobsPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const [jobs, setJobs] = useState<JobListItem[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(true);

  const isClient = user?.role === "client";

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const data = isClient
          ? await API.myJobs()
          : await API.listJobs(`?status=open${category ? `&category=${encodeURIComponent(category)}` : ""}`);
        if (active) setJobs((data || []) as JobListItem[]);
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [isClient, category]);

  const filtered = jobs.filter((j) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      j.title.toLowerCase().includes(q) ||
      j.description.toLowerCase().includes(q) ||
      (j.required_skills || []).some((s) => s.toLowerCase().includes(q))
    );
  });

  if (loading) return <DashShell><Loading /></DashShell>;

  return (
    <DashShell>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: "2.5rem", flexWrap: "wrap", gap: "1rem" }}>
        <div>
          <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
            MARKETPLACE
          </div>
          <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>
            {isClient ? t("dash.myJobs") : t("jobs.browse")}
          </h1>
        </div>
        {isClient && (
          <Link href="/dashboard/jobs/new" style={{ textDecoration: "none" }}>
            <Btn>{t("nav.createJob")}</Btn>
          </Link>
        )}
      </header>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "2.5rem", flexWrap: "wrap" }}>
        <input
          style={{ ...inputStyle, maxWidth: "360px" }}
          placeholder={t("jobs.search")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          style={{ ...inputStyle, maxWidth: "240px" }}
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">{t("jobs.allCategories")}</option>
          {[...CATEGORIES, "Other"].map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {filtered.length === 0 ? (
        <div className="premium-card" style={{ textAlign: "center", padding: "4rem" }}>
          <div style={{ fontSize: "2.5rem", marginBottom: "1rem" }}>🔍</div>
          <p style={{ color: "var(--text-secondary)" }}>{t("dash.emptyJobs")}</p>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: "1.8rem" }}>
          {filtered.map((j) => (
            <JobCard key={j.id} job={j} />
          ))}
        </div>
      )}
    </DashShell>
  );
}
