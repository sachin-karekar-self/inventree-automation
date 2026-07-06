# EPAM Quality Architect Assessment — InvenTree Parts Module
### Agent-assisted QA workflow: requirements → test cases → runnable automation

**Candidate:** Sachin · **Agent stack:** Claude (chat) + Claude Code · **Frameworks:** pytest + requests (API), Playwright Python (UI)

**▶ Video walkthrough:** [recording on Google Drive](https://drive.google.com/file/d/1qIx9QTXQ7n30WYHGHevRqdVB8N0Hj9dj/view?usp=sharing) — generation, execution, and live refinement (see `video/recording-link.md`)

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

## 5. Coverage matrix — brief requirements → manual cases → automation

> "Automated" = a test in `automation/` directly exercises the behaviour.
> **Partial** = the core positive/negative path is automated but sibling variations remain manual-only (listed in Notes).

### Phase 1 — UI

| Brief requirement | Manual case ID(s) | Automated | Notes |
|---|---|---|---|
| Part creation — manual entry | UI-PART-001..009 | Partial | 001 (create) and 004 (empty-name validation) automated; permission/duplicate/boundary variants manual |
| Part creation — import flow | UI-PART-010..012 | No | Manual-only by prioritization (P1 automation slice) |
| Tab: Stock | UI-PART-021, 022 | Partial | Stock creation + listing automated in cross-functional flow; export manual |
| Tab: BOM | UI-PART-023 | Partial | Negative half automated (hidden for non-assembly); positive half manual |
| Tab: Allocated | UI-PART-024 | No | Manual-only |
| Tab: Build Orders | UI-PART-026 | No | Manual-only |
| Tab: Parameters | UI-PART-070..073 | Partial | Template seeding + add-parameter automated in cross-functional flow (071); template mgmt manual |
| Tab: Variants | UI-PART-050..053 | No | Manual-only |
| Tab: Revisions | UI-PART-080..087 | No (UI) | Revision behaviour automated at API layer instead (API-PART-050..053) |
| Tab: Attachments | UI-PART-027 | No | Manual-only |
| Tab: Related Parts | UI-PART-028 | No | Manual-only |
| Tab: Test Templates | UI-PART-029 | No | Manual-only |
| Categories — hierarchy | UI-PART-060 | Partial | Hierarchy automated at API layer (API-PART-041); cascading UI display manual |
| Categories — part-list filtering & navigation | UI-PART-061, 062, 065 | Partial | Part-appears-in-category-view automated in cross-functional flow; filter controls manual |
| Categories — parametric tables | UI-PART-063, 064 | No | Manual-only |
| Attribute: Virtual | UI-PART-040, 041 | No | Manual-only |
| Attribute: Template | UI-PART-050, 085 | No | Manual-only |
| Attribute: Assembly | UI-PART-023, 026, 086 | Partial | BOM-tab gating (negative) automated |
| Attribute: Component | UI-PART-024, 025, 045 | No | Manual-only |
| Attribute: Trackable | UI-PART-042, 052 | No | Manual-only |
| Attribute: Purchaseable | UI-PART-043 | No | Manual-only |
| Attribute: Salable | UI-PART-024, 030, 045 | No | Manual-only |
| Attribute: Active/Inactive | UI-PART-044, 091 | Partial | Deactivate-then-delete rule automated at API layer (API-PART-015/016) and exercised by every teardown; UI restrictions manual |
| Units of measure | UI-PART-002, 009 | Partial | Units persistence automated at API layer (API-PART-011); UI default/custom display manual |
| Revisions — creation | UI-PART-080, 081 | Partial | Automated at API layer (API-PART-050); UI flow manual |
| Revisions — circular reference prevented | UI-PART-084 | Partial | Automated at API layer (API-PART-051) |
| Revisions — unique revision codes | UI-PART-082 | Partial | Automated at API layer (API-PART-052) |
| Revisions — template restriction | UI-PART-085 | No | Manual-only (UI-PART-085, API-PART-054) |
| Revisions — revision-of-revision prevention | UI-PART-083 | Partial | Automated at API layer (API-PART-053) — instance **allows** it; documented divergence (corrections log #2) |
| Negative: duplicate IPN | UI-PART-006 | Partial | Setting-aware assertion automated at API layer (API-PART-035); UI form path manual |
| Negative: inactive part restrictions | UI-PART-044, 091 | Partial | API-PART-015/016 automated; UI-side restrictions manual |

### Phase 2 — API

| Brief requirement | Manual case ID(s) | Automated | Notes |
|---|---|---|---|
| Parts CRUD | API-PART-010..017 | Partial | 7 of 8 automated; PUT full-update (014) manual-only |
| Part Categories CRUD | API-PART-040..045 | Partial | Create/subcategory/update/circular-parent/assign automated; delete-with-children (044) manual-only |
| Filtering | API-PART-022, 023, 027 | Yes | Category, active, invalid-value all automated |
| Pagination | API-PART-020, 021, 026 | Partial | Envelope + offset-disjointness automated; boundary limits (026, P3) manual |
| Search & ordering | API-PART-024, 025 | Yes | |
| Validation: required fields | API-PART-030 | Yes | |
| Validation: max length | API-PART-031, 032 | Yes | Parametrized 100/101-char IPN boundary |
| Validation: nullable | API-PART-034 | No | Manual-only (P3) |
| Validation: read-only fields | API-PART-033 | Yes | |
| Relational integrity | API-PART-041, 043, 045, 046 | Partial | Parent link, circular-tree rejection, part↔category automated; default-location chain (046, P3) manual |
| Edge: invalid payloads | API-PART-027, 037 | Yes | Type-invalid and malformed-filter, asserting 4xx never 5xx |
| Edge: unauthorised access | API-PART-001..004 | Partial | Token/no-auth/bad-token automated; role-restricted 403 (004) manual (needs a second, limited user) |
| Edge: conflict scenarios | API-PART-036, 043, 051..053 | Yes | Name+revision uniqueness, circular refs, duplicate revision codes all automated |

**True gaps (required item with no manual case): none** — every item enumerated in the brief maps to at least one manual case.

### Code coverage of the API suite (illustrative)

`pytest --cov --cov-report=term-missing` over `automation/api` (33/33 passing against the
live instance). Note what this measures: coverage of the **automation code itself** — i.e.
that no test/fixture/helper logic is dead — not coverage of InvenTree server code, which
runs in a separate container. It is illustrative of test reach, not a hard target.

```
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
conftest.py                             69      1    99%   125
tests/test_categories_and_edges.py      76      1    99%   133
tests/test_field_validation.py          62      1    98%   87
tests/test_part_crud.py                 50      0   100%
tests/test_part_list.py                 61      0   100%
utils/schemas.py                        16      0   100%
------------------------------------------------------------------
TOTAL                                  334      3    99%
```

The 3 uncovered lines are environment-conditional branches that only execute on
deployments configured differently from this one: the fallback when a global setting
can't be read (`conftest.py:125`), the `xfail` guard for instances with revisions
disabled (`test_categories_and_edges.py:133`), and the reject-arm of the setting-aware
duplicate-IPN assertion (`test_field_validation.py:87`).

## 6. Submission tree

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
    └── recording-link.md          ← Google Drive link to the final recording
```
