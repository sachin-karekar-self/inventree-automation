"""Field-level validation matrix (parametrized). Implements API-PART-030..038."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conftest import api, unique  # noqa: E402


@pytest.mark.validation
def test_missing_name_rejected(client, default_category):
    """API-PART-030: name is required."""
    resp = client.post(
        api("/api/part/"),
        json={"description": "no name", "category": default_category},
        timeout=30,
    )
    assert resp.status_code == 400
    assert "name" in resp.json(), f"Expected error keyed on 'name': {resp.text}"


@pytest.mark.validation
@pytest.mark.parametrize(
    "ipn_len,expected_status",
    [(100, 201), (101, 400)],
    ids=["ipn-at-max-100", "ipn-over-max-101"],
)
def test_ipn_length_boundary(client, default_category, ipn_len, expected_status):
    """API-PART-031/032: IPN maxLength=100 per schema."""
    payload = {
        "name": unique("QA-IPN"),
        "description": "ipn boundary",
        "category": default_category,
        "IPN": "X" * ipn_len,
    }
    resp = client.post(api("/api/part/"), json=payload, timeout=30)
    assert resp.status_code == expected_status, resp.text
    if resp.status_code == 201:
        # cleanup inline (factory not used because failure path shouldn't create)
        pk = resp.json()["pk"]
        client.patch(api(f"/api/part/{pk}/"), json={"active": False}, timeout=30)
        client.delete(api(f"/api/part/{pk}/"), timeout=30)


@pytest.mark.validation
def test_read_only_fields_not_writable(part_factory, client):
    """API-PART-033: read-only fields (barcode_hash, allocated_*) cannot be set by client."""
    part = part_factory(barcode_hash="HACKED", allocated_to_build_orders=999)
    # DRF ignores read-only fields on write; server-computed values must not equal ours
    assert part.get("barcode_hash") != "HACKED"
    resp = client.patch(
        api(f"/api/part/{part['pk']}/"), json={"barcode_hash": "HACKED-2"}, timeout=30
    )
    if resp.status_code == 200:
        assert resp.json().get("barcode_hash") != "HACKED-2"


@pytest.mark.validation
def test_duplicate_ipn_respects_global_setting(client, part_factory, default_category):
    """API-PART-035: duplicate-IPN acceptance is governed by PART_ALLOW_DUPLICATE_IPN."""
    from conftest import get_global_setting

    ipn = unique("DUP-IPN")[:50]
    part_factory(IPN=ipn)

    setting = get_global_setting(client, "PART_ALLOW_DUPLICATE_IPN")
    resp = client.post(
        api("/api/part/"),
        json={
            "name": unique("QA-DupIPN"),
            "description": "dup ipn probe",
            "category": default_category,
            "IPN": ipn,
        },
        timeout=30,
    )
    allow = str(setting).lower() in ("true", "1")
    if allow:
        assert resp.status_code == 201, f"Setting allows duplicates but create failed: {resp.text}"
        pk = resp.json()["pk"]
        client.patch(api(f"/api/part/{pk}/"), json={"active": False}, timeout=30)
        client.delete(api(f"/api/part/{pk}/"), timeout=30)
    else:
        assert resp.status_code == 400, (
            f"Setting forbids duplicates but got {resp.status_code}: {resp.text}"
        )


@pytest.mark.validation
def test_duplicate_name_revision_rejected(client, part_factory, default_category):
    """API-PART-036: name+revision uniqueness enforced."""
    original = part_factory()
    resp = client.post(
        api("/api/part/"),
        json={
            "name": original["name"],
            "description": "duplicate name probe",
            "category": default_category,
        },
        timeout=30,
    )
    assert resp.status_code == 400, f"Duplicate name accepted: {resp.text}"


@pytest.mark.validation
@pytest.mark.parametrize(
    "field,value",
    [("active", "banana"), ("category", "not-an-id")],
    ids=["bool-field-garbage", "fk-field-garbage"],
)
def test_invalid_type_payloads_yield_400(client, default_category, field, value):
    """API-PART-037: type-invalid payloads → 400 field errors, never 5xx."""
    payload = {"name": unique("QA-BadType"), "description": "x", "category": default_category}
    payload[field] = value
    resp = client.post(api("/api/part/"), json=payload, timeout=30)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"


@pytest.mark.validation
def test_options_metadata_exposes_field_contract(client):
    """API-PART-038: OPTIONS lists field metadata used to build forms."""
    resp = client.options(api("/api/part/"), timeout=30)
    assert resp.status_code == 200
    body = resp.json()
    post_fields = body.get("actions", {}).get("POST", {})
    assert "name" in post_fields, f"OPTIONS metadata missing 'name': keys={list(post_fields)[:10]}"
    assert post_fields["name"].get("required") is True
