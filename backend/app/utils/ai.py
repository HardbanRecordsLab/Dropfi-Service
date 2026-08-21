"""AI engine: job analysis (Claude with rule-based fallback) and embeddings (OpenAI with local fallback)."""
import hashlib
import json
import logging
import math
import re

from sqlalchemy import text

from app.config import settings

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Photography", "Coding", "Design", "Writing", "Marketing",
    "Video & Animation", "E-commerce", "Translation", "Consulting",
    # Tier-2 verticals (doku/MEGA_PLATFORM_BLUEPRINT.md §11) — same matching/escrow/
    # AI-QA engine, just recognized categories/skills, so they route correctly
    # instead of falling through to "Other".
    "Real Estate", "Audio & Podcast", "Publishing", "Events", "Music Production",
    "Data & AI Services", "Other",
]

CATEGORY_KEYWORDS = {
    "Photography": ["photo", "foto", "fotograf", "zdjęc", "zdjec", "product shoot", "retouch", "retusz"],
    "Coding": ["code", "developer", "program", "kod", "programista", "api", "app", "script", "software", "frontend", "backend", "wordpress", "game dev", "unity", "unreal"],
    "Design": ["design", "logo", "graphic", "ui", "ux", "projekt", "grafika", "banner", "figma", "fashion", "moda", "wzornictwo"],
    "Writing": ["write", "writing", "content", "copy", "text", "blog", "artykuł", "artykul", "copywriting", "translation", "tlumacz", "tłumacz"],
    "Marketing": ["marketing", "seo", "ads", "campaign", "social media", "reklama", "kampania", "influencer", "email marketing", "ugc"],
    "Video & Animation": ["video", "film", "animation", "animacj", "youtube", "motion", "editing", "montaż", "montaz", "3d"],
    "E-commerce": ["e-commerce", "ecommerce", "shopify", "woocommerce", "dropshipping", "allegro", "amazon", "sklep"],
    "Translation": ["translate", "tlumaczenie", "tłumaczenie", "translator", "language", "przekład"],
    "Consulting": ["consult", "doradztwo", "strateg", "audyt", "audit", "analiza", "growth", "konsultacj"],
    "Real Estate": ["real estate", "nieruchomo", "property listing", "virtual staging", "mieszkanie na sprzedaż", "dom na sprzedaż", "apartament"],
    "Audio & Podcast": ["podcast", "voiceover", "lektor", "audio production", "nagranie audio", "audiobook"],
    "Publishing": ["publishing", "ghostwriting", "ghostwriter", "book cover", "okładka książki", "self-publishing", "redakcja książki", "wydawnictwo"],
    "Events": ["event planning", "wydarzenie", "konferencja", "wesele", "organizacja imprezy", "organizacja eventu"],
    "Music Production": ["music production", "produkcja muzyczna", "mixing", "mastering", "session musician", "muzyk sesyjny", "beat", "utwór muzyczny", "cover art"],
    "Data & AI Services": ["data labeling", "data annotation", "etykietowanie danych", "adnotacja danych", "training data", "dane treningowe"],
}

SKILL_KEYWORDS = {
    "photography": ["foto", "photo", "fotograf", "zdjęc", "zdjec", "obiektyw", "camera", "shoot"],
    "video": ["video", "film", "youtube", "montaż", "montaz", "editing", "motion"],
    "graphic design": ["design", "logo", "grafika", "graphic", "photoshop", "illustrator"],
    "web development": ["web", "frontend", "front-end", "backend", "code", "developer", "wordpress", "react", "api"],
    "ui/ux": ["ui", "ux", "interfejs", "user experience", "figma"],
    "copywriting": ["copy", "content", "text", "artykuł", "artykul", "blog", "copywriting"],
    "seo": ["seo", "pozycjonowanie", "google ranking", "organic"],
    "marketing": ["marketing", "social media", "reklama", "kampania", "ads", "influencer"],
    "translation": ["tłumaczenie", "tlumaczenie", "translation", "translate", "translator"],
    "e-commerce": ["e-commerce", "ecommerce", "shopify", "woocommerce", "allegro", "dropshipping", "amazon"],
    "animation": ["animacj", "animation", "3d", "motion graphics"],
    "consulting": ["consult", "doradztwo", "audyt", "audit", "strateg", "analiza"],
    "data analysis": ["data", "analytics", "analiza danych", "excel", "sql", "python"],
    "audio": ["audio", "sound", "dźwięk", "dzwiek", "mix", "podcast", "music", "muzyka"],
    "retouching": ["retouch", "retusz", "photoshop", "lightroom", "korekta"],
    "real estate": ["real estate", "nieruchomo", "property", "virtual staging"],
    "podcast production": ["podcast", "audio editing", "montaż audio"],
    "voiceover": ["voiceover", "lektor", "narracja"],
    "publishing": ["publishing", "self-publishing", "wydawnictwo"],
    "ghostwriting": ["ghostwriting", "ghostwriter"],
    "event planning": ["event", "wydarzenie", "impreza", "wesele", "konferencja"],
    "music production": ["music production", "produkcja muzyczna", "beat", "utwór"],
    "mixing & mastering": ["mixing", "mastering", "mix", "master"],
    "session musician": ["session musician", "muzyk sesyjny", "instrumentalist"],
    "fashion design": ["fashion", "moda", "wzornictwo odzieży", "projektowanie odzieży"],
    "game development": ["game dev", "unity", "unreal", "gra wideo", "gamedev"],
    "data labeling": ["data labeling", "data annotation", "etykietowanie danych", "adnotacja danych"],
}

URGENCY_KEYWORDS = {
    "critical": ["urgent", "natychmiast", "asap", "pilne", "critical", "yesterday", "dziś", "dzis"],
    "high": ["szybko", "fast", "quick", "3 dni", "3 days", "5 dni", "5 days", "high", "wysoki"],
    "medium": ["medium", "week", "tydzień", "tydzien", "2 weeks"],
}

# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------

def _hash_token_sign(token: str) -> int:
    d = hashlib.md5(token.encode("utf-8")).digest()
    idx = (d[0] << 8) | d[1]
    sign = 1 if d[2] % 2 == 0 else -1
    return sign


def local_embed(text: str, dim: int | None = None) -> list[float]:
    """Deterministic hashing-vectorizer embedding (works offline, zero cost)."""
    dim = dim or settings.EMBEDDING_DIM
    vec = [0.0] * dim
    tokens = re.findall(r"[a-ząćęłńóśżź0-9]+", text.lower())
    for t in tokens:
        vec[(hashlib.md5(t.encode("utf-8")).digest()[0:2][0] << 8
             | hashlib.md5(t.encode("utf-8")).digest()[0:2][1]) % dim] += _hash_token_sign(t)
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def remote_embed(text: str) -> list[float] | None:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        resp = client.embeddings.create(
            input=text[:8000],
            model="text-embedding-3-small",
        )
        return resp.data[0].embedding
    except Exception as exc:
        logger.warning("OpenAI embedding failed (%s), using local embedding", exc)
        return None


def embed_text(text: str) -> list[float]:
    if settings.OPENAI_API_KEY:
        vec = remote_embed(text)
        if vec:
            return vec
    return local_embed(text)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(x * x for x in b)) or 1.0
    return max(0.0, min(1.0, dot / (na * nb)))


# ---------------------------------------------------------------------------
# Job analysis
# ---------------------------------------------------------------------------

def _rule_based_analysis(title: str, description: str, budget: float) -> dict:
    blob = f"{title} {description}".lower()
    category = "Other"
    best = 0
    for cat, kws in CATEGORY_KEYWORDS.items():
        hits = sum(1 for k in kws if k in blob)
        if hits > best:
            best = hits
            category = cat

    skills = []
    for skill, kws in SKILL_KEYWORDS.items():
        if any(k in blob for k in kws):
            skills.append(skill)

    urgency = "medium"
    best = 0
    for level, kws in URGENCY_KEYWORDS.items():
        hits = sum(1 for k in kws if k in blob)
        if hits > best:
            best = hits
            urgency = level

    fair_price = budget
    if category in ("Coding", "Video & Animation", "Consulting", "Music Production"):
        fair_price = max(budget, 3000)
    elif category in ("Photography", "Real Estate", "Publishing", "Events"):
        fair_price = max(budget, 1500)
    elif category in ("Writing", "Translation", "Audio & Podcast"):
        fair_price = max(budget, 500)
    elif category == "Data & AI Services":
        fair_price = max(budget, 300)

    return {
        "category": category,
        "subcategory": "",
        "skills": skills[:5],
        "urgency": urgency,
        "experience_level": "mid",
        "fair_price": round(fair_price, 2),
        "key_requirements": description[:300],
        "model": "rules",
    }


ANALYSIS_PROMPT = """You are an expert job classifier for a freelance / e-commerce matching marketplace. Analyze the job posting and return ONLY valid JSON (no markdown, no commentary) with exactly these keys:

{
  "category": one of {categories},
  "subcategory": "short specific type",
  "skills": ["3-5 required skills, lowercase english"],
  "urgency": "critical|high|medium|low",
  "experience_level": "junior|mid|senior",
  "fair_price": estimated fair price in PLN as a number,
  "key_requirements": "1-2 sentence summary"
}

Job title: {title}
Description: {description}
Budget: {budget} PLN
Deadline: {deadline}
Location: {location}
"""


def claude_analysis(title: str, description: str, budget: float, deadline: str, location: str) -> dict | None:
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = ANALYSIS_PROMPT.format(
            categories=", ".join(CATEGORIES),
            title=title[:200],
            description=description[:1500],
            budget=budget,
            deadline=deadline,
            location=location,
        )
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)
        data["model"] = "claude"
        return data
    except Exception as exc:
        logger.warning("Claude analysis failed (%s), using rules", exc)
        return None


def analyze_job(title: str, description: str, budget: float, deadline: str, location: str) -> dict:
    if settings.ANTHROPIC_API_KEY:
        data = claude_analysis(title, description, budget, deadline, location)
        if data:
            return data
    return _rule_based_analysis(title, description, budget)


# ---------------------------------------------------------------------------
# Sprint 2 AI tools (#1, #2, #3, #14)
# ---------------------------------------------------------------------------

DEFAULT_INTERVIEW_QUESTIONS = [
    "Describe your experience with similar projects (2-3 examples).",
    "What tools and workflow would you use for this job?",
    "How quickly can you deliver, and what does your communication look like during work?",
    "What is your exact price for this scope and what does it include?",
    "Share a link to relevant portfolio examples.",
]

DEFAULT_INTERVIEW_QUESTIONS_PL = [
    "Opisz swoje doświadczenie w podobnych projektach (2-3 przykłady).",
    "Jakie narzędzia i proces pracy zastosujesz przy tym zleceniu?",
    "Jak szybko możesz dostarczyć i jak wygląda komunikacja w trakcie pracy?",
    "Jaka jest Twoja dokładna wycena tego zakresu i co obejmuje?",
    "Podaj link do przykładów z portfolio.",
]


def _looks_polish(text: str) -> bool:
    return bool(re.search(r"[ąćęłńóśżź]", text.lower()))


def _claude_json(prompt: str, max_tokens: int = 600) -> dict | None:
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
        return json.loads(raw)
    except Exception as exc:
        logger.warning("Claude JSON call failed (%s)", exc)
        return None


def generate_interview_questions(title: str, description: str) -> list[str]:
    """#1 AI Instant Interviews: generate 4-5 vetting questions for the job."""
    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            f"Create 4-5 short interview questions to vet a freelancer for this job. "
            f"Return JSON only: {{\"questions\": [\"...\"]}}. Use the language of the job.\n"
            f"Title: {title[:200]}\nDescription: {description[:1200]}"
        )
        if data and data.get("questions"):
            return [str(q) for q in data["questions"][:6]]
    return DEFAULT_INTERVIEW_QUESTIONS_PL if _looks_polish(title + " " + description) else DEFAULT_INTERVIEW_QUESTIONS


def score_interview(title: str, description: str, questions: list[str], answers: list[str]) -> dict:
    """#1 score freelancer answers 0-100 with feedback (Claude, fallback semantic)."""
    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            "You are a hiring manager evaluating a freelancer's interview answers for a job.\n"
            f"Job: {title}\nDescription: {description[:1200]}\n\n"
            "Questions and answers (JSON):\n"
            f"{json.dumps([{'q': q, 'a': a} for q, a in zip(questions, answers)], ensure_ascii=False)}\n\n"
            "Return JSON only: {\"score\": 0-100, \"feedback\": \"2-3 sentence evaluation in the job's language\", "
            "\"strengths\": [\"...\"], \"risks\": [\"...\"]}",
            max_tokens=500,
        )
        if data:
            return {
                "score": int(max(0, min(100, data.get("score", 50)))),
                "feedback": data.get("feedback", ""),
                "strengths": data.get("strengths", []),
                "risks": data.get("risks", []),
                "model": "claude",
            }

    # Fallback: semantic overlap of answers with the job brief
    job_vec = embed_text(job_search_text(title, description, None))
    ans_vec = embed_text(" ".join(answers))
    score = int(cosine_similarity(job_vec, ans_vec) * 100)
    return {
        "score": score,
        "feedback": (
            f"Semantic overlap between answers and job brief: {score}/100. "
            "Answers address the requirements partially; review manually for specifics."
        ),
        "strengths": [],
        "risks": ["AI fallback scoring — verify manually"],
        "model": "rules",
    }


def generate_job_draft(idea: str) -> dict:
    """#14 AI onboarding: one sentence → complete job post draft."""
    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            "You help a client create a job post. From this short idea, generate a complete job draft.\n"
            f"Idea: {idea[:500]}\n\n"
            "Return JSON only: {\"title\": \"short clear title\", \"description\": \"2-4 sentence description\", "
            "\"category\": \"one of: Photography, Coding, Design, Writing, Marketing, Video & Animation, "
            "E-commerce, Translation, Consulting\", \"required_skills\": [\"3-5 skills\"], "
            "\"suggested_budget\": number in PLN, \"suggested_deadline_days\": number}",
            max_tokens=500,
        )
        if data and data.get("title"):
            return data

    analysis = _rule_based_analysis("Job idea", idea, 1000)
    return {
        "title": idea.strip()[:80],
        "description": idea.strip(),
        "category": analysis["category"],
        "required_skills": analysis["skills"] or ["general"],
        "suggested_budget": int(analysis["fair_price"]),
        "suggested_deadline_days": 14,
    }


def check_deliverables(title: str, description: str, analysis: dict | None, deliverables: str, url: str = "") -> dict:
    """#2 AI Deliverable Checker: QA report comparing delivered work vs job requirements."""
    requirements = []
    if analysis:
        requirements.append(analysis.get("key_requirements", ""))
    requirements += list((analysis or {}).get("skills", []))
    requirements += [title, description]

    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            "You are a QA reviewer. The freelancer delivered work for this job.\n"
            f"Job title: {title}\nJob description: {description[:1200]}\n\n"
            f"Delivered description: {deliverables[:1500]}\n"
            f"Delivered link: {url or 'none'}\n\n"
            "Return JSON only: {\"score\": 0-100, \"summary\": \"1-2 sentences\", "
            "\"checklist\": [{\"requirement\": \"...\", \"met\": true/false, \"comment\": \"...\"}], "
            "\"issues\": [\"...\"], \"recommendation\": \"approve|revisions|reject\"}",
            max_tokens=600,
        )
        if data:
            return data

    blob = (deliverables + " " + url).lower()
    checklist = []
    met_count = 0
    for req in [r for r in requirements if r][:6]:
        met = any(str(req).lower()[:20] in blob for kw in [str(req)]) or str(req).lower()[:12] in blob
        # looser: token overlap
        if not met:
            tokens = [t for t in re.findall(r"[a-ząćęłńóśżź0-9]+", str(req).lower()) if len(t) > 3]
            met = sum(1 for t in tokens if t in blob) >= max(1, len(tokens) // 2)
        checklist.append({"requirement": str(req)[:120], "met": bool(met), "comment": ""})
        met_count += bool(met)

    score = int(met_count / len(checklist) * 100) if checklist else 50
    return {
        "score": score,
        "summary": f"Deliverables cover {score}% of stated requirements (rule-based check).",
        "checklist": checklist,
        "issues": [c["requirement"] for c in checklist if not c["met"]][:5],
        "recommendation": "approve" if score >= 70 else ("revisions" if score >= 40 else "reject"),
        "model": "rules",
    }


def generate_price_proposal(title: str, description: str, budget: float, fair_price: float) -> dict:
    """#3 AI Price Negotiator: fair range + rationale."""
    low = round(fair_price * 0.85)
    high = round(fair_price * 1.15)
    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            f"Job: {title}\nDescription: {description[:800]}\nClient budget: {budget} PLN\nAI fair price: {fair_price} PLN\n\n"
            "Return JSON only: {\"range_min\": number, \"range_max\": number, "
            "\"rationale\": \"2 sentences in the job's language explaining a fair price and a compromise point\"}",
            max_tokens=300,
        )
        if data and data.get("range_min"):
            return {
                "range_min": int(data["range_min"]),
                "range_max": int(data["range_max"]),
                "rationale": data.get("rationale", ""),
                "model": "claude",
            }
    return {
        "range_min": low,
        "range_max": high,
        "rationale": (
            f"AI fair-price analysis for this scope suggests {fair_price:.0f} PLN "
            f"(client budget: {budget:.0f} PLN). Recommended negotiation window: {low}-{high} PLN."
        ),
        "model": "rules",
    }


def generate_milestones(title: str, description: str, budget: float, analysis: dict | None) -> list[dict]:
    """#5 Milestones: AI-proposed payment split (title, amount, due_days)."""
    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            f"Job: {title}\nDescription: {description[:1200]}\nBudget: {budget} PLN\n\n"
            "Propose 2-4 payment milestones for this fixed-price contract. Each milestone must have "
            "a deliverable and a fair payment share. Return JSON only: "
            "{\"milestones\": [{\"title\": \"...\", \"amount\": number, \"due_days\": number}]} "
            "where amounts sum to approximately the budget.",
            max_tokens=500,
        )
        if data and data.get("milestones"):
            items = data["milestones"][:4]
            total = sum(float(m.get("amount", 0)) for m in items) or 1
            scale = budget / total
            return [
                {
                    "title": str(m.get("title", f"Milestone {i + 1}"))[:200],
                    "amount": round(float(m.get("amount", 0)) * scale, 2),
                    "due_days": int(m.get("due_days", 7)),
                }
                for i, m in enumerate(items)
            ]

    # Fallback: even split into 3 milestones (typical for fixed-price work)
    n = 3
    base = round(budget / n, 2)
    amounts = [base] * n
    amounts[-1] = round(budget - base * (n - 1), 2)
    return [
        {"title": "Start & scope confirmation", "amount": amounts[0], "due_days": 2},
        {"title": "Main delivery", "amount": amounts[1], "due_days": 7},
        {"title": "Final delivery & revisions", "amount": amounts[2], "due_days": 14},
    ]


def generate_daily_insights(metrics: dict, anomalies: list[str]) -> str:
    """AI ops analyst: Claude-generated action recommendations with rule-based fallback."""
    if settings.ANTHROPIC_API_KEY:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            prompt = (
                "You are the operations analyst of a freelance AI-matching marketplace called DROPIFY. "
                "Here are today's metrics (JSON) and detected anomalies (list):\n"
                f"metrics: {json.dumps(metrics)}\n"
                f"anomalies: {json.dumps(anomalies)}\n"
                "Return 2-3 short, actionable recommendations for the platform owner. "
                "Plain text only, max 150 words, no markdown headers, no bullet symbols (use '-')."
            )
            resp = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.content[0].text.strip()
        except Exception as exc:
            logger.warning("AI insights failed (%s), using rule fallback", exc)

    if anomalies:
        return "Action needed: " + " ".join(f"- {a}" for a in anomalies)
    return (
        "No anomalies detected. Keep executing the growth plan: "
        "referral program (#15), dynamic fees (#8), and e-commerce integrations."
    )


# ---------------------------------------------------------------------------
# Sprint 4 AI tools — 8 new platform features (#F1-#F8)
# ---------------------------------------------------------------------------

def _claude_text(prompt: str, max_tokens: int = 500) -> str | None:
    if not settings.ANTHROPIC_API_KEY:
        return None
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()
    except Exception as exc:
        logger.warning("Claude text call failed (%s)", exc)
        return None


def generate_listing(product_name: str, description: str, source_url: str, language: str, marketplace: str) -> dict:
    """#F1 AI Listing Factory: turn a product name/description into a full,
    SEO-ready multi-marketplace listing (title, bullets, SEO tags, meta)."""
    lang_name = "Polish" if language == "pl" else "English"
    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            f"You are an e-commerce copywriter preparing a {marketplace} listing. Write in {lang_name}.\n"
            f"Product: {product_name}\nNotes: {description[:800]}\nSource link: {source_url or 'none'}\n\n"
            "Return JSON only: {\"title\": \"<=70 chars, keyword-rich\", "
            "\"description\": \"3-4 persuasive sentences\", "
            "\"bullet_points\": [\"5 short benefit bullets\"], "
            "\"seo_tags\": [\"8-12 SEO keywords\"], "
            "\"meta_description\": \"<=155 chars for search snippets\"}",
            max_tokens=700,
        )
        if data and data.get("title"):
            data["model"] = "claude"
            return data

    base = product_name.strip() or "Product"
    if language == "pl":
        return {
            "title": f"{base} — Najwyższa jakość",
            "description": description or f"{base}. Wysoka jakość, szybka wysyłka, gwarancja satysfakcji.",
            "bullet_points": ["Wysokiej jakości materiały", "Szybka wysyłka", "30 dni na zwrot", "Zweryfikowany dostawca", "Ograniczona ilość"],
            "seo_tags": [t for t in base.lower().split() if len(t) > 2][:10] or ["produkt"],
            "meta_description": (base + " — kup online, szybka wysyłka.")[:155],
            "model": "rules",
        }
    return {
        "title": f"{base} — Premium Quality",
        "description": description or f"{base}. High quality, fast shipping, satisfaction guaranteed.",
        "bullet_points": ["Premium materials", "Fast worldwide shipping", "30-day returns", "Verified supplier", "Limited stock"],
        "seo_tags": [t for t in base.lower().split() if len(t) > 2][:10] or ["product"],
        "meta_description": (base + " — buy online, fast shipping.")[:155],
        "model": "rules",
    }


def generate_video_script(product_name: str, description: str, language: str) -> dict:
    """#F6 Marketing Video Script & Voiceover Generator: 20-30s vertical ad script."""
    lang_name = "Polish" if language == "pl" else "English"
    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            f"Write a 20-30 second vertical video ad script (TikTok/Reels) in {lang_name} for this product.\n"
            f"Product: {product_name}\nNotes: {description[:600]}\n\n"
            "Return JSON only: {\"hook\": \"first 3 seconds line\", "
            "\"script\": \"full voiceover script, 4-6 short lines\", "
            "\"cta\": \"final call to action line\", \"duration_seconds\": 25}",
            max_tokens=500,
        )
        if data and data.get("script"):
            data["model"] = "claude"
            return data

    base = product_name.strip() or ("ten produkt" if language == "pl" else "this product")
    if language == "pl":
        return {
            "hook": f"Zatrzymaj się! Zobacz {base}.",
            "script": f"To {base} zmienia zasady gry. Szybka wysyłka. Sprawdzona jakość. Klienci już to kochają.",
            "cta": "Kliknij i zamów teraz!",
            "duration_seconds": 25,
            "model": "rules",
        }
    return {
        "hook": f"Wait — you need to see {base}.",
        "script": f"{base} is changing the game. Fast shipping. Proven quality. Customers already love it.",
        "cta": "Tap now and order yours!",
        "duration_seconds": 25,
        "model": "rules",
    }


AGREEMENT_TEMPLATE_EN = """SERVICE AGREEMENT (auto-generated by DROPIFY)

Contract: {contract_id}
Job: {job_title}
Client: {client_name}
Freelancer: {freelancer_name}

1. SCOPE OF WORK
{job_description}

2. PAYMENT
Total contract value: {amount:.2f} PLN
Platform fee ({fee_rate:.0%}): {fee:.2f} PLN
Payment structure: milestone-based escrow via DROPIFY, released on client approval or
auto-released 48 hours after delivery without objection.

3. DELIVERABLES & ACCEPTANCE
Deliverables are reviewed via DROPIFY's AI Deliverable Checker and/or manual client approval.

4. CROSS-BORDER NOTE
{tax_note}

5. GOVERNING TERMS
This document is a plain-language summary generated for convenience and does not
replace DROPIFY's Terms of Service, which govern the relationship between the parties.
Generated on {date}.
"""

AGREEMENT_TEMPLATE_PL = """UMOWA O ŚWIADCZENIE USŁUG (wygenerowana automatycznie przez DROPIFY)

Kontrakt: {contract_id}
Zlecenie: {job_title}
Zleceniodawca: {client_name}
Wykonawca: {freelancer_name}

1. ZAKRES PRAC
{job_description}

2. PŁATNOŚĆ
Wartość kontraktu: {amount:.2f} PLN
Prowizja platformy ({fee_rate:.0%}): {fee:.2f} PLN
Płatność etapami (escrow) przez DROPIFY, zwalniana po akceptacji klienta lub
automatycznie po 48h od dostarczenia bez zastrzeżeń.

3. ODBIÓR PRAC
Odbiór weryfikowany przez AI Deliverable Checker DROPIFY i/lub akceptację klienta.

4. UWAGA MIĘDZYNARODOWA
{tax_note}

5. POSTANOWIENIA KOŃCOWE
Ten dokument to podsumowanie w prostym języku, wygenerowane dla wygody stron — nie
zastępuje Regulaminu DROPIFY, który reguluje relację między stronami.
Wygenerowano: {date}.
"""


def generate_contract_agreement(contract, job, client, freelancer, tax_note: str, language: str = "en") -> str:
    """#F3 AI Contract & Compliance Generator: jurisdiction-aware plain-text agreement."""
    from datetime import date as _date
    template = AGREEMENT_TEMPLATE_PL if language == "pl" else AGREEMENT_TEMPLATE_EN
    return template.format(
        contract_id=contract.id,
        job_title=job.title,
        client_name=client.display_name if client else "-",
        freelancer_name=freelancer.display_name if freelancer else "-",
        job_description=job.description,
        amount=contract.amount,
        fee_rate=contract.fee_rate,
        fee=contract.platform_fee,
        tax_note=tax_note,
        date=_date.today().isoformat(),
    )


def answer_copilot(job_title: str, job_description: str, context: str, question: str, language: str) -> str:
    """#F5 AI Co-Pilot: answer a question about an active job, grounded in its context."""
    lang_name = "Polish" if language == "pl" else "English"
    text_ = _claude_text(
        f"You are DROPIFY's AI project co-pilot, embedded inside a freelance job. Answer in {lang_name}, "
        "concisely (max 120 words), grounded only in the job context below. If asked something outside "
        "this job's scope, say you can only help with this job.\n\n"
        f"Job: {job_title}\nDescription: {job_description[:1200]}\nExtra context: {context[:800]}\n\n"
        f"Question: {question[:500]}",
        max_tokens=350,
    )
    if text_:
        return text_

    if language == "pl":
        return (
            f"[Tryb offline AI] Zlecenie „{job_title}”: {job_description[:220]}… "
            "Skonfiguruj ANTHROPIC_API_KEY, aby uzyskać pełne odpowiedzi AI Co-Pilota na pytania kontekstowe."
        )
    return (
        f"[AI offline mode] Job \"{job_title}\": {job_description[:220]}… "
        "Configure ANTHROPIC_API_KEY to get full AI Co-Pilot answers to contextual questions."
    )


def generate_source_finder_plan(product_ref: str, notes: str, language: str) -> dict:
    """Sprint 4 #12 Product Source Finder: decompose a product link/description
    into a full fulfillment plan (suggested jobs, each postable directly)."""
    lang_name = "Polish" if language == "pl" else "English"
    if settings.ANTHROPIC_API_KEY:
        data = _claude_json(
            f"A client pasted this product reference for a dropshipping/e-commerce fulfillment plan. Respond in {lang_name}.\n"
            f"Product reference: {product_ref[:500]}\nNotes: {notes[:500]}\n\n"
            "Return JSON only: {\"product_summary\": \"1-2 sentences\", "
            "\"suggested_jobs\": [{\"category\": \"one of: Photography, Writing, Video & Animation, Marketing, E-commerce\", "
            "\"title\": \"...\", \"description\": \"...\", \"suggested_budget\": number in PLN}], "
            "\"total_budget_estimate\": number}",
            max_tokens=700,
        )
        if data and data.get("suggested_jobs"):
            data["model"] = "claude"
            return data

    base = product_ref.strip()[:80] or ("produkt" if language == "pl" else "product")
    if language == "pl":
        jobs = [
            {"category": "Photography", "title": f"Zdjęcia produktowe: {base}", "description": "Sesja zdjęciowa produktu na białym tle + lifestyle.", "suggested_budget": 400},
            {"category": "Writing", "title": f"Opis i SEO: {base}", "description": "Opis produktu, tagi SEO, meta opis.", "suggested_budget": 200},
            {"category": "Video & Animation", "title": f"Wideo produktowe: {base}", "description": "Krótkie wideo produktowe 15-30s pod social media.", "suggested_budget": 500},
        ]
        summary = f"Plan realizacji dla: {base}."
    else:
        jobs = [
            {"category": "Photography", "title": f"Product photos: {base}", "description": "Product photoshoot, white background + lifestyle.", "suggested_budget": 400},
            {"category": "Writing", "title": f"Listing copy & SEO: {base}", "description": "Product description, SEO tags, meta description.", "suggested_budget": 200},
            {"category": "Video & Animation", "title": f"Product video: {base}", "description": "Short 15-30s product video for social media.", "suggested_budget": 500},
        ]
        summary = f"Fulfillment plan for: {base}."
    return {
        "product_summary": summary,
        "suggested_jobs": jobs,
        "total_budget_estimate": sum(j["suggested_budget"] for j in jobs),
        "model": "rules",
    }


def job_search_text(title: str, description: str, analysis: dict | None) -> str:
    parts = [title, description]
    if analysis:
        parts += [
            analysis.get("category", ""),
            analysis.get("subcategory", ""),
            " ".join(analysis.get("skills", [])),
            analysis.get("key_requirements", ""),
        ]
    return " ".join(parts)


def freelancer_search_text(user) -> str:
    parts = [user.first_name, user.last_name, user.bio, user.location, user.company]
    parts += list(user.skills or [])
    parts += list(user.languages or [])
    return " ".join(str(p) for p in parts if p)


# ---------------------------------------------------------------------------
# Semantic search (pgvector preferred, Python fallback)
# ---------------------------------------------------------------------------

def semantic_search_freelancers(db, query_vec: list[float], limit: int = 20, exclude_ids: set | None = None) -> list[tuple[str, float]]:
    """Return [(user_id, similarity)] ranked. Uses pgvector when available."""
    exclude_ids = exclude_ids or set()
    try:
        from app.database import is_pgvector_ready
        if is_pgvector_ready():
            vec_literal = "[" + ",".join(f"{x:.6f}" for x in query_vec) + "]"
            q = text("""
                SELECT id, 1 - (profile_embedding <=> :vec::vector) AS similarity
                FROM users
                WHERE role = 'freelancer'
                  AND profile_embedding IS NOT NULL
                ORDER BY profile_embedding <=> :vec::vector ASC
                LIMIT :lim
            """)
            rows = db.execute(q, {"vec": vec_literal, "lim": limit * 4}).fetchall()
            return [(r[0], float(r[1])) for r in rows]
    except Exception as exc:
        logger.warning("pgvector search failed (%s), using Python scan", exc)

    freelancers = (
        db.execute(
            text("SELECT id, embedding_json FROM users WHERE role='freelancer' AND embedding_json IS NOT NULL")
        ).fetchall()
    )
    scored = []
    for user_id, emb_json in freelancers:
        if user_id in exclude_ids:
            continue
        try:
            vec = json.loads(emb_json)
        except (TypeError, json.JSONDecodeError):
            continue
        sim = cosine_similarity(query_vec, vec)
        if sim > 0.15:
            scored.append((user_id, sim))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[: limit * 4]
