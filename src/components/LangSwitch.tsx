"use client";

import { useLang } from "@/lib/i18n";
import type { Lang } from "@/lib/i18n";

export default function LangSwitch() {
  const { lang, setLang } = useLang();
  const langs: { code: Lang; label: string }[] = [
    { code: "pl", label: "PL" },
    { code: "en", label: "EN" },
  ];
  return (
    <div
      style={{
        display: "flex",
        border: "1px solid var(--border-subtle)",
        borderRadius: "4px",
        overflow: "hidden",
      }}
    >
      {langs.map((l) => (
        <button
          key={l.code}
          onClick={() => setLang(l.code)}
          style={{
            padding: "0.5rem 0.9rem",
            fontSize: "0.75rem",
            fontWeight: "700",
            background: lang === l.code ? "var(--accent-gold)" : "transparent",
            color: lang === l.code ? "#000" : "var(--text-secondary)",
          }}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}
