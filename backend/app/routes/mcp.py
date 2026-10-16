"""DROPIFY as an MCP server — hire from inside Claude, ChatGPT, Cursor or any
MCP-capable agent.

Upwork ships a ChatGPT app for *searching* talent; this goes further: an agent
can draft a brief, post the job, watch AI matches arrive and talk to the
freelancer — the full hiring loop without opening the website.

Transport: MCP "Streamable HTTP", stateless, JSON responses (no SSE needed)
at ``POST /api/mcp``. Auth: a DROPIFY partner API key (``/dashboard/developer``)
as ``Authorization: Bearer dpk_...`` or ``X-Api-Key``.
"""
from __future__ import annotations

import json
import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Job, Match, User
from app.routes.developer import _auth_partner
from app.schemas import JobCreate
from app.utils.ai import embed_text, generate_interview_questions, generate_job_draft, semantic_search_freelancers
from app.utils.jobs import create_job_and_match
from app.utils.ratelimit import hit

logger = logging.getLogger(__name__)
router = APIRouter(tags=["MCP server"])

SUPPORTED_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")
SERVER_INFO = {"name": "dropify", "title": "DROPIFY — AI freelance matching", "version": "1.0.0"}

TOOLS = [
    {
        "name": "search_freelancers",
        "description": "Semantic search of DROPIFY freelancers (e-commerce, design, photo, dev, marketing). "
                       "Returns public profiles ranked by relevance.",
        "inputSchema": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What you need, in any language"},
            "limit": {"type": "integer", "minimum": 1, "maximum": 20, "default": 5},
        }, "required": ["query"]},
    },
    {
        "name": "draft_job",
        "description": "Turn a one-sentence idea into a complete job brief (title, description, skills, "
                       "suggested budget in PLN and deadline). Does not publish anything.",
        "inputSchema": {"type": "object", "properties": {
            "idea": {"type": "string", "description": "e.g. 'white-background photos of 30 shoes'"},
        }, "required": ["idea"]},
    },
    {
        "name": "post_job",
        "description": "Publish a job on the API key owner's account. DROPIFY's AI immediately finds and "
                       "notifies the best freelancers. Confirm the details with the user before calling.",
        "inputSchema": {"type": "object", "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "budget": {"type": "number", "description": "Budget in PLN"},
            "deadline": {"type": "string", "description": "YYYY-MM-DD (default: in 14 days)"},
            "required_skills": {"type": "array", "items": {"type": "string"}},
            "location": {"type": "string"},
        }, "required": ["title", "description", "budget"]},
    },
    {
        "name": "list_my_jobs",
        "description": "List the API key owner's jobs with status and number of AI matches.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_job_matches",
        "description": "AI-ranked freelancer matches for one of your jobs, incl. interview score and "
                       "negotiated price. Use match_id with send_message.",
        "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string"}}, "required": ["job_id"]},
    },
    {
        "name": "send_message",
        "description": "Send a chat message to the freelancer of a match (contact details are masked "
                       "until a contract exists). Confirm the wording with the user before calling.",
        "inputSchema": {"type": "object", "properties": {
            "match_id": {"type": "string"}, "body": {"type": "string"},
        }, "required": ["match_id", "body"]},
    },
    {
        "name": "estimate_fees",
        "description": "Compare what a job of a given value costs on DROPIFY vs Upwork vs Fiverr.",
        "inputSchema": {"type": "object", "properties": {
            "amount": {"type": "number", "description": "Job value in PLN"},
        }, "required": ["amount"]},
    },
]


class ToolError(Exception):
    pass


def _public_profile(u: User, similarity: float | None = None) -> dict:
    out = {
        "id": u.id, "name": u.display_name, "bio": (u.bio or "")[:300], "skills": u.skills or [],
        "location": u.location, "languages": u.languages or [], "hourly_rate_pln": u.hourly_rate,
        "rating": round(u.rating or 0, 2), "rating_count": u.rating_count,
        "completed_jobs": u.completed_jobs, "availability": u.availability,
        "profile_url": f"{settings.FRONTEND_URL.rstrip('/')}/dashboard/freelancers?id={u.id}",
    }
    if similarity is not None:
        out["relevance"] = round(similarity, 3)
    return out


def _tool_search_freelancers(db: Session, owner: User, args: dict):
    query = str(args.get("query", "")).strip()
    if len(query) < 2:
        raise ToolError("query is required")
    limit = max(1, min(int(args.get("limit") or 5), 20))
    ranked = semantic_search_freelancers(db, embed_text(query), limit=limit)
    ids = [uid for uid, _ in ranked]
    users = {u.id: u for u in db.query(User).filter(User.id.in_(ids), User.is_active == True).all()}  # noqa: E712
    results = [_public_profile(users[uid], sim) for uid, sim in ranked if uid in users][:limit]
    if not results:  # nothing semantically close -> top rated as a useful fallback
        top = (db.query(User).filter(User.role == "freelancer", User.is_active == True)  # noqa: E712
               .order_by(User.rating.desc()).limit(limit).all())
        results = [_public_profile(u) for u in top]
    return {"freelancers": results}


def _tool_draft_job(db: Session, owner: User, args: dict):
    idea = str(args.get("idea", "")).strip()
    if len(idea) < 5:
        raise ToolError("idea must be at least 5 characters")
    return {"draft": generate_job_draft(idea[:1000]), "next_step": "Review with the user, then call post_job."}


def _tool_post_job(db: Session, owner: User, args: dict):
    payload = {
        "title": args.get("title"), "description": args.get("description"), "budget": args.get("budget"),
        "deadline": args.get("deadline") or str(date.today() + timedelta(days=14)),
        "required_skills": args.get("required_skills") or [], "location": args.get("location") or "",
    }
    try:
        data = JobCreate(**payload)
    except ValidationError as exc:
        raise ToolError("Invalid job: " + "; ".join(f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()))
    job = create_job_and_match(
        db, title=data.title, description=data.description, budget=data.budget, deadline=data.deadline,
        location=data.location, required_skills=data.required_skills, client_id=owner.id,
        interview_questions=generate_interview_questions(data.title, data.description), source="mcp",
    )
    n = db.query(Match).filter(Match.job_id == job.id).count()
    return {"job_id": job.id, "status": job.status, "ai_matches": n,
            "next_step": "Call get_job_matches to see the ranked freelancers."}


def _tool_list_my_jobs(db: Session, owner: User, args: dict):
    jobs = db.query(Job).filter(Job.client_id == owner.id).order_by(Job.created_at.desc()).limit(50).all()
    return {"jobs": [{
        "id": j.id, "title": j.title, "status": j.status, "budget_pln": j.budget,
        "deadline": str(j.deadline), "matches": len(j.matches),
    } for j in jobs]}


def _tool_get_job_matches(db: Session, owner: User, args: dict):
    job = db.get(Job, str(args.get("job_id", "")))
    if not job or job.client_id != owner.id:
        raise ToolError("Job not found on this account")
    matches = db.query(Match).filter(Match.job_id == job.id).order_by(Match.score.desc()).all()
    return {"job": {"id": job.id, "title": job.title, "status": job.status}, "matches": [{
        "match_id": m.id, "score": round(m.score, 1), "status": m.status,
        "interview_score": m.interview_score, "agreed_price_pln": m.agreed_price,
        "freelancer": _public_profile(m.freelancer),
    } for m in matches]}


def _tool_send_message(db: Session, owner: User, args: dict):
    from fastapi import HTTPException
    from app.routes.messages import send_message
    try:
        out = send_message(db, owner, str(args.get("match_id", "")), str(args.get("body", "")))
    except HTTPException as exc:
        raise ToolError(str(exc.detail))
    return {"message_id": out["id"], "sent": True, "flagged": out["flagged"], "warning": out.get("warning")}


def _tool_estimate_fees(db: Session, owner: User, args: dict):
    try:
        amount = float(args.get("amount"))
    except (TypeError, ValueError):
        raise ToolError("amount must be a number")
    if amount <= 0:
        raise ToolError("amount must be positive")
    rates = {"DROPIFY": settings.PLATFORM_FEE_RATE, "Upwork (approx.)": 0.19, "Fiverr (approx.)": 0.277}
    rows = {name: {"fee_pln": round(amount * r, 2), "rate": r} for name, r in rates.items()}
    saving = round(amount * (0.19 - settings.PLATFORM_FEE_RATE), 2)
    return {"amount_pln": amount, "platforms": rows, "saving_vs_upwork_pln": saving,
            "note": f"DROPIFY tiers: top-rated {settings.FEE_RATE_TOP:.0%}, new {settings.FEE_RATE_NEW:.0%}."}


HANDLERS = {
    "search_freelancers": _tool_search_freelancers,
    "draft_job": _tool_draft_job,
    "post_job": _tool_post_job,
    "list_my_jobs": _tool_list_my_jobs,
    "get_job_matches": _tool_get_job_matches,
    "send_message": _tool_send_message,
    "estimate_fees": _tool_estimate_fees,
}


def _ok(rid, result):
    return {"jsonrpc": "2.0", "id": rid, "result": result}


def _err(rid, code, message):
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def _dispatch(db: Session, owner: User, msg: dict):
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0" or "method" not in msg:
        return _err(msg.get("id") if isinstance(msg, dict) else None, -32600, "Invalid Request")
    method, rid, params = msg["method"], msg.get("id"), msg.get("params") or {}
    if rid is None:  # notification (e.g. notifications/initialized) -> no response
        return None
    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0]
        return _ok(rid, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO,
            "instructions": "DROPIFY finds freelancers with AI. Typical flow: draft_job -> (confirm with user) "
                            "-> post_job -> get_job_matches -> send_message. Budgets are in PLN; fee is 8%.",
        })
    if method == "ping":
        return _ok(rid, {})
    if method == "tools/list":
        return _ok(rid, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        handler = HANDLERS.get(name)
        if not handler:
            return _err(rid, -32602, f"Unknown tool: {name}")
        try:
            data = handler(db, owner, params.get("arguments") or {})
            return _ok(rid, {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, default=str)}],
                             "structuredContent": data, "isError": False})
        except ToolError as exc:
            return _ok(rid, {"content": [{"type": "text", "text": str(exc)}], "isError": True})
        except Exception:  # noqa: BLE001
            logger.exception("MCP tool %s failed", name)
            db.rollback()
            return _ok(rid, {"content": [{"type": "text", "text": "Internal error"}], "isError": True})
    return _err(rid, -32601, f"Method not found: {method}")


@router.post("/mcp")
async def mcp_endpoint(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None, alias="X-Api-Key"),
    db: Session = Depends(get_db),
):
    raw_key = x_api_key
    if not raw_key and authorization and authorization.lower().startswith("bearer "):
        raw_key = authorization[7:].strip()
    key = _auth_partner(db, raw_key)  # 401 on missing/invalid key
    hit(f"mcp:{key.id}", 120, 60)
    owner = db.get(User, key.user_id)
    if not owner or not owner.is_active:
        return JSONResponse(status_code=401, content={"detail": "API key owner inactive"})

    try:
        payload = await request.json()
    except Exception:  # noqa: BLE001
        return JSONResponse(status_code=400, content=_err(None, -32700, "Parse error"))

    if isinstance(payload, list):
        responses = [r for r in (_dispatch(db, owner, m) for m in payload) if r is not None]
        return JSONResponse(responses) if responses else Response(status_code=202)
    resp = _dispatch(db, owner, payload)
    return JSONResponse(resp) if resp is not None else Response(status_code=202)


@router.get("/mcp")
def mcp_get():
    # Stateless server: no server-initiated SSE stream.
    return Response(status_code=405, headers={"Allow": "POST"})
