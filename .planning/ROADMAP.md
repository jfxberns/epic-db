# Roadmap: Epic DB Assessment

## Overview

This roadmap delivers a complete extraction and documentation of Epic Gear's Access database (epic_db.accdb) -- a Thai-language fishing lure manufacturing system running for ~10 years. The work proceeds in four phases: validate tooling and environment, extract the schema foundation, extract all logic and interface components (queries, VBA, forms, reports), then translate everything to English and synthesize the final rebuild blueprint. Each phase gates the next -- tooling must work before extraction, schema must exist before logic extraction, and all components must be extracted before translation and cross-referencing can produce the final assessment.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Setup and Validation** - Validate extraction tooling, Thai encoding, and produce complete object inventory
- [ ] **Phase 2: Schema Foundation** - Extract all table definitions, relationships, indexes, and data profiles
- [ ] **Phase 3: Logic and Interface Extraction** - Extract all queries, VBA modules, forms, and reports with business logic documentation
- [ ] **Phase 4: Translation and Synthesis** - Translate all Thai content to English and produce the cross-referenced rebuild blueprint

## Phase Details

### Phase 1: Setup and Validation
**Goal**: Extraction environment is proven capable of reading all Access object types with correct Thai encoding
**Depends on**: Nothing (first phase)
**Requirements**: SETUP-01, SETUP-02, SETUP-03, SETUP-04
**Success Criteria** (what must be TRUE):
  1. User can run a Python script that reads table data from epic_db.accdb on macOS and outputs correctly rendered Thai text
  2. User can view a complete inventory of every object in the database (tables, queries, forms, reports, modules, macros) with counts per type
  3. User can confirm whether a Windows environment is needed for form/report/VBA extraction, and if needed, that environment is accessible
**Plans**: TBD

Plans:
- [ ] 01-01: TBD
- [ ] 01-02: TBD

### Phase 2: Schema Foundation
**Goal**: User has complete documentation of every table, column, relationship, and index in the database with sample data
**Depends on**: Phase 1
**Requirements**: SCHM-01, SCHM-02, SCHM-03, SCHM-04, SCHM-05
**Success Criteria** (what must be TRUE):
  1. User can view every table's column definitions including names, data types, sizes, nullable flags, and defaults
  2. User can view all relationships between tables -- both declared foreign keys and implicit relationships from MSysRelationships and lookup fields
  3. User can view all indexes and primary key / foreign key constraints per table
  4. User can view sample data (5-10 rows) from each table with row counts and can identify which tables appear abandoned or unused
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Logic and Interface Extraction
**Goal**: User has complete documentation of all queries, VBA business logic, forms, and reports -- the full logic and interface layer of the database
**Depends on**: Phase 2
**Requirements**: QURY-01, QURY-02, QURY-03, VBA-01, VBA-02, VBA-03, VBA-04, VBA-05, FORM-01, FORM-02, FORM-03
**Success Criteria** (what must be TRUE):
  1. User can view all query SQL with type classification (SELECT, UPDATE, crosstab, etc.) and purpose annotations, plus a dependency graph showing which queries reference which tables and other queries
  2. User can view all VBA modules (standalone and form/report code-behind) with event handlers identified and their triggers documented
  3. User can view pricing/discount logic and formula/recipe logic documented in plain English, synthesized from VBA, queries, and table rules
  4. User can view a catalogue of all forms and reports with their purpose, data sources, fields, and the form navigation workflow (which form opens which)
  5. User can view complete business process flows mapped across VBA, queries, and forms
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Translation and Synthesis
**Goal**: User has a fully English-translated, cross-referenced rebuild blueprint that stands alone as the complete specification for rebuilding the system
**Depends on**: Phase 3
**Requirements**: TRNS-01, TRNS-02, TRNS-03, SYNTH-01, SYNTH-02, SYNTH-03
**Success Criteria** (what must be TRUE):
  1. User can reference a Thai-English glossary with consistent translations for every field name, label, and business term found in the database
  2. User can view all extracted documentation (schema, queries, VBA, forms, reports) with Thai content translated to English, including identification of Buddhist calendar dates and Thai business term mappings
  3. User can view a cross-reference map showing how all components connect (tables to queries to forms to reports to VBA) with a textual entity-relationship diagram
  4. User can view a rebuild feasibility assessment with effort estimates per component
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Setup and Validation | 0/TBD | Not started | - |
| 2. Schema Foundation | 0/TBD | Not started | - |
| 3. Logic and Interface Extraction | 0/TBD | Not started | - |
| 4. Translation and Synthesis | 0/TBD | Not started | - |
