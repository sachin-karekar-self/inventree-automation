# Agent Prompts — InvenTree Parts Module Assessment

> This file records the prompt sequence used to drive the AI agent (Claude Code, with
> Claude chat used for upfront analysis). It is both a deliverable (per the assessment's
> Agent Artefacts requirement) and the script for the recorded end-to-end session.
> Prompts are numbered in execution order. Corrections issued during iteration are
> logged in README.md → "Agent corrections log".

---

## Phase 0 — Environment & context loading

### P0.1 — Session bootstrap
```
Read agents/system-instructions.md and agents/CLAUDE.md in full. Confirm you understand:
(1) the domain rules for the InvenTree Parts module, (2) the quality standards for each
artefact type, (3) the output conventions. Summarize the revision constraints and the
tab-visibility rules back to me in two sentences each, so I can verify you've absorbed them.
```

### P0.2 — Verify the environment before generating anything
```
The InvenTree instance should be running via docker compose. Verify it:
1. GET ${INVENTREE_URL}/api/ and report the apiVersion.
2. Obtain a token via GET /api/user/token/ using INVENTREE_USER/INVENTREE_PASSWORD.
3. GET /api/part/ with the token and report the part count.
If any step fails, diagnose and tell me what to fix before we proceed. Do not generate
any tests until the instance responds.
```

---

## Phase 1 — Requirements analysis & UI test case generation

### P1.1 — Ingest requirements
```
Ingest the InvenTree Parts documentation from https://docs.inventree.org/en/stable/part/
and these sub-pages: Part Views, Part Parameters, Part Templates, Part Revisions,
Creating a Part, Trackable Parts, Virtual Parts. Produce a requirements inventory:
a bullet list of every testable behaviour you found, grouped by feature area
(creation, detail-view tabs, categories, attributes, units, revisions). Flag any
behaviour that is gated by a global setting. Do not write test cases yet — I want to
review the inventory first.
```

### P1.2 — Generate UI test cases (after my review of the inventory)
```
Using the approved requirements inventory, generate test-cases/ui-manual-tests.md.
Requirements:
- Cover at minimum: part creation (manual + import), every part-detail tab (Stock, BOM,
  Allocated, Build Orders, Parameters, Variants, Revisions, Attachments, Related Parts,
  Test Templates), category hierarchy/filtering/parametric tables, all part attribute
  flags (Virtual, Template, Assembly, Component, Trackable, Purchaseable, Salable,
  Active/Inactive), units of measure, and revision constraints (circular reference,
  unique codes, template restriction, revision-of-revision prevention).
- Include negative and boundary scenarios: duplicate IPN (setting-dependent), inactive
  part restrictions, tab visibility for parts lacking the relevant attribute.
- Use the table format and ID scheme from system-instructions.md, with a traceability
  column referencing the doc section.
- Target comprehensive breadth: every enumerated area must have positive, negative,
  and boundary coverage.
```

---

## Phase 2 — API schema analysis & API test generation

### P2.1 — Ingest the API schema
```
Ingest the Part API schema from https://docs.inventree.org/en/stable/api/schema/part/
and, from the live instance, the OPTIONS metadata for /api/part/ and /api/part/category/.
Produce an endpoint inventory: for each endpoint, list methods, required fields, read-only
fields, filter/search/ordering parameters, and pagination behaviour. Cross-check the
docs schema against the live OPTIONS response and flag any drift.
```

### P2.2 — Generate API manual test cases
```
Generate test-cases/api-manual-tests.md from the approved endpoint inventory. Cover:
CRUD on Parts and Part Categories; filtering, pagination, and search on the parts list;
field-level validation (required fields, max lengths, nullable and read-only constraints);
relational integrity (category assignment, default locations); and edge cases (invalid
payloads, unauthorised access, conflict scenarios like deleting an active part and
circular revision references). Same ID/format standards as Phase 1.
```

### P2.3 — Generate the API automation project
```
Generate the pytest + requests project in automation/api/ implementing the P1 (critical)
manual cases:
- conftest.py: session-scoped token auth fixture, api client helper, part factory fixture
  with teardown (deactivate-then-delete), unique-name helper.
- utils/schemas.py: minimal response-schema validators for Part and PartCategory.
- tests/: part CRUD; list filtering/pagination/search/ordering; field validation matrix
  (parametrized: missing name, IPN at 100 and 101 chars, read-only field write attempts);
  category CRUD + hierarchy; edge cases (401 unauthenticated, delete-active-part 400,
  duplicate IPN asserted against the live PART_ALLOW_DUPLICATE_IPN setting, circular
  revision_of rejection).
Then RUN the suite against the live instance, report failures, and fix them. Document
every fix you make in the README corrections log.
```

---

## Phase 3 — UI automation

### P3.1 — Generate the UI automation project
```
Generate the Playwright Python project in automation/ui/ implementing the core flows from
the Phase 1 test cases:
- pages/: LoginPage, PartsIndexPage, PartCreateForm, PartDetailPage (tab navigation),
  CategoryPage.
- tests/: login smoke; part create → verify detail; part edit; part deactivate;
  the mandatory cross-functional flow: create part → add a parameter → create stock →
  verify the part appears in its category view with correct stock;
  negative: attribute-gated tab hidden for a part without that attribute.
- Locator strategy per system-instructions (role/label-based). Mark any locator you
  cannot verify against the live DOM with # VERIFY-LIVE.
Then RUN the suite headed against the live instance. For each VERIFY-LIVE locator that
fails, inspect the DOM, fix the locator, and log the correction.
```

---

## Phase 4 — Packaging

### P4.1 — README and final assembly
```
Write README.md at the submission root: setup instructions (Docker for InvenTree, install
and run commands for both suites), tool choices and why, approach summary (the phase
workflow above), the scope-prioritization rationale, and the complete Agent corrections
log. Verify the submission tree matches the required layout exactly, then stop for my
final review.
```

---

## Notes on tool usage
- **Claude (chat)** was used for upfront analysis: ingesting the assessment brief and the
  InvenTree documentation, designing this prompt pack, the system instructions, and the
  initial artefact drafts.
- **Claude Code** executes this prompt pack against the live Docker instance: running
  suites, fixing failures, refining locators — the recorded session shows this loop.
- Corrections made by the human architect at each review gate are the "iterative
  refinement" evidence required by the video deliverable.
