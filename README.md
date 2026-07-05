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
export INVENTREE_URL=http://localhost:8000   # adjust to your compose port
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
