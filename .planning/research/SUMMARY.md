# Project Research Summary

**Project:** Epic DB Assessment -- Access Database Extraction & Documentation
**Domain:** Database Assessment and Migration Blueprint
**Researched:** 2026-02-14
**Confidence:** MEDIUM-HIGH

## Executive Summary

This project extracts and documents a 10-year-old Microsoft Access database (epic_db.accdb) built by a non-programmer for a Thai business. The database contains tables, queries, forms, reports, and VBA business logic that must be comprehensively documented to serve as a rebuild blueprint. The extraction must happen on macOS arm64, which creates significant tooling constraints. The recommended approach is a layered, hybrid extraction strategy: use mdbtools and access-parser on macOS for tables, schema, relationships, and queries, then use a Windows environment (VM or cloud instance) to extract forms, reports, and VBA modules which cannot be read by open-source tools on macOS. Thai text must be carefully handled (UTF-8 encoding validation) and systematically translated to English via glossary-based consistency.

The critical architectural insight is that Access databases built by non-programmers distribute business logic across multiple layers: table validation rules, query calculations, form event handlers (VBA), and implicit relationships not declared as foreign keys. The assessment must capture all these layers to serve as a complete rebuild blueprint. The extraction pipeline follows strict dependency ordering: schema foundation first (tables, relationships, indexes), then logic layer (queries, VBA), then interface layer (forms, reports), then translation and cross-referencing to tie everything together.

The highest-risk pitfall is attempting macOS-only extraction and missing forms, reports, and VBA entirely -- this would capture only 50% of the system. Secondary risks include Thai encoding corruption, incomplete relationship extraction (missing implicit relationships and lookup fields), and treating queries as "just SQL" rather than recognizing them as the primary business logic layer in non-programmer databases. These risks are all mitigated with proper tooling setup validation, early encoding tests with Thai sample data, MSysRelationships table extraction, and query dependency graphing.

## Key Findings

### Recommended Stack

The extraction requires a layered tooling approach because no single tool reads all Access components. mdbtools (Homebrew) provides robust table, schema, relationship, and query extraction on macOS. Python's access-parser provides deep binary parsing for system tables and metadata. oletools extracts VBA from OLE streams but may not support .accdb format VBA fully -- this needs early validation. pandas handles all tabular data manipulation and CSV processing. For forms, reports, and guaranteed VBA extraction, a Windows environment with Microsoft Access (even the free Runtime) is essential. Claude (already in the workflow) handles Thai-to-English translation with domain context.

**Core technologies:**
- **mdbtools (1.0+)**: CLI tools for tables, schema, relationships, queries -- only mature open-source Access reader on macOS
- **pandas (>=2.0)**: Data manipulation, CSV processing, analysis -- standard for tabular work
- **access-parser**: Python library for deep .accdb binary parsing -- extracts system tables and metadata where mdbtools cannot
- **oletools (>=0.60)**: VBA extraction from OLE streams -- established for Office macro extraction
- **Windows/Access environment**: For forms, reports, and guaranteed VBA extraction -- cannot be avoided for complete assessment

**Critical version note:** mdbtools must be 0.9+ for .accdb support. Verify with `mdb-ver data/epic_db.accdb` immediately after installation.

### Expected Features

The assessment deliverable is a rebuild blueprint, not iterative software. However, extraction phases are dependencies on each other.

**Must have (table stakes):**
- Table schema extraction (columns, types, constraints, PKs, FKs, indexes, validation rules)
- Relationship extraction (foreign keys, referential integrity, cascade rules) from MSysRelationships
- Query extraction with SQL text, type classification, dependency mapping
- VBA module extraction (all code including form/report code-behind)
- Form inventory with control bindings, record sources, event procedures
- Report inventory with grouping, data sources, calculated fields
- Thai-to-English translation of all UI labels, field names, comments
- Complete object inventory and cross-reference dependency map

**Should have (differentiators):**
- ERD generation from extracted relationships
- Data dictionary with business semantics (what each field means)
- Business logic summary (plain-English descriptions of VBA pricing/discount/formula logic)
- Query dependency graph visualization
- Data anomaly detection (orphaned records, integrity violations)
- Calculated field documentation across all forms and reports

**Defer:**
- Full data migration (sample data only for context -- 5-10 rows per table)
- Suggested normalized schema redesign (design decisions belong in rebuild phase)
- VBA-to-pseudocode translation (rebuild team can translate from VBA directly once stack chosen)
- Performance benchmarks of current system (meaningless for rebuild on different stack)

### Architecture Approach

The extraction pipeline is a read-extract-transform-document flow with strict dependency ordering. The .accdb file contains six object types (tables, queries, forms, reports, VBA, macros) with internal cross-references that must be respected. The architecture isolates each extraction component (schema, queries, forms, reports, VBA) as independent modules that can run in parallel once the probe phase completes. Schema extraction is the foundation -- all other objects reference tables and columns. After parallel extraction of all components, sequential synthesis phases (translation, cross-referencing, documentation assembly) tie everything together into the final blueprint.

**Major components:**
1. **Probe** -- Validate file, inventory all objects, detect tool capabilities (gates everything)
2. **Schema Extractor** -- Tables, columns, types, relationships, indexes, constraints (foundation for all else)
3. **Query Extractor** -- Saved queries with SQL, type classification, dependency graph (logic layer)
4. **VBA Extractor** -- All modules including form/report code-behind (business logic layer)
5. **Form/Report Extractor** -- UI definitions, control bindings, event handlers (interface layer)
6. **Translator** -- Thai-to-English glossary-based translation (cross-cutting)
7. **Cross-Referencer** -- Dependency graph builder (synthesis)
8. **Document Assembler** -- Final blueprint output (synthesis)

**Output structure:** Per-object markdown files organized by type (schema/, queries/, forms/, reports/, vba/), plus business-logic/ consolidation directory that synthesizes pricing, discounts, and formulas from scattered VBA/query/table sources. Each directory has an _overview.md index. Top-level README.md, glossary.md, and dependencies.md provide navigation.

### Critical Pitfalls

1. **macOS tools cannot extract forms, reports, or VBA** -- mdbtools and access-parser read tables and queries but NOT UI objects or code. This is not a limitation to work around -- it is a fundamental constraint. Without Windows/Access, the assessment captures only 50% of the system. Prevention: Secure Windows environment (VM, cloud, or remote desktop) from day one. Test VBA extraction immediately in probe phase.

2. **Thai encoding corruption silently breaks extraction** -- Access databases from Thai Windows systems may use Windows-874/TIS-620 encoding. If mdbtools outputs garbled Thai characters, all translation fails. Prevention: Extract one known-Thai table in probe phase, visually verify characters render correctly, experiment with `mdb-export -e utf-8` or `-e cp874` until correct, document encoding setting in config for all subsequent extractions.

3. **Implicit relationships are missed** -- Non-programmer Access databases have relationships defined in MSysRelationships and lookup fields that do not appear in table schema. Integer ID columns with no declared foreign key are often undocumented relationships. Prevention: Extract MSysRelationships system table explicitly with `mdb-export database.accdb MSysRelationships`, cross-reference all integer columns against queries and relationships, extract column properties (RowSource) for lookup fields.

4. **Queries ARE the business logic** -- In non-programmer databases, complex pricing and aggregation logic lives in stacked queries (queries referencing other queries). Treating queries as "just SQL" misses calculated columns, IIF expressions, and query chains that implement business rules. Prevention: Build query dependency graph showing which queries reference which tables and other queries, document all calculated columns separately, classify query types (SELECT/CROSSTAB/UPDATE/PARAMETER), identify queries that call VBA functions.

5. **Assessment scope underestimation** -- "Extract a database" sounds simple but a 10-year-old non-programmer Access system with Thai interface requires multi-phase extraction with encoding validation, Windows tooling setup, VBA code analysis, form workflow mapping, translation glossary creation, and comprehensive cross-referencing. Prevention: Explicit per-phase scope boundaries with verification gates, accept that Windows environment setup takes time, validate sample extraction against original after each phase.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Assessment Setup and Validation
**Rationale:** Must validate tooling and encoding before any bulk extraction. The macOS tooling limitation and Thai encoding risk are project-blocking if not addressed upfront. This phase gates everything else.

**Delivers:**
- Verified mdbtools installation with .accdb support
- Windows/Access environment secured (VM, cloud instance, or remote desktop)
- Thai encoding validated with sample extraction
- Complete object inventory (table/query/form/report/module counts)

**Addresses:**
- Pitfall 1 (macOS extraction limitations) -- validate Windows access
- Pitfall 2 (Thai encoding) -- test with known-Thai table
- Feature: Complete object inventory

**Avoids:** Proceeding with incomplete tooling and discovering forms/VBA cannot be extracted after tables are done

**Research flag:** No additional research needed -- standard setup and validation

### Phase 2: Schema Foundation
**Rationale:** Schema is the foundation. Every other object type (queries, forms, reports, VBA) references tables and columns. Cannot document anything else without schema context. Relationships define data integrity rules that the rebuild must preserve.

**Delivers:**
- All table schemas (columns, types, sizes, nullable, defaults)
- Primary keys and indexes
- Relationships from MSysRelationships (FKs, referential integrity, cascade rules)
- Lookup field definitions
- Row counts per table
- Sample data (5-10 rows per table) with Thai content

**Uses:** mdbtools (mdb-tables, mdb-schema, mdb-export), pandas

**Implements:** Schema Extractor component

**Addresses:**
- Features: Table schema extraction, relationship extraction, row counts, sample data
- Pitfall 4 (implicit relationships) -- MSysRelationships extraction required

**Avoids:** Missing implicit relationships and lookup field bindings

**Research flag:** No additional research needed -- well-documented mdbtools capabilities

### Phase 3: Query and Logic Extraction
**Rationale:** Queries encode data transformations and business logic as SQL. They reference tables (from Phase 2) and are referenced by forms/reports (Phase 4). Query dependency chains reveal calculation pipelines. Can run in parallel with VBA extraction (Phase 4) since both read from .accdb independently.

**Delivers:**
- All saved queries as SQL text
- Query type classification (SELECT/CROSSTAB/UPDATE/INSERT/DELETE/PARAMETER)
- Query dependency graph (which queries reference which tables and other queries)
- Calculated column documentation (IIF, Switch, Choose expressions)
- Parameter query definitions

**Uses:** mdbtools (mdb-queries), custom SQL parser for dependency extraction

**Implements:** Query Extractor component

**Addresses:**
- Features: Query extraction with SQL, query type classification, query dependency mapping
- Pitfall 5 (queries as business logic) -- dependency graph and calculated column docs

**Avoids:** Treating queries as flat SQL list instead of recognizing them as business logic layer

**Research flag:** No additional research needed -- query dependency parsing is straightforward

### Phase 4: VBA and Business Logic Extraction
**Rationale:** VBA contains core business logic (pricing, discounts, formulas/recipes). This is the highest-value extraction for rebuild. Can run in parallel with Phase 3 (queries). Must include form/report code-behind, not just standalone modules. HIGH RISK phase due to macOS tooling gaps.

**Delivers:**
- All VBA modules (.bas files) -- standard modules, class modules, form/report code-behind
- Module dependency map (which modules call which functions)
- External library references (COM dependencies)
- Business logic summary in plain English (pricing rules, discount logic, formula calculations)

**Uses:** Windows/Access with VBA export, oletools (if .accdb VBA extraction works), access-parser

**Implements:** VBA Extractor component

**Addresses:**
- Features: VBA module extraction, module dependency mapping, external library references, business logic summary
- Pitfall 3 (VBA extraction failure) -- Windows fallback plan required

**Avoids:** Missing form/report code-behind by only extracting standalone modules

**Research flag:** MEDIUM -- oletools .accdb VBA support needs validation in probe phase. If oletools fails, Windows/Access export is the fallback (well-documented).

### Phase 5: Forms and Reports Interface Layer
**Rationale:** Forms define data entry workflows and user experience. Reports define business outputs (invoices, labels). Lower priority than schema/queries/VBA because UI can be understood from data bindings even if pixel-perfect layout cannot be extracted on macOS. Depends on schema (record sources) and VBA (event procedures).

**Delivers:**
- Form inventory with record sources (which table/query each form edits)
- Form control listings (text boxes, combo boxes, buttons) with bound fields
- Form event procedures (button clicks, validation, cascading updates)
- Form navigation map (which form opens which)
- Report inventory with record sources, grouping rules, calculated fields

**Uses:** Windows/Access with Application.SaveAsText for forms/reports, access-parser for partial metadata

**Implements:** Form/Report Extractor component

**Addresses:**
- Features: Form extraction, form-to-table bindings, subform relationships, form event procedures, report extraction, report grouping
- Pitfall 7 (workflow not captured) -- explicit navigation mapping required

**Avoids:** Extracting form metadata without documenting user workflows and navigation flow

**Research flag:** No additional research needed -- standard form/report extraction patterns

### Phase 6: Translation and Glossary
**Rationale:** Translation touches all output from all previous phases. Running as dedicated pass after all extraction ensures consistency (same Thai term always gets same English translation). Glossary-first approach prevents inconsistent translations across different files.

**Delivers:**
- Thai-to-English glossary (all field names, labels, UI text, comments)
- Annotated versions of all extraction output with English translations
- Translation validation with business owner for critical terms (pricing, products, customers)

**Uses:** Claude API (already in workflow), glossary-based mechanical application

**Implements:** Translator component

**Addresses:**
- Features: Thai-to-English translation of labels, Thai field name mapping, Thai data sample translation
- Pitfall 11 (inconsistent translation) -- glossary-first approach required

**Avoids:** Translating during extraction, causing context loss and inconsistencies

**Research flag:** No additional research needed -- translation is straightforward with glossary approach

### Phase 7: Cross-Reference and Final Assessment
**Rationale:** All individual extractions become a coherent blueprint. Dependency map is the single most valuable rebuild artifact (shows "if I change X, what breaks?"). Business logic consolidation synthesizes pricing/discount/formula logic from scattered VBA, queries, and tables into unified documentation.

**Delivers:**
- Complete object dependency graph (bidirectional references)
- Data flow diagrams (table -> query -> form/report chains)
- Business process documentation (order flow, pricing flow, inventory flow)
- Rebuild effort estimate
- Final assessment documentation tree (schema/, queries/, forms/, reports/, vba/, business-logic/)

**Uses:** All previous phase outputs

**Implements:** Cross-Referencer and Document Assembler components

**Addresses:**
- Features: Complete object inventory, data flow diagram, business logic summary, rebuild effort estimate
- Pitfall 9 (not documenting gaps) -- explicit completeness statements per category

**Avoids:** Presenting parts list without assembly manual (structure without workflow understanding)

**Research flag:** No additional research needed -- synthesis patterns are well-established

### Phase Ordering Rationale

- **Phase 1 first** because tooling validation is a gate for everything. Cannot extract without working tools and encoding.
- **Phase 2 second** because schema is the foundation. All objects reference tables/columns.
- **Phases 3 & 4 parallel** because queries and VBA both read from .accdb independently. No cross-dependency.
- **Phase 5 after 2-4** because forms/reports depend on understanding schema (record sources) and VBA (event procedures).
- **Phase 6 after 2-5** because translation needs all raw extracted content to build complete glossary.
- **Phase 7 last** because cross-referencing requires all components extracted and translated.

This ordering respects the inherent dependencies in the Access object model while maximizing parallelization where possible.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 4 (VBA Extraction):** oletools .accdb VBA support is MEDIUM confidence -- needs validation in probe. If it fails, fallback to Windows/Access VBA export is well-documented but requires environment setup research.

Phases with standard patterns (skip research-phase):
- **Phase 1:** Tooling installation and validation is standard DevOps
- **Phase 2:** mdbtools schema extraction is well-documented with stable APIs
- **Phase 3:** Query extraction and SQL parsing is straightforward
- **Phase 5:** Form/report extraction via Windows/Access is established
- **Phase 6:** Translation with glossary is standard localization pattern
- **Phase 7:** Documentation synthesis is standard technical writing

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | mdbtools/pandas/access-parser recommendations are HIGH confidence (proven tools). oletools .accdb VBA support is MEDIUM (needs validation). Version numbers unverified against live sources but architecture is sound. |
| Features | HIGH | Access object model is stable for 20+ years. Table stakes features (tables, queries, forms, reports, VBA) are canonical. Platform extraction constraints are well-documented. |
| Architecture | HIGH | Layered extraction pipeline with dependency ordering is standard for Access assessment. Output structure optimized for rebuild consumption is well-established pattern. |
| Pitfalls | HIGH | macOS tooling limitations are well-documented. Thai encoding issues are common in multi-language databases. Non-programmer Access patterns (implicit relationships, query chains) are universal in this domain. |

**Overall confidence:** MEDIUM-HIGH

Confidence is not higher because:
- Tool version numbers could not be verified against live package repositories
- oletools .accdb VBA support needs empirical validation
- Thai encoding (UTF-8 vs CP874/TIS-620) must be tested with actual file
- Buddhist calendar date usage (if present) needs verification

Confidence is not lower because:
- Core architecture (mdbtools for tables, Windows/Access for forms/VBA) is proven
- Access binary format and object model are stable and well-documented
- Pitfalls are based on established domain expertise in Access migration

### Gaps to Address

- **VBA extraction method:** Validate oletools with epic_db.accdb in probe phase. If it fails, Windows/Access VBA export is the fallback. This must be resolved in Phase 1.
- **Thai encoding:** Test with sample extraction immediately. Document correct encoding flags for mdbtools before bulk extraction.
- **Windows environment access:** Confirm availability of Windows VM, cloud instance, or remote Windows machine with Access installed before starting Phase 4/5.
- **Buddhist calendar dates:** Check if dates use Buddhist calendar (year 2567 = Gregorian 2024). If yes, document conversion logic.
- **Linked tables:** Check MSysObjects for Type 6 (linked tables). If found, document connection strings and external dependencies.
- **OLE/Attachment fields:** Check schema for OLE Object or Attachment columns. If found, flag as requiring Windows extraction.

All gaps are resolvable in Phase 1 (probe and validation) before bulk extraction begins.

## Sources

### From STACK.md
- mdbtools GitHub (https://github.com/mdbtools/mdbtools) -- HIGH confidence, well-maintained, 1000+ stars
- access-parser PyPI (https://pypi.org/project/access-parser/) -- MEDIUM confidence, smaller project
- oletools GitHub (https://github.com/decalage2/oletools) -- HIGH confidence, security-focused, actively maintained
- pandas documentation (https://pandas.pydata.org/) -- HIGH confidence
- Training data knowledge of Access binary format internals -- MEDIUM confidence

### From FEATURES.md
- Microsoft Access developer documentation (DAO object model, MSysObjects schema) -- stable since Access 2007, HIGH confidence
- Access database migration assessment best practices -- well-established domain, HIGH confidence
- macOS extraction tooling capabilities -- based on tool documentation, MEDIUM confidence

### From ARCHITECTURE.md
- Microsoft Access binary format documentation -- well-established, stable since Access 2007, HIGH confidence
- mdbtools project documentation -- open-source, actively maintained, macOS compatible via Homebrew, HIGH confidence
- jackcess Java library -- most complete open-source Access parser, cross-platform via JVM, HIGH confidence
- Training data knowledge of Access internals, extraction patterns, and macOS tooling constraints -- MEDIUM-HIGH confidence

### From PITFALLS.md
- mdbtools issue tracker (common user-reported problems) -- HIGH confidence
- Access database migration best practices -- well-established domain, HIGH confidence
- Unicode encoding handling for Thai text (TIS-620/Windows-874) -- HIGH confidence
- Domain expertise with Access migration projects -- HIGH confidence

### Overall Source Quality
All four research files synthesized findings from established tools, official documentation, and domain expertise. No web verification tools were available during research, so version numbers and current tool capabilities should be verified at installation time. Core architectural recommendations (mdbtools + Windows/Access hybrid approach) are HIGH confidence based on well-documented tool capabilities.

---
*Research completed: 2026-02-14*
*Ready for roadmap: yes*
