// Wybór języka wspólny dla ekosystemu HRL: ?lang= w adresie > ciasteczko hrl_lang (wspólne dla *.hardbanrecordslab.online) > localStorage > angielski.
export type Lang = "en" | "pl";

export function isLang(v: unknown): v is Lang {
  return v === "en" || v === "pl";
}

export function readLangCookie(): Lang | null {
  try {
    const m = document.cookie.match(/(?:^|;\s*)hrl_lang=(en|pl)\b/);
    return m ? (m[1] as Lang) : null;
  } catch {
    return null;
  }
}

export function writeLangCookie(lang: Lang): void {
  try {
    const shared = /(^|\.)hardbanrecordslab\.online$/.test(window.location.hostname) ? ";domain=.hardbanrecordslab.online" : "";
    document.cookie = `hrl_lang=${lang};path=/;max-age=31536000;SameSite=Lax${shared}`;
  } catch {
    /* ciasteczka zablokowane — wybór i tak zostaje w localStorage */
  }
}

/** Wywoływane tylko w przeglądarce (useEffect). */
export function resolveInitialLang(storageKey: string): Lang {
  try {
    const q = new URLSearchParams(window.location.search).get("lang");
    if (isLang(q)) {
      try {
        localStorage.setItem(storageKey, q);
      } catch {
        /* ignore */
      }
      writeLangCookie(q);
      return q;
    }
  } catch {
    /* brak window.location */
  }
  const fromCookie = readLangCookie();
  if (fromCookie) return fromCookie;
  try {
    const stored = localStorage.getItem(storageKey);
    if (isLang(stored)) return stored;
  } catch {
    /* ignore */
  }
  return "en";
}

/** Adres strony WordPressa w wybranym języku (wersja polska pod /pl/). */
export function wpUrl(path: string, lang: string): string {
  const p = path.startsWith("/") ? path : `/${path}`;
  return `https://hardbanrecordslab.online${lang === "pl" ? "/pl" : ""}${p}`;
}
