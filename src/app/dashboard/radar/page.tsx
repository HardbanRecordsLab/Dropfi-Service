"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading, StatCard, Toast, inputStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { ExternalListing, ExternalTalent, RadarSource, RadarStats } from "@/lib/types";

// RADAR_ALERT_MIN_SCORE on the backend defaults to 60 and isn't exposed via
// an endpoint; "only relevant" mirrors that default rather than reading the
// live setting.
const RELEVANT_SCORE_THRESHOLD = 60;

type Tab = "listings" | "talent" | "sources";

export default function RadarPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const isAdmin = user?.role === "admin";
  const canAct = user?.role === "admin" || user?.role === "client";

  const [tab, setTab] = useState<Tab>("listings");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const [listings, setListings] = useState<ExternalListing[]>([]);
  const [talent, setTalent] = useState<ExternalTalent[]>([]);
  const [sources, setSources] = useState<RadarSource[]>([]);
  const [stats, setStats] = useState<RadarStats | null>(null);

  const [q, setQ] = useState("");
  const [source, setSource] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [onlyRelevant, setOnlyRelevant] = useState(false);
  const [sortByScore, setSortByScore] = useState(false);

  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [offerDrafts, setOfferDrafts] = useState<Record<string, string>>({});
  const [wonAmounts, setWonAmounts] = useState<Record<string, string>>({});

  // Plain closure function — recreated each render, so it always sees the
  // latest filter values. Not a hook and not in any dependency array.
  const load = async () => {
    const p = new URLSearchParams();
    if (q.trim()) p.set("q", q.trim());
    if (source) p.set("source", source);
    if (remoteOnly) p.set("remote", "true");
    if (onlyRelevant) p.set("min_score", String(RELEVANT_SCORE_THRESHOLD));
    if (sortByScore) p.set("sort", "score");
    const listParams = p.toString() ? `?${p.toString()}` : "";
    try {
      const [l, tl, s, st] = await Promise.all([
        API.radarListings(listParams) as Promise<ExternalListing[]>,
        API.radarTalent(source ? `?source=${source}` : "") as Promise<ExternalTalent[]>,
        API.radarSources() as Promise<RadarSource[]>,
        API.radarStats() as Promise<RadarStats>,
      ]);
      setListings(l);
      setTalent(tl);
      setSources(s);
      setStats(st);
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      try {
        const [l, tl, s, st] = await Promise.all([
          API.radarListings("") as Promise<ExternalListing[]>,
          API.radarTalent("") as Promise<ExternalTalent[]>,
          API.radarSources() as Promise<RadarSource[]>,
          API.radarStats() as Promise<RadarStats>,
        ]);
        if (!active) return;
        setListings(l);
        setTalent(tl);
        setSources(s);
        setStats(st);
      } catch (err) {
        if (active) setMsg(getErrorMessage(err));
      } finally {
        if (active) setLoading(false);
      }
    })();
    return () => {
      active = false;
    };
  }, [user]);

  const scan = async (slug = "") => {
    setBusy(true);
    try {
      await API.radarScan(slug);
      setMsg(t("radar.scanQueued"));
      setTimeout(load, 1500);
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const act = async (fn: () => Promise<unknown>) => {
    setBusy(true);
    try {
      await fn();
      await load();
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const toggleDetails = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const generateOffer = async (id: string, regenerate: boolean) => {
    setBusy(true);
    try {
      const row = (await API.radarGenerateOffer(id, regenerate)) as ExternalListing;
      setListings((prev) => prev.map((l) => (l.id === id ? row : l)));
      setOfferDrafts((prev) => ({ ...prev, [id]: row.offer_text || "" }));
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const copyOffer = async (id: string, fallback: string) => {
    const text = offerDrafts[id] ?? fallback;
    try {
      await navigator.clipboard.writeText(text);
      setMsg(t("radar.offer.copied"));
    } catch (err) {
      setMsg(getErrorMessage(err));
    }
  };

  const updatePipeline = async (id: string, status: "applied" | "replied" | "won" | "lost") => {
    if (status === "won") {
      const amount = Number(wonAmounts[id]);
      if (!amount || amount <= 0) {
        setMsg(t("radar.pipeline.amountRequired"));
        return;
      }
      await act(() => API.radarUpdatePipeline(id, { status, amount_pln: amount }));
      return;
    }
    await act(() => API.radarUpdatePipeline(id, { status }));
  };

  if (loading) return <DashShell><Loading /></DashShell>;

  const tabBtn = (id: Tab, label: string) => (
    <button
      onClick={() => setTab(id)}
      style={{
        padding: "0.7rem 1.4rem",
        borderRadius: "4px",
        fontSize: "0.8rem",
        fontWeight: "700",
        textTransform: "uppercase",
        letterSpacing: "1px",
        background: tab === id ? "var(--accent-gold)" : "transparent",
        color: tab === id ? "#000" : "var(--text-secondary)",
        border: tab === id ? "none" : "1px solid var(--border-subtle)",
      }}
    >
      {label}
    </button>
  );

  return (
    <DashShell>
      <header style={{ marginBottom: "2rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          PORTAL RADAR
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("radar.title")}</h1>
        <p style={{ color: "var(--text-secondary)", fontWeight: "300", marginTop: "0.5rem", maxWidth: "680px" }}>{t("radar.subtitle")}</p>
      </header>

      {isAdmin && stats && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: "1.2rem", marginBottom: "2rem" }}>
          <StatCard icon="🎯" label={t("radar.stats.relevant24h")} value={stats.sales_agent.relevant_24h} />
          <StatCard icon="📈" label={t("radar.stats.relevant7d")} value={stats.sales_agent.relevant_7d} />
          <StatCard icon="✉️" label={t("radar.stats.sent")} value={stats.sales_agent.sent_total} />
          <StatCard icon="↩️" label={t("radar.stats.replyRate")} value={`${Math.round(stats.sales_agent.reply_rate * 100)}%`} />
          <StatCard icon="🏆" label={t("radar.stats.winRate")} value={`${Math.round(stats.sales_agent.win_rate * 100)}%`} />
          <StatCard icon="💰" label={t("radar.stats.wonTotal")} value={`${stats.sales_agent.won_total_pln.toLocaleString()} PLN`} />
        </div>
      )}

      <div style={{ display: "flex", gap: "0.6rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
        {tabBtn("listings", t("radar.tab.listings"))}
        {tabBtn("talent", t("radar.tab.talent"))}
        {tabBtn("sources", t("radar.tab.sources"))}
      </div>

      {tab !== "sources" && (
        <div style={{ display: "flex", gap: "0.8rem", marginBottom: "1.5rem", flexWrap: "wrap", alignItems: "center" }}>
          <input style={{ ...inputStyle, maxWidth: "260px" }} placeholder={t("radar.search")} value={q}
            onChange={(e) => setQ(e.target.value)} onKeyDown={(e) => e.key === "Enter" && load()} />
          <select style={{ ...inputStyle, maxWidth: "220px" }} value={source} onChange={(e) => setSource(e.target.value)}>
            <option value="">{t("radar.filter.source")}</option>
            {sources.map((s) => <option key={s.slug} value={s.slug}>{s.name}</option>)}
          </select>
          {tab === "listings" && (
            <>
              <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                <input type="checkbox" checked={remoteOnly} onChange={(e) => setRemoteOnly(e.target.checked)} />
                {t("radar.filter.remote")}
              </label>
              <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
                <input type="checkbox" checked={onlyRelevant} onChange={(e) => setOnlyRelevant(e.target.checked)} />
                {t("radar.filter.onlyRelevant")}
              </label>
              <select style={{ ...inputStyle, maxWidth: "180px" }} value={sortByScore ? "score" : "newest"}
                onChange={(e) => setSortByScore(e.target.value === "score")}>
                <option value="newest">{t("radar.sort.newest")}</option>
                <option value="score">{t("radar.sort.score")}</option>
              </select>
            </>
          )}
          <Btn variant="outline" onClick={() => load()} disabled={busy}>{t("radar.search")}</Btn>
        </div>
      )}

      {/* LISTINGS */}
      {tab === "listings" && (
        listings.length === 0 ? (
          <div className="premium-card" style={{ textAlign: "center", padding: "3rem" }}>
            <p style={{ color: "var(--text-secondary)" }}>{t("radar.none")}</p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
            {listings.map((l) => (
              <div key={l.id} className="premium-card" style={{ padding: "1.3rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem", flexWrap: "wrap" }}>
                  <div style={{ flex: 1, minWidth: "260px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap", marginBottom: "0.4rem" }}>
                      <Badge>{l.source}</Badge>
                      {l.is_remote && <Badge>remote</Badge>}
                      {l.status !== "new" && <Badge>{l.status === "imported" ? t("radar.imported") : t("radar.dismissed")}</Badge>}
                      {l.fit_score !== null && (
                        <Badge color={l.fit_score >= RELEVANT_SCORE_THRESHOLD ? "#4ade80" : "var(--accent-gold)"}>
                          {t("radar.score")}: {Math.round(l.fit_score)}
                        </Badge>
                      )}
                      {l.pipeline && (
                        <Badge color={l.pipeline === "won" ? "#4ade80" : l.pipeline === "lost" ? "#f87171" : "var(--accent-gold)"}>
                          {t(`radar.pipeline.${l.pipeline}`)}
                        </Badge>
                      )}
                    </div>
                    <div style={{ fontWeight: "700", fontSize: "1.02rem" }}>{l.title}</div>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginTop: "0.2rem" }}>
                      {[l.company, l.location, l.budget_text || (l.budget_max ? `${l.budget_min ?? "?"}–${l.budget_max} ${l.currency}` : "")].filter(Boolean).join(" · ")}
                    </div>
                    {l.description && (
                      <p style={{ fontSize: "0.82rem", color: "var(--text-secondary)", marginTop: "0.6rem", maxWidth: "760px" }}>
                        {l.description.slice(0, 260)}{l.description.length > 260 ? "…" : ""}
                      </p>
                    )}
                    {l.contact && <div style={{ fontSize: "0.78rem", color: "var(--accent-gold)", marginTop: "0.4rem" }}>{t("radar.contact")}: {l.contact}</div>}
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", alignItems: "flex-end" }}>
                    <a href={l.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: "0.78rem", color: "var(--accent-gold)" }}>{t("radar.open")} ↗</a>
                    {canAct && l.status === "new" && (
                      <>
                        <Btn onClick={() => act(() => API.radarImportListing(l.id))} disabled={busy}>{t("radar.import")}</Btn>
                        <Btn variant="ghost" onClick={() => act(() => API.radarDismissListing(l.id))} disabled={busy}>{t("radar.dismiss")}</Btn>
                      </>
                    )}
                    {isAdmin && (
                      <Btn variant="ghost" onClick={() => toggleDetails(l.id)} disabled={busy} style={{ padding: "0.5rem 1rem" }}>
                        {expanded[l.id] ? t("radar.hideDetails") : t("radar.details")}
                      </Btn>
                    )}
                  </div>
                </div>

                {isAdmin && expanded[l.id] && (
                  <div style={{ marginTop: "1.1rem", paddingTop: "1.1rem", borderTop: "1px solid var(--border-subtle)" }}>
                    {l.fit_reason && (
                      <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.8rem" }}>{l.fit_reason}</p>
                    )}

                    <div style={{ display: "flex", gap: "0.6rem", marginBottom: "0.8rem", flexWrap: "wrap" }}>
                      <Btn variant="outline" disabled={busy}
                        onClick={() => generateOffer(l.id, !!l.offer_text)}>
                        {l.offer_text ? t("radar.offer.regenerate") : t("radar.offer.generate")}
                      </Btn>
                      {l.offer_text && (
                        <Btn variant="ghost" disabled={busy} onClick={() => copyOffer(l.id, l.offer_text || "")}>
                          {t("radar.offer.copy")}
                        </Btn>
                      )}
                    </div>

                    {l.offer_text && (
                      <>
                        <textarea
                          value={offerDrafts[l.id] ?? l.offer_text}
                          onChange={(e) => setOfferDrafts((prev) => ({ ...prev, [l.id]: e.target.value }))}
                          style={{ ...inputStyle, minHeight: "140px", resize: "vertical", fontSize: "0.85rem", marginBottom: "0.8rem" }}
                        />
                        {(l.offer_price_min || l.offer_price_max) && (
                          <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "0.6rem" }}>
                            {t("radar.offer.priceRange")}: {l.offer_price_min ?? "?"}–{l.offer_price_max ?? "?"} PLN
                          </div>
                        )}
                        {l.offer_questions && l.offer_questions.length > 0 && (
                          <div style={{ marginBottom: "0.8rem" }}>
                            <div style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginBottom: "0.3rem" }}>{t("radar.offer.questions")}:</div>
                            <ul style={{ fontSize: "0.8rem", color: "var(--text-secondary)", paddingLeft: "1.2rem" }}>
                              {l.offer_questions.map((q2, i) => <li key={i}>{q2}</li>)}
                            </ul>
                          </div>
                        )}
                      </>
                    )}

                    <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap", alignItems: "center", marginTop: "0.6rem" }}>
                      <Btn variant="outline" disabled={busy} onClick={() => updatePipeline(l.id, "applied")} style={{ padding: "0.6rem 1.2rem" }}>{t("radar.pipeline.applied")}</Btn>
                      <Btn variant="outline" disabled={busy} onClick={() => updatePipeline(l.id, "replied")} style={{ padding: "0.6rem 1.2rem" }}>{t("radar.pipeline.replied")}</Btn>
                      <input
                        type="number"
                        placeholder={t("radar.pipeline.amountPlaceholder")}
                        value={wonAmounts[l.id] ?? ""}
                        onChange={(e) => setWonAmounts((prev) => ({ ...prev, [l.id]: e.target.value }))}
                        style={{ ...inputStyle, maxWidth: "140px", padding: "0.6rem 0.8rem" }}
                      />
                      <Btn variant="outline" disabled={busy} onClick={() => updatePipeline(l.id, "won")} style={{ padding: "0.6rem 1.2rem" }}>{t("radar.pipeline.won")}</Btn>
                      <Btn variant="ghost" disabled={busy} onClick={() => updatePipeline(l.id, "lost")} style={{ padding: "0.6rem 1.2rem" }}>{t("radar.pipeline.lost")}</Btn>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )
      )}

      {/* TALENT */}
      {tab === "talent" && (
        talent.length === 0 ? (
          <div className="premium-card" style={{ textAlign: "center", padding: "3rem" }}>
            <p style={{ color: "var(--text-secondary)" }}>{t("radar.none")}</p>
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: "1rem" }}>
            {talent.map((p) => (
              <div key={p.id} className="premium-card" style={{ padding: "1.2rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.4rem" }}>
                  <Badge>{p.source}</Badge>
                  {p.status !== "new" && <Badge>{p.status}</Badge>}
                </div>
                <div style={{ fontWeight: "700" }}>{p.name}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "0.3rem" }}>{p.headline}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.4rem" }}>
                  {[p.location, p.skills.slice(0, 4).join(", "), p.followers ? `★ ${p.followers}` : ""].filter(Boolean).join(" · ")}
                </div>
                <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.8rem", flexWrap: "wrap" }}>
                  <a href={p.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: "0.78rem", color: "var(--accent-gold)" }}>{t("radar.open")} ↗</a>
                  {canAct && (
                    <>
                      <Btn variant="ghost" onClick={() => act(() => API.radarSetTalentStatus(p.id, "contacted"))} disabled={busy} style={{ padding: "0.5rem 1rem" }}>{t("radar.talent.contacted")}</Btn>
                      <Btn variant="ghost" onClick={() => act(() => API.radarSetTalentStatus(p.id, "invited"))} disabled={busy} style={{ padding: "0.5rem 1rem" }}>{t("radar.talent.invited")}</Btn>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )
      )}

      {/* SOURCES */}
      {tab === "sources" && (
        <>
          {isAdmin && (
            <div style={{ marginBottom: "1.2rem" }}>
              <Btn onClick={() => scan("")} disabled={busy}>{t("radar.scanAll")}</Btn>
            </div>
          )}
          {!isAdmin && <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginBottom: "1rem" }}>{t("radar.adminOnly")}</p>}
          <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
            {sources.map((s) => (
              <div key={s.slug} className="premium-card" style={{ padding: "1.1rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.8rem" }}>
                <div>
                  <div style={{ fontWeight: "700" }}>
                    {s.name}{" "}
                    <Badge>{s.region}</Badge>{" "}
                    <Badge>{t(s.kind === "talent" ? "radar.kind.talent" : "radar.kind.listings")}</Badge>
                    {!s.enabled && <> <Badge>{s.requires_key ? t("radar.needsKey") : t("radar.disabled")}</Badge></>}
                  </div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
                    {s.access} · {t("radar.lastScan")}:{" "}
                    {s.last_scan_at ? new Date(s.last_scan_at).toLocaleString() : t("radar.status.never")}
                    {s.last_scan_ok === false && <span style={{ color: "#f87171" }}> · {t("radar.status.fail")}</span>}
                    {s.last_scan_ok === true && <span style={{ color: "#4ade80" }}> · {t("radar.status.ok")}</span>}
                    {" · "}{s.listings_count + s.talents_count} rec.
                  </div>
                  {s.last_scan_error && <div style={{ fontSize: "0.72rem", color: "#f87171", marginTop: "0.2rem" }}>{s.last_scan_error}</div>}
                </div>
                <div style={{ display: "flex", gap: "0.5rem" }}>
                  <a href={s.homepage} target="_blank" rel="noopener noreferrer" style={{ fontSize: "0.78rem", color: "var(--accent-gold)" }}>↗</a>
                  {isAdmin && s.enabled && (
                    <Btn variant="outline" onClick={() => scan(s.slug)} disabled={busy} style={{ padding: "0.5rem 1rem" }}>{t("radar.scanNow")}</Btn>
                  )}
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      <Toast message={msg} />
    </DashShell>
  );
}
