# Phase 1: Setup and Validation - Context

**Gathered:** 2026-02-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate that Python extraction tooling can read all Access object types from epic_db.accdb on macOS with correct Thai encoding, and produce a complete inventory of every object in the database. This phase gates all subsequent extraction work.

</domain>

<decisions>
## Implementation Decisions

### Tooling preferences
- Claude's discretion on which tool to try first (mdbtools, access-parser, or other Python libraries)
- Python-only dependencies — no Homebrew. Everything must install via pip/uv into the project venv
- Mix tools if needed — use different tools per object type rather than requiring one tool to handle everything
- Validation bar: tool must successfully read ALL tables and queries (not just one sample) before we commit to it

### Output & inventory format
- Inventory as a Markdown document in `assessment/` top-level folder
- Include brief metadata per object: row counts for tables, query type (SELECT/UPDATE/etc.), module line counts where available
- Extraction scripts should be kept as clean, reusable tools — not throwaway code. The .accdb may need re-extraction
- Subfolders per object type within assessment/ (tables/, queries/, etc.)

### Windows fallback strategy
- User can set up a Windows VM but doesn't have one now
- Claude decides when to recommend Windows vs. keep trying macOS — based on what tool validation reveals
- Windows threshold: if macOS tools can't even LIST forms/reports/VBA names, Windows is needed. If names are accessible but detail isn't, that's still macOS-viable
- If Windows is needed, scripts must be fully automated/headless — user runs one command, gets output files

### Thai encoding
- Correct Thai rendering is a BLOCKER — do not proceed to Phase 2 if encoding is broken (mojibake)
- Both column/field names AND row data must render Thai correctly
- User can spot-check some Thai but cannot read it fluently — validation should include visual output the user can verify with help
- No known reference values yet — user can check the database to get test values if needed

### Claude's Discretion
- Specific tool selection and evaluation order
- When to recommend Windows vs. exhaust macOS options
- Encoding detection and fix strategy
- Script architecture and module organization
- Assessment directory internal structure beyond the top-level convention

</decisions>

<specifics>
## Specific Ideas

- Assessment outputs live in `assessment/` with subfolders per object type
- Scripts should be rerunnable — if the .accdb file updates, re-extraction should be straightforward
- The inventory is meant to answer "what's in this database?" at a glance before deep extraction begins

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-setup-and-validation*
*Context gathered: 2026-02-14*
