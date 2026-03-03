# Epic DB Assessment

## What This Is

A complete extraction, documentation, and English translation of Epic Gear's RipRoy Access database (`epic_db.accdb`) — a ~10-year-old Microsoft Access system running a fishing lure manufacturing business in Samut Prakan, Thailand. The assessment covers every table, relationship, query, form, report, and business logic formula, producing a comprehensive rebuild blueprint (`docs/BLUEPRINT.md`).

## Core Value

Extract and document all components from the Access database with enough fidelity and clarity that a complete rebuild can be executed from the assessment alone — no need to re-examine the .accdb file.

## Current State

**v1.0 shipped (2026-02-16)** — Full assessment complete.

Deliverable: `docs/BLUEPRINT.md` (3,045 lines) containing:
- 244-term Thai-English glossary with 3 lookup views
- Data model with ER diagrams for all 10 tables and 14 relationships
- 5 business domain sections with translated schemas, queries, forms, reports
- 8 workflow diagrams (shop/retail orders, inventory, points, payments, invoicing)
- Cross-reference maps and component connection diagrams
- Risks, anti-patterns, and 12 improvement opportunities
- Rebuild assessment: 3 tech stacks, 65 component estimates, 6-phase plan (214-442 hours)

Supporting artifacts in `assessment/` and `scripts/` directories.

## Requirements

### Validated

- ✓ Extract all database tables with column definitions, data types, and relationships — v1.0
- ✓ Document all queries with their SQL, purpose, and dependencies — v1.0
- ✓ Catalogue all forms with their function, fields, and connected tables/queries — v1.0 (4 previously-corrupt forms recovered from 2019 backup)
- ✓ Catalogue all reports with purpose, data sources, and output format — v1.0
- ✓ Extract all VBA modules with business logic explained in English — v1.0 (zero VBA found; all logic in SQL queries)
- ✓ Document pricing and discount logic — v1.0 (11 formulas documented)
- ✓ Document formula/recipe logic — v1.0 (no recipe logic found; business is retail/distribution, not manufacturing formulas)
- ✓ Translate all Thai field names, labels, and data descriptions to English — v1.0 (244 terms)
- ✓ Map all table relationships — v1.0 (14 relationships: 8 table-to-table, 4 table-to-query, 2 system)
- ✓ Produce assessment summary with rebuild feasibility and effort indicators — v1.0

### Active

(None — milestone complete. Use `/gsd:new-milestone` to define next scope.)

### Out of Scope

- Rebuilding the system as a web app — separate project after assessment
- Modifying or fixing the existing Access database — assessment is read-only
- Migrating data out of Access — extraction is documentation, not data migration
- Performance optimization of the Access DB — not relevant for assessment
- Pixel-perfect form/report layout capture — data bindings and purpose captured, not visual layout

## Context

- The .accdb file is located at `data/epic_db.accdb` (~10MB, no password)
- Database scale: 10 tables, 33 user queries, 29 hidden subqueries, 11 exported forms (4 recovered from 2019 backup), 11 reports
- Data scale: 30,016 total rows, ~1,000 customers, ~10,000 orders, 8 products
- All business logic lives in SQL calculated columns — zero VBA code-behind in any component
- 4 forms with corrupt VBA projects were recovered from the 2019-09-07 backup (frm_salesorder_fishingshop, frm_salesorder_retail, frm_stck_fishingshop, qry stck subform2) — corruption introduced between Sep 2019 and Jul 2020
- Python 3.11 via uv with access_parser_c + Jackcess 4.0.8 (via JPype1) for macOS extraction
- Windows (Access COM via UTM VM) used for SaveAsText form/report export
- Phase documents and verification reports in `.planning/phases/`

## Constraints

- **Platform**: macOS arm64 — cannot run Microsoft Access natively
- **File format**: Binary .accdb — requires specialized libraries
- **Language**: All Thai content translated to English in blueprint
- **Read-only**: Assessment did not modify the original .accdb file

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Full extraction (not selective) | Assessment is blueprint for rebuild — completeness matters | ✓ Good — 84 objects documented |
| Translate all Thai to English | Owner can't read Thai; rebuild will be English | ✓ Good — 244 terms glossary |
| Python for extraction tooling | Available on machine, good library ecosystem | ✓ Good — access_parser_c + Jackcess |
| McSash fork (access_parser_c) | Upstream access-parser incompatible with DB version | ✓ Good — all tables readable |
| Jackcess via JPype for queries | macOS can't run Access; Jackcess reads query SQL natively | ✓ Good — all 62 queries extracted |
| Windows VM for forms/reports | SaveAsText requires Access COM, unavailable on macOS | ✓ Good — 7 forms, 11 reports exported |
| 4-phase sequential structure | Each phase gates the next (tooling → schema → logic → translation) | ✓ Good — clean dependencies |
| Translation deferred to Phase 4 | Ensures glossary consistency across all terms | ✓ Good — 244 terms, 3 views |
| Risks as dedicated section | Consolidates anti-patterns rather than scattering per-component | ✓ Good — 12 improvement opportunities |
| Next.js + PostgreSQL recommended | Best bilingual i18n, modern stack, good fit for simple CRUD | — Pending (rebuild not started) |

---
*Last updated: 2026-03-03 — corrupt-form recovery complete, all todos closed*
