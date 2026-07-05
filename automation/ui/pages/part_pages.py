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
        # VERIFY-LIVE: platform UI login route; adjust to /web/login or /accounts/login/
        self.page.goto("/web/login")
        self.page.get_by_label("Username").fill(username)          # VERIFY-LIVE
        self.page.get_by_label("Password").fill(password)          # VERIFY-LIVE
        self.page.get_by_role("button", name="Log in").click()     # VERIFY-LIVE (name may be "Login"/"Sign in")
        # Successful login navigates away from the login route
        expect(self.page).not_to_have_url(re.compile(r".*login.*"), timeout=15000)


class PartsIndexPage:
    """Parts landing view: category tree + parts table + Add Parts menu."""

    def __init__(self, page: Page):
        self.page = page

    def open(self) -> None:
        self.page.goto("/web/part/")                                # VERIFY-LIVE route
        expect(self.page.get_by_role("heading", name="Parts")).to_be_visible(timeout=15000)  # VERIFY-LIVE

    def open_create_part_form(self) -> None:
        self.page.get_by_role("button", name="Add Parts").click()   # VERIFY-LIVE (may be icon button)
        self.page.get_by_role("menuitem", name="Create Part").click()  # VERIFY-LIVE

    def search_part(self, name: str) -> None:
        self.page.get_by_placeholder("Search").fill(name)           # VERIFY-LIVE
        self.page.keyboard.press("Enter")


class PartCreateForm:
    """Modal/form for creating a part."""

    def __init__(self, page: Page):
        self.page = page

    def fill_and_submit(self, name: str, description: str, category: str | None = None,
                        ipn: str | None = None) -> None:
        self.page.get_by_label("Name").fill(name)                   # VERIFY-LIVE
        self.page.get_by_label("Description").fill(description)    # VERIFY-LIVE
        if category:
            cat = self.page.get_by_label("Category")                # VERIFY-LIVE (likely a combobox)
            cat.click()
            self.page.get_by_role("option", name=category).click()  # VERIFY-LIVE
        if ipn:
            self.page.get_by_label("IPN").fill(ipn)                 # VERIFY-LIVE
        self.page.get_by_role("button", name="Submit").click()      # VERIFY-LIVE

    def expect_field_error(self, field_label: str) -> None:
        # DRF form errors render adjacent to the field in the platform UI
        field = self.page.get_by_label(field_label)                 # VERIFY-LIVE
        expect(field).to_have_attribute("aria-invalid", "true", timeout=5000)  # VERIFY-LIVE fallback: error text locator


class PartDetailPage:
    """Part detail view with conditional tabs."""

    TABS = ["Details", "Parameters", "Stock", "Variants", "BOM", "Build Orders",
            "Used In", "Allocations", "Revisions", "Attachments", "Related Parts",
            "Test Templates"]

    def __init__(self, page: Page):
        self.page = page

    def expect_loaded(self, part_name: str) -> None:
        expect(self.page.get_by_role("heading", name=part_name)).to_be_visible(timeout=15000)  # VERIFY-LIVE

    def tab(self, name: str):
        return self.page.get_by_role("tab", name=name)              # VERIFY-LIVE

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
        self.page.get_by_role("button", name="Add parameter").click()      # VERIFY-LIVE
        tpl = self.page.get_by_label("Parameter template")                  # VERIFY-LIVE
        tpl.click()
        self.page.get_by_role("option", name=template_name).click()
        self.page.get_by_label("Value").fill(value)                          # VERIFY-LIVE
        self.page.get_by_role("button", name="Submit").click()

    def expect_parameter(self, template_name: str, value: str) -> None:
        row = self.page.get_by_role("row", name=template_name)              # VERIFY-LIVE
        expect(row).to_contain_text(value)

    # ---- Stock tab ----
    def create_stock(self, quantity: str) -> None:
        self.open_tab("Stock")
        self.page.get_by_role("button", name="Add Stock").click()           # VERIFY-LIVE (may be "New Stock Item")
        self.page.get_by_label("Quantity").fill(quantity)                    # VERIFY-LIVE
        self.page.get_by_role("button", name="Submit").click()

    def expect_in_stock(self, quantity: str) -> None:
        self.open_tab("Stock")
        expect(self.page.get_by_role("table")).to_contain_text(quantity, timeout=10000)  # VERIFY-LIVE

    # ---- Edit / lifecycle ----
    def edit_part(self, **fields: str) -> None:
        self.page.get_by_role("button", name="Part actions").click()        # VERIFY-LIVE (kebab/actions menu)
        self.page.get_by_role("menuitem", name="Edit").click()               # VERIFY-LIVE
        for label, value in fields.items():
            self.page.get_by_label(label).fill(value)
        self.page.get_by_role("button", name="Submit").click()


class CategoryPage:
    """Category view: part listing (cascading) + parametric table."""

    def __init__(self, page: Page):
        self.page = page

    def open(self, category_pk: int) -> None:
        self.page.goto(f"/web/part/category/{category_pk}/")                 # VERIFY-LIVE route
        expect(self.page.get_by_role("tab", name="Parts")).to_be_visible(timeout=15000)  # VERIFY-LIVE

    def expect_part_listed(self, part_name: str) -> None:
        table = self.page.get_by_role("table")                               # VERIFY-LIVE
        expect(table).to_contain_text(part_name, timeout=10000)

    def open_part(self, part_name: str) -> None:
        self.page.get_by_role("link", name=part_name).click()                # VERIFY-LIVE
