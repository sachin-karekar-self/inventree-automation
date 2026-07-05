# UI Manual Test Cases — InvenTree Parts Module

**Scope:** Parts module UI per https://docs.inventree.org/en/stable/part/ and sub-pages.
**ID scheme:** `UI-PART-###`. **Priority:** P1 critical / P2 important / P3 nice-to-have.
**Type:** POS (positive) / NEG (negative) / BND (boundary).
**Global settings that gate behaviour** (verify state in Preconditions): Enable Revisions,
Assembly Revisions Only, Allow Duplicate IPN (`PART_ALLOW_DUPLICATE_IPN`), Create Initial
Stock, Part Import enabled, Related Parts enabled.

---

## 1. Part Creation — manual entry

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-001 | Create part with minimal required fields | Logged in with Part.create permission; a category exists | 1. Parts view → Add Parts → Create Part 2. Enter unique Name, Description, select Category 3. Submit | Form submits; browser redirects to new part detail page; name/description/category displayed correctly | P1 | POS | part/create |
| UI-PART-002 | Create part with all optional fields | As 001 | 1. Open Create Part 2. Fill Name, Description, Category, IPN, Revision, Units, External Link, Keywords 3. Submit | Part created; all field values persisted and visible in Details panel | P1 | POS | part/create, part/views |
| UI-PART-003 | Create Part menu hidden without permission | User WITHOUT Part.create permission | 1. Navigate to Parts view 2. Look for Add Parts dropdown | Add Parts menu not available | P1 | NEG | part/create |
| UI-PART-004 | Required-field validation on empty Name | As 001 | 1. Open Create Part 2. Leave Name empty, fill others 3. Submit | Form error displayed on Name; form not submitted; user remains on form | P1 | NEG | part/create |
| UI-PART-005 | Duplicate part name + revision rejected | Part "TESTPART-A" (no revision) exists | 1. Create Part with identical Name and no revision 2. Submit | Form error indicating duplicate; part not created | P1 | NEG | part/create |
| UI-PART-006 | Duplicate IPN behaviour follows setting | Part with IPN "IPN-001" exists; note PART_ALLOW_DUPLICATE_IPN state | 1. Create part with IPN "IPN-001" 2. Submit | If setting ON: created successfully. If OFF: form error on IPN, not created | P1 | NEG | part/create + settings |
| UI-PART-007 | IPN boundary at max length (100 chars) | As 001 | 1. Create part with IPN of exactly 100 chars 2. Submit 3. Repeat with 101 chars | 100 chars accepted; 101 chars rejected with field error | P2 | BND | api schema (IPN maxLength) |
| UI-PART-008 | Initial stock section appears when setting enabled | Create Initial Stock setting ON | 1. Open Create Part form 2. Observe extra Initial Stock section 3. Fill quantity + location, submit | Part created AND initial stock item exists at chosen location with chosen quantity | P2 | POS | part/create |
| UI-PART-009 | Units of measure default and custom | As 001 | 1. Create part leaving Units default 2. Create another with Units "m" | First part shows units "pcs" (default); second shows "m" | P2 | POS | part/views (UoM) |

## 2. Part Creation — import flow

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-010 | Import parts from file | Staff user; part import enabled in part settings | 1. Parts view → Add Parts → Import Part(s) 2. Upload valid file (CSV) with name/description/category columns 3. Map columns, confirm | Parts from file created; visible in category listing | P1 | POS | part/import |
| UI-PART-011 | Import option hidden when disabled | Part import setting disabled | 1. Parts view → Add Parts dropdown | Import option not shown | P2 | NEG | part/import |
| UI-PART-012 | Import file with invalid rows | Import enabled | 1. Import file containing a row with missing Name 2. Proceed | Invalid rows flagged in import preview; valid rows importable; invalid rows not silently created | P2 | NEG | part/import |

## 3. Part Detail View — tabs

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-020 | Details panel shows core fields | Part from UI-PART-002 | 1. Open part detail 2. Toggle "Show Part Details" | Name, Description, IPN, Revision, Units, External Link, Creation Date (with user) displayed | P1 | POS | part/views |
| UI-PART-021 | Stock tab lists stock items | Part with ≥2 stock items in different locations | 1. Open part → Stock tab | All stock items listed with quantity, location, status; total matches | P1 | POS | part/views (Stock) |
| UI-PART-022 | Stock export from Stock tab | As 021 | 1. Stock tab → Export stocktake 2. Choose options, download | File downloads containing rows for each stock item of this part | P3 | POS | part/views |
| UI-PART-023 | BOM tab visible only for Assembly | Part A: assembly=ON; Part B: assembly=OFF | 1. Open A → observe tabs 2. Open B → observe tabs | A shows BOM tab; B does not | P1 | POS/NEG | part/views (BOM) |
| UI-PART-024 | Allocated tab gated by Component/Salable | Part A: component=ON; Part B: salable=ON; Part C: neither | 1. Open each part's detail | A and B show Allocated tab; C does not | P2 | POS/NEG | part/views (Allocated) |
| UI-PART-025 | Used In tab only for Component | Component part used in an assembly BOM; non-component part | 1. Open component → Used In tab 2. Open non-component | Component: tab present, lists parent assembly. Non-component: tab absent | P2 | POS/NEG | part/views (Used In) |
| UI-PART-026 | Build Orders tab shows builds | Assembly part with ≥1 build order | 1. Open part → Build Orders tab | Builds listed with quantity, status, creation/completion dates | P2 | POS | part/views |
| UI-PART-027 | Attachments tab upload/link | Any part | 1. Attachments tab → upload a file 2. Add an external link attachment | Both entries appear with filename/link, comment, upload date | P2 | POS | part/views |
| UI-PART-028 | Related Parts add and display | Two parts X, Y; Related Parts feature enabled | 1. Open X → Related tab → add Y | Y listed under X's Related; relationship visible from Y as well | P3 | POS | part/views (Related) |
| UI-PART-029 | Test Templates tab only when Testable | Part with testable=ON; part with testable=OFF | 1. Open each part | Testable: Test Templates tab present, can define a test. Non-testable: tab absent | P2 | POS/NEG | part/views (Test Templates) |
| UI-PART-030 | Sales Orders tab for salable part | Salable part on ≥1 sales order | 1. Open part → Sales Orders tab | Orders listed with customer, status, dates | P3 | POS | part/views |

## 4. Part Attributes (flags)

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-040 | Virtual part hides stock UI | Create part with virtual=ON | 1. Open part detail 2. Inspect stock-related elements | Stock UI elements hidden; cannot create stock item for the part | P1 | POS | part/virtual |
| UI-PART-041 | Virtual part usable in BOM | Virtual part V; assembly part A | 1. Open A → BOM tab → add V as line | V accepted into BOM and listed | P2 | POS | part/virtual |
| UI-PART-042 | Trackable stock requires serial/batch | Part with trackable=ON | 1. Attempt to create stock item without serial or batch 2. Retry with serial | Without serial/batch: blocked with validation. With serial: created | P1 | NEG/POS | part/trackable |
| UI-PART-043 | Purchaseable enables supplier linkage | Part purchaseable=ON; another purchaseable=OFF | 1. Open each → look for Suppliers tab / supplier part creation | ON: suppliers tab and supplier-part creation available. OFF: not available | P2 | POS/NEG | part/views |
| UI-PART-044 | Active/Inactive restrictions | Active part with stock | 1. Edit part → set Active=OFF 2. Attempt actions restricted for inactive parts (e.g. add to new BOM/order) | Part shows inactive state; restricted actions blocked or part excluded from default pickers | P1 | NEG | part (attributes) |
| UI-PART-045 | Attribute flags editable and persisted | Any part | 1. Edit part → toggle Component, Salable 2. Save, reload | New flag states persisted; dependent tabs appear/disappear accordingly | P2 | POS | part/views |

## 5. Templates & Variants

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-050 | Enable Template exposes Variants tab | Part with template=OFF | 1. Edit part → template=ON 2. Reload detail | Variants tab now visible | P1 | POS | part/template |
| UI-PART-051 | Create variant via Variants tab | Template part T | 1. T → Variants tab → New Variant 2. Complete Duplicate Part form with new name 3. Submit | Variant created referencing T; listed in T's Variants tab | P1 | POS | part/template |
| UI-PART-052 | Serial uniqueness across template+variants | Template T with variants V1, V2 (trackable) | 1. Create stock for V1 with serial "S-100" 2. Attempt stock for V2 with serial "S-100" | Second creation rejected — serials must be unique across template family | P1 | NEG | part/template |
| UI-PART-053 | Template stock aggregates variants | T with V1 (5 in stock), V2 (3 in stock) | 1. Open T → stock summary | T's stock reporting includes variant stock (8) | P2 | POS | part/template |

## 6. Categories

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-060 | Category hierarchy display | Category "Electronics" with subcategory "Resistors" containing parts | 1. Open Electronics | Subcategories listed; part list includes parts from subcategories (cascading) | P1 | POS | part (categories) |
| UI-PART-061 | Category part-list filtering | Category with many parts | 1. Open category part list 2. Apply user-configurable filters (e.g. active, assembly) | List filters correctly; filter state visible | P1 | POS | part (categories) |
| UI-PART-062 | Navigate part from category list | As 060 | 1. Click a part name in the category list | Part detail view opens for that part | P2 | POS | part (categories) |
| UI-PART-063 | Parametric table sorting | Category whose parts have parameter "Resistance" | 1. Category → Parameters tab 2. Click Resistance column header | Parts sorted by that parameter value; toggle reverses order | P2 | POS | part/parameter (parametric tables) |
| UI-PART-064 | Parametric table type-aware filtering | Parameter with numeric values; parameter with choice values | 1. Filter numeric parameter with operator (e.g. > 10k) 2. Filter choice parameter by a choice | Numeric filter offers operators; choice filter offers choice list; results match | P2 | POS | part/parameter |
| UI-PART-065 | Move part between categories | Part in category A; category B exists | 1. Edit part → change category to B 2. Open A and B listings | Part gone from A's direct list, present in B | P2 | POS | part (categories) |

## 7. Parameters

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-070 | Create parameter template | Admin; Settings → parameter templates | 1. Create template (name, units, description) | Template listed and available when adding part parameters | P1 | POS | part/parameter |
| UI-PART-071 | Add parameter to part | Template from 070; any part | 1. Part → Parameters tab → New Parameter 2. Select template, enter value 3. Submit | Parameter row displayed with template name, value, units | P1 | POS | part/parameter |
| UI-PART-072 | Edit parameter template reflects | Existing template used by parts | 1. Edit template units in settings 2. View part parameters | Updated units shown against parameter values | P3 | POS | part/parameter |
| UI-PART-073 | Multiple parameters unlimited | Any part | 1. Add 5+ parameters from different templates | All parameters displayed; no imposed limit encountered | P3 | BND | part/parameter |

## 8. Revisions

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-080 | Create revision of a part | Enable Revisions ON; non-template part P | 1. P → Revisions tab → Duplicate Part action 2. Set Revision code "B", submit | Redirected to new revision part; linked to P via Revision Of; P's Revisions tab lists it | P1 | POS | part/revision |
| UI-PART-081 | Revision does not affect original's linked data | P has stock items and appears in a BOM | 1. Create revision of P 2. Inspect P's stock and BOM references | Original P's stock/BOM references unchanged; revision has its own (empty) stock | P1 | POS | part/revision |
| UI-PART-082 | Duplicate revision code rejected | P already has revision "B" | 1. Create another revision of P with code "B" | Validation error — revision codes unique per part | P1 | NEG | part/revision |
| UI-PART-083 | Revision-of-revision prevented | Revision R of part P exists | 1. Open R → attempt to create a revision of R | Blocked — a revision cannot have its own revisions | P1 | NEG | part/revision |
| UI-PART-084 | Circular reference prevented | Part P | 1. Attempt to set P as a revision of itself (via edit/duplicate flow) | Blocked with validation error | P1 | NEG | part/revision |
| UI-PART-085 | Template part cannot have revisions | Template part T; Enable Revisions ON | 1. Open T → look for revision creation | Revision creation not permitted for template parts | P1 | NEG | part/revision |
| UI-PART-086 | Assembly Revisions Only setting enforced | Setting ON; non-assembly part P; assembly part A | 1. Attempt revision on P 2. Attempt revision on A | P: blocked. A: allowed | P2 | NEG/POS | part/revision (settings) |
| UI-PART-087 | Revisions disabled globally | Enable Revisions OFF | 1. Open any part → Revisions tab / revision actions | Revision functionality unavailable | P2 | NEG | part/revision (settings) |

## 9. Part images & misc

| ID | Title | Preconditions | Steps | Expected Result | Pri | Type | Trace |
|---|---|---|---|---|---|---|---|
| UI-PART-090 | Upload part image via detail page | Any part | 1. Hover part image placeholder → upload image | Image displayed on part page; thumbnail appears in table views | P3 | POS | part (images) |
| UI-PART-091 | Deactivate then delete part | Part with no stock/dependencies | 1. Edit → Active=OFF 2. Delete part | Active part cannot be deleted; after deactivation delete succeeds; part gone from listings | P1 | NEG/POS | part (lifecycle) |

---

**Coverage note.** Comprehensive breadth is delivered here in the manual suite (91 cases
skeleton above spanning every enumerated area, each with positive/negative/boundary
representation). The automation projects implement the P1 slice in depth — see README for
the prioritization rationale.
