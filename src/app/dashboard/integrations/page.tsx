"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading, inputStyle, labelStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { StoreConnection } from "@/lib/types";

export default function IntegrationsPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const [connections, setConnections] = useState<StoreConnection[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const [shopDomain, setShopDomain] = useState("");
  const [shopToken, setShopToken] = useState("");
  const [shopSecret, setShopSecret] = useState("");

  const [blToken, setBlToken] = useState("");
  const [blLabel, setBlLabel] = useState("");

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      const items = (await API.myStoreConnections().catch(() => [])) as StoreConnection[];
      if (active) setConnections(items);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, [user]);

  const reload = async () => setConnections((await API.myStoreConnections()) as StoreConnection[]);

  const connectShopify = async () => {
    if (!shopDomain.trim() || !shopToken.trim()) return;
    setBusy(true);
    try {
      await API.connectShopify({ shop_domain: shopDomain, access_token: shopToken, webhook_secret: shopSecret });
      setShopDomain("");
      setShopToken("");
      setShopSecret("");
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const connectBaselinker = async () => {
    if (!blToken.trim()) return;
    setBusy(true);
    try {
      await API.connectBaselinker({ access_token: blToken, label: blLabel || "BaseLinker account" });
      setBlToken("");
      setBlLabel("");
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const sync = async (id: string) => {
    setBusy(true);
    try {
      const res = (await API.syncBaselinker(id)) as { orders_synced: number };
      setMsg(`${t("int.sync")}: ${res.orders_synced}`);
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const disconnect = async (id: string) => {
    setBusy(true);
    try {
      await API.disconnectStore(id);
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

  if (loading) return <DashShell><Loading /></DashShell>;

  return (
    <DashShell>
      <header style={{ marginBottom: "2.5rem" }}>
        <div style={{ color: "var(--accent-gold)", fontSize: "0.8rem", fontWeight: "700", letterSpacing: "3px", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          SPRINT 4 · #9-#11
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("int.title")}</h1>
        <p style={{ color: "var(--text-secondary)", fontWeight: "300", marginTop: "0.5rem", maxWidth: "640px" }}>{t("int.subtitle")}</p>
      </header>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
        <div className="premium-card">
          <h3 style={{ fontSize: "1.1rem", fontFamily: "var(--font-playfair)", marginBottom: "1rem" }}>🛍️ {t("int.shopify")}</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label style={labelStyle}>{t("int.shopDomain")}</label>
              <input style={inputStyle} value={shopDomain} onChange={(e) => setShopDomain(e.target.value)} placeholder="my-store.myshopify.com" />
            </div>
            <div>
              <label style={labelStyle}>{t("int.accessToken")}</label>
              <input style={inputStyle} type="password" value={shopToken} onChange={(e) => setShopToken(e.target.value)} placeholder="shpat_..." />
            </div>
            <div>
              <label style={labelStyle}>{t("int.webhookSecret")}</label>
              <input style={inputStyle} type="password" value={shopSecret} onChange={(e) => setShopSecret(e.target.value)} />
            </div>
            <Btn onClick={connectShopify} disabled={busy}>{t("int.connect")}</Btn>
          </div>
        </div>

        <div className="premium-card">
          <h3 style={{ fontSize: "1.1rem", fontFamily: "var(--font-playfair)", marginBottom: "1rem" }}>📦 {t("int.baselinker")}</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            <div>
              <label style={labelStyle}>{t("int.label")}</label>
              <input style={inputStyle} value={blLabel} onChange={(e) => setBlLabel(e.target.value)} placeholder="My BaseLinker" />
            </div>
            <div>
              <label style={labelStyle}>{t("int.accessToken")}</label>
              <input style={inputStyle} type="password" value={blToken} onChange={(e) => setBlToken(e.target.value)} />
            </div>
            <Btn onClick={connectBaselinker} disabled={busy}>{t("int.connect")}</Btn>
          </div>
        </div>
      </div>

      <h2 style={{ fontSize: "1.3rem", fontFamily: "var(--font-playfair)", marginBottom: "1.2rem" }}>{t("int.connected")}</h2>
      {connections.length === 0 ? (
        <div className="premium-card" style={{ textAlign: "center", padding: "3rem" }}>
          <p style={{ color: "var(--text-secondary)" }}>{t("int.none")}</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
          {connections.map((c) => (
            <div key={c.id} className="premium-card" style={{ padding: "1.2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.8rem" }}>
              <div>
                <div style={{ fontWeight: "700" }}>
                  <Badge>{c.platform}</Badge> {c.label}
                </div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
                  {t("int.lastSynced")}: {c.last_synced_at ? new Date(c.last_synced_at).toLocaleString() : t("int.never")}
                </div>
                {c.platform === "shopify" && (
                  <div style={{ fontSize: "0.72rem", color: "var(--text-muted)", marginTop: "0.3rem" }}>
                    {t("int.webhookUrl")}: <code>{apiBase}/integrations/shopify/webhook/{c.id}</code>
                  </div>
                )}
              </div>
              <div style={{ display: "flex", gap: "0.6rem" }}>
                {c.platform === "baselinker" && (
                  <Btn variant="outline" onClick={() => sync(c.id)} disabled={busy}>{t("int.sync")}</Btn>
                )}
                <Btn variant="danger" onClick={() => disconnect(c.id)} disabled={busy}>{t("int.disconnect")}</Btn>
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
