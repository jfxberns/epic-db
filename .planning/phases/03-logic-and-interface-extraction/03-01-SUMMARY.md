---
phase: 03-logic-and-interface-extraction
plan: 01
subsystem: database
tags: [jackcess, jpype, query-extraction, dependency-graph, sql-analysis, thai, mermaid]

# Dependency graph
requires:
  - phase: 01-02
    provides: "MSysObjects inventory with 32 query names and type flags"
  - phase: 02-01
    provides: "db_reader.py with get_user_tables() returning 10 table names"
provides:
  - "62 query SQL statements extracted (33 user + 29 hidden system) in assessment/queries/_raw_queries.json"
  - "Query catalogue with type classification and English purpose annotations in assessment/queries/_overview.md"
  - "Mermaid dependency graph + hub table/query analysis in assessment/queries/dependency_graph.md"
  - "Rerunnable extraction script scripts/extract_query_sql.py using Jackcess via JPype"
  - "Rerunnable analysis script scripts/analyze_queries.py for document regeneration"
  - "Jackcess 4.0.8 + dependencies in lib/ for future Java-based Access reading"
affects: [03-03-business-logic-synthesis, 04-translation-and-synthesis]

# Tech tracking
tech-stack:
  added: [openjdk-11, jpype1-1.6.0, jackcess-4.0.8, commons-lang3-3.14.0, commons-logging-1.3.0]
  patterns: [JPype JVM startup with JAVA_HOME auto-detection, Jackcess toSQLString() for SQL reconstruction, safe_id() hash for Mermaid node IDs with Thai names]

key-files:
  created:
    - scripts/extract_query_sql.py
    - scripts/analyze_queries.py
    - assessment/queries/_raw_queries.json
    - assessment/queries/_overview.md
    - assessment/queries/dependency_graph.md
    - lib/jackcess-4.0.8.jar
    - lib/commons-lang3-3.14.0.jar
    - lib/commons-logging-1.3.0.jar
  modified: []

key-decisions:
  - "Java 11 via Homebrew added as bridge dependency for Jackcess -- not replacing Python parser, enabling query SQL extraction on macOS"
  - "Jackcess found 33 user queries (vs 32 from MSysObjects) -- extra query qry_ร้านค้าส่งของให้ก่อน was missed by MSysObjects enumeration"
  - "All 62 queries classified as SELECT (61) or UNION (1) from actual SQL -- confirming MSysObjects flags were correct but now validated"
  - "Hidden ~sq_* subqueries categorized into 3 types: ~sq_c (subform sources, 8), ~sq_d (lookup/combo sources, 14), ~sq_r (report record sources, 7)"
  - "Hub tables identified: สินค้า (26 refs), รายละเอียดออเดอร์ (23 refs) -- these are the core data tables for the business"
  - "Hub queries identified: qry สินค้าในแต่ละออเดอร์ร้านค้า (11 dependents) is the most-referenced query -- central to shop order processing"

patterns-established:
  - "extract_query_sql.py pattern: JPype JVM startup -> Jackcess DatabaseBuilder.open -> getQueries() -> toSQLString() -> JSON output"
  - "analyze_queries.py pattern: load raw JSON -> classify SQL type -> extract references -> generate purpose annotations -> produce markdown docs"
  - "safe_id() for Mermaid: MD5 hash of Thai name truncated to 8 chars with 'n' prefix for valid node IDs"

# Metrics
duration: ~6min
completed: 2026-02-15
---

# Phase 3 Plan 1: Query SQL Extraction and Assessment Summary

**62 query SQL statements extracted via Jackcess/JPype with type classification, English purpose annotations, dependency graph, and hub table/query identification**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-02-14T18:14:05Z
- **Completed:** 2026-02-14T18:20:03Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Extracted all 62 query SQL statements from epic_db.accdb using Jackcess 4.0.8 via JPype1 on macOS ARM -- 0 extraction errors
- Produced assessment/queries/_overview.md with complete catalogue of 33 user queries and 29 hidden system subqueries, each with type classification and English purpose annotation
- Produced assessment/queries/dependency_graph.md with Mermaid visualization showing table-to-query and query-to-query data flow
- Identified hub tables (สินค้า: 26 refs, รายละเอียดออเดอร์: 23 refs) and hub queries (qry สินค้าในแต่ละออเดอร์ร้านค้า: 11 dependents) as core business data nodes
- Discovered 33 user queries (1 more than Phase 1 inventory's 32) -- qry_ร้านค้าส่งของให้ก่อน was not visible in MSysObjects enumeration
- Identified 7 parameterized queries (PARAMETERS keyword) and 10 form-referencing queries ([Forms]!... patterns)

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Java + Jackcess and create query SQL extraction script** - `872c64e` (feat)
2. **Task 2: Analyze queries and produce assessment documents** - `b8951bb` (feat)

## Files Created/Modified
- `scripts/extract_query_sql.py` - Jackcess/JPype query SQL extraction with JAVA_HOME auto-detection, error handling, and fallback messaging
- `scripts/analyze_queries.py` - SQL type classification, reference extraction, purpose annotation, and Markdown document generation
- `assessment/queries/_raw_queries.json` - Raw extraction output: 62 queries with name, type, SQL, error, hidden fields
- `assessment/queries/_overview.md` - Query catalogue with type distribution, parameterized query details, hidden subquery documentation
- `assessment/queries/dependency_graph.md` - Mermaid graph + dependency table + orphan/hub analysis
- `lib/jackcess-4.0.8.jar` - Jackcess library for Access database reading (1.3MB)
- `lib/commons-lang3-3.14.0.jar` - Jackcess dependency (658KB)
- `lib/commons-logging-1.3.0.jar` - Jackcess dependency (71KB)

## Decisions Made
- Added Java 11 via Homebrew as a bridge dependency. Phase 1 locked "Python-only dependencies" for the parser, but Java is needed for Jackcess -- the only reliable way to extract query SQL on macOS since MSysQueries is inaccessible via the Python parser.
- Included all hidden `~sq_*` system subqueries in extraction and documentation (per research Pitfall 7). These 29 hidden queries are essential data sources for forms and reports.
- Used actual SQL content for type classification instead of MSysObjects flags. All 32+1 user queries confirmed as SELECT (32) or UNION (1), matching the Phase 1 classification.
- Categorized hidden subqueries into 3 functional groups: `~sq_c` (subform control sources), `~sq_d` (lookup/combo data sources), `~sq_r` (report record sources).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added jpype.imports import for Java class interop**
- **Found during:** Task 1 (extract_query_sql.py execution)
- **Issue:** `from com.healthmarketscience.jackcess import DatabaseBuilder` failed with "No module named 'com'" because `jpype.imports` was not imported
- **Fix:** Added `import jpype.imports` to the start_jvm() function, which enables Python-style imports of Java packages
- **Files modified:** scripts/extract_query_sql.py
- **Verification:** Script ran successfully after fix, extracting all 62 queries
- **Committed in:** 872c64e (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Trivial fix for JPype import mechanism. No scope creep.

## Issues Encountered
- Jackcess extracted 33 user queries vs the 32 from Phase 1 MSysObjects inventory. The extra query `qry_ร้านค้าส่งของให้ก่อน` (shops requiring advance shipment) was not visible in the MSysObjects enumeration but is a valid user query. This is not an error -- Jackcess reads the query definitions directly from MSysQueries which has more complete visibility.

## User Setup Required

None - Java was installed via Homebrew automatically. JPype1 was installed in the project venv.

## Next Phase Readiness
- Query extraction complete: all SQL available for business logic synthesis in Plan 03-03
- Dependency graph available: shows data flow for process flow documentation
- Hub tables and hub queries identified: guides priority for business logic analysis
- Windows still needed for Plan 03-02: 17 forms and 25 reports require Access COM for content extraction
- The 10 form-referencing queries provide clues about form-query relationships ahead of Windows extraction

## Self-Check: PASSED

- FOUND: scripts/extract_query_sql.py
- FOUND: scripts/analyze_queries.py
- FOUND: assessment/queries/_raw_queries.json
- FOUND: assessment/queries/_overview.md
- FOUND: assessment/queries/dependency_graph.md
- FOUND: lib/jackcess-4.0.8.jar
- FOUND: lib/commons-lang3-3.14.0.jar
- FOUND: lib/commons-logging-1.3.0.jar
- FOUND: commit 872c64e
- FOUND: commit b8951bb

---
*Phase: 03-logic-and-interface-extraction*
*Completed: 2026-02-15*
