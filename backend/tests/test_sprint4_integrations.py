"""Sprint 4 (#9-#12, doku/PLAN_20_FUNKCJI_PONAD_KONKURENCJA.md): e-commerce
integrations. Shopify/BaseLinker tests stub the outbound httpx calls (no real
network access to third-party APIs from the test suite) but exercise every
line of DROPIFY's own code: auth, HMAC verification, job creation."""
import base64
import hashlib
import hmac
import json

from tests.helpers import auth_headers, register


def _shopify_hmac(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    return base64.b64encode(digest).decode()


def test_shopify_connect_list_and_disconnect(client):
    data = register(client, "client")
    token = data["access_token"]
    resp = client.post("/api/integrations/shopify/connect", headers=auth_headers(token), json={
        "shop_domain": "my-test-shop.myshopify.com",
        "access_token": "shpat_fake_token",
        "webhook_secret": "whsec_shopify_test",
    })
    assert resp.status_code == 200, resp.text
    conn_id = resp.json()["id"]

    listed = client.get("/api/integrations/mine", headers=auth_headers(token)).json()
    assert any(c["id"] == conn_id and c["platform"] == "shopify" for c in listed)

    disconnect = client.delete(f"/api/integrations/{conn_id}", headers=auth_headers(token))
    assert disconnect.status_code == 200


def test_shopify_webhook_requires_valid_signature_and_creates_job(client):
    data = register(client, "client")
    token = data["access_token"]
    conn = client.post("/api/integrations/shopify/connect", headers=auth_headers(token), json={
        "shop_domain": "signed-shop.myshopify.com",
        "access_token": "shpat_fake",
        "webhook_secret": "whsec_test_123",
    }).json()

    body = json.dumps({"title": "Cool Gadget", "body_html": "<p>A very cool gadget.</p>"}).encode()

    bad = client.post(
        f"/api/integrations/shopify/webhook/{conn['id']}",
        content=body,
        headers={"content-type": "application/json", "x-shopify-hmac-sha256": "not-a-valid-signature"},
    )
    assert bad.status_code == 401

    good_sig = _shopify_hmac("whsec_test_123", body)
    good = client.post(
        f"/api/integrations/shopify/webhook/{conn['id']}",
        content=body,
        headers={"content-type": "application/json", "x-shopify-hmac-sha256": good_sig},
    )
    assert good.status_code == 200, good.text
    assert good.json()["job_id"]


def test_shopify_webhook_unknown_connection_rejected(client):
    resp = client.post("/api/integrations/shopify/webhook/does-not-exist", json={"title": "x"})
    assert resp.status_code == 404


def test_shopify_push_listing_reports_upstream_failure_gracefully(client):
    """No mocking here on purpose: pushing to a fake, unreachable shop domain
    must fail as a clean 502, not crash the request."""
    data = register(client, "client")
    token = data["access_token"]
    conn = client.post("/api/integrations/shopify/connect", headers=auth_headers(token), json={
        "shop_domain": "this-shop-does-not-exist-dropify-test.invalid",
        "access_token": "shpat_fake",
        "webhook_secret": "",
    }).json()
    listing = client.post("/api/factory/listing", headers=auth_headers(token), json={
        "product_name": "Test Product", "language": "en",
    }).json()

    resp = client.post(
        f"/api/integrations/shopify/{conn['id']}/push-listing",
        headers=auth_headers(token),
        json={"product_id": "12345", "listing_id": listing["id"]},
    )
    assert resp.status_code == 502


def test_baselinker_connect_and_sync_creates_jobs(client, monkeypatch):
    import app.routes.integrations as integrations_module

    class _FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "status": "SUCCESS",
                "orders": [
                    {"order_id": 111, "products": [{"name": "A"}]},
                    {"order_id": 112, "products": [{"name": "B"}, {"name": "C"}]},
                ],
            }

    monkeypatch.setattr(integrations_module.httpx, "post", lambda *a, **k: _FakeResponse())

    data = register(client, "client")
    token = data["access_token"]
    conn = client.post("/api/integrations/baselinker/connect", headers=auth_headers(token), json={
        "access_token": "fake-bl-token", "label": "My BaseLinker",
    }).json()
    assert conn["platform"] == "baselinker"

    resp = client.post(f"/api/integrations/baselinker/{conn['id']}/sync", headers=auth_headers(token))
    assert resp.status_code == 200, resp.text
    assert resp.json()["orders_synced"] == 2


def test_baselinker_sync_surfaces_api_error(client, monkeypatch):
    import app.routes.integrations as integrations_module

    class _FakeErrorResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"status": "ERROR", "error_message": "ERROR_INVALID_TOKEN"}

    monkeypatch.setattr(integrations_module.httpx, "post", lambda *a, **k: _FakeErrorResponse())

    data = register(client, "client")
    token = data["access_token"]
    conn = client.post("/api/integrations/baselinker/connect", headers=auth_headers(token), json={
        "access_token": "bad-token",
    }).json()

    resp = client.post(f"/api/integrations/baselinker/{conn['id']}/sync", headers=auth_headers(token))
    assert resp.status_code == 502


def test_product_source_finder_and_bulk_job_creation(client):
    data = register(client, "client")
    token = data["access_token"]

    resp = client.post("/api/factory/source-finder", headers=auth_headers(token), json={
        "product_ref": "https://www.aliexpress.com/item/example-gadget.html",
        "notes": "",
        "language": "en",
    })
    assert resp.status_code == 200, resp.text
    plan = resp.json()
    assert plan["suggested_jobs"]
    assert plan["total_budget_estimate"] > 0

    create_resp = client.post(
        "/api/factory/source-finder/create-jobs",
        headers=auth_headers(token),
        json={"jobs": plan["suggested_jobs"]},
    )
    assert create_resp.status_code == 200, create_resp.text
    assert len(create_resp.json()["created_job_ids"]) == len(plan["suggested_jobs"])
