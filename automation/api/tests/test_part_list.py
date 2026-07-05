"""Parts list endpoint: pagination, filtering, search, ordering.
Implements API-PART-020..027.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conftest import api, unique  # noqa: E402
from utils.schemas import assert_paginated  # noqa: E402


@pytest.mark.listing
def test_paginated_envelope(client):
    """API-PART-020: DRF envelope with limit respected."""
    resp = client.get(api("/api/part/"), params={"limit": 5}, timeout=30)
    assert resp.status_code == 200
    results = assert_paginated(resp.json(), "parts-list")
    assert len(results) <= 5


@pytest.mark.listing
def test_offset_pages_do_not_overlap(client, part_factory):
    """API-PART-021: consecutive pages are disjoint; count is stable."""
    for _ in range(6):  # ensure at least 6 parts exist
        part_factory()
    p1 = client.get(api("/api/part/"), params={"limit": 5, "offset": 0, "ordering": "pk"}, timeout=30).json()
    p2 = client.get(api("/api/part/"), params={"limit": 5, "offset": 5, "ordering": "pk"}, timeout=30).json()
    ids1 = {r["pk"] for r in p1["results"]}
    ids2 = {r["pk"] for r in p2["results"]}
    assert ids1.isdisjoint(ids2), f"Pages overlap: {ids1 & ids2}"
    assert p1["count"] == p2["count"]


@pytest.mark.listing
def test_filter_by_category(client, part_factory, category_factory):
    """API-PART-022: category filter returns only that category's parts."""
    cat = category_factory()
    inside = part_factory(category=cat["pk"])
    part_factory()  # a part in the default suite category (outside)
    # limit is required for the paginated envelope: without it InvenTree returns a plain array
    resp = client.get(api("/api/part/"), params={"category": cat["pk"], "limit": 100}, timeout=30)
    assert resp.status_code == 200
    results = assert_paginated(resp.json())
    pks = {r["pk"] for r in results}
    assert inside["pk"] in pks
    assert all(r["category"] == cat["pk"] for r in results)


@pytest.mark.listing
def test_filter_by_active_false(client, part_factory):
    """API-PART-023: active=false returns only inactive parts."""
    part = part_factory()
    client.patch(api(f"/api/part/{part['pk']}/"), json={"active": False}, timeout=30)
    resp = client.get(api("/api/part/"), params={"active": "false", "limit": 100}, timeout=30)
    results = assert_paginated(resp.json())
    assert all(r["active"] is False for r in results)
    assert part["pk"] in {r["pk"] for r in results}


@pytest.mark.listing
def test_search_by_unique_fragment(client, part_factory):
    """API-PART-024: search finds the seeded part by its unique name fragment."""
    fragment = unique("Searchable")
    part = part_factory(name=fragment)
    resp = client.get(api("/api/part/"), params={"search": fragment, "limit": 100}, timeout=30)
    results = assert_paginated(resp.json())
    assert part["pk"] in {r["pk"] for r in results}


@pytest.mark.listing
def test_ordering_asc_desc(client, part_factory):
    """API-PART-025: ordering=name asc/desc."""
    part_factory(name=unique("AAA-Order"))
    part_factory(name=unique("ZZZ-Order"))
    asc = [r["name"] for r in client.get(api("/api/part/"), params={"ordering": "name", "limit": 100}, timeout=30).json()["results"]]
    desc = [r["name"] for r in client.get(api("/api/part/"), params={"ordering": "-name", "limit": 100}, timeout=30).json()["results"]]
    assert asc == sorted(asc, key=str.casefold) or asc == sorted(asc)  # tolerate server collation
    assert desc[0] >= desc[-1]


@pytest.mark.listing
def test_invalid_filter_value_no_5xx(client):
    """API-PART-027: malformed filter must yield 4xx, never a server error."""
    resp = client.get(api("/api/part/"), params={"category": "not-a-number"}, timeout=30)
    assert 400 <= resp.status_code < 500, f"Expected 4xx, got {resp.status_code}"
