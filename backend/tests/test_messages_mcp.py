"""Chat (client <-> freelancer) and the MCP server — offline/no-LLM paths."""
from datetime import date, timedelta

from app.utils.messaging import scan_message
from tests.helpers import auth_headers, make_freelancer, register


def _future(days: int) -> str:
    return str(date.today() + timedelta(days=days))


def _job_with_match(client, title="Packaging design for organic tea", bio="Packaging and label designer for food brands"):
    fr = make_freelancer(client, bio=bio, skills=["packaging design", "label design", "branding"],
                         first_name="Ewa", last_name="Pakuła")
    cl = register(client, "client", first_name="Tomasz", last_name="Herbata")
    job = client.post("/api/jobs", headers=auth_headers(cl["access_token"]), json={
        "title": title,
        "description": "We need packaging and label design for a new organic tea line, branding included.",
        "budget": 3000, "deadline": _future(20),
    }).json()
    matches = client.get(f"/api/matches/job/{job['id']}", headers=auth_headers(cl["access_token"])).json()
    match = next(m for m in matches if m["freelancer_id"] == fr["user"]["id"])
    return cl, fr, job, match


def test_scan_message_masks_contacts_and_flags_off_platform():
    body, reasons = scan_message(
        "Napisz na jan.kowalski@gmail.com albo +48 601 234 567, whatsapp: jan_k. Zapłać mi bezpośrednio przelewem.",
        mask=True,
    )
    assert "gmail.com" not in body and "601" not in body and "jan_k" not in body
    assert {"email", "phone", "messenger", "off_platform_payment"} <= set(reasons)
    # budgets and dates are not phone numbers
    body, reasons = scan_message("Budżet 4000 PLN, termin 2026-11-30.", mask=True)
    assert reasons == [] and "4000" in body


def test_chat_flow_masking_unread_and_access(client):
    cl, fr, job, match = _job_with_match(client)
    c_h, f_h = auth_headers(cl["access_token"]), auth_headers(fr["access_token"])

    sent = client.post(f"/api/messages/{match['id']}", headers=c_h,
                       json={"body": "Hi! Can you start Monday? Mail me at boss@tea.pl"})
    assert sent.status_code == 200, sent.text
    assert sent.json()["flagged"] and "boss@tea.pl" not in sent.json()["body"]
    assert sent.json()["warning"]

    assert client.get("/api/messages/unread-count", headers=f_h).json()["unread"] >= 1
    threads = client.get("/api/messages/threads", headers=f_h).json()
    assert any(t["match_id"] == match["id"] and t["unread"] >= 1 for t in threads)

    thread = client.get(f"/api/messages/{match['id']}", headers=f_h).json()
    assert thread["messages"][0]["mine"] is False
    assert client.get("/api/messages/unread-count", headers=f_h).json()["unread"] == 0

    client.post(f"/api/messages/{match['id']}", headers=f_h, json={"body": "Yes, Monday works. Price 3000 PLN ok?"})
    summary = client.get(f"/api/messages/{match['id']}/summary?language=en", headers=c_h).json()
    assert summary["summary"] and summary["open_questions"]
    replies = client.get(f"/api/messages/{match['id']}/suggest-replies?language=pl", headers=c_h).json()["replies"]
    assert len(replies) == 3

    outsider = register(client, "client")
    assert client.get(f"/api/messages/{match['id']}", headers=auth_headers(outsider["access_token"])).status_code == 404
    assert client.post(f"/api/messages/{match['id']}", headers=auth_headers(outsider["access_token"]),
                       json={"body": "hello"}).status_code == 404


def _mcp(client, key, method, params=None, rid=1):
    return client.post("/api/mcp", headers={"Authorization": f"Bearer {key}"},
                       json={"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})


def test_mcp_server_full_hiring_loop(client):
    make_freelancer(client, bio="Amazon and Allegro listing copywriter, SEO product descriptions",
                    skills=["copywriting", "seo", "allegro"])
    cl = register(client, "client")
    key = client.post("/api/developer/keys", headers=auth_headers(cl["access_token"]), json={"name": "Claude"}).json()["key"]

    assert client.post("/api/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}).status_code == 401

    init = _mcp(client, key, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                             "clientInfo": {"name": "test", "version": "0"}}).json()
    assert init["result"]["protocolVersion"] == "2025-06-18"
    assert init["result"]["serverInfo"]["name"] == "dropify"
    assert client.post("/api/mcp", headers={"Authorization": f"Bearer {key}"},
                       json={"jsonrpc": "2.0", "method": "notifications/initialized"}).status_code == 202

    names = {t["name"] for t in _mcp(client, key, "tools/list").json()["result"]["tools"]}
    assert {"search_freelancers", "post_job", "get_job_matches", "send_message"} <= names

    found = _mcp(client, key, "tools/call", {"name": "search_freelancers",
                                             "arguments": {"query": "allegro listing copywriting seo"}}).json()
    assert found["result"]["isError"] is False
    assert found["result"]["structuredContent"]["freelancers"]
    assert "email" not in found["result"]["structuredContent"]["freelancers"][0]

    posted = _mcp(client, key, "tools/call", {"name": "post_job", "arguments": {
        "title": "Allegro product descriptions for 40 SKUs",
        "description": "SEO copywriting of Allegro listings for 40 kitchen products, Polish language.",
        "budget": 1600,
    }}).json()["result"]
    assert posted["isError"] is False, posted
    job_id = posted["structuredContent"]["job_id"]

    matches = _mcp(client, key, "tools/call", {"name": "get_job_matches", "arguments": {"job_id": job_id}}).json()
    rows = matches["result"]["structuredContent"]["matches"]
    assert rows
    msg = _mcp(client, key, "tools/call", {"name": "send_message", "arguments": {
        "match_id": rows[0]["match_id"], "body": "Hi, are you available this week?"}}).json()
    assert msg["result"]["structuredContent"]["sent"] is True

    bad = _mcp(client, key, "tools/call", {"name": "post_job", "arguments": {"title": "x", "description": "y", "budget": -5}}).json()
    assert bad["result"]["isError"] is True

    other = register(client, "client")
    other_key = client.post("/api/developer/keys", headers=auth_headers(other["access_token"]), json={}).json()["key"]
    stolen = _mcp(client, other_key, "tools/call", {"name": "get_job_matches", "arguments": {"job_id": job_id}}).json()
    assert stolen["result"]["isError"] is True

    fees = _mcp(client, key, "tools/call", {"name": "estimate_fees", "arguments": {"amount": 1000}}).json()
    assert fees["result"]["structuredContent"]["saving_vs_upwork_usd"] > 0
    assert _mcp(client, key, "nope").json()["error"]["code"] == -32601
