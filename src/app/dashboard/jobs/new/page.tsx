"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import DashShell from "@/components/DashShell";
import { Btn, inputStyle, labelStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";

export default function NewJobPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { t } = useLang();
  const [form, setForm] = useState({
    title: "",
    description: "",
    budget: "",
    deadline: "",
    location: "",
    skills: "",
    category: "",
  });
  const [idea, setIdea] = useState("");
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const job = (await API.createJob({
        title: form.title,
        description: form.description,
        budget: parseFloat(form.budget),
        deadline: form.deadline,
        location: form.location,
        category: form.category,
        required_skills: form.skills.split(",").map((s) => s.trim()).filter(Boolean),
      })) as { id: string };
      router.push(`/dashboard/jobs/${job.id}`);
    } catch (err) {
      setError(getErrorMessage(err, t("common.error")));
    } finally {
      setLoading(false);
    }
  };

  const generate = async () => {
    setError("");
    setGenerating(true);
    try {
      const res = (await API.generateJobDraft(idea)) as {
        draft: {
          title: string;
          description: string;
          category: string;
          required_skills: string[];
          suggested_budget: number;
          suggested_deadline_days: number;
        };
      };
      const d = res.draft;
      setForm((f) => ({
        ...f,
        title: d.title || f.title,
        description: d.description || f.description,
        budget: d.suggested_budget ? String(d.suggested_budget) : f.budget,
        deadline:
          d.suggested_deadline_days
            ? new Date(Date.now() + d.suggested_deadline_days * 86400000).toISOString().slice(0, 10)
            : f.deadline,
        category: d.category || f.category,
        skills: (d.required_skills || []).join(", "),
      }));
      setGenerated(true);
    } catch (err) {
      setError(getErrorMessage(err, t("common.error")));
    } finally {
      setGenerating(false);
    }
  };

  if (user && user.role !== "client") {
    return (
      <DashShell>
        <div className="premium-card" style={{ textAlign: "center", padding: "4rem" }}>
          <p style={{ color: "var(--text-secondary)" }}>Only clients can post jobs.</p>
        </div>
      </DashShell>
    );
  }

  return (
    <DashShell>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          {t("nav.createJob")}
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("jobs.new")}</h1>
        <p style={{ color: "var(--text-secondary)", fontWeight: "300", marginTop: "0.5rem" }}>{t("jobs.ai.willAnalyze")}</p>
      </header>

      {/* #14: AI onboarding generator */}
      <div className="premium-card" style={{ maxWidth: "800px", padding: "2.5rem", marginBottom: "2rem", background: "linear-gradient(135deg, rgba(197,160,89,0.08) 0%, rgba(5,5,5,0) 60%)", border: "1px dashed var(--border-gold)" }}>
        <h2 style={{ fontSize: "1.3rem", fontFamily: "var(--font-playfair)", marginBottom: "0.4rem" }}>{t("gen.title")}</h2>
        <p style={{ fontSize: "0.88rem", color: "var(--text-secondary)", marginBottom: "1.2rem" }}>{t("gen.desc")}</p>
        <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <input
            style={{ ...inputStyle, flex: 1, minWidth: "260px" }}
            placeholder={t("gen.idea")}
            value={idea}
            onChange={(e) => setIdea(e.target.value)}
          />
          <Btn onClick={generate} disabled={generating || idea.trim().length < 10}>
            {generating ? t("common.loading") : t("gen.button")}
          </Btn>
        </div>
        {generated && (
          <p style={{ marginTop: "0.8rem", fontSize: "0.82rem", color: "#4ade80", fontWeight: "600" }}>✓ {t("gen.used")}</p>
        )}
      </div>

      <form onSubmit={submit} className="premium-card" style={{ maxWidth: "800px", padding: "3rem", display: "flex", flexDirection: "column", gap: "2rem" }}>
        <div>
          <label style={labelStyle}>{t("jobs.titleLabel")} *</label>
          <input style={inputStyle} value={form.title} onChange={(e) => set("title", e.target.value)} required minLength={3} />
        </div>

        <div>
          <label style={labelStyle}>{t("jobs.desc")} *</label>
          <textarea
            style={{ ...inputStyle, resize: "vertical", minHeight: "160px" }}
            rows={7}
            placeholder={t("jobs.descPlaceholder")}
            value={form.description}
            onChange={(e) => set("description", e.target.value)}
            required
            minLength={10}
          />
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "1.5rem" }}>
          <div>
            <label style={labelStyle}>{t("jobs.budget")} *</label>
            <input style={inputStyle} type="number" min={1} value={form.budget} onChange={(e) => set("budget", e.target.value)} required />
          </div>
          <div>
            <label style={labelStyle}>{t("jobs.deadline")} *</label>
            <input style={inputStyle} type="date" value={form.deadline} onChange={(e) => set("deadline", e.target.value)} required />
          </div>
          <div>
            <label style={labelStyle}>{t("jobs.location")}</label>
            <input style={inputStyle} value={form.location} onChange={(e) => set("location", e.target.value)} placeholder={t("common.remote")} />
          </div>
        </div>

        <div>
          <label style={labelStyle}>{t("jobs.category")}</label>
          <select style={inputStyle} value={form.category} onChange={(e) => set("category", e.target.value)}>
            <option value="">Auto (AI)</option>
            {["Photography", "Coding", "Design", "Writing", "Marketing", "Video & Animation", "E-commerce", "Translation", "Consulting"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div>
          <label style={labelStyle}>{t("jobs.skills")}</label>
          <input style={inputStyle} value={form.skills} onChange={(e) => set("skills", e.target.value)} placeholder={t("jobs.skillsHint")} />
        </div>

        {error && (
          <div style={{ padding: "0.9rem 1rem", background: "rgba(248,113,113,0.1)", border: "1px solid rgba(248,113,113,0.3)", borderRadius: "4px", color: "#f87171", fontSize: "0.85rem" }}>
            {error}
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <Btn type="submit" disabled={loading}>
            {loading ? t("common.loading") : t("jobs.post")}
          </Btn>
        </div>
      </form>
    </DashShell>
  );
}
