# Epic DB Assessment

## What This Is

A complete extraction and documentation of Epic Gear's RipRoy Access database (`epic_db.accdb`) — a ~10-year-old Microsoft Access system running a fishing lure manufacturing business in Samut Prakan, Thailand. The assessment extracts every table, relationship, query, form, report, and VBA module, translating all Thai content to English, producing a comprehensive blueprint for a future rebuild.

## Core Value

Extract and document all components from the Access database with enough fidelity and clarity that a complete rebuild can be executed from the assessment alone — no need to re-examine the .accdb file.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Extract all database tables with column definitions, data types, and relationships
- [ ] Document all queries with their SQL, purpose, and dependencies
- [ ] Catalogue all forms with their function, fields, and connected tables/queries
- [ ] Catalogue all reports with their function, layout purpose, and data sources
- [ ] Extract all VBA modules with business logic explained in English
- [ ] Document pricing and discount logic (volume discounts, customer overrides)
- [ ] Document formula/recipe logic (raw materials to finished products)
- [ ] Translate all Thai field names, labels, and data descriptions to English
- [ ] Map all table relationships (foreign keys, referential integrity)
- [ ] Produce assessment summary with rebuild feasibility and effort indicators

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Rebuilding the system as a web app — that's a separate project after this assessment
- Modifying or fixing the existing Access database — assessment is read-only
- Migrating data out of Access — extraction is documentation, not data migration
- Performance optimization of the Access DB — not relevant for assessment
- User training or documentation for the current Access system

## Context

- The .accdb file is located at `data/epic_db.accdb` (~10MB, no password)
- The entire interface and most data is in Thai — the owner cannot read Thai, making this translation critical
- The system was built by a non-programmer, so structure may be unconventional
- Current usage: 1-3 concurrent users, 10-50 orders/day, ~1,000 customers, ~10,000 orders, 8 products
- Python 3.11 is available via uv with a `.venv/` already set up — no dependencies installed yet
- The .accdb binary format requires programmatic extraction (e.g., mdbtools, pyodbc, or similar)
- Running on macOS (arm64) — some Access tools are Windows-only, so tooling choice matters
- Codebase map exists at `.planning/codebase/` with architecture and structure analysis

## Constraints

- **Platform**: macOS arm64 — cannot run Microsoft Access natively, need compatible extraction tools
- **File format**: Binary .accdb — requires specialized libraries to read programmatically
- **Language**: All Thai content must be translated to English in the assessment output
- **Read-only**: Assessment must not modify the original .accdb file
- **Tooling**: Python available; need to determine best library for .accdb on macOS (mdbtools, access-parser, etc.)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Full extraction (not selective) | Assessment is blueprint for rebuild — completeness matters | — Pending |
| Translate all Thai to English | Owner can't read Thai; rebuild will be English | — Pending |
| Python for extraction tooling | Available on machine, good library ecosystem for data work | — Pending |
| Output format: best for rebuild | Let extraction tooling and content determine optimal format | — Pending |

---
*Last updated: 2026-02-14 after initialization*
