"""Pytest configuration: runs the real FastAPI app against a throwaway SQLite
database, so the suite needs no Postgres/Redis/pgvector/n8n infrastructure.

No ANTHROPIC_API_KEY / OPENAI_API_KEY / STRIPE_SECRET_KEY are set here on
purpose — every test exercises this platform's own rule-based/local AI
fallbacks and Stripe's "demo mode", the same "self-working without paid
keys" paths a fresh deployment uses before an operator adds real API keys.

Run from the `backend/` directory: `cd backend && pytest`.
"""
import os
import pathlib

_TEST_DB = pathlib.Path(__file__).parent / "test_dropify.db"
if _TEST_DB.exists():
    _TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production-min-32-characters"
os.environ["SEED_DEMO_DATA"] = "False"
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["STRIPE_SECRET_KEY"] = ""
os.environ["STRIPE_WEBHOOK_SECRET"] = ""
os.environ["N8N_WEBHOOK_URL"] = ""
os.environ["N8N_WEBHOOK_SECRET"] = ""
os.environ["ADMIN_EMAIL"] = "admin@dropify.app"
os.environ["ADMIN_PASSWORD"] = "admin-test-123"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    """One shared app + SQLite DB for the whole test session (fast; safe
    because tests use distinct semantic domains — see test_categories.py's
    cross-domain-similarity assertion for why that's a deliberate, checked
    assumption and not a hope)."""
    with TestClient(app) as c:
        yield c

    from app.database import engine
    engine.dispose()  # release SQLite's file handle before deleting it
    try:
        if _TEST_DB.exists():
            _TEST_DB.unlink()
    except PermissionError:
        pass  # Windows can hold a brief lock after dispose(); harmless leftover test DB file
