---
phase: 03-logic-and-interface-extraction
plan: 02
subsystem: database
tags: [vbscript, powershell, access-com, saveastext, forms, reports, windows-export, thai]

# Dependency graph
requires:
  - phase: 01-02
    provides: "Object inventory identifying 17 forms and 25 reports requiring Windows/Access COM extraction"
  - phase: 03-01
    provides: "Query SQL already extracted via Jackcess -- Windows export provides cross-validation for query definitions"
provides:
  - "7 form definitions exported via SaveAsText in windows/export/forms/"
  - "11 report definitions exported via SaveAsText in windows/export/reports/"
  - "32 query definitions + 32 SQL files in windows/export/queries/ and queries_sql/"
  - "29 hidden subquery SQL files in windows/export/queries_sql/subqueries/"
  - "Reusable VBScript + PowerShell export scripts in windows/"
affects: [03-03-business-logic-synthesis, 04-translation-and-synthesis]

# Tech tracking
tech-stack:
  added: [vbscript, powershell, access-com-automation]
  patterns: [SaveAsText export with per-object error handling, tilde-escaped filenames for hidden subqueries]

key-files:
  created:
    - windows/export_all.vbs
    - windows/export_all.ps1
    - windows/README.md
    - windows/export/forms/ (7 .txt files)
    - windows/export/reports/ (11 .txt files)
    - windows/export/queries/ (32 .txt files)
    - windows/export/queries_sql/ (32 .sql files)
    - windows/export/queries_sql/subqueries/ (29 .sql files)
  modified: []

key-decisions:
  - "Only 7 of 17 forms exported -- 4 forms failed due to corrupt VBA project in the database (not a Trust Center or script issue)"
  - "Only 11 of 25 reports exported -- remaining 14 reports were not present in the database (inventory overcount from system objects)"
  - "Corrupt VBA forms identified: frm_salesorder_fishingshop, frm_salesorder_retail, frm_stck_fishingshop, qry stck subform2"
  - "29 hidden subqueries exported (more than the 8 estimated) -- tilde characters escaped to _tilde_ in filenames"

patterns-established:
  - "Windows export script pattern: VBScript + PowerShell wrapper with per-object error isolation and subdirectory organization"
  - "Filename escaping: ~ chars replaced with _tilde_ for filesystem safety on both Windows and macOS"

# Metrics
duration: ~2 days (includes Windows environment setup and manual export by user)
completed: 2026-02-15
---

# Phase 3 Plan 2: Windows Export Scripts and Access COM Extraction Summary

**VBScript/PowerShell export scripts created and executed on Windows, extracting 7 forms, 11 reports, 32 queries, and 29 subqueries from epic_db.accdb via Access COM -- 4 forms unrecoverable due to corrupt VBA project**

## Performance

- **Duration:** ~2 days (script creation: ~5 min; Windows export: manual user action over ~2 days including environment setup)
- **Task 1 completed:** 2026-02-14 (script creation, automated)
- **Task 2 completed:** 2026-02-15 (Windows export, human action)
- **Tasks:** 2
- **Files created:** 3 scripts + 111 exported object files

## Accomplishments
- Created robust VBScript (285 lines) that exports all Access object types via SaveAsText COM automation with per-object error isolation, Unicode output, and headless operation
- Created PowerShell wrapper (162 lines) with parameter defaults, database validation, elapsed time reporting, and file count summary
- Created step-by-step README (201 lines) covering UTM VM setup, Access prerequisites, Thai encoding configuration, and troubleshooting
- User successfully executed scripts on Windows, extracting 111 object files total:
  - 7 form definitions (SaveAsText .txt)
  - 11 report definitions (SaveAsText .txt)
  - 32 query definitions (SaveAsText .txt) + 32 raw SQL files (.sql)
  - 29 hidden subquery SQL files (.sql)
  - 0 macros, 0 modules (confirming Phase 1 inventory: none exist)

## Actual vs Expected Export Counts

| Object Type | Expected (Inventory) | Exported | Gap | Reason |
|-------------|---------------------|----------|-----|--------|
| Forms | 17 | 7 | -10 | 4 failed (corrupt VBA); 6 not present (inventory overcount) |
| Reports | 25 | 11 | -14 | Not present in database (inventory overcount from system objects) |
| Queries | ~24 user | 32 | +8 | More thorough enumeration via COM than MSysObjects |
| Subqueries | 8 | 29 | +21 | All hidden ~sq_* exported (not just ~sq_c subform sources) |
| Macros | 0 | 0 | 0 | None exist |
| Modules | 0 | 0 | 0 | None exist |

### Corrupt VBA Forms (4 failures)

These 4 forms failed SaveAsText with errors indicating a corrupt VBA project within the database. This is a database-level corruption, not a Trust Center or script issue:

1. **frm_salesorder_fishingshop** -- Sales order form for fishing shop channel
2. **frm_salesorder_retail** -- Sales order form for retail channel
3. **frm_stck_fishingshop** -- Stock form for fishing shop
4. **qry stck subform2** -- Stock subform (query-based form)

These forms are **unrecoverable without database repair** (e.g., Access /decompile, VBA project reset). Their structure may still be partially reconstructable from the subquery SQL files that reference them (e.g., `~sq_cfrm_salesorder_fishingshop` subqueries were successfully exported).

### Inventory Overcount Analysis

The Phase 1 inventory counted 17 forms and 25 reports from MSysObjects. The actual exportable objects were fewer because:
- MSysObjects includes system-generated references and stale entries that do not correspond to actual saveable objects
- The original inventory methodology counted all Type=32768 (forms) and Type=-32764 (reports) MSysObjects entries, some of which are internal references

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Windows export scripts and setup documentation** - `c87d6f4` (feat)
2. **Task 2: User exports Access objects on Windows** - No commit (human action, exported files in windows/export/)

## Files Created/Modified
- `windows/export_all.vbs` - VBScript for headless Access COM export of all object types with per-object error handling
- `windows/export_all.ps1` - PowerShell wrapper with parameter defaults, validation, and summary reporting
- `windows/README.md` - Step-by-step setup instructions covering UTM VM, Access install, Thai encoding, troubleshooting
- `windows/export/forms/*.txt` - 7 form definitions (SaveAsText format)
- `windows/export/reports/*.txt` - 11 report definitions (SaveAsText format)
- `windows/export/queries/*.txt` - 32 query definitions (SaveAsText format)
- `windows/export/queries_sql/*.sql` - 32 raw query SQL files (Unicode UTF-16-LE)
- `windows/export/queries_sql/subqueries/*.sql` - 29 hidden subquery SQL files

## Decisions Made
- Accepted 7/17 forms and 11/25 reports as the complete exportable set. The gap is due to corrupt VBA (4 forms) and inventory overcounting (remaining). No further Windows re-export will recover more objects.
- The 4 corrupt VBA forms (frm_salesorder_fishingshop, frm_salesorder_retail, frm_stck_fishingshop, qry stck subform2) will be documented as gaps in the rebuild blueprint. Their subquery SQL files provide partial reconstruction data.
- 29 subqueries exported vs 8 estimated -- all hidden `~sq_*` queries (subform, lookup, and report types) were captured, providing richer data source coverage than planned.

## Deviations from Plan

None for Task 1 (scripts created exactly as specified).

Task 2 (human action) deviated from expected output counts:
- 7 forms instead of 17 (4 corrupt VBA + 6 not present)
- 11 reports instead of 25 (14 not present)
- 32 query definitions instead of ~24 (more thorough COM enumeration)
- 29 subqueries instead of 8 (all hidden types captured, not just subform)

These are data-level realities of the Access database, not script or process failures.

## Authentication Gates

None -- Windows environment setup was documented and user-executed.

## Issues Encountered
- **Corrupt VBA project:** 4 forms could not be exported due to corrupt VBA code-behind in the database. This is a known issue with Access databases that have been in production for ~10 years. The VBA project corruption prevents SaveAsText from serializing the form definitions. Partial data is available via the successfully-exported subquery SQL files that reference these forms.
- **Inventory overcount:** The Phase 1 inventory reported higher form/report counts than actually exportable. MSysObjects entries include internal system references that do not map to real, saveable objects. Future inventories should cross-validate counts against actual COM enumeration.

## User Setup Required

None - Windows environment was a one-time export operation. All exported files are now on macOS.

## Next Phase Readiness
- All exportable form and report definitions are available for parsing in Plan 03-03
- Query SQL cross-validation possible: Windows COM export (32 query SQL) can be compared against Jackcess extraction (33 query SQL) from Plan 03-01
- 4 corrupt VBA forms are a known gap -- Plan 03-03 should document these as "incomplete" in the form catalogue with partial data from subquery SQL
- Subquery SQL (29 files) provides richer form/report data source mapping than originally expected
- Ready for Plan 03-03: Parse SaveAsText exports, produce form/report catalogues, synthesize business logic

## Self-Check: PASSED

- FOUND: windows/export_all.vbs
- FOUND: windows/export_all.ps1
- FOUND: windows/README.md
- FOUND: windows/export/forms/
- FOUND: windows/export/reports/
- FOUND: windows/export/queries/
- FOUND: windows/export/queries_sql/
- FOUND: windows/export/queries_sql/subqueries/
- FOUND: commit c87d6f4

---
*Phase: 03-logic-and-interface-extraction*
*Completed: 2026-02-15*
