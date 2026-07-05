"""Fixtures for the InvenTree Parts UI suite (Playwright + Python).

Design decisions (architect-directed):
- UI login once per session via the login page; storage state reused across tests
  for speed and stability.
- Test data that is not itself the behaviour under test is seeded via the API
  (faster, less flaky) — the UI flow under test is exercised through the UI.

Environment: INVENTREE_URL / INVENTREE_USER / INVENTREE_PASSWORD (same as API suite).
"""
from __future__ import annotations

import os
import uuid

import pytest
import requests

BASE_URL = os.environ.get("INVENTREE_URL", "http://localhost").rstrip("/")
USER = os.environ.get("INVENTREE_USER", "admin")
PASSWORD = os.environ.get("INVENTREE_PASSWORD", "inventree")

STATE_PATH = ".auth-state.json"


def unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


# ---------------- API seeding helpers ----------------

@pytest.fixture(scope="session")
def api_token() -> str:
    resp = requests.get(f"{BASE_URL}/api/user/token/", auth=(USER, PASSWORD), timeout=30)
    assert resp.status_code == 200, f"Instance not reachable/credentials wrong: {resp.status_code}"
    return resp.json()["token"]


@pytest.fixture(scope="session")
def api_client(api_token: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({"Authorization": f"Token {api_token}"})
    return s


@pytest.fixture(scope="session")
def seed_category(api_client: requests.Session) -> dict:
    resp = api_client.post(
        f"{BASE_URL}/api/part/category/", json={"name": unique("UI-Suite-Cat")}, timeout=30
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


@pytest.fixture
def seeded_part(api_client: requests.Session, seed_category: dict):
    """A part created via API for tests that need an existing part; torn down after."""
    resp = api_client.post(
        f"{BASE_URL}/api/part/",
        json={
            "name": unique("UI-Seed-Part"),
            "description": "Seeded for UI test",
            "category": seed_category["pk"],
        },
        timeout=30,
    )
    assert resp.status_code == 201, resp.text
    part = resp.json()
    yield part
    api_client.patch(f"{BASE_URL}/api/part/{part['pk']}/", json={"active": False}, timeout=30)
    api_client.delete(f"{BASE_URL}/api/part/{part['pk']}/", timeout=30)


# ---------------- Browser auth session ----------------

@pytest.fixture(scope="session")
def authenticated_state(browser) -> str:
    """Login once via the UI; persist storage state for all tests.

    Login route and locators confirmed against the live platform UI
    (see pages/part_pages.py::LoginPage).
    """
    from pages.login_page import LoginPage

    context = browser.new_context(base_url=BASE_URL)
    page = context.new_page()
    LoginPage(page).login(USER, PASSWORD)
    context.storage_state(path=STATE_PATH)
    context.close()
    return STATE_PATH


@pytest.fixture
def app_page(browser, authenticated_state):
    """A fresh authenticated page per test."""
    context = browser.new_context(base_url=BASE_URL, storage_state=authenticated_state)
    page = context.new_page()
    yield page
    context.close()
