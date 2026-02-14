# Architecture Patterns: Access Database Extraction Pipeline

**Domain:** Access database assessment and extraction (read-only, documentation-focused)
**Researched:** 2026-02-14
**Confidence:** HIGH (well-established domain; Access internals are stable and well-documented)

## Recommended Architecture

The extraction pipeline follows a **layered read-extract-transform-document** pattern. The Access `.accdb` file is a single binary containing six distinct object categories, each with internal cross-references. The architecture must respect these dependencies to produce a coherent rebuild blueprint.

### High-Level Pipeline

```
epic_db.accdb (binary)
       |
  [1. PROBE] --- Tool discovery, file validation, object inventory
       |
  [2. EXTRACT SCHEMA] --- Tables, columns, types, relationships, indexes
       |
  [3. EXTRACT DATA SAMPLES] --- Representative rows per table (for context)
       |
  [4. EXTRACT QUERIES] --- Saved queries (SQL), parameter queries
       |
  [5. EXTRACT FORMS] --- Form definitions, controls, event bindings
       |
  [6. EXTRACT REPORTS] --- Report layouts, grouping, data sources
       |
  [7. EXTRACT VBA] --- All modules, class modules, form/report code-behind
       |
  [8. TRANSLATE] --- Thai labels/names/comments to English
       |
  [9. CROSS-REFERENCE] --- Build dependency map between all objects
       |
  [10. DOCUMENT] --- Structured output as rebuild blueprint
```

### Component Boundaries

| Component | Responsibility | Inputs | Outputs | Independent? |
|-----------|---------------|--------|---------|-------------|
| **Probe** | Validate file, detect tool capabilities, inventory all objects by type and count | `.accdb` file | Object manifest (tables, queries, forms, reports, modules list) | YES -- run first, gates everything |
| **Schema Extractor** | Extract table definitions, column metadata, relationships, indexes, constraints | `.accdb` file | `schema/` directory with per-table JSON/Markdown | YES -- no dependency on other extractors |
| **Data Sampler** | Pull representative rows from each table for context | `.accdb` file + schema output | `data-samples/` directory with per-table CSV/JSON | Depends on Schema (needs table list) |
| **Query Extractor** | Extract all saved queries as SQL text with metadata | `.accdb` file | `queries/` directory with per-query SQL files | YES -- independent extraction |
| **Form Extractor** | Extract form definitions, control layouts, event bindings | `.accdb` file | `forms/` directory with per-form documentation | YES -- but limited on macOS (see below) |
| **Report Extractor** | Extract report layouts, groupings, data sources | `.accdb` file | `reports/` directory with per-report documentation | YES -- but limited on macOS (see below) |
| **VBA Extractor** | Extract all VBA code: standard modules, class modules, form/report code-behind | `.accdb` file | `vba/` directory with per-module `.bas`/`.cls` files | YES -- but tool-dependent (see below) |
| **Translator** | Translate Thai field names, labels, UI text, comments to English | All extracted output | Annotated versions of all output files | Depends on ALL extractors completing |
| **Cross-Referencer** | Build dependency graph: which queries reference which tables, which forms use which queries, which VBA modules are called from where | All extracted output | `dependencies.md` -- full cross-reference map | Depends on ALL extractors completing |
| **Document Assembler** | Compile all extracted and translated content into structured blueprint | All translated + cross-referenced output | Final `assessment/` documentation tree | Depends on Translator + Cross-Referencer |

### What Can Be Extracted Independently (Parallel)

These four extraction steps have zero dependencies on each other and can run in parallel once Probe completes:

1. **Schema Extractor** -- tables, columns, relationships
2. **Query Extractor** -- saved SQL queries
3. **Form Extractor** -- form definitions (limited)
4. **Report Extractor** -- report definitions (limited)
5. **VBA Extractor** -- all code modules

After those complete, the sequential steps are:
- Data Sampler (needs schema)
- Translator (needs all raw extractions)
- Cross-Referencer (needs all raw extractions)
- Document Assembler (needs everything)

## Processing Order and Dependencies

This is the critical ordering. Getting this wrong means extracting things you cannot contextualize.

### Phase 1: Probe and Inventory (MUST be first)

**Why first:** You cannot plan extraction without knowing what exists. The probe reveals the object count, names, and tool capabilities -- which directly determines what the remaining phases can achieve.

**Deliverable:** Object manifest listing every table, query, form, report, macro, and module by name.

**Tool dependency:** `mdbtools` (`mdb-tables`, `mdb-queries`, etc.) or `access-parser` (Python). On macOS arm64, `mdbtools` is available via Homebrew and handles `.accdb` files. `access-parser` is a pure-Python alternative but has limitations with forms/reports.

### Phase 2: Schema Extraction (Foundation layer)

**Why second:** Schema is the foundation of the entire database. Every other object type (queries, forms, reports, VBA) references tables and columns. Without schema documentation, nothing else makes sense.

**Deliverable:** Per-table documentation including:
- Column names (Thai originals + English translations)
- Data types and sizes
- Primary keys
- Foreign key relationships
- Indexes
- Row counts

**Dependencies:** None (reads directly from `.accdb`).

**Key concern:** Thai column names and table names need to be preserved exactly as-is (for cross-referencing) AND translated (for understanding). Both versions must appear in output.

### Phase 3: Query Extraction (Logic layer)

**Why third:** Queries encode business logic as SQL. They reference tables (from Phase 2) and are referenced by forms and reports (Phases 4-5). Understanding queries requires schema context.

**Deliverable:** Per-query documentation including:
- Query name
- SQL text (raw)
- Query type (SELECT, INSERT, UPDATE, DELETE, crosstab, parameter)
- Tables referenced
- Parameters (if any)
- English translation of Thai elements

**Dependencies:** Schema (Phase 2) for context, but extraction itself is independent.

### Phase 4: Form Extraction (UI layer)

**Why after schema/queries:** Forms bind to tables and queries. Documenting a form without knowing its record source is useless. On macOS, form extraction is the most limited -- `mdbtools` cannot extract form layout/controls from `.accdb` files. Options:

1. **access-parser** (Python) -- can extract some form metadata but not full layout
2. **Manual via Windows VM** -- if available, Microsoft Access can export form definitions
3. **VBA code-behind** -- extract the VBA attached to forms (this IS possible via mdbtools/jackcess)

**Deliverable:** Per-form documentation including:
- Form name
- Record source (table or query)
- Control list (text boxes, combo boxes, buttons) with bound fields
- Event procedures (VBA code-behind)
- Navigation/workflow relationships (which form opens which)

**macOS limitation:** Full form layout extraction requires either a Windows environment or the `jackcess` Java library (which can read Access form XML). The VBA code-behind of forms IS extractable and is the highest-value component.

### Phase 5: Report Extraction (Output layer)

**Why after schema/queries:** Same rationale as forms -- reports bind to queries and tables. Reports also define the physical output (invoices, shipping labels) that the business depends on.

**Deliverable:** Per-report documentation including:
- Report name
- Record source (table or query)
- Grouping and sorting rules
- Calculated fields and expressions
- Layout purpose (invoice, label, summary, etc.)
- Page setup (dimensions, orientation) -- important for labels

**macOS limitation:** Same as forms. Report layout extraction is limited without Windows/Access. Prioritize extracting the record source, grouping, and calculated expressions.

### Phase 6: VBA Extraction (Business logic layer)

**Why after schema but can run parallel:** VBA modules contain the core business logic (pricing, discounts, formulas). They reference tables and queries but are extractable independently. Understanding them requires schema context.

**Deliverable:** Per-module documentation including:
- Module name and type (standard, class, form code-behind, report code-behind)
- Full source code
- Function/sub inventory with signatures
- English annotations explaining business logic
- Cross-references to tables, queries, forms called

**Key value:** VBA is where pricing logic, discount calculations, and formula/recipe calculations live. This is the highest-value extraction target for rebuild planning.

### Phase 7: Translation (Cross-cutting)

**Why last before assembly:** Translation touches every output from every previous phase. Running it as a dedicated pass ensures consistency (same Thai term always gets the same English translation).

**Deliverable:** Translation glossary + annotated versions of all extraction output.

**Approach:** Build a glossary first, then apply it systematically. This prevents inconsistent translations (e.g., the same Thai word translated differently in table names vs. form labels).

### Phase 8: Cross-Reference and Assembly (Synthesis)

**Why absolutely last:** This is where all individual extractions become a coherent blueprint. The cross-reference map shows how data flows through the system.

**Deliverable:**
- Object dependency graph
- Data flow diagrams (table -> query -> form/report)
- Business process documentation (order flow, pricing flow, inventory flow)
- Rebuild feasibility assessment

## Data Flow

### Within the Access Database (what we are documenting)

```
Tables (data storage)
  |
  v
Queries (data transformation / business logic as SQL)
  |
  +-------> Forms (data entry / user interaction)
  |            |
  |            v
  |         VBA Modules (business logic / validation / calculation)
  |            |
  |            v
  |         Tables (data written back)
  |
  +-------> Reports (data output / printing)
               |
               v
            Printer / Screen (invoices, labels, summaries)
```

### Within the Extraction Pipeline (what we are building)

```
epic_db.accdb
  |
  +--[mdbtools / access-parser]--> Raw schema JSON
  |                                  |
  +--[mdb-queries / SQL parse]----> Raw query SQL
  |                                  |
  +--[access-parser / jackcess]---> Raw form metadata
  |                                  |
  +--[access-parser / jackcess]---> Raw report metadata
  |                                  |
  +--[mdb-export / VBA parse]-----> Raw VBA source code
  |
  v
[Translation Engine] -- glossary-based Thai->English
  |
  v
[Cross-Reference Builder] -- dependency graph construction
  |
  v
[Document Assembler] -- structured Markdown output
  |
  v
docs/assessment/  (final blueprint)
```

## Output Organization (Blueprint Structure)

The output should be organized by object type, with a top-level index that ties everything together. This structure optimizes for the downstream consumer (a developer rebuilding the system).

```
docs/assessment/
├── README.md                    # Executive summary, how to use this blueprint
├── glossary.md                  # Thai-to-English translation glossary
├── dependencies.md              # Full cross-reference / dependency graph
│
├── schema/
│   ├── _overview.md             # Table inventory, relationship diagram (text-based)
│   ├── customers.md             # Per-table: columns, types, relationships, sample data
│   ├── orders.md
│   ├── order_details.md
│   ├── products.md
│   ├── inventory.md
│   ├── pricing.md
│   ├── discounts.md
│   └── [other tables].md
│
├── queries/
│   ├── _overview.md             # Query inventory, categorized by purpose
│   ├── [query_name].sql         # Raw SQL per query
│   └── [query_name].md          # Annotated explanation per query
│
├── forms/
│   ├── _overview.md             # Form inventory, workflow map
│   └── [form_name].md           # Per-form: purpose, record source, controls, VBA
│
├── reports/
│   ├── _overview.md             # Report inventory, categorized by type
│   └── [report_name].md         # Per-report: purpose, data source, layout, calculations
│
├── vba/
│   ├── _overview.md             # Module inventory, business logic map
│   ├── [module_name].bas        # Raw VBA source code
│   └── [module_name].md         # Annotated explanation with English comments
│
└── business-logic/
    ├── pricing.md               # Consolidated pricing logic (from VBA + queries + tables)
    ├── discounts.md             # Discount rules and override logic
    ├── formulas.md              # Recipe/formula calculations
    ├── order-flow.md            # End-to-end order processing workflow
    └── inventory-flow.md        # Inventory tracking and management workflow
```

### Why This Structure

1. **Per-object files** -- A developer rebuilding can look up any individual table, query, or form without reading the entire assessment.

2. **`_overview.md` indexes** -- Each directory has a summary file that provides the inventory and relationships for that object type. A developer reads the overview first, then dives into specifics.

3. **`business-logic/` consolidation** -- The most critical output for rebuild. Pricing, discounts, and formulas are scattered across VBA, queries, and table structures in Access. Consolidating them into dedicated files means a developer does not need to reconstruct business rules from raw extraction output.

4. **Raw + annotated** -- VBA source is preserved exactly (`.bas` files) AND explained in English (`.md` files). The raw source is the source of truth; the annotation is for understanding.

5. **`glossary.md` as single source** -- All Thai-to-English translations in one place. If a translation is wrong, fix it in one place and the meaning propagates.

6. **`dependencies.md` as the map** -- The cross-reference graph is the single most valuable document for rebuild planning. It answers "if I change table X, what breaks?"

## Patterns to Follow

### Pattern 1: Extract-Then-Annotate

**What:** Extract raw data first, annotate/translate second. Never mix extraction and interpretation in the same pass.

**Why:** Keeps extraction reproducible. If translations improve, re-run annotation without re-extracting. If the extraction tool changes, annotations are preserved.

**Implementation:**
```
Step 1: extract_schema() -> raw JSON/dict with Thai field names
Step 2: translate_schema(raw, glossary) -> annotated Markdown with both languages
```

### Pattern 2: Glossary-First Translation

**What:** Build a Thai-to-English glossary from all extracted content before translating anything. Then apply the glossary consistently.

**Why:** Without a glossary, the same Thai word gets translated differently in different contexts. The glossary ensures "field X in table Y" and "label X on form Z" both get the same English name.

**Implementation:**
```
Step 1: Collect all Thai strings from all extractions
Step 2: Deduplicate and translate (one pass, one glossary)
Step 3: Apply glossary to all output files
```

### Pattern 3: Dependency-Aware Documentation

**What:** Every documented object includes "References" (what it uses) and "Referenced By" (what uses it).

**Why:** A rebuild developer needs to know the impact of changing any object. Bidirectional references make this trivial.

**Example in a table doc:**
```markdown
## Table: Orders

### References
- Customers (foreign key: customer_id)
- Products (via OrderDetails junction table)

### Referenced By
- Query: qryOrdersByCustomer
- Query: qryMonthlyRevenue
- Form: frmOrderEntry
- Report: rptInvoice
- VBA: modPricing.CalculateOrderTotal()
```

### Pattern 4: Business Process Documentation Over Object Documentation

**What:** In addition to per-object docs, create end-to-end business process docs that trace data flow across multiple objects.

**Why:** A developer rebuilding the system needs to understand workflows, not just individual components. "How does an order get processed?" spans tables, forms, queries, VBA, and reports.

**Implementation:** The `business-logic/` directory consolidates cross-cutting concerns.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Monolithic Extraction Script

**What:** One giant Python script that extracts everything in sequence.

**Why bad:** If form extraction fails, you lose everything. If you need to re-run just VBA extraction, you re-run the whole pipeline.

**Instead:** Modular extractors per object type. Each can run independently. A coordinator script orchestrates them but each is self-contained.

### Anti-Pattern 2: Translation During Extraction

**What:** Translating Thai to English while extracting from the `.accdb` file.

**Why bad:** Mixes concerns. Translation quality depends on context (the same Thai word may mean different things in different tables). Extraction should be mechanical and reproducible; translation is interpretive.

**Instead:** Extract raw (preserving Thai), translate as a separate pass with full context.

### Anti-Pattern 3: Single Output File

**What:** One massive `assessment.md` file with everything.

**Why bad:** Unusable for rebuild. A developer cannot Ctrl+F through a 500-page document effectively. No granular version control.

**Instead:** Per-object files with overview indexes (see Output Organization above).

### Anti-Pattern 4: Extracting Data Without Schema Context

**What:** Dumping all table data to CSV without first understanding column types, relationships, and constraints.

**Why bad:** A CSV of 10,000 rows with columns named in Thai and no type information is useless. Schema context makes data samples meaningful.

**Instead:** Schema first, then selective data samples with annotations.

## Component Extraction Feasibility on macOS arm64

This is the critical platform constraint. Access is a Windows-native format.

| Component | mdbtools | access-parser (Python) | jackcess (Java) | Windows/Access |
|-----------|----------|----------------------|-----------------|----------------|
| Table schema | YES | YES | YES | YES |
| Table data | YES | YES | YES | YES |
| Relationships | YES (mdb-schema) | Partial | YES | YES |
| Queries (SQL) | YES (mdb-queries) | NO | YES | YES |
| Forms (layout) | NO | Partial (metadata) | Partial (XML) | YES (full) |
| Reports (layout) | NO | Partial (metadata) | Partial (XML) | YES (full) |
| VBA source code | NO | NO | NO | YES (full) |
| Macros | NO | Partial | Partial | YES (full) |

**Critical gap: VBA extraction on macOS.** None of the macOS-native tools can extract VBA source code from `.accdb` files. VBA is stored in a proprietary compressed binary stream within the file. Options:

1. **Use `oletools` (Python)** -- The `olevba` tool can extract VBA from OLE2 compound documents. `.accdb` files use a different container than `.mdb`, but `oletools` has some support. MEDIUM confidence this works for `.accdb`.

2. **Use a Windows VM or cloud instance** -- Run Microsoft Access on Windows to export VBA modules. This is the guaranteed approach but adds infrastructure complexity.

3. **Use `officeparser` or similar** -- Some Python libraries can parse Office Open XML and extract embedded VBA. Feasibility for `.accdb` is uncertain.

4. **Hybrid approach (recommended)** -- Extract everything possible on macOS first (schema, data, queries via mdbtools). For VBA and detailed form/report layouts, use a one-time Windows session (VM, remote desktop, or cloud instance).

## Scalability Considerations

| Concern | This Project (10MB DB) | Larger Access DBs (100MB+) | Notes |
|---------|----------------------|---------------------------|-------|
| Extraction time | Seconds per component | Minutes per component | Not a concern at this scale |
| Output size | ~50-100 files, ~1-2MB total | 500+ files, 10MB+ | Per-file structure scales well |
| Translation volume | Hundreds of Thai strings | Thousands | Glossary approach scales; LLM batch translation is fast |
| Cross-referencing | Manual verification feasible | Needs automated tooling | At this scale, manual review is practical |
| Data sampling | Full dump feasible for small tables | Sample-only for large tables | 10K orders is manageable as full export |

## Build Order Implications for Roadmap

Based on the dependency graph and platform constraints, the roadmap should follow this order:

### Phase 1: Tooling Setup and Probe
- Install `mdbtools` (Homebrew), `access-parser` (pip), `oletools` (pip)
- Validate each tool can read `epic_db.accdb`
- Generate complete object inventory
- **Gate:** Know exactly what exists before planning extraction

### Phase 2: Schema and Relationships
- Extract all table definitions, column metadata, relationships
- This is the foundation -- everything else references schema
- **Gate:** Complete schema documentation before moving to queries/VBA

### Phase 3: Queries and Data Samples
- Extract all saved queries as SQL
- Pull representative data samples from each table
- Can run in parallel with Phase 4 (VBA) if tooling allows
- **Gate:** Understand what data transformations exist

### Phase 4: VBA and Business Logic
- Extract all VBA modules (may require Windows tooling)
- This is the highest-risk phase due to macOS extraction limitations
- **Gate:** All business logic captured and documented

### Phase 5: Forms and Reports
- Extract form/report metadata (limited on macOS)
- Document record sources, controls, layout purposes
- Lower priority than schema/queries/VBA because forms/reports are UI, not logic
- **Gate:** UI layer documented sufficiently for rebuild

### Phase 6: Translation
- Build Thai-to-English glossary from all extracted content
- Apply glossary to all output files
- **Gate:** All output readable in English

### Phase 7: Cross-Reference and Assembly
- Build dependency graph
- Write business process documentation
- Compile final assessment with rebuild recommendations
- **Gate:** Complete blueprint ready for rebuild project

## Sources

- Microsoft Access binary format documentation (well-established, stable since Access 2007)
- mdbtools project documentation (open-source, actively maintained, macOS compatible via Homebrew)
- access-parser Python library (pure-Python Access parser, pip installable)
- jackcess Java library (most complete open-source Access parser, cross-platform via JVM)
- oletools Python library (OLE/VBA extraction toolkit)
- Training data knowledge of Access internals, extraction patterns, and macOS tooling constraints

**Confidence notes:**
- Schema/query extraction on macOS: HIGH confidence (mdbtools is proven)
- VBA extraction on macOS: LOW confidence (no confirmed tool; may require Windows)
- Form/report layout extraction on macOS: LOW confidence (partial metadata only)
- Output organization pattern: HIGH confidence (standard documentation architecture)
- Processing order and dependencies: HIGH confidence (inherent to Access object model)

---

*Architecture research: 2026-02-14*
