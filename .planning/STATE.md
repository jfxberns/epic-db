# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-14)

**Core value:** Extract and document all components from the Access database with enough fidelity that a complete rebuild can be executed from the assessment alone
**Current focus:** Phase 3 - Logic and Interface Extraction

## Current Position

Phase: 3 of 4 (Logic and Interface Extraction)
Plan: 2 of 3 in current phase (03-02 complete)
Status: 03-02 complete, ready for 03-03
Last activity: 2026-02-15 -- Completed 03-02 (Windows Export Scripts & Access COM Extraction)

Progress: [██████░░░░] 60%

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: ~6 min (excluding human-action plans)
- Total execution time: ~0.5 hours (automated only)

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-setup-and-validation | 2/2 | ~18 min | ~9 min |
| 02-schema-foundation | 2/2 | ~7 min | ~3.5 min |
| 03-logic-and-interface-extraction | 2/3 | ~6 min + ~2 days | ~6 min (auto) |

**Recent Trend:**
- Last 5 plans: 02-01 (~5 min), 02-02 (~2 min), 03-01 (~6 min), 03-02 (~5 min auto + ~2 days human)
- Trend: Consistent (~4 min avg for automated tasks)

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: 4-phase structure -- Setup, Schema, Logic+Interface, Translation+Synthesis
- [Roadmap]: Queries + VBA + Forms/Reports combined into single phase (depth: quick)
- [Roadmap]: Translation deferred until after all extraction to ensure glossary consistency
- [01-01]: Used McSash fork (access_parser_c) instead of upstream access-parser for database version compatibility
- [01-01]: Null bytes in row data are Unicode compression artifacts, strippable -- not corruption
- [01-01]: Thai encoding verdict PASS -- user confirmed visual rendering correct
- [01-02]: MSysQueries not accessible -- query types classified from MSysObjects Flags (flags=0 -> SELECT by convention)
- [01-02]: Type=8 MSysObjects entries are relationships (12 table-to-table links detected)
- [01-02]: Windows IS NEEDED for Phase 3: 17 forms and 25 reports require Access COM for content extraction
- [01-02]: Zero modules and zero macros in database (only temp system macro exists)
- [02-01]: Moved AccessTable/TableObj imports to module level for reuse across schema extraction functions
- [02-01]: FK indexes with idx_num >= real_index_count have empty column lists; MSysRelationships is the authoritative source for FK column mappings
- [02-01]: 14 relationships total: 8 table-to-table, 4 table-to-query, 2 system (MSysNavPane)
- [02-02]: Used tabulate pipe-format for all generated markdown tables
- [02-02]: Decimal binary values shown as [Binary: N bytes] (known parser limitation for 31-byte format)
- [02-02]: คะแนนที่ลูกค้าใช้ไป identified as Likely Abandoned (0 rows + no relationships)
- [03-01]: Java 11 added as bridge dependency for Jackcess query SQL extraction on macOS
- [03-01]: Jackcess found 33 user queries (vs 32 from MSysObjects) -- qry_ร้านค้าส่งของให้ก่อน was previously invisible
- [03-01]: All queries confirmed SELECT (32) or UNION (1) from actual SQL -- MSysObjects flags were correct
- [03-01]: Hidden ~sq_* subqueries categorized: ~sq_c (subform, 8), ~sq_d (lookup, 14), ~sq_r (report, 7)
- [03-01]: Hub tables: สินค้า (26 refs), รายละเอียดออเดอร์ (23 refs) -- core business data
- [03-01]: Hub query: qry สินค้าในแต่ละออเดอร์ร้านค้า (11 dependents) -- central to shop order processing
- [03-02]: Only 7/17 forms exported -- 4 failed (corrupt VBA project: frm_salesorder_fishingshop, frm_salesorder_retail, frm_stck_fishingshop, qry stck subform2), 6 not present
- [03-02]: Only 11/25 reports exported -- remaining 14 not present (MSysObjects inventory overcounted with system references)
- [03-02]: 29 hidden subqueries exported (vs 8 estimated) -- all ~sq_c, ~sq_d, ~sq_r types captured
- [03-02]: Corrupt VBA forms are unrecoverable without database repair; partial data available via their subquery SQL files

### Pending Todos

None yet.

### Blockers/Concerns

- [Research] [RESOLVED in 03-02]: Windows export complete -- 7 forms, 11 reports extracted. 4 forms unrecoverable (corrupt VBA). Inventory overcounted forms/reports.
- [Research] [RESOLVED in 01-01]: Thai encoding confirmed PASS with access_parser_c -- no mojibake, compression artifacts strippable
- [Research] [RESOLVED in 03-02]: oletools moot -- zero VBA modules in database. Corrupt VBA in 4 forms is project-level corruption, not extractable by any tool.
- [03-02] [ACTIVE]: 4 forms with corrupt VBA (frm_salesorder_fishingshop, frm_salesorder_retail, frm_stck_fishingshop, qry stck subform2) will be gaps in rebuild blueprint

## Session Continuity

Last session: 2026-02-15
Stopped at: Completed 03-02-PLAN.md -- Windows export scripts and Access COM extraction
Resume file: .planning/phases/03-logic-and-interface-extraction/03-02-SUMMARY.md
