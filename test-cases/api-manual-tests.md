# API Manual Test Cases — InvenTree Parts & Part Categories

**Scope:** `/api/part/` and `/api/part/category/` per
https://docs.inventree.org/en/stable/api/schema/part/ and live OPTIONS metadata.
**Auth:** Token (obtained via `GET /api/user/token/` with basic auth) unless a case states otherwise.
**ID scheme:** `API-PART-###`. Priorities/types as in the UI suite.

---

## 1. Authentication & access

| ID | Title | Steps | Expected | Pri | Type |
|---|---|---|---|---|---|
| API-PART-001 | Token retrieval with valid basic auth | GET `/api/user/token/` with valid user:pass | 200; body contains non-empty `token` | P1 | POS |
| API-PART-002 | Unauthenticated request rejected | GET `/api/part/` with no auth header | 401 | P1 | NEG |
| API-PART-003 | Invalid token rejected | GET `/api/part/` with `Authorization: Token garbage` | 401 | P1 | NEG |
| API-PART-004 | Role-restricted write blocked | POST `/api/part/` as user lacking part.add role | 403 | P2 | NEG |

## 2. Part CRUD

| ID | Title | Steps | Expected | Pri | Type |
|---|---|---|---|---|---|
| API-PART-010 | Create part (minimal) | POST `/api/part/` {name, description, category} | 201; body echoes fields; `pk` integer; `active` true by default | P1 | POS |
| API-PART-011 | Create part (full) | POST with IPN, units, keywords, attribute flags | 201; all writable fields persisted | P1 | POS |
| API-PART-012 | Retrieve part detail | GET `/api/part/{pk}/` | 200; schema keys present (pk, name, description, category, IPN, active, assembly, component, virtual, trackable, purchaseable, salable, units) | P1 | POS |
| API-PART-013 | Update via PATCH | PATCH `/api/part/{pk}/` {description} | 200; description updated; other fields unchanged | P1 | POS |
| API-PART-014 | Full update via PUT | PUT with complete payload | 200; resource matches payload | P2 | POS |
| API-PART-015 | Delete blocked while active | DELETE `/api/part/{pk}/` on active part | 400 with validation detail; part still retrievable | P1 | NEG |
| API-PART-016 | Delete after deactivation | PATCH active=false → DELETE | 204; subsequent GET → 404 | P1 | POS |
| API-PART-017 | Get nonexistent part | GET `/api/part/999999999/` | 404 | P2 | NEG |

## 3. Parts list — filtering, pagination, search

| ID | Title | Steps | Expected | Pri | Type |
|---|---|---|---|---|---|
| API-PART-020 | Paginated envelope | GET `/api/part/?limit=5` | 200; body has count, next, previous, results; len(results) ≤ 5 | P1 | POS |
| API-PART-021 | Offset paging consistency | Page with limit=5&offset=0 then offset=5 | No overlap between pages; count constant | P1 | POS |
| API-PART-022 | Filter by category | GET `?category={id}` | All results belong to that category (or its tree per API semantics) | P1 | POS |
| API-PART-023 | Filter by active | GET `?active=false` | Only inactive parts returned | P1 | POS |
| API-PART-024 | Search by name substring | GET `?search={unique-fragment}` | Result set includes the seeded part; unrelated parts absent | P1 | POS |
| API-PART-025 | Ordering | GET `?ordering=name` then `?ordering=-name` | Results sorted asc then desc by name | P2 | POS |
| API-PART-026 | Boundary limit values | `?limit=0`, `?limit=1`, very large limit | Sensible behaviour: no 5xx; documented handling (0 → default/all per DRF config) | P3 | BND |
| API-PART-027 | Invalid filter value | `?category=not-a-number` | 400 with field error (no 5xx) | P2 | NEG |

## 4. Field-level validation

| ID | Title | Steps | Expected | Pri | Type |
|---|---|---|---|---|---|
| API-PART-030 | Missing required name | POST without name | 400; error keyed on name | P1 | NEG |
| API-PART-031 | IPN at max length 100 | POST with 100-char IPN | 201 | P2 | BND |
| API-PART-032 | IPN over max length | POST with 101-char IPN | 400; error keyed on IPN | P2 | BND |
| API-PART-033 | Read-only field write ignored/rejected | POST/PATCH attempting to set barcode_hash, allocated_to_build_orders | Values not persisted (DRF ignores read-only); response shows server-computed values | P2 | NEG |
| API-PART-034 | Nullable category accepted | POST with category=null | 201; category null | P3 | POS |
| API-PART-035 | Duplicate IPN vs setting | Read `PART_ALLOW_DUPLICATE_IPN`; POST part with existing IPN | Setting true → 201; false → 400 on IPN | P1 | NEG |
| API-PART-036 | Duplicate name+revision rejected | POST duplicate of existing name/revision combo | 400 uniqueness error | P1 | NEG |
| API-PART-037 | Invalid type payloads | POST with active="banana", category="x" | 400 field errors; no 5xx | P2 | NEG |
| API-PART-038 | OPTIONS metadata exposes fields | OPTIONS `/api/part/` | 200; actions.POST lists fields with type/required/read_only attributes | P3 | POS |

## 5. Part Categories

| ID | Title | Steps | Expected | Pri | Type |
|---|---|---|---|---|---|
| API-PART-040 | Create category | POST `/api/part/category/` {name} | 201 | P1 | POS |
| API-PART-041 | Create subcategory | POST {name, parent: {id}} | 201; parent set; appears in parent's tree | P1 | POS |
| API-PART-042 | Category detail & update | GET/PATCH `/api/part/category/{pk}/` | 200; edits persisted | P1 | POS |
| API-PART-043 | Category as own parent rejected | PATCH category parent=self | 400 (circular tree prevented) | P1 | NEG |
| API-PART-044 | Delete category behaviour with children/parts | DELETE category having subcategory/parts | Documented behaviour: children/parts re-parented or 400 per API contract — assert actual contract from OPTIONS/docs | P2 | NEG |
| API-PART-045 | Assign part to category | PATCH part category={id} | 200; part filtered under new category | P1 | POS |
| API-PART-046 | Default location relational integrity | Set category default_location; create part+stock using defaults | Stock location honours category default | P3 | POS |

## 6. Revisions & conflict scenarios (API)

| ID | Title | Steps | Expected | Pri | Type |
|---|---|---|---|---|---|
| API-PART-050 | Create revision via API | POST part with revision code + revision_of={parent pk} (Enable Revisions ON) | 201; revision linked | P2 | POS |
| API-PART-051 | Circular revision rejected | PATCH part revision_of=self | 400 | P1 | NEG |
| API-PART-052 | Duplicate revision code per parent rejected | Second revision with same code for same parent | 400 | P1 | NEG |
| API-PART-053 | Revision of a revision rejected | POST revision_of={revision pk} | 400 | P1 | NEG |
| API-PART-054 | Template part revision rejected | POST revision_of={template part pk} | 400 | P2 | NEG |
| API-PART-055 | PATCH-on-list custom operation | PATCH `/api/part/` with documented bulk payload | Documented custom behaviour honoured (cross-check OPTIONS) | P3 | POS |

---

**Note on assertions marked "documented behaviour":** where the public docs are ambiguous
(e.g. category delete semantics), the case directs the tester to assert the contract
exposed by the live instance's OPTIONS metadata — drift between docs and instance is
itself a reportable finding.
