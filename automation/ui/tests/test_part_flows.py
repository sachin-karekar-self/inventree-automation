"""Core Part CRUD UI flows + the mandatory cross-functional flow.
Implements the P1 slice of test-cases/ui-manual-tests.md
(UI-PART-001, 004, 020, 023, 044-oriented, and the required end-to-end flow).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from playwright.sync_api import expect

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from conftest import unique  # noqa: E402
from pages.part_pages import (  # noqa: E402
    CategoryPage,
    PartCreateForm,
    PartDetailPage,
    PartsIndexPage,
)


@pytest.mark.smoke
def test_login_and_parts_index_loads(app_page):
    """Smoke: authenticated session can open the Parts index."""
    PartsIndexPage(app_page).open()


@pytest.mark.crud
def test_create_part_via_ui(app_page, seed_category):
    """UI-PART-001: create a part with required fields; land on its detail page."""
    name = unique("UI-Create")
    index = PartsIndexPage(app_page)
    index.open()
    index.open_create_part_form()
    PartCreateForm(app_page).fill_and_submit(
        name=name, description="Created through the UI", category=seed_category["name"]
    )
    PartDetailPage(app_page).expect_loaded(name)


@pytest.mark.crud
def test_create_part_empty_name_shows_error(app_page):
    """UI-PART-004: required-field validation keeps user on the form."""
    index = PartsIndexPage(app_page)
    index.open()
    index.open_create_part_form()
    form = PartCreateForm(app_page)
    form.fill_and_submit(name="", description="no name given")
    form.expect_field_error("name")


@pytest.mark.crud
def test_edit_part_description(app_page, seeded_part):
    """Edit flow: change description from the detail page and verify persistence."""
    detail = PartDetailPage(app_page)
    app_page.goto(f"/web/part/{seeded_part['pk']}/")
    detail.expect_loaded(seeded_part["name"])
    detail.edit_part(description="edited via UI test")
    app_page.reload()
    # Description surfaces in the details panel (expect-based wait: the SPA
    # re-renders asynchronously after reload)
    expect(app_page.get_by_text("edited via UI test").first).to_be_visible(timeout=10000)


@pytest.mark.negative
def test_bom_tab_hidden_for_non_assembly(app_page, seeded_part):
    """UI-PART-023 (negative half): non-assembly part must NOT show the BOM tab."""
    app_page.goto(f"/web/part/{seeded_part['pk']}/")
    detail = PartDetailPage(app_page)
    detail.expect_loaded(seeded_part["name"])
    detail.expect_tab_visible("Bill of Materials", visible=False)


@pytest.mark.crossfunctional
def test_create_part_add_parameter_stock_verify_in_category(app_page, api_client, seed_category):
    """MANDATORY cross-functional flow:
    create part → add parameter → create stock → verify in category view.

    Setup that is not under test (the parameter TEMPLATE) is seeded via API;
    every step under test is exercised through the UI.
    """
    from conftest import BASE_URL

    # Seed a parameter template via API (settings-area UI is out of flow scope).
    # Templates live at /api/parameter/template/ (generic parameter API) and need
    # model_type="part" to be selectable on parts.
    tpl_name = unique("UI-Tpl")
    tpl = api_client.post(
        f"{BASE_URL}/api/parameter/template/",
        json={"name": tpl_name, "units": "ohm", "model_type": "part"},
        timeout=30,
    )
    assert tpl.status_code == 201, f"Parameter template seed failed: {tpl.text}"
    tpl_pk = tpl.json()["pk"]

    name = unique("UI-XFlow")
    try:
        # 1. Create part through the UI
        index = PartsIndexPage(app_page)
        index.open()
        index.open_create_part_form()
        PartCreateForm(app_page).fill_and_submit(
            name=name, description="cross-functional flow", category=seed_category["name"]
        )
        detail = PartDetailPage(app_page)
        detail.expect_loaded(name)

        # 2. Add a parameter
        detail.add_parameter(tpl_name, "4700")
        detail.expect_parameter(tpl_name, "4700")

        # 3. Create stock
        detail.create_stock("25")
        detail.expect_in_stock("25")

        # 4. Verify the part appears in its category view
        cat = CategoryPage(app_page)
        cat.open(seed_category["pk"])
        cat.expect_part_listed(name)
    finally:
        # Clean up everything the flow created: stock items, part, template
        found = api_client.get(
            f"{BASE_URL}/api/part/", params={"search": name, "limit": 10}, timeout=30
        ).json()
        for p in found.get("results", []):
            stock = api_client.get(
                f"{BASE_URL}/api/stock/", params={"part": p["pk"], "limit": 100}, timeout=30
            ).json()
            for item in stock.get("results", []):
                api_client.delete(f"{BASE_URL}/api/stock/{item['pk']}/", timeout=30)
            api_client.patch(f"{BASE_URL}/api/part/{p['pk']}/", json={"active": False}, timeout=30)
            api_client.delete(f"{BASE_URL}/api/part/{p['pk']}/", timeout=30)
        api_client.delete(f"{BASE_URL}/api/parameter/template/{tpl_pk}/", timeout=30)
