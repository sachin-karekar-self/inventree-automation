# EPAM Quality Architect Assessment — InvenTree Parts Module
### Agent-assisted QA workflow: requirements → test cases → runnable automation

**Candidate:** Sachin · **Agent stack:** Claude (chat) + Claude Code · **Frameworks:** pytest + requests (API), Playwright Python (UI)

---

## 1. Setup

### Application under test
```bash
git clone https://github.com/inventree/InvenTree.git
cd InvenTree
docker compose up -d
# note the served port from compose output; create/confirm admin credentials
```

### Environment (both suites read the same variables)
```bash
export INVENTREE_URL=http://localhost   # compose serves via Caddy proxy on port 80
export INVENTREE_USER=admin
export INVENTREE_PASSWORD=inventree
```

### API suite
```bash
cd automation/api
pip install -r requirements.txt
pytest -v                     # full suite
pytest -m crud -v             # markers: crud | listing | validation | categories | edge
```

### UI suite
```bash
cd automation/ui
pip install -r requirements.txt
playwright install chromium
pytest -m smoke -v            # sanity first
pytest -v                     # full suite (markers: smoke | crud | crossfunctional | negative)
```

## 2. Tool choices & rationale

| Choice | Why |
|---|---|
| **Claude Code** as primary agent | Terminal-native agentic loop: reads the repo (CLAUDE.md), runs suites, fixes failures in place — the exact generate→execute→refine cycle this assessment grades. |
| **Claude (chat)** for upfront analysis | Brief + documentation ingestion, requirements inventory, prompt-pack and system-instruction design before any code was generated. |
| **pytest + requests** for API | InvenTree is Python/Django; a Python stack keeps one language across AUT, API and UI suites. requests keeps assertions transparent (status/schema/business rule) with zero framework magic. |
| **Playwright (Python)** for UI | Modern auto-waiting locators (role/label-based) suit InvenTree's React platform UI; Python keeps the toolchain unified. |
| **Docker** for the AUT | Reproducible instance; suites are environment-agnostic via `INVENTREE_URL`. |

## 3. Approach summary

The workflow is the deliverable. It ran in four gated phases (full prompt pack in
`agents/prompts.md`; agent rules in `agents/system-instructions.md`):

1. **Ground truth first.** The agent ingested the Parts documentation (views, parameters,
   templates, revisions, trackable, virtual) and the API schema, and produced a
   requirements inventory that I reviewed **before** any test cases were written.
   Setting-gated behaviours (Enable Revisions, `PART_ALLOW_DUPLICATE_IPN`, Create Initial
   Stock) were flagged at this stage and encoded into test preconditions.
2. **Breadth in manual cases, depth in automation.** The manual suites
   (`test-cases/`) cover every enumerated area with positive/negative/boundary cases and
   doc-level traceability. The automation implements the P1-critical slice end-to-end.
3. **Environment before generation.** No automation was accepted until the agent verified
   the live instance (API version, token auth, part count) — code that can't run is worth
   nothing here.
4. **Execute → refine → log.** Suites were run against the live instance; failures and
   unverified locators (`# VERIFY-LIVE` tags) were fixed by the agent under direction, and
   every correction is logged below.

### Scope prioritization (deliberate)
Automation targets **runnable depth on core flows** — CRUD, list semantics, the validation
matrix, category hierarchy, revision constraints, and the mandatory cross-functional UI
flow — rather than a sprawling shallow suite. The full behavioural catalogue lives in the
manual test cases with IDs the automation traces back to. In a real engagement this is the
same call: certify the revenue-critical spine first, expand breadth iteratively.

### Design notes an evaluator should see
- **Setting-aware assertions:** duplicate-IPN tests read `PART_ALLOW_DUPLICATE_IPN` from
  the live instance and assert conditionally — behaviour-correct on any deployment.
- **Business-rule teardown:** part deletion honours the deactivate-then-delete rule, so
  cleanup itself exercises the product's lifecycle constraint.
- **Hybrid seeding in UI tests:** data that isn't under test is seeded via API; the
  behaviour under test is always exercised through the UI. Faster and less flaky without
  weakening coverage.
- **Honest uncertainty:** locators/routes not yet confirmed against the live DOM are
  tagged `# VERIFY-LIVE` rather than presented as certain — resolving them on camera is
  the refinement evidence the brief asks for.

## 4. Agent corrections log

> Append-only. Each line: what the agent got wrong → what was changed and why.
> (Rule 6 of the brief: "If the agent produced code that needed fixes, document what you
> changed and why.")

| # | Artefact | What was wrong | Correction |
|---|---|---|---|
| 1 | `automation/api/tests/test_part_list.py` (filter-by-category, active=false, search tests) | Assumed `/api/part/` always returns the paginated `count/next/previous/results` envelope; InvenTree returns a plain JSON array when `limit` is omitted, so `assert_paginated` failed | Added explicit `limit=100` to the three list requests so the envelope assertion matches documented pagination behaviour |
| 2 | `automation/api/tests/test_categories_and_edges.py::test_revision_lifecycle_and_constraints` (API-PART-053) | Asserted revision-of-a-revision is rejected (400) per Parts docs; InvenTree 1.4.1 deliberately accepts it (no nested-revision check in `Part.validate_revision`; upstream unit test asserts success) — a docs-vs-implementation divergence, not a test-environment fluke | Changed assertion to expect 201 with cleanup of the nested part, and documented the divergence in the test body and this log |
| 3 | `automation/ui/pages/part_pages.py::LoginPage` | Doc-guessed `get_by_label("Username"/"Password")` and button `"Log in"` — fields carry aria-labels, not visible labels | Real locators from operator codegen: `get_by_role("textbox", name="login-username"/"login-password")`, button `"Log In"` (single click suffices; codegen's double click was an artifact) |
| 4 | `PartsIndexPage.open` route | `/web/part/` is not a platform-UI route — it bounces to `/web/logged-in` | Parts table lives at `/web/part/category/index/parts` (verified via nav link and direct goto with storage state) |
| 5 | `PartsIndexPage.open` ready-check | Waited for a `"Parts"` heading that the page never renders | Readiness = `get_by_label("panel-tabs-partcategory")` tablist visible |
| 6 | `PartsIndexPage.open_create_part_form` | Guessed button `"Add Parts"` / menuitem `"Create Part"` | Live aria-labels: button `action-menu-add-parts`, menuitem `action-menu-add-parts-create-part` |
| 7 | `PartCreateForm` text fields | Guessed `get_by_label("Name"/"Description"/"IPN")` | Dialog-scoped `get_by_role("textbox", name="text-field-name"/"text-field-description"/"text-field-IPN")` — the form exposes stable `text-field-*`/`boolean-field-*` aria-labels |
| 8 | `PartCreateForm` category select | Guessed `get_by_label("Category")`; codegen offered only a brittle `.css-z6y6gf` chain | React-select input has aria-label `related-field-category` (combobox role): click, type fragment, pick `get_by_role("option")` |
| 9 | `PartCreateForm.expect_field_error` | Located field by visible label (unresolvable) | `text-field-<field>` input gets `aria-invalid="true"` plus a Mantine error element — verified live on empty-name submit |
| 10 | `PartDetailPage.expect_loaded` | Expected a heading with the part name; detail view renders no heading element | Readiness = `panel-tabs-part` tablist visible + part name text visible |
| 11 | `PartDetailPage.tab` | Unscoped `get_by_role("tab")` — tab names like "Stock" collide with main-navigation tabs | Scoped to `get_by_label("panel-tabs-part")`; TABS list replaced with live names from an all-flags probe part |
| 12 | `test_bom_tab_hidden_for_non_assembly` | Checked for a tab named `"BOM"`, which never exists — the negative assertion passed vacuously | Real tab name is `"Bill of Materials"` (confirmed present on an assembly-flagged part, absent otherwise) |
| 13 | `PartDetailPage.edit_part` | Guessed `"Part actions"` button / `"Edit"` menuitem and visible-label fields | Live aria-labels: `action-menu-part-actions` → `action-menu-part-actions-edit`; dialog fields via `text-field-<api-field>`; waits for modal close on success |
| 14 | `test_edit_part_description` assertion | Non-waiting `.count()` immediately after `reload()` raced the SPA re-render and failed intermittently | Replaced with `expect(...).to_be_visible()` per the explicit-wait rule |
| 15 | crossfunctional test — parameter template seeding | Seeded via `/api/part/parameter/template/`, which no longer exists in InvenTree 1.4.1 (404) — parameters were genericised | Now posts to `/api/parameter/template/` with the required `model_type: "part"` |
| 16 | `PartDetailPage.add_parameter` | Guessed `"Add parameter"` button and `"Parameter template"`/`"Value"` labels | Live path: `action-menu-add-parameters` → menuitem `action-menu-add-parameters-create-parameter`; dialog fields `related-field-template` (combobox, type-ahead + option) and `text-field-data` |
| 17 | `PartDetailPage.create_stock` | Guessed `"Add Stock"` button and `"Quantity"` label; assumed the app stays on the part page after submit | Live: `action-button-add-stock-item` → dialog field `number-field-quantity` (part comes pre-selected; no other required fields). Submitting navigates to the NEW stock item's detail page — the page object asserts that redirect, then `go_back()`s to the part page so follow-up assertions work |
| 18 | `PartDetailPage.expect_parameter` / `expect_in_stock` | Row/table locators unverified; `get_by_role("table")` could be ambiguous | Row matched by template name with value containment; table assertions pinned to `.first` with explicit timeouts — verified against the live parameter and stock tables |
| 19 | `CategoryPage.open` | Asserted an unscoped `tab "Parts"` — ambiguous with the main-navigation "Parts" tab — and never selected the tab | Waits for `panel-tabs-partcategory`, then clicks its "Parts" tab (route `/web/part/category/<pk>/` redirects to `/details`, parts list is not the default tab) |
| 20 | `CategoryPage.expect_part_listed` / `open_part` | Assumed part names render as links in the category table | They render as plain cell text: containment assertion on the table, row-click for navigation |
| 21 | crossfunctional test — teardown | Flow left the UI-created part, its stock item, and the parameter template behind (violates the clean-up rule) | Added `try/finally` API cleanup: stock items → part (deactivate-then-delete) → parameter template |

## 5. Submission tree

```
submission/
├── README.md                      ← this file
├── agents/
│   ├── prompts.md                 ← prompt pack (= recording script)
│   ├── system-instructions.md     ← agent role, domain rules, quality bar
│   └── CLAUDE.md                  ← Claude Code project config
├── test-cases/
│   ├── ui-manual-tests.md         ← 9 feature areas, POS/NEG/BND, doc traceability
│   └── api-manual-tests.md        ← auth, CRUD, list semantics, validation, categories, revisions
├── automation/
│   ├── api/                       ← pytest + requests (runnable; see §1)
│   └── ui/                        ← Playwright Python, POM (runnable; see §1)
└── video/
```
