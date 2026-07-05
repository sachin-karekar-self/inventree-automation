"""Shared fixtures for the InvenTree Parts API suite.

Environment:
    INVENTREE_URL       base URL of running instance (default http://localhost — the
                        compose stack serves via the Caddy proxy on port 80)
    INVENTREE_USER      admin username (default admin)
    INVENTREE_PASSWORD  admin password (default inventree)
"""
from __future__ import annotations

import os
import uuid
from typing import Any, Callable

import pytest
import requests

BASE_URL = os.environ.get("INVENTREE_URL", "http://localhost").rstrip("/")
USER = os.environ.get("INVENTREE_USER", "admin")
PASSWORD = os.environ.get("INVENTREE_PASSWORD", "inventree")


def api(path: str) -> str:
    """Build a full API URL from a path like '/api/part/'."""
    return f"{BASE_URL}{path}"


def unique(prefix: str) -> str:
    """Unique name so tests are independent and re-runnable."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def token() -> str:
    """Obtain an auth token via basic auth (recommended by InvenTree docs)."""
    resp = requests.get(api("/api/user/token/"), auth=(USER, PASSWORD), timeout=30)
    assert resp.status_code == 200, (
        f"Token retrieval failed ({resp.status_code}): is the instance up at {BASE_URL} "
        f"and are INVENTREE_USER/INVENTREE_PASSWORD correct?"
    )
    tok = resp.json().get("token")
    assert tok, "Token endpoint returned no token"
    return tok


@pytest.fixture(scope="session")
def client(token: str) -> requests.Session:
    """Authenticated session used by all tests."""
    s = requests.Session()
    s.headers.update({"Authorization": f"Token {token}"})
    return s


@pytest.fixture(scope="session")
def anon() -> requests.Session:
    """Unauthenticated session for auth-negative tests."""
    return requests.Session()


@pytest.fixture(scope="session")
def default_category(client: requests.Session) -> int:
    """A category all test parts can live in; created once per session."""
    resp = client.post(api("/api/part/category/"), json={"name": unique("QA-Suite-Cat")}, timeout=30)
    assert resp.status_code == 201, f"Could not create suite category: {resp.text}"
    return resp.json()["pk"]


def _delete_part(client: requests.Session, pk: int) -> None:
    """Teardown helper: deactivate (business rule) then delete; tolerate already-gone."""
    client.patch(api(f"/api/part/{pk}/"), json={"active": False}, timeout=30)
    client.delete(api(f"/api/part/{pk}/"), timeout=30)


@pytest.fixture
def part_factory(client: requests.Session, default_category: int) -> Callable[..., dict[str, Any]]:
    """Create parts with automatic teardown.

    Usage: part = part_factory(name=..., **extra_fields)
    """
    created: list[int] = []

    def make(**overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": unique("QA-Part"),
            "description": "Created by API automation suite",
            "category": default_category,
        }
        payload.update(overrides)
        resp = client.post(api("/api/part/"), json=payload, timeout=30)
        assert resp.status_code == 201, f"part_factory failed: {resp.status_code} {resp.text}"
        body = resp.json()
        created.append(body["pk"])
        return body

    yield make

    for pk in created:
        _delete_part(client, pk)


@pytest.fixture
def category_factory(client: requests.Session) -> Callable[..., dict[str, Any]]:
    """Create categories with automatic teardown."""
    created: list[int] = []

    def make(**overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": unique("QA-Cat")}
        payload.update(overrides)
        resp = client.post(api("/api/part/category/"), json=payload, timeout=30)
        assert resp.status_code == 201, f"category_factory failed: {resp.status_code} {resp.text}"
        body = resp.json()
        created.append(body["pk"])
        return body

    yield make

    for pk in reversed(created):  # children before parents
        client.delete(api(f"/api/part/category/{pk}/"), timeout=30)


def get_global_setting(client: requests.Session, key: str) -> Any:
    """Read a global setting value (e.g. PART_ALLOW_DUPLICATE_IPN)."""
    resp = client.get(api(f"/api/settings/global/{key}/"), timeout=30)
    if resp.status_code != 200:
        return None
    return resp.json().get("value")
