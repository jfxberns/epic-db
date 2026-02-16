---
phase: 03-logic-and-interface-extraction
plan: 03
subsystem: database
tags: [access, saveastext, forms, reports, business-logic, vba, inventory, pricing, thai]

# Dependency graph
requires:
  - phase: 03-01
    provides: "Query SQL extraction (62 queries in _raw_queries.json) and query overview"
  - phase: 03-02
    provides: "Windows SaveAsText exports (7 forms, 11 reports in windows/export/)"
provides:
  - "SaveAsText recursive descent parser (scripts/parse_saveastext.py)"
  - "Assessment document generator (scripts/extract_forms_reports.py)"
  - "Form catalogue with 7 exported + 4 corrupt form gaps documented"
  - "Report catalogue with 11 exported reports documented"
  - "Form navigation workflow with Mermaid diagram"
  - "Business process flows mapping orders, inventory, customers, financial reporting"
  - "Complete pricing/discount formula documentation (shop 2-tier + retail + VAT + points)"
  - "Stock level calculation formula documentation"
  - "Loyalty points system documentation"
affects: [04-schema-design, 05-migration]

# Tech tracking
tech-stack:
  added: [tabulate]
  patterns: [recursive-descent-parser, utf16le-encoding, saveastext-format]

key-files:
  created:
    - scripts/parse_saveastext.py
    - scripts/extract_forms_reports.py
    - assessment/forms/_overview.md
    - assessment/forms/navigation.md
    - assessment/reports/_overview.md
    - assessment/business_logic/process_flows.md
    - assessment/business_logic/pricing_discounts.md
  modified: []

key-decisions:
  - "Recursive descent parser for SaveAsText BEGIN/END blocks instead of regex"
  - "Binary data blocks (Property = Begin...End) must be skipped rather than parsed as nested blocks"
  - "Adapted plan from 17 forms/25 reports to actual 7 forms/11 reports available"
  - "Documented corrupt VBA forms as gaps with partial data from subquery SQL"
  - "All pricing formulas documented from query SQL -- no VBA code-behind found in any exported component"

patterns-established:
  - "SaveAsText format: UTF-16-LE encoded, hierarchical Begin/End blocks, binary hex data blocks"
  - "Subquery naming convention ~sq_c{parent}~sq_c{child} reveals subform nesting"
  - "ธนาคาร (bank) field used as payment status enum, not just bank identifier"
  - "Dual pricing tracks: VAT-inclusive for bills, pre-VAT for tax invoices"
  - "Stock is calculated (received - sold - issued), never stored as a balance"

# Metrics
duration: 16min
completed: 2026-02-16
---

# Phase 03 Plan 03: Form/Report Parsing and Business Logic Assessment Summary

**Recursive descent parser for SaveAsText exports producing form/report catalogues, navigation workflows, and complete business logic documentation with 11 pricing formulas identified**

## Performance

- **Duration:** 16 min
- **Started:** 2026-02-16T03:14:26Z
- **Completed:** 2026-02-16T03:30:38Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Built recursive descent SaveAsText parser handling UTF-16-LE, binary data blocks, and Thai text
- Generated form catalogue (7 exported + 4 corrupt gaps), report catalogue (11 reports), and navigation workflow with Mermaid diagram
- Documented 4 core business process flows: Order Management (dual-channel shop/retail), Inventory (receipt/issue/stock), Customer/Member Management (loyalty points), Financial Reporting (tax invoices, bank transfers)
- Extracted and documented 11 distinct pricing/calculation formulas from query SQL including shop 2-tier discounts, VAT at 7%, loyalty points (1 pt/100 baht), and stock calculation (received - sold - issued)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create SaveAsText parser and generate form/report catalogues** - `455d9aa` (feat)
2. **Task 2: Synthesize business logic and process flow documentation** - `ff76be8` (feat)

## Files Created/Modified
- `scripts/parse_saveastext.py` - Recursive descent parser for Access SaveAsText export format
- `scripts/extract_forms_reports.py` - Assessment document generator combining parsed forms/reports with query SQL
- `assessment/forms/_overview.md` - Form catalogue: 7 exported forms with controls, bindings, and 4 corrupt form gaps
- `assessment/forms/navigation.md` - Form navigation workflow with subform hierarchy and Mermaid diagram
- `assessment/reports/_overview.md` - Report catalogue: 11 exported reports with key fields and output types
- `assessment/business_logic/process_flows.md` - Business process flows tracing data through forms, tables, queries, reports
- `assessment/business_logic/pricing_discounts.md` - All pricing, discount, VAT, points, and stock formulas documented in English

## Decisions Made
- **Recursive descent over regex:** SaveAsText BEGIN/END blocks have nested structure requiring proper parsing, not ad-hoc regex
- **Binary block detection:** Lines like `RecSrcDt = Begin` introduce binary hex data blocks that must be skipped; the parser detects `val == "Begin"` and skips to matching `End`
- **Adapted to actual exports:** Plan expected 17 forms/25 reports; actual exports were 7 forms/11 reports. Documented 4 corrupt VBA forms as gaps with partial data from subquery SQL
- **No VBA found:** All exported forms/reports have zero code-behind. Business logic is entirely in query SQL calculated columns.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed binary data block parsing in SaveAsText parser**
- **Found during:** Task 1 (parser development)
- **Issue:** Parser treated `RecSrcDt = Begin` as a property with value "Begin" instead of recognizing it as a binary data block start. This caused the parser to skip controls and produce empty results.
- **Fix:** Added detection for `val == "Begin"` in three methods (_parse_block_contents, _parse_control, _parse_section) to call _skip_binary_block(). Also added `"=" not in current` check to prevent confusing property lines with nested Begin blocks.
- **Files modified:** scripts/parse_saveastext.py
- **Verification:** Parser correctly extracts 58 controls across 7 forms after fix
- **Committed in:** 455d9aa (Task 1 commit)

**2. [Rule 3 - Blocking] Installed missing tabulate dependency**
- **Found during:** Task 1 (running extract_forms_reports.py)
- **Issue:** tabulate package not installed, ModuleNotFoundError
- **Fix:** `python3 -m pip install tabulate`
- **Files modified:** (system package only)
- **Verification:** Script runs successfully
- **Committed in:** 455d9aa (Task 1 commit)

**3. [Rule 3 - Blocking] Fixed PYTHONPATH for module imports**
- **Found during:** Task 1 (running extract_forms_reports.py)
- **Issue:** `from scripts.parse_saveastext import ...` failed when running directly
- **Fix:** Run with `PYTHONPATH=/Users/jb/Dev/epic_gear/epic-db`
- **Files modified:** (none - runtime configuration)
- **Verification:** Script runs with correct PYTHONPATH
- **Committed in:** 455d9aa (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All auto-fixes necessary for parser correctness and script execution. No scope creep.

## Issues Encountered
- Form/report counts differ from inventory: database lists 17 forms/25 reports but only 7 forms/11 reports were exported via SaveAsText. 4 forms have corrupt VBA preventing export; remainder were not included in the Windows export batch.
- No VBA code-behind in any exported component -- the 4 corrupt forms that could not be exported are likely the ones containing VBA event handlers.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 03 (Logic and Interface Extraction) is now complete across all 3 plans
- All assessment deliverables produced: table schemas, query SQL, form catalogues, report catalogues, business logic documentation
- Ready for Phase 04 (Schema Design) with complete understanding of the source database structure, business logic, and data flows
- Key concern: 4 corrupt VBA forms remain undocumented for code-behind content; if they contain critical business logic beyond what queries implement, that logic will need to be discovered during migration testing

## Self-Check: PASSED

All 7 created files verified present. Both task commits (455d9aa, ff76be8) verified in git log.

---
*Phase: 03-logic-and-interface-extraction*
*Completed: 2026-02-16*
