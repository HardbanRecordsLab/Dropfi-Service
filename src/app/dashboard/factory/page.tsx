"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading, inputStyle, labelStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { ListingContent, ListingHistoryItem, VideoScript } from "@/lib/types";

const MARKETPLACES = ["generic", "shopify", "woocommerce", "allegro"];

export default function FactoryPage() {
  const { user } = useAuth();
  const { t, lang } = useLang();

  const [productName, setProductName] = useState("");
  const [description, setDescription] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [marketplace, setMarketplace] = useState("generic");

  const [listing, setListing] = useState<ListingContent | null>(null);
  const [videoScript, setVideoScript] = useState<VideoScript | null>(null);
  const [history, setHistory] = useState<ListingHistoryItem[]>([]);
  const [busyListing, setBusyListing] = useState(false);
  const [busyVideo, setBusyVideo] = useState(false);
  const [msg, setMsg] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      const items = (await API.listingHistory().catch(() => [])) as ListingHistoryItem[];
      if (active) setHistory(items);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, [user]);

  const generateListing = async () => {
    if (!productName.trim()) {
      setMsg(lang === "pl" ? "Podaj nazwę produktu" : "Enter a product name");
      return;
    }
    setBusyListing(true);
    try {
      const res = (await API.generateListing({
        product_name: productName,
        description,
        source_url: sourceUrl,
        language: lang,
        marketplace,
      })) as { id: string; content: ListingContent };
      setListing(res.content);
      const items = (await API.listingHistory().catch(() => [])) as ListingHistoryItem[];
      setHistory(items);
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusyListing(false);
    }
  };

  const generateVideo = async () => {
    if (!productName.trim()) {
      setMsg(lang === "pl" ? "Podaj nazwę produktu" : "Enter a product name");
      return;
    }
    setBusyVideo(true);
    try {
      const res = (await API.generateVideoScript({ product_name: productName, description, language: lang })) as VideoScript;
      setVideoScript(res);
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusyVideo(false);
    }
  };

  if (loading) return <DashShell><Loading /></DashShell>;

  return (
    <DashShell>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          AI FACTORY · #F1 + #F6
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("factory.title")}</h1>
        <p style={{ color: "var(--text-secondary)", fontWeight: "300", marginTop: "0.5rem", maxWidth: "640px" }}>{t("factory.subtitle")}</p>
      </header>

      <div className="premium-card" style={{ marginBottom: "2rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1.2rem" }}>
          <div>
            <label style={labelStyle}>{t("factory.productName")}</label>
            <input style={inputStyle} value={productName} onChange={(e) => setProductName(e.target.value)} placeholder="e.g. Wireless earbuds X200" />
          </div>
          <div>
            <label style={labelStyle}>{t("factory.marketplace")}</label>
            <select style={inputStyle} value={marketplace} onChange={(e) => setMarketplace(e.target.value)}>
              {MARKETPLACES.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </div>
        </div>
        <div style={{ marginTop: "1.2rem" }}>
          <label style={labelStyle}>{t("factory.sourceUrl")}</label>
          <input style={inputStyle} value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} placeholder="https://…" />
        </div>
        <div style={{ marginTop: "1.2rem" }}>
          <label style={labelStyle}>{t("factory.description")}</label>
          <textarea style={{ ...inputStyle, resize: "vertical", minHeight: "80px" }} value={description} onChange={(e) => setDescription(e.target.value)} />
        </div>
        <div style={{ marginTop: "1.5rem", display: "flex", gap: "1rem", flexWrap: "wrap" }}>
          <Btn onClick={generateListing} disabled={busyListing}>{busyListing ? t("common.loading") : t("factory.generateListing")}</Btn>
          <Btn variant="outline" onClick={generateVideo} disabled={busyVideo}>{busyVideo ? t("common.loading") : t("factory.generateVideo")}</Btn>
        </div>
      </div>

      {listing && (
        <div className="premium-card" style={{ marginBottom: "2rem", border: "1px dashed var(--border-gold)" }}>
          <div style={{ fontSize: "0.75rem", fontWeight: "800", letterSpacing: "2px", color: "var(--accent-gold)", marginBottom: "1rem" }}>
            🤖 {listing.model === "claude" ? "CLAUDE" : "RULES"}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("factory.listingTitle")}</div>
          <div style={{ fontSize: "1.3rem", fontWeight: "800", marginBottom: "1rem" }}>{listing.title}</div>
          <p style={{ color: "var(--text-secondary)", fontWeight: "300", marginBottom: "1rem" }}>{listing.description}</p>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.5rem" }}>{t("factory.bullets")}</div>
          <ul style={{ marginBottom: "1rem", paddingLeft: "1.2rem", color: "var(--text-secondary)" }}>
            {(listing.bullet_points || []).map((b, i) => <li key={i}>{b}</li>)}
          </ul>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px", marginBottom: "0.5rem" }}>{t("factory.seoTags")}</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: "0.4rem", marginBottom: "1rem" }}>
            {(listing.seo_tags || []).map((s, i) => <Badge key={i}>{s}</Badge>)}
          </div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("factory.meta")}</div>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>{listing.meta_description}</p>
        </div>
      )}

      {videoScript && (
        <div className="premium-card" style={{ marginBottom: "2rem" }}>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("factory.videoHook")}</div>
          <div style={{ fontSize: "1.1rem", fontWeight: "700", marginBottom: "1rem" }}>{videoScript.hook}</div>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("factory.videoScript")}</div>
          <p style={{ color: "var(--text-secondary)", fontWeight: "300", marginBottom: "1rem", whiteSpace: "pre-wrap" }}>{videoScript.script}</p>
          <div style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "1px" }}>{t("factory.videoCta")}</div>
          <div style={{ fontWeight: "700" }} className="gold-gradient-text">{videoScript.cta}</div>
        </div>
      )}

      <h2 style={{ fontSize: "1.3rem", fontFamily: "var(--font-playfair)", marginBottom: "1.2rem" }}>{t("factory.history")}</h2>
      {history.length === 0 ? (
        <div className="premium-card" style={{ textAlign: "center", padding: "3rem" }}>
          <p style={{ color: "var(--text-secondary)" }}>{t("factory.empty")}</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
          {history.map((h) => (
            <div key={h.id} className="premium-card" style={{ padding: "1.2rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.5rem" }}>
                <div>
                  <div style={{ fontWeight: "700" }}>{h.content?.title || h.product_name}</div>
                  <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>{h.marketplace} · {h.language}</div>
                </div>
                <Badge>{new Date(h.created_at).toLocaleDateString()}</Badge>
              </div>
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
