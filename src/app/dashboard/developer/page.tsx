"use client";

import { useEffect, useState } from "react";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading, inputStyle, labelStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import type { ApiKeyItem, NewApiKey } from "@/lib/types";

export default function DeveloperPage() {
  const { user } = useAuth();
  const { t } = useLang();
  const [keys, setKeys] = useState<ApiKeyItem[]>([]);
  const [name, setName] = useState("");
  const [brandName, setBrandName] = useState("");
  const [newKey, setNewKey] = useState<NewApiKey | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!user) return;
    let active = true;
    (async () => {
      const items = (await API.listApiKeys().catch(() => [])) as ApiKeyItem[];
      if (active) setKeys(items);
      setLoading(false);
    })();
    return () => {
      active = false;
    };
  }, [user]);

  const reload = async () => setKeys((await API.listApiKeys()) as ApiKeyItem[]);

  const create = async () => {
    setBusy(true);
    try {
      const res = (await API.createApiKey(name || "API key", brandName)) as NewApiKey;
      setNewKey(res);
      setName("");
      setBrandName("");
      await reload();
    } catch (err) {
      setMsg(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const revoke = async (id: string) => {
    setBusy(true);
    try {
      await API.revokeApiKey(id);
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
          WHITE-LABEL · #F8
        </div>
        <h1 style={{ fontSize: "2.4rem", fontFamily: "var(--font-playfair)" }}>{t("dev.title")}</h1>
        <p style={{ color: "var(--text-secondary)", fontWeight: "300", marginTop: "0.5rem", maxWidth: "640px" }}>{t("dev.subtitle")}</p>
      </header>

      <div className="premium-card" style={{ marginBottom: "2rem" }}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1.2rem", marginBottom: "1.2rem" }}>
          <div>
            <label style={labelStyle}>{t("dev.keyName")}</label>
            <input style={inputStyle} value={name} onChange={(e) => setName(e.target.value)} placeholder="Production key" />
          </div>
          <div>
            <label style={labelStyle}>{t("dev.brandName")}</label>
            <input style={inputStyle} value={brandName} onChange={(e) => setBrandName(e.target.value)} placeholder="My Agency" />
          </div>
        </div>
        <Btn onClick={create} disabled={busy}>{t("dev.createKey")}</Btn>

        {newKey && (
          <div style={{ marginTop: "1.5rem", padding: "1.2rem", background: "rgba(197,160,89,0.06)", border: "1px dashed var(--border-gold)", borderRadius: "4px" }}>
            <div style={{ fontSize: "0.78rem", color: "var(--accent-gold)", fontWeight: "700", marginBottom: "0.5rem" }}>⚠️ {t("dev.newKeyWarning")}</div>
            <code style={{ display: "block", wordBreak: "break-all", fontSize: "0.85rem", color: "#fff", background: "var(--bg-tertiary)", padding: "0.8rem", borderRadius: "4px" }}>
              {newKey.key}
            </code>
          </div>
        )}
      </div>

      <div className="premium-card" style={{ marginBottom: "2rem" }}>
        <div style={{ fontSize: "0.75rem", fontWeight: "800", letterSpacing: "1px", color: "var(--text-muted)", textTransform: "uppercase", marginBottom: "0.6rem" }}>
          {t("dev.endpoint")}
        </div>
        <code style={{ display: "block", fontSize: "0.82rem", color: "var(--text-secondary)", wordBreak: "break-all" }}>
          POST {apiBase}/v1/external/jobs
        </code>
        <code style={{ display: "block", fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
          Header: X-Api-Key: dpk_… · Body: {"{"} title, description, budget, deadline, location, required_skills[] {"}"}
        </code>
      </div>

      <h2 style={{ fontSize: "1.3rem", fontFamily: "var(--font-playfair)", marginBottom: "1.2rem" }}>{t("dev.yourKeys")}</h2>
      {keys.length === 0 ? (
        <div className="premium-card" style={{ textAlign: "center", padding: "3rem" }}>
          <p style={{ color: "var(--text-secondary)" }}>{t("dev.noKeys")}</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: "0.8rem" }}>
          {keys.map((k) => (
            <div key={k.id} className="premium-card" style={{ padding: "1.2rem", display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "0.8rem" }}>
              <div>
                <div style={{ fontWeight: "700" }}>{k.name} {k.brand_name && `· ${k.brand_name}`}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                  {k.prefix}… · {k.request_count} {t("dev.requests")}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.8rem" }}>
                <Badge color={k.active ? "#4ade80" : "#f87171"}>{k.active ? "active" : "revoked"}</Badge>
                {k.active && (
                  <Btn variant="outline" onClick={() => revoke(k.id)} disabled={busy}>{t("dev.revoke")}</Btn>
                )}
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
