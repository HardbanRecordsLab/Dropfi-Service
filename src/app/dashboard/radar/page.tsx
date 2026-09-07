"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading, Toast, inputStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { ExternalListing, ExternalTalent, RadarSource } from "@/lib/types";

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

  const [q, setQ] = useState("");
  const [source, setSource] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(false);

  // Plain closure function — recreated each render, so it always sees the
  // latest filter values. Not a hook and not in any dependency array.
  const load = async () => {
    const p = new URLSearchParams();
    if (q.trim()) p.set("q", q.trim());
    if (source) p.set("source", source);
    if (remoteOnly) p.set("remote", "true");
    const listParams = p.toString() ? `?${p.toString()}` : "";
    try {
      const [l, tl, s] = await Promise.all([
        API.radarListings(listParams) as Promise<ExternalListing[]>,
        API.radarTalent(source ? `?source=${source}` : "") as Promise<ExternalTalent[]>,
        API.radarSources() as Promise<RadarSource[]>,
      ]);
      setListings(l);
      setTalent(tl);
      setSources(s);
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
        const [l, tl, s] = await Promise.all([
          API.radarListings("") as Promise<ExternalListing[]>,
          API.radarTalent("") as Promise<ExternalTalent[]>,
          API.radarSources() as Promise<RadarSource[]>,
        ]);
        if (!active) return;
        setListings(l);
        setTalent(tl);
        setSources(s);
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
            <label style={{ display: "flex", alignItems: "center", gap: "0.4rem", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
              <input type="checkbox" checked={remoteOnly} onChange={(e) => setRemoteOnly(e.target.checked)} />
              {t("radar.filter.remote")}
            </label>
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
                  </div>
                </div>
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
