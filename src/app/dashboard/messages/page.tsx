"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import DashShell from "@/components/DashShell";
import { Badge, Btn, Loading, inputStyle } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { useLang } from "@/lib/i18n";
import { API, getErrorMessage } from "@/lib/api";
import { Ico } from "@/components/Ico";

type Thread = {
  match_id: string;
  job_id: string;
  job_title: string;
  match_status: string;
  score: number;
  other_name: string;
  last_message: { body: string; mine: boolean; created_at: string } | null;
  unread: number;
};

type Msg = {
  id: string;
  mine: boolean;
  body: string;
  translated: string | null;
  flagged: boolean;
  flag_reasons: string[];
  created_at: string;
};

type ThreadDetail = {
  match_id: string;
  job_id: string;
  job_title: string;
  match_status: string;
  has_contract: boolean;
  messages: Msg[];
};

type Summary = { summary: string; decisions: string[]; open_questions: string[]; mentioned_prices: string[]; source: string };

const L = {
  pl: {
    title: "Wiadomości",
    empty: "Brak rozmów. Rozmowa pojawi się, gdy AI dopasuje zlecenie.",
    pick: "Wybierz rozmowę z listy.",
    placeholder: "Napisz wiadomość…",
    send: "Wyślij",
    translate: "Przetłumacz na polski",
    summary: "Streszczenie AI",
    suggest: "Podpowiedz odpowiedź",
    guard: "Dane kontaktowe są ukrywane do czasu podpisania kontraktu — płatności poza DROPIFY nie są chronione escrow.",
    flagged: "Ukryto dane kontaktowe / ostrzeżenie o płatności poza platformą",
    decisions: "Ustalenia",
    questions: "Otwarte pytania",
    prices: "Kwoty",
    noAi: "Tłumaczenie AI wymaga skonfigurowanego klucza LLM.",
    readonly: "Dopasowanie odrzucone — rozmowa tylko do odczytu.",
    job: "Zlecenie",
    error: "Nie udało się wczytać wiadomości",
  },
  en: {
    title: "Messages",
    empty: "No conversations yet. One appears when AI matches a job.",
    pick: "Pick a conversation.",
    placeholder: "Write a message…",
    send: "Send",
    translate: "Translate to English",
    summary: "AI summary",
    suggest: "Suggest a reply",
    guard: "Contact details stay hidden until a contract is signed — payments outside DROPIFY are not protected by escrow.",
    flagged: "Contact details hidden / off-platform payment warning",
    decisions: "Decisions",
    questions: "Open questions",
    prices: "Amounts",
    noAi: "AI translation needs an LLM key configured.",
    readonly: "Match rejected — this thread is read-only.",
    job: "Job",
    error: "Could not load messages",
  },
};

export default function MessagesPage() {
  const { user } = useAuth();
  const { lang } = useLang();
  const tx = L[lang];
  const [threads, setThreads] = useState<Thread[] | null>(null);
  const [active, setActive] = useState<string | null>(null);
  const [detail, setDetail] = useState<ThreadDetail | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [summary, setSummary] = useState<Summary | null>(null);
  const [replies, setReplies] = useState<string[]>([]);
  const bottom = useRef<HTMLDivElement>(null);

  const loadThreads = useCallback(async () => {
    try {
      setThreads((await API.messageThreads()) as Thread[]);
    } catch (err) {
      setError(getErrorMessage(err, tx.error));
      setThreads((t) => t ?? []);
    }
  }, [tx.error]);

  const loadDetail = useCallback(
    async (matchId: string) => {
      try {
        setDetail((await API.messageThread(matchId, lang)) as ThreadDetail);
      } catch (err) {
        setError(getErrorMessage(err, tx.error));
      }
    },
    [lang, tx.error]
  );

  useEffect(() => {
    if (!user) return;
    const initial = new URLSearchParams(window.location.search).get("m");
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time read of ?m= deep link
    if (initial) setActive(initial);
    loadThreads();
  }, [user, loadThreads]);

  // Poll the open thread and the thread list (lightweight, no websocket infra needed).
  useEffect(() => {
    if (!active) return;
    const first = window.setTimeout(() => loadDetail(active), 0);
    const id = window.setInterval(() => {
      loadDetail(active);
      loadThreads();
    }, 8000);
    return () => {
      window.clearTimeout(first);
      window.clearInterval(id);
    };
  }, [active, loadDetail, loadThreads]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [detail?.messages.length]);

  const open = (matchId: string) => {
    setActive(matchId);
    setDetail(null);
    setSummary(null);
    setReplies([]);
    setNotice("");
    setError("");
  };

  const send = async () => {
    if (!active || !draft.trim()) return;
    setBusy(true);
    setError("");
    try {
      const res = (await API.sendMessage(active, draft.trim())) as { warning?: string | null };
      setDraft("");
      setReplies([]);
      setNotice(res.warning || "");
      await Promise.all([loadDetail(active), loadThreads()]);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const translate = async () => {
    if (!active) return;
    setBusy(true);
    try {
      const res = (await API.translateThread(active, lang)) as { ai_available: boolean };
      if (!res.ai_available) setNotice(tx.noAi);
      await loadDetail(active);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const summarize = async () => {
    if (!active) return;
    setBusy(true);
    try {
      setSummary((await API.threadSummary(active, lang)) as Summary);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const suggest = async () => {
    if (!active) return;
    setBusy(true);
    try {
      setReplies((await API.suggestReplies(active, lang)).replies);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setBusy(false);
    }
  };

  const readOnly = detail?.match_status === "rejected";

  return (
    <DashShell>
      <h1 style={{ fontSize: "2rem", marginBottom: "1.5rem" }}>{tx.title}</h1>
      {threads === null ? (
        <Loading />
      ) : (
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1.5rem", alignItems: "flex-start" }}>
          <div className="premium-card" style={{ flex: "1 1 260px", maxWidth: 360, padding: 0, overflow: "hidden" }}>
            {threads.length === 0 && <p style={{ padding: "1.25rem", color: "var(--text-secondary)" }}>{tx.empty}</p>}
            {threads.map((t) => (
              <button
                key={t.match_id}
                onClick={() => open(t.match_id)}
                style={{
                  display: "block",
                  width: "100%",
                  textAlign: "left",
                  padding: "1rem 1.25rem",
                  background: active === t.match_id ? "rgba(255,255,255,0.05)" : "transparent",
                  border: "none",
                  borderBottom: "1px solid var(--border-subtle)",
                  color: "inherit",
                  cursor: "pointer",
                  fontFamily: "inherit",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", gap: "0.5rem" }}>
                  <strong style={{ fontSize: "0.95rem" }}>{t.other_name || "—"}</strong>
                  {t.unread > 0 && <Badge>{t.unread}</Badge>}
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--accent-gold)", margin: "0.2rem 0" }}>{t.job_title}</div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {t.last_message ? `${t.last_message.mine ? "↩ " : ""}${t.last_message.body}` : `${Math.round(t.score)}% match · ${t.match_status}`}
                </div>
              </button>
            ))}
          </div>

          <div className="premium-card" style={{ flex: "3 1 340px", minWidth: 0, padding: "1.5rem" }}>
            {!active ? (
              <p style={{ color: "var(--text-secondary)" }}>{tx.pick}</p>
            ) : !detail ? (
              <Loading />
            ) : (
              <>
                <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem", marginBottom: "1rem" }}>
                  <div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>{tx.job}</div>
                    <Link href={`/dashboard/jobs/${detail.job_id}`} style={{ fontWeight: 700 }}>{detail.job_title}</Link>
                  </div>
                  <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
                    <Btn variant="outline" disabled={busy} onClick={translate} style={{ padding: "0.5rem 0.9rem" }}>{tx.translate}</Btn>
                    <Btn variant="outline" disabled={busy || detail.messages.length === 0} onClick={summarize} style={{ padding: "0.5rem 0.9rem" }}>{tx.summary}</Btn>
                  </div>
                </div>

                {!detail.has_contract && (
                  <p style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginBottom: "1rem" }}><Ico e="🛡️" /> {tx.guard}</p>
                )}

                {summary && (
                  <div style={{ border: "1px solid var(--border-gold)", borderRadius: 4, padding: "1rem", marginBottom: "1rem", fontSize: "0.9rem" }}>
                    <p>{summary.summary}</p>
                    {[[tx.decisions, summary.decisions], [tx.questions, summary.open_questions], [tx.prices, summary.mentioned_prices]].map(
                      ([label, items]) =>
                        (items as string[]).length > 0 && (
                          <div key={label as string} style={{ marginTop: "0.5rem" }}>
                            <strong>{label as string}:</strong>
                            <ul style={{ margin: "0.25rem 0 0 1.2rem" }}>
                              {(items as string[]).map((x, i) => <li key={i}>{x}</li>)}
                            </ul>
                          </div>
                        )
                    )}
                  </div>
                )}

                <div style={{ maxHeight: "55vh", overflowY: "auto", display: "flex", flexDirection: "column", gap: "0.6rem", paddingRight: "0.25rem" }}>
                  {detail.messages.map((m) => (
                    <div key={m.id} style={{ alignSelf: m.mine ? "flex-end" : "flex-start", maxWidth: "80%" }}>
                      <div
                        style={{
                          background: m.mine ? "var(--accent-gold)" : "var(--bg-tertiary)",
                          color: m.mine ? "#000" : "var(--text-primary)",
                          padding: "0.6rem 0.9rem",
                          borderRadius: 8,
                          whiteSpace: "pre-wrap",
                          overflowWrap: "anywhere",
                          fontSize: "0.92rem",
                        }}
                      >
                        {m.translated && !m.mine ? m.translated : m.body}
                      </div>
                      <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", marginTop: 2, textAlign: m.mine ? "right" : "left" }}>
                        {new Date(m.created_at).toLocaleString(lang === "pl" ? "pl-PL" : "en-GB", { dateStyle: "short", timeStyle: "short" })}
                        {m.flagged && ` · ${tx.flagged}`}
                        {m.translated && !m.mine && " · AI"}
                      </div>
                    </div>
                  ))}
                  <div ref={bottom} />
                </div>

                {readOnly ? (
                  <p style={{ marginTop: "1rem", color: "var(--text-secondary)" }}>{tx.readonly}</p>
                ) : (
                  <div style={{ marginTop: "1rem" }}>
                    {replies.length > 0 && (
                      <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.6rem" }}>
                        {replies.map((r, i) => (
                          <button
                            key={i}
                            onClick={() => setDraft(r)}
                            style={{ fontSize: "0.8rem", padding: "0.4rem 0.7rem", borderRadius: 14, border: "1px solid var(--border-gold)", background: "transparent", color: "var(--accent-gold)", cursor: "pointer", fontFamily: "inherit", textAlign: "left" }}
                          >
                            {r}
                          </button>
                        ))}
                      </div>
                    )}
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) send();
                      }}
                      placeholder={tx.placeholder}
                      maxLength={4000}
                      rows={3}
                      style={{ ...inputStyle, resize: "vertical" }}
                    />
                    <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem", flexWrap: "wrap" }}>
                      <Btn disabled={busy || !draft.trim()} onClick={send}>{tx.send}</Btn>
                      <Btn variant="ghost" disabled={busy} onClick={suggest}><Ico e="✨" /> {tx.suggest}</Btn>
                    </div>
                  </div>
                )}
              </>
            )}
            {notice && <p style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "var(--accent-gold)" }}>{notice}</p>}
            {error && <p style={{ marginTop: "0.75rem", fontSize: "0.85rem", color: "#f87171" }}>{error}</p>}
          </div>
        </div>
      )}
    </DashShell>
  );
}
