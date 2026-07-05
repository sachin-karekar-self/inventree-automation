"""Part CRUD lifecycle tests. Implements API-PART-010..017."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conftest import api, unique  # noqa: E402
from utils.schemas import PART_SCHEMA, assert_schema  # noqa: E402


@pytest.mark.crud
def test_create_part_minimal(part_factory):
    """API-PART-010: minimal create returns 201 with schema-compliant body, active by default."""
    part = part_factory()
    assert_schema(part, PART_SCHEMA, "create-minimal")
    assert part["active"] is True


@pytest.mark.crud
def test_create_part_full_fields(part_factory):
    """API-PART-011: writable optional fields are persisted."""
    part = part_factory(
        IPN=unique("IPN")[:100],
        units="m",
        keywords="qa,automation",
        component=True,
        purchaseable=True,
    )
    assert part["units"] == "m"
    assert part["component"] is True
    assert part["purchaseable"] is True


@pytest.mark.crud
def test_retrieve_part_detail(client, part_factory):
    """API-PART-012: GET detail returns full schema."""
    pk = part_factory()["pk"]
    resp = client.get(api(f"/api/part/{pk}/"), timeout=30)
    assert resp.status_code == 200
    assert_schema(resp.json(), PART_SCHEMA, "detail")


@pytest.mark.crud
def test_patch_updates_single_field(client, part_factory):
    """API-PART-013: PATCH updates description, leaves name intact."""
    part = part_factory()
    resp = client.patch(
        api(f"/api/part/{part['pk']}/"), json={"description": "patched"}, timeout=30
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["description"] == "patched"
    assert body["name"] == part["name"]


@pytest.mark.crud
def test_delete_active_part_blocked(client, part_factory):
    """API-PART-015: business rule — active parts cannot be deleted."""
    pk = part_factory()["pk"]
    resp = client.delete(api(f"/api/part/{pk}/"), timeout=30)
    assert resp.status_code == 400, (
        f"Expected 400 deleting ACTIVE part, got {resp.status_code}: {resp.text}"
    )
    # still retrievable
    assert client.get(api(f"/api/part/{pk}/"), timeout=30).status_code == 200


@pytest.mark.crud
def test_delete_after_deactivation(client, default_category):
    """API-PART-016: deactivate → delete → 404 on subsequent GET.

    Creates its own part (not via factory) since deletion is the behaviour under test.
    """
    create = client.post(
        api("/api/part/"),
        json={"name": unique("QA-Del"), "description": "delete-path", "category": default_category},
        timeout=30,
    )
    assert create.status_code == 201
    pk = create.json()["pk"]

    assert client.patch(api(f"/api/part/{pk}/"), json={"active": False}, timeout=30).status_code == 200
    assert client.delete(api(f"/api/part/{pk}/"), timeout=30).status_code == 204
    assert client.get(api(f"/api/part/{pk}/"), timeout=30).status_code == 404


@pytest.mark.crud
def test_get_nonexistent_part_404(client):
    """API-PART-017."""
    resp = client.get(api("/api/part/999999999/"), timeout=30)
    assert resp.status_code == 404
