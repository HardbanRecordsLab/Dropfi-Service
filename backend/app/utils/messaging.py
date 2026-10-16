"""Client <-> freelancer chat helpers.

What makes this better than a plain inbox (Upwork/Fiverr):
- **Fee-leak + scam guard** — emails, phone numbers, messenger handles and IBANs
  are masked until a contract exists; "pay me outside the platform" phrases are
  flagged. Off-platform deals are the #1 way marketplaces lose revenue and the
  #1 way clients get scammed.
- **AI translation** — a Polish client and an English freelancer each read the
  thread in their own language (cached per message).
- **AI thread summary + reply suggestions** — decisions, open questions,
  agreed prices/dates in one glance.

Every AI helper returns a rule-based fallback when no LLM key is configured.
"""
from __future__ import annotations

import re

from app.utils.ai import _claude_text, _llm_json, _looks_polish

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
# 9+ digits allowing separators — long enough to skip budgets ("4000 PLN") and dates.
_PHONE_RE = re.compile(r"(?<![\w])\+?\d(?:[\s\-().]?\d){8,}(?![\w])")
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}\b")
_MESSENGER_RE = re.compile(
    r"(?:https?://)?(?:wa\.me|t\.me|telegram\.me|discord\.gg|m\.me)/\S+"
    r"|\b(?:whatsapp|telegram|skype|signal|viber|discord|wechat)\s*[:@]?\s*[@\w.+-]{3,}",
    re.IGNORECASE,
)
_OFF_PLATFORM_RE = re.compile(
    r"\b(?:pay(?:ment)?\s+(?:me\s+)?(?:directly|outside|off[- ]platform|via\s+(?:paypal|revolut|wise|crypto|blik))"
    r"|outside\s+(?:of\s+)?(?:the\s+)?(?:platform|dropify)"
    r"|poza\s+(?:platform\w*|dropify)"
    r"|bezpo[sś]rednio\s+(?:na\s+konto|przelew\w*)"
    r"|zap[lł]a[cć]\s+(?:mi\s+)?(?:bezpo[sś]rednio|blikiem|na\s+revolut\w*|przez\s+paypal\w*)"
    r"|omin\w*\s+prowizj\w*|bez\s+prowizji|avoid\s+(?:the\s+)?fees?)",
    re.IGNORECASE,
)

MASK = "[ukryte do czasu kontraktu / hidden until contract]"


def scan_message(body: str, mask: bool) -> tuple[str, list[str]]:
    """Return (possibly masked body, flag reasons)."""
    reasons: list[str] = []
    out = body
    for reason, rx in (
        ("email", _EMAIL_RE),
        ("messenger", _MESSENGER_RE),
        ("bank_account", _IBAN_RE),
        ("phone", _PHONE_RE),
    ):
        if rx.search(out):
            reasons.append(reason)
            if mask:
                out = rx.sub(MASK, out)
    if _OFF_PLATFORM_RE.search(body):
        reasons.append("off_platform_payment")
    return out, reasons


def detect_language(text: str) -> str:
    return "pl" if _looks_polish(text) else "en"


def translate_text(text: str, target_lang: str) -> str | None:
    """AI translation; None when no LLM is configured or source is already in target."""
    target_lang = "pl" if target_lang == "pl" else "en"
    if detect_language(text) == target_lang:
        return text
    lang_name = "Polish" if target_lang == "pl" else "English"
    return _claude_text(
        f"Translate the following chat message into {lang_name}. Keep the tone, numbers, "
        "names and formatting. Output ONLY the translation.\n\n" + text[:2000],
        max_tokens=600,
    )


_PRICE_RE = re.compile(r"\b\d[\d\s.,]*\s?(?:pln|zł|zl|eur|€|usd|\$)", re.IGNORECASE)
_DATE_RE = re.compile(r"\b\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?\b|\b\d{4}-\d{2}-\d{2}\b")


def summarize_thread(job_title: str, lines: list[tuple[str, str]], language: str) -> dict:
    """lines = [(role, body)] oldest first. Returns {summary, decisions, open_questions, mentioned_prices, source}."""
    transcript = "\n".join(f"{role}: {body}" for role, body in lines[-60:])
    lang_name = "Polish" if language == "pl" else "English"
    data = _llm_json(
        f"Summarize this client/freelancer chat about the job \"{job_title}\" in {lang_name}. "
        'Return ONLY JSON: {"summary": "2-3 sentences", "decisions": ["..."], '
        '"open_questions": ["..."], "mentioned_prices": ["..."]}\n\n' + transcript[:6000],
        max_tokens=700,
    )
    if isinstance(data, dict) and data.get("summary"):
        return {
            "summary": str(data.get("summary", "")),
            "decisions": [str(x) for x in data.get("decisions", [])][:10],
            "open_questions": [str(x) for x in data.get("open_questions", [])][:10],
            "mentioned_prices": [str(x) for x in data.get("mentioned_prices", [])][:10],
            "source": "ai",
        }

    questions = [b.strip() for _, b in lines if "?" in b][-5:]
    prices = sorted({m.group(0).strip() for _, b in lines for m in _PRICE_RE.finditer(b)})[:10]
    dates = sorted({m.group(0) for _, b in lines for m in _DATE_RE.finditer(b)})[:10]
    if language == "pl":
        summary = f"Wątek „{job_title}”: {len(lines)} wiadomości."
        if dates:
            summary += f" Wspomniane terminy: {', '.join(dates)}."
    else:
        summary = f"Thread \"{job_title}\": {len(lines)} messages."
        if dates:
            summary += f" Dates mentioned: {', '.join(dates)}."
    return {
        "summary": summary,
        "decisions": [],
        "open_questions": questions,
        "mentioned_prices": prices,
        "source": "rules",
    }


def suggest_replies(job_title: str, role: str, lines: list[tuple[str, str]], language: str) -> list[str]:
    """Three short reply drafts for `role` (client|freelancer)."""
    transcript = "\n".join(f"{r}: {b}" for r, b in lines[-15:])
    lang_name = "Polish" if language == "pl" else "English"
    data = _llm_json(
        f"You help the {role} reply in a freelance job chat about \"{job_title}\". "
        f"Write 3 short, professional reply options in {lang_name} (max 35 words each). "
        "Never suggest sharing contact details or paying outside the platform. "
        'Return ONLY JSON: {"replies": ["...", "...", "..."]}\n\n' + transcript[:3000],
        max_tokens=400,
    )
    if isinstance(data, dict) and isinstance(data.get("replies"), list) and data["replies"]:
        return [str(r) for r in data["replies"]][:3]

    last = lines[-1][1] if lines else ""
    asked = "?" in last
    if language == "pl":
        base = ["Dziękuję, potwierdzam — działamy zgodnie z ustaleniami.",
                "Czy możemy doprecyzować zakres i termin pierwszego etapu?"]
        if asked:
            base.insert(0, "Dobre pytanie — odpowiem szczegółowo jeszcze dziś.")
        elif role == "freelancer":
            base.insert(0, "Zaczynam pracę, pierwszy podgląd wyślę w ramach pierwszego etapu.")
        else:
            base.insert(0, "Świetnie, czekam na pierwszy podgląd.")
    else:
        base = ["Thanks, confirmed — let's proceed as agreed.",
                "Could we clarify the scope and the deadline of the first milestone?"]
        if asked:
            base.insert(0, "Good question — I'll answer in detail later today.")
        elif role == "freelancer":
            base.insert(0, "Starting now, I'll share a first preview with milestone one.")
        else:
            base.insert(0, "Great, looking forward to the first preview.")
    return base[:3]
