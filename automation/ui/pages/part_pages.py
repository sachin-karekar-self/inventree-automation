"""Page objects for the InvenTree platform UI (Parts module).

Locator strategy (architect-directed, per system-instructions):
- Prefer get_by_role / get_by_label / get_by_placeholder over CSS chains.
- Every locator not yet confirmed against the live DOM carries a # VERIFY-LIVE tag;
  the recorded Claude Code session resolves these against the running instance and
  the corrections are logged in README.md.
"""
from __future__ import annotations

import re

from playwright.sync_api import Page, expect


class LoginPage:
    """InvenTree platform UI login."""

    def __init__(self, page: Page):
        self.page = page

    def login(self, username: str, password: str) -> None:
        self.page.goto("/web/login")
        self.page.get_by_role("textbox", name="login-username").fill(username)
        self.page.get_by_role("textbox", name="login-password").fill(password)
        self.page.get_by_role("button", name="Log In").click()
        # Successful login navigates away from the login route
        expect(self.page).not_to_have_url(re.compile(r".*login.*"), timeout=15000)


class PartsIndexPage:
    """Parts landing view: category tree + parts table + Add Parts menu."""

    def __init__(self, page: Page):
        self.page = page

    def open(self) -> None:
        # /web/part/ is not a route in the platform UI; the parts table lives on the
        # category index under the "Parts" panel tab. The page renders no "Parts"
        # heading — readiness is signalled by the category panel tablist.
        self.page.goto("/web/part/category/index/parts")
        expect(self.page.get_by_label("panel-tabs-partcategory")).to_be_visible(timeout=15000)

    def open_create_part_form(self) -> None:
        self.page.get_by_role("button", name="action-menu-add-parts").click()
        self.page.get_by_role("menuitem", name="action-menu-add-parts-create-part").click()

    def search_part(self, name: str) -> None:
        self.page.get_by_placeholder("Search").fill(name)           # VERIFY-LIVE
        self.page.keyboard.press("Enter")


class PartCreateForm:
    """The "Add Part" modal. Field inputs carry stable aria-labels of the form
    text-field-<api-field> / related-field-<api-field> / boolean-field-<api-field>."""

    def __init__(self, page: Page):
        self.page = page
        self.dialog = page.get_by_role("dialog")

    def fill_and_submit(self, name: str, description: str, category: str | None = None,
                        ipn: str | None = None) -> None:
        self.dialog.get_by_role("textbox", name="text-field-name").fill(name)
        self.dialog.get_by_role("textbox", name="text-field-description").fill(description)
        if category:
            combo = self.dialog.get_by_role("combobox", name="related-field-category")
            combo.click()
            combo.fill(category)
            self.page.get_by_role("option", name=re.compile(re.escape(category))).first.click()
        if ipn:
            self.dialog.get_by_role("textbox", name="text-field-IPN").fill(ipn)
        self.dialog.get_by_role("button", name="Submit").click()

    def expect_field_error(self, field: str) -> None:
        """Assert a validation error on an API field (e.g. "name"): the input is
        flagged aria-invalid and a Mantine error message renders in its wrapper."""
        locator = self.dialog.get_by_role("textbox", name=f"text-field-{field}")
        expect(locator).to_have_attribute("aria-invalid", "true", timeout=5000)


class PartDetailPage:
    """Part detail view (/web/part/<pk>/) with conditional tabs.

    Tab names confirmed live on an all-flags part; conditional ones in brackets:
    Part Details, Stock, [Variants], [Allocations], [Bill of Materials], [Used In],
    Part Pricing, [Suppliers], [Purchase Orders], [Sales Orders], [Build Orders],
    [Test Templates], [Test Results], Related Parts, Parameters, Attachments, Notes.
    """

    TABS = ["Part Details", "Stock", "Variants", "Allocations", "Bill of Materials",
            "Used In", "Part Pricing", "Suppliers", "Purchase Orders", "Sales Orders",
            "Build Orders", "Test Templates", "Test Results", "Related Parts",
            "Parameters", "Attachments", "Notes"]

    def __init__(self, page: Page):
        self.page = page

    def expect_loaded(self, part_name: str) -> None:
        # The detail view renders no <h*> heading; readiness = the part panel
        # tablist plus the part name in the header area.
        expect(self.page.get_by_label("panel-tabs-part")).to_be_visible(timeout=15000)
        expect(self.page.get_by_text(part_name).first).to_be_visible(timeout=15000)

    def tab(self, name: str):
        # Must be scoped to the part panel: names like "Stock" also exist as
        # main-navigation tabs.
        return self.page.get_by_label("panel-tabs-part").get_by_role("tab", name=name)

    def open_tab(self, name: str) -> None:
        self.tab(name).click()

    def expect_tab_visible(self, name: str, visible: bool = True) -> None:
        if visible:
            expect(self.tab(name)).to_be_visible(timeout=10000)
        else:
            expect(self.tab(name)).to_have_count(0)

    # ---- Parameters tab ----
    def add_parameter(self, template_name: str, value: str) -> None:
        self.open_tab("Parameters")
        self.page.get_by_role("button", name="action-menu-add-parameters").click()
        self.page.get_by_role("menuitem", name="action-menu-add-parameters-create-parameter").click()
        dialog = self.page.get_by_role("dialog")
        tpl = dialog.get_by_role("combobox", name="related-field-template")
        tpl.click()
        tpl.fill(template_name)
        self.page.get_by_role("option", name=re.compile(re.escape(template_name))).first.click()
        dialog.get_by_role("textbox", name="text-field-data").fill(value)
        dialog.get_by_role("button", name="Submit").click()
        expect(dialog).to_have_count(0, timeout=10000)

    def expect_parameter(self, template_name: str, value: str) -> None:
        row = self.page.get_by_role("row", name=re.compile(re.escape(template_name)))
        expect(row.first).to_contain_text(value, timeout=10000)

    # ---- Stock tab ----
    def create_stock(self, quantity: str) -> None:
        self.open_tab("Stock")
        self.page.get_by_role("button", name="action-button-add-stock-item").click()
        dialog = self.page.get_by_role("dialog")
        # Part is pre-selected (hidden, disabled combobox); quantity is the only
        # field the flow needs — everything else in "Add Stock Item" is optional.
        dialog.get_by_role("textbox", name="number-field-quantity").fill(quantity)
        dialog.get_by_role("button", name="Submit").click()
        # Successful creation navigates to the NEW STOCK ITEM's detail page —
        # that redirect is the user-visible success signal. Return to the part
        # page so follow-up assertions run against its Stock tab.
        expect(self.page).to_have_url(re.compile(r".*/web/stock/item/\d+.*"), timeout=15000)
        self.page.go_back()
        expect(self.page.get_by_label("panel-tabs-part")).to_be_visible(timeout=15000)

    def expect_in_stock(self, quantity: str) -> None:
        self.open_tab("Stock")
        expect(self.page.get_by_role("table").first).to_contain_text(quantity, timeout=10000)

    # ---- Edit / lifecycle ----
    def edit_part(self, **fields: str) -> None:
        """Open Part Actions → Edit and update text fields.

        Keyword names are API field names (e.g. description="...") mapped onto the
        "Edit Part" dialog's text-field-<name> aria-labels.
        """
        self.page.get_by_role("button", name="action-menu-part-actions").click()
        self.page.get_by_role("menuitem", name="action-menu-part-actions-edit").click()
        dialog = self.page.get_by_role("dialog")
        for field, value in fields.items():
            dialog.get_by_role("textbox", name=f"text-field-{field}").fill(value)
        dialog.get_by_role("button", name="Submit").click()
        expect(dialog).to_have_count(0, timeout=10000)  # modal closes on success


class CategoryPage:
    """Category view: part listing (cascading) + parametric table."""

    def __init__(self, page: Page):
        self.page = page

    def open(self, category_pk: int) -> None:
        # Route redirects to /web/part/category/<pk>/details; the "Parts" tab must
        # be selected from the category panel tablist (the name also exists in the
        # main navigation, so the locator is panel-scoped).
        self.page.goto(f"/web/part/category/{category_pk}/")
        panel = self.page.get_by_label("panel-tabs-partcategory")
        expect(panel).to_be_visible(timeout=15000)
        panel.get_by_role("tab", name="Parts", exact=True).click()

    def expect_part_listed(self, part_name: str) -> None:
        expect(self.page.get_by_role("table").first).to_contain_text(part_name, timeout=10000)

    def open_part(self, part_name: str) -> None:
        # Part names render as plain cell text in the category parts table, not links
        self.page.get_by_role("row", name=re.compile(re.escape(part_name))).first.click()
