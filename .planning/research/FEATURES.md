# Feature Landscape

**Domain:** Microsoft Access Database Assessment and Extraction (Migration Blueprint)
**Researched:** 2026-02-14

## Table Stakes

Features that must be present or the assessment is incomplete. Missing any of these means a rebuild team would need to re-examine the original .accdb file, defeating the purpose.

### Data Layer Extraction

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Table schema extraction** (all tables) | Foundation of the entire database; without column names, data types, sizes, nullable flags, defaults, the rebuild has no starting point | Low | Access stores this in MSysObjects + system tables. Extract: table name, column name, data type, size, required/nullable, default value, description, validation rule, validation text |
| **Primary key identification** | Cannot rebuild relational integrity without knowing which columns are primary keys | Low | Stored in table indexes with Primary flag |
| **Foreign key / relationship extraction** | The relationship graph is the skeleton of the system; without it, tables are just disconnected spreadsheets | Medium | Access stores relationships in MSysRelationships. Extract: parent table, child table, parent column, child column, enforce referential integrity flag, cascade update, cascade delete |
| **Index extraction** | Indexes encode performance decisions and uniqueness constraints; unique indexes are business rules (e.g., "no duplicate customer codes") | Low | Stored alongside table definitions. Extract: index name, table, columns, unique flag, primary flag |
| **Table row counts** | Rebuild team needs to know data volume per table for capacity planning and testing | Low | Simple COUNT(*) per table |
| **Sample data per table** | Schema alone is ambiguous -- seeing 5-10 rows reveals what fields actually contain (especially important for Thai content where field names may be cryptic) | Low | SELECT TOP 10 from each table; critical for understanding data patterns |
| **Validation rules (table-level and field-level)** | These are business rules baked into the schema; missing them means silent data integrity regressions in the rebuild | Medium | Access stores validation rules as expressions on fields and tables. Extract the expression text and the validation error message |

### Query Extraction

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **All saved queries with SQL** | Queries encode business logic, reporting aggregations, and data transformations. They are first-class objects in Access used by forms and reports | Medium | Access stores query SQL in MSysQueries or accessible via QueryDef objects. Extract: query name, SQL text, query type (Select/Action/Crosstab/Union/PassThrough) |
| **Query type classification** | Select queries vs Action queries (UPDATE/INSERT/DELETE/MAKE TABLE) have radically different rebuild implications -- action queries are automated business operations | Low | Derivable from SQL parsing or QueryDef.Type property |
| **Query parameter identification** | Parameterized queries are reusable components; parameters define the interface contract | Medium | Parameters are declared in query design or implicit from form references. Extract parameter name, data type, prompt text |
| **Query dependency mapping** | Queries reference tables and other queries; the dependency graph determines build order and reveals hidden coupling | Medium | Parse SQL to extract FROM/JOIN/IN references. Build directed dependency graph |

### Form Extraction

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Form inventory with purpose** | Forms are the user interface; the rebuild must replicate the same workflows | Medium | Extract: form name, record source (bound table/query), description. Infer purpose from record source and control names |
| **Form field/control listing** | Each control maps to a UI element in the rebuild. Missing a control means missing a feature | High | Access forms contain controls (TextBox, ComboBox, ListBox, Button, SubForm, etc.). Extract: control name, control type, control source (bound column), label text, default value, input mask, validation rule |
| **Form-to-table/query binding** | Which form reads/writes which table is the core of the data flow architecture | Medium | RecordSource property on the form + ControlSource on each bound control |
| **Subform relationships** | Subforms implement master-detail patterns (e.g., Order header -> Order lines). Missing these means missing the UI architecture | High | Extract: parent form, child subform, link master fields, link child fields. These define the master-detail join |
| **Form event procedures (VBA)** | Button clicks, on-load, before-update handlers contain business logic. A "Save Order" button that runs validation + calculation is core business logic, not just UI | High | Extract VBA code behind each form. Map event name (OnClick, BeforeUpdate, AfterUpdate, OnOpen, OnClose) to the code it runs |

### Report Extraction

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Report inventory with purpose** | Reports are business outputs (invoices, shipping labels, inventory summaries). The rebuild must produce identical outputs | Medium | Extract: report name, record source, description |
| **Report field/control listing** | Which data appears on each report and how it is calculated | Medium | Extract: control name, control source, format string, calculated expressions |
| **Report grouping and sorting** | Report structure (group by customer, sort by date, subtotals per group) defines the output format | Medium | Access reports have GroupLevel objects: field name, group on, sort order, group header/footer visibility |
| **Report parameters and filters** | How reports are filtered (date range, customer, product) defines the report's interface | Medium | WhereCondition passed from calling form or hardcoded filter |

### VBA Module Extraction

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **All standard modules with source code** | Standard modules contain shared business logic (pricing calculations, discount formulas, utility functions) | Medium | Access stores VBA in binary format within the .accdb. Extract via COM automation, mdbtools, or access-parser |
| **All class modules with source code** | Class modules define custom objects (if any). Less common in non-programmer-built databases but must be checked | Medium | Same extraction method as standard modules |
| **Form/Report code-behind modules** | Event handlers and helper functions attached to specific forms/reports | High | Each form/report can have its own VBA module. Extract and associate with the parent form/report |
| **Module dependency mapping** | Which modules call which other modules; which reference external libraries | Medium | Parse VBA for function calls, references to other modules. Document call graph |
| **External library references** | VBA projects can reference external COM libraries (e.g., Microsoft Excel, Outlook, DAO, ADO). These are hidden dependencies | Medium | References collection in VBA project. Extract: library name, GUID, version, path |

### Translation Layer

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Thai-to-English translation of all UI labels** | Owner cannot read Thai. Rebuild will be in English. Every form label, button caption, column header, report title, error message must be translated | High | Volume is the challenge: potentially hundreds of labels across all forms and reports. Need consistent translation of domain terms (e.g., the Thai word for "customer" should always translate the same way) |
| **Thai field name mapping** | If table/field names are in Thai, create a consistent English name mapping for the rebuild schema | Medium | May or may not apply -- field names might already be in English per the architecture analysis. Verify during extraction |
| **Thai data sample translation** | Sample data in Thai needs translation to verify understanding of what each field contains | Medium | Translate sample rows from each table. Critical for fields where the column name is ambiguous |

### Assessment Documentation

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Complete object inventory** | Summary count: N tables, N queries, N forms, N reports, N modules. Gives rebuild team scope at a glance | Low | Enumerate all objects from MSysObjects or equivalent |
| **Data flow diagram** | How data moves through the system: which forms write to which tables, which queries feed which reports | Medium | Synthesized from form record sources, query dependencies, and report record sources |
| **Business logic summary** | Plain-English description of what the VBA code does: pricing rules, discount tiers, formula calculations | High | Requires reading and understanding VBA code, then documenting the business rules it implements |
| **Rebuild effort estimate** | Hours/complexity per component. The assessment's ultimate deliverable for decision-making | Medium | Based on component counts, complexity of VBA, number of forms/reports |

## Differentiators

Features that would make the rebuild significantly easier but are not strictly required for completeness.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **ERD (Entity Relationship Diagram) generation** | Visual diagram of table relationships is worth a thousand words for a rebuild team. Faster than reading relationship tables | Medium | Generate from extracted relationships. Mermaid or PlantUML format for portability |
| **Data dictionary with domain semantics** | Beyond raw schema: document what each field means in business terms (e.g., "unit_price is the per-unit price BEFORE discounts, in Thai Baht") | High | Requires human interpretation of field purpose. Combine schema + sample data + form context to infer meaning |
| **Form screenshots or layout descriptions** | Visual representation of each form's layout helps the rebuild team understand UX flow without running Access | Medium | Cannot screenshot from macOS. Instead, generate layout description from control positions (Top, Left, Width, Height properties) |
| **Macro extraction** | Access Macros (not VBA) are a separate automation system. Some databases use macros instead of or alongside VBA | Low | Check for macros in MSysObjects. Extract action sequences. Less likely in a 10-year-old DB (VBA was preferred), but must verify |
| **Navigation pane organization** | How objects are grouped in the Access nav pane reveals the mental model of the original developer | Low | Custom nav pane groups stored in MSysNavPaneGroups and related system tables |
| **Calculated field documentation** | Separate listing of all calculated/computed fields across forms and reports with their formulas | Medium | Aggregation of ControlSource expressions that start with "=" across all forms and reports |
| **Data anomaly detection** | Identify orphaned records, null foreign keys, duplicate entries, data quality issues | Medium | Run integrity checks: orphan detection (FK values with no matching PK), null analysis, duplicate detection on key fields |
| **Conditional formatting rules** | Forms and reports may use conditional formatting to highlight overdue orders, low inventory, etc. These encode business rules | Medium | Extract conditional formatting conditions and the visual treatment (color, font, visibility) |
| **Data type mapping to target platform** | Map Access data types to PostgreSQL/MySQL equivalents for the rebuild | Low | Deterministic mapping: Text->VARCHAR, Long Integer->INTEGER, Currency->NUMERIC(19,4), Date/Time->TIMESTAMP, etc. |
| **Suggested normalized schema** | If the existing schema has denormalization or design issues, propose an improved schema for the rebuild | High | Requires analysis of current schema, identification of normalization violations, and proposed improvements. Goes beyond documentation into design |
| **Query performance annotations** | Flag queries that use anti-patterns (SELECT *, no WHERE clause, Cartesian joins, nested subqueries) that will need optimization in the rebuild | Low | Static analysis of extracted SQL |
| **VBA-to-pseudocode translation** | Convert VBA business logic to language-neutral pseudocode that a developer in any stack can implement | High | Useful when rebuild stack is not yet decided. Abstracts away VBA syntax |
| **Attachment/OLE field inventory** | Identify any binary data stored in the database (images, documents, embedded files) | Medium | Check for Attachment and OLE Object data types. Document what is stored (file types, sizes). These need special handling in migration |
| **Linked table identification** | Access databases can link to external data sources (other Access files, Excel, ODBC, SharePoint). These are hidden external dependencies | Low | Check for linked tables in MSysObjects (Type 6). Extract connection strings and source paths |
| **Database properties extraction** | Application title, startup form, menu bars, ribbon customization, database-level properties | Low | These configure the Access "application shell" behavior |

## Anti-Features

Things to deliberately NOT extract or document. Including these would add noise, waste effort, or create misleading artifacts.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Full data dump of all records** | This is an assessment, not a data migration. Dumping 10,000 orders and 1,000 customers creates noise and privacy risk. The schema + sample data is sufficient for rebuild planning | Extract sample data only (5-10 rows per table). Full data migration is a separate phase after the rebuild system exists |
| **Access UI theme/styling details** | Colors, fonts, form backgrounds are Access-specific visual chrome that will not carry over to a web rebuild. Documenting exact pixel positions and color codes wastes effort | Document layout structure (which controls exist, their grouping, tab order) not visual styling |
| **Temporary/system tables** | MSys* tables are Access engine internals (MSysObjects, MSysACEs, MSysQueries, etc.). Documenting their schema adds no rebuild value | Use system tables as extraction sources but do not include them in the assessment output |
| **Deleted/hidden objects** | Access may retain deleted objects or have hidden objects from old iterations. These are historical noise | Only document active, visible objects unless a hidden object contains critical business logic (flag and note if found) |
| **Compile state / VBA project internals** | VBA project binary state (P-code, compiler flags, project GUID) is Access-runtime specific | Extract source code text only. Compile state is irrelevant to rebuild |
| **Access security model (user-level)** | Legacy Access user-level security (MDW files, workgroup security) was deprecated by Microsoft and is irrelevant to a rebuild | Note whether security was configured (for completeness) but do not document the security model in detail |
| **Performance benchmarks of current system** | Measuring query execution times in the current Access database is meaningless for a rebuild on a different stack | Document query complexity and data volumes instead. Let the rebuild team benchmark their own system |
| **AutoExec macros or startup behavior** | While startup form is useful (listed as differentiator in database properties), detailed AutoExec macro replication is Access-specific plumbing | Note the startup form. Document any business-critical startup logic in the business logic summary |

## Feature Dependencies

```
Table Schema Extraction
  -> Relationship Extraction (needs table names)
  -> Index Extraction (needs table names)
  -> Sample Data Extraction (needs table names)
  -> Validation Rule Extraction (extracted with schema)
  -> Row Count Extraction (needs table names)
  -> ERD Generation (needs schema + relationships)
  -> Data Anomaly Detection (needs schema + relationships + data)
  -> Data Type Mapping (needs schema)

Query Extraction (SQL)
  -> Query Type Classification (needs SQL text)
  -> Query Parameter Identification (needs SQL text)
  -> Query Dependency Mapping (needs SQL text + table names)
  -> Query Performance Annotations (needs SQL text)

Form Extraction
  -> Form Field/Control Listing (needs form objects)
  -> Form-to-Table Binding (needs form record sources + table names)
  -> Subform Relationships (needs form objects)
  -> Form Event Procedures / VBA (needs form objects)
  -> Calculated Field Documentation (needs control sources)
  -> Conditional Formatting Rules (needs form objects)
  -> Thai-to-English Label Translation (needs label text from forms)

Report Extraction
  -> Report Field/Control Listing (needs report objects)
  -> Report Grouping and Sorting (needs report objects)
  -> Report Parameters/Filters (needs report objects)
  -> Thai-to-English Label Translation (needs label text from reports)

VBA Module Extraction
  -> Module Dependency Mapping (needs source code)
  -> External Library References (needs VBA project)
  -> Business Logic Summary (needs all VBA source)
  -> VBA-to-Pseudocode Translation (needs source code)

All Extraction Features
  -> Complete Object Inventory (needs all object lists)
  -> Data Flow Diagram (needs forms, queries, reports, tables)
  -> Rebuild Effort Estimate (needs all component counts + complexity)
  -> Thai Data Sample Translation (needs sample data)
```

## MVP Recommendation

**The assessment is the MVP** -- there is no iterative product here. However, extraction should be phased for practical reasons:

### Phase 1: Data Foundation (must complete first)
1. **Table schema extraction** -- everything else depends on this
2. **Relationship extraction** -- defines the data architecture
3. **Index extraction** -- captures uniqueness constraints
4. **Row counts** -- scope indicator
5. **Sample data** -- validates understanding

### Phase 2: Logic Layer
6. **Query extraction with SQL** -- reveals data transformations
7. **Query classification and dependencies** -- maps the logic graph
8. **VBA module extraction** -- captures business rules
9. **External library references** -- identifies hidden dependencies

### Phase 3: Interface Layer
10. **Form inventory and control listing** -- maps the user interface
11. **Form-to-table bindings and subform relationships** -- connects UI to data
12. **Form event procedures** -- captures UI-triggered business logic
13. **Report inventory and control listing** -- maps the output layer
14. **Report grouping/sorting/parameters** -- defines report structure

### Phase 4: Translation and Synthesis
15. **Thai-to-English translation** (all labels, sample data, field names)
16. **Business logic summary** (plain-English descriptions of VBA)
17. **Data flow diagram** -- synthesized from all previous phases
18. **Complete object inventory** -- final count
19. **Rebuild effort estimate** -- the capstone deliverable

### Defer to Rebuild Phase:
- **Suggested normalized schema**: Design decisions should happen in the rebuild project, not the assessment
- **Data anomaly detection**: Useful but not critical for the blueprint. Can be done during data migration
- **VBA-to-pseudocode**: The rebuild team will choose their stack and translate directly from VBA source

## Confidence Assessment

| Category | Confidence | Notes |
|----------|------------|-------|
| Table stakes completeness | HIGH | Access object model is stable and well-documented for 20+ years. The components listed (tables, queries, forms, reports, VBA) are the canonical object types in an Access database |
| Extraction feasibility | MEDIUM | Feasibility depends on tooling available on macOS arm64. mdbtools can extract tables/queries but NOT forms/reports/VBA. COM automation requires Windows. access-parser (Python) has partial support. Tooling gaps are a known risk |
| Complexity estimates | MEDIUM | Based on typical Access databases of this vintage and scale. Actual complexity depends on how the original non-programmer developer structured the system |
| Translation effort | MEDIUM | Volume of Thai content unknown until extraction begins. Could be modest (English field names, Thai labels only) or extensive (Thai everywhere) |
| Anti-features accuracy | HIGH | Standard assessment practice. Full data dumps and styling details are universally excluded from migration assessments |

## Platform-Specific Extraction Constraints

**Critical note for downstream planning:** On macOS arm64, Access database extraction has significant tooling limitations:

- **mdbtools** (C library): Can extract table schemas, data, and some query SQL. CANNOT extract forms, reports, or VBA modules. Available via Homebrew.
- **access-parser** (Python): Can read table schemas and data. Limited metadata extraction. No form/report/VBA support.
- **pyodbc + mdbtools ODBC driver**: Table data access only. No object model access.
- **jackcess** (Java): Most complete open-source option. Can read tables, relationships, queries, and some system tables. Form/report extraction is partial.
- **COM automation** (Windows only): Full access to every object. The only way to extract forms, reports, and VBA programmatically with complete fidelity.

**Implication:** A hybrid approach may be needed -- extract what is possible on macOS, then use a Windows VM or remote Windows machine for form/report/VBA extraction. This constraint must be addressed in the tooling research (STACK.md).

## Sources

- Microsoft Access developer documentation (DAO object model, MSysObjects schema) -- stable since Access 2007, HIGH confidence
- Access database migration assessment best practices -- well-established domain, HIGH confidence
- macOS extraction tooling capabilities -- based on tool documentation, MEDIUM confidence (verify current versions)
- Project context from `.planning/PROJECT.md` and `.planning/codebase/` analysis files

---

*Feature landscape: 2026-02-14*
