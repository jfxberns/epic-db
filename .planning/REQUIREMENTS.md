# Requirements: Epic DB Assessment

**Defined:** 2026-02-14
**Core Value:** Extract and document all components from the Access database with enough fidelity that a complete rebuild can be executed from the assessment alone

## v1 Requirements

Requirements for complete assessment. Each maps to roadmap phases.

### Setup & Tooling

- [ ] **SETUP-01**: Python extraction environment configured with all necessary libraries for .accdb reading on macOS
- [ ] **SETUP-02**: Thai text encoding validated against sample data before bulk extraction
- [ ] **SETUP-03**: Windows environment identified and validated for form/report/VBA extraction (if macOS tools insufficient)
- [ ] **SETUP-04**: Complete inventory of all Access objects in epic_db.accdb (tables, queries, forms, reports, modules, macros)

### Schema & Data

- [ ] **SCHM-01**: User can view all table definitions with column names, data types, and sizes
- [ ] **SCHM-02**: User can view all declared and implicit relationships between tables (foreign keys, lookup fields)
- [ ] **SCHM-03**: User can view all indexes and primary/foreign key constraints per table
- [ ] **SCHM-04**: User can view sample data from each table with row counts and data profiling
- [ ] **SCHM-05**: User can identify abandoned or unused tables via reference analysis

### Queries

- [ ] **QURY-01**: User can view all query SQL extracted with purpose annotations
- [ ] **QURY-02**: User can view query dependency graph showing which queries reference other queries
- [ ] **QURY-03**: User can view queries classified by type (SELECT, UPDATE, crosstab, action, etc.) with referenced tables mapped

### VBA & Business Logic

- [ ] **VBA-01**: User can view all VBA modules extracted (standalone modules and form/report code-behind)
- [ ] **VBA-02**: User can view pricing and discount calculation logic documented in English
- [ ] **VBA-03**: User can view formula/recipe logic documented (raw materials to finished products mapping)
- [ ] **VBA-04**: User can view complete business process flows mapped across VBA, queries, and forms
- [ ] **VBA-05**: User can view all event handlers identified with their triggers and effects

### Forms & Reports

- [ ] **FORM-01**: User can view catalogue of all forms with their purpose, fields, and connected data sources
- [ ] **FORM-02**: User can view catalogue of all reports with purpose, data sources, and output format
- [ ] **FORM-03**: User can view form navigation workflow (which form opens which, menu structure)

### Translation

- [ ] **TRNS-01**: User can reference a Thai-English glossary with consistent translations for all field names and business terms
- [ ] **TRNS-02**: User can view all field names, form labels, and report headers translated to English
- [ ] **TRNS-03**: User can identify date fields using Buddhist calendar (BE) vs Gregorian and Thai business term mappings

### Assessment Synthesis

- [ ] **SYNTH-01**: User can view cross-reference map showing how all components connect (tables -> queries -> forms -> reports -> VBA)
- [ ] **SYNTH-02**: User can view complete entity-relationship diagram (textual) of the data model
- [ ] **SYNTH-03**: User can view rebuild feasibility assessment with effort estimates per component

## v2 Requirements

### Data Migration

- **MIGR-01**: Export all data from Access tables to portable format (CSV, JSON, or SQL)
- **MIGR-02**: Data cleaning and deduplication of customer records
- **MIGR-03**: Date format normalization (Buddhist to Gregorian if applicable)

### Enhanced Documentation

- **DOC-01**: Visual entity-relationship diagrams (generated images, not just textual)
- **DOC-02**: Interactive data dictionary with search
- **DOC-03**: Side-by-side Thai/English comparison views

## Out of Scope

| Feature | Reason |
|---------|--------|
| Rebuilding as web app | Separate project after assessment is complete |
| Modifying the Access database | Assessment is read-only; no changes to source |
| Performance optimization | Not relevant for documentation project |
| User training on Access | Goal is extraction, not continued Access usage |
| Pixel-perfect form/report layout capture | Data bindings and purpose matter for rebuild, not exact visual layout |
| Migrating live data out of Access | Assessment documents structure and logic, not data migration |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | — | Pending |
| SETUP-02 | — | Pending |
| SETUP-03 | — | Pending |
| SETUP-04 | — | Pending |
| SCHM-01 | — | Pending |
| SCHM-02 | — | Pending |
| SCHM-03 | — | Pending |
| SCHM-04 | — | Pending |
| SCHM-05 | — | Pending |
| QURY-01 | — | Pending |
| QURY-02 | — | Pending |
| QURY-03 | — | Pending |
| VBA-01 | — | Pending |
| VBA-02 | — | Pending |
| VBA-03 | — | Pending |
| VBA-04 | — | Pending |
| VBA-05 | — | Pending |
| FORM-01 | — | Pending |
| FORM-02 | — | Pending |
| FORM-03 | — | Pending |
| TRNS-01 | — | Pending |
| TRNS-02 | — | Pending |
| TRNS-03 | — | Pending |
| SYNTH-01 | — | Pending |
| SYNTH-02 | — | Pending |
| SYNTH-03 | — | Pending |

**Coverage:**
- v1 requirements: 26 total
- Mapped to phases: 0
- Unmapped: 26 ⚠️

---
*Requirements defined: 2026-02-14*
*Last updated: 2026-02-14 after initial definition*
