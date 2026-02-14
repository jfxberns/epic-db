# Domain Pitfalls

**Domain:** Microsoft Access database extraction and documentation on macOS arm64
**Researched:** 2026-02-14
**Overall Confidence:** MEDIUM-HIGH (based on domain expertise; web verification unavailable for current tool versions)

---

## Critical Pitfalls

Mistakes that cause significant rework, incomplete extraction, or misleading documentation.

---

### Pitfall 1: macOS Extraction Tools Cannot Read Forms, Reports, or VBA

**What goes wrong:** Developer installs mdbtools or access-parser, extracts tables and queries, declares extraction complete. Forms, reports, VBA modules, and macros are completely missed. The assessment is roughly 50-60% complete but presented as done.

**Why it happens:** mdbtools is the most visible and well-documented tool for Access on macOS. Its success with tables creates false confidence that the full database has been extracted. The .accdb format stores UI objects (forms, reports) and code (VBA) in opaque binary streams that only Microsoft's own libraries can parse. Open-source tools reverse-engineered the table/data layer but not the UI/code layers.

**Consequences:**
- Assessment is table-and-query-only, missing the majority of business logic
- Pricing calculations, discount logic, formula/recipe calculations, validation rules -- all embedded in VBA -- are undocumented
- Form workflows (which fields trigger which calculations, field order, required fields, data entry flow) are invisible
- Report layouts (invoice format, shipping label layout, inventory reports) cannot be captured
- The assessment fails its core purpose: being a complete blueprint for rebuild

**Warning signs:**
- Extraction scripts only produce CSV/SQL table dumps
- No VBA code appears in any output
- No form definitions appear in any output
- Documentation has detailed table schemas but vague descriptions of "business logic"

**Prevention:**
- Accept that a Windows environment is required for full extraction. Options:
  - A Windows VM (Parallels or UTM on Apple Silicon)
  - A Windows machine with Access installed (even the free Access Runtime)
  - A temporary cloud VM (Azure, AWS)
- Use Access VBA to export its own objects: `Application.SaveAsText acForm, "FormName", "output.txt"` for forms, reports, macros, and modules
- Alternative: use Python COM automation on Windows with `win32com.client` to programmatically open Access and export all objects
- Plan the extraction in two tracks: Track 1 (macOS) for tables/queries/data, Track 2 (Windows) for forms/reports/VBA
- Use the extraction capability matrix in STACK.md as a checklist

**Detection:** After extraction, compare the object inventory (from mdb-tables and MSysObjects) against the extraction output. If the output has tables/ and queries/ but no forms/, reports/, or vba/ directories, the extraction is incomplete.

**Phase mapping:** Phase 1 (Assessment Setup) -- must be resolved before any extraction begins. Tooling decision is a prerequisite.

**Confidence:** HIGH -- well-documented limitation of all non-Microsoft .accdb tools.

---

### Pitfall 2: Thai Character Encoding Corruption During Extraction

**What goes wrong:** Thai text extracted from the .accdb file appears as garbled characters (mojibake), question marks, or empty strings. This silently corrupts data samples and field name translations. The assessment then contains corrupted Thai data that cannot be translated, and nobody notices until later phases.

**Why it happens:** Multiple encoding layers interact:
- Access databases created on Thai Windows systems may use Windows-874 (TIS-620) encoding rather than UTF-8. The .accdb format (Access 2007+) uses Unicode internally, but legacy data may have been imported or entered under CP874 assumptions.
- mdbtools defaults to a character encoding that may not match. Its JET4 backend reads Unicode but output encoding depends on system locale and command-line flags.
- access-parser (Python) reads raw bytes and may misinterpret the encoding.
- Python string handling, CSV writing, and JSON serialization each add encoding conversion steps where corruption can occur.
- Terminal display and file editors may mask problems (showing replacement characters that "look fine" in logs but are actually corrupted data).

**Consequences:**
- Customer names, product names, addresses, and form labels become unreadable
- Translation becomes impossible for corrupted fields
- If corruption is silent (wrong characters instead of obvious errors), the translated content will be wrong
- Data integrity cannot be verified against the original without going back to the .accdb on Windows
- Every downstream extraction must be re-run once encoding is fixed

**Warning signs:**
- Thai text appears as `?????`, `\xc3\x82\xc2\xb9`, `\x00`, or random Latin characters
- String lengths change unexpectedly (Thai in UTF-8 is 3 bytes per character; in CP874 it is 1 byte)
- Some Thai fields work but others do not (mixed encoding within the database)
- Python `UnicodeDecodeError` or `UnicodeEncodeError` during extraction

**Prevention:**
1. In the probe phase, extract one table known to contain Thai text
2. Visually verify the Thai characters render correctly
3. If garbled, experiment with mdb-export encoding flags: `-e utf-8`, `-e tis-620`, `-e cp874`
4. Once the correct encoding is determined, use it consistently for ALL subsequent extractions
5. Store the encoding setting in a config file so it is never forgotten
6. For Python scripts: always use `open(file, 'w', encoding='utf-8')` and never rely on system default encoding
7. Create a verification step: extract a known Thai string, compare byte-for-byte against expected UTF-8 encoding of Thai Unicode range (U+0E00 to U+0E7F)

**Detection:** After any extraction step, spot-check Thai text in the output. If characters like `?????` or `\xc3\x82` appear instead of Thai script, the encoding is wrong.

**Phase mapping:** Phase 1 (Assessment Setup) -- encoding must be validated before bulk extraction.

**Confidence:** HIGH -- Thai encoding issues in Access extraction are well-known and frequently reported.

---

### Pitfall 3: VBA Extraction Failure on .accdb Format

**What goes wrong:** oletools or access-parser cannot extract VBA source code from the .accdb file. The developer spends hours debugging, then discovers the .accdb binary format stores VBA differently than .mdb, and the tools simply do not support it.

**Why it happens:** VBA in .mdb files is stored as OLE2 compound document streams. VBA in .accdb files (Access 2007+) is stored in a different internal format. Most open-source VBA extraction tools were built for the .mdb format. Additionally, VBA code in Access hides in multiple locations:
- Standard modules (appear in Modules folder)
- Form modules (each form has its own code-behind with event handlers)
- Report modules (reports can also have event code)
- Class modules (custom objects)

**Consequences:** The most valuable extraction (business logic for pricing, discounts, formulas) is blocked. Without VBA extraction, the assessment cannot document the business rules that the rebuild must implement. A 10-year-old system with 10+ forms should have substantial event code that is completely invisible.

**Warning signs:**
- oletools produces no output, empty output, or binary gibberish
- VBA module extraction returns very little code (suggests forms have event code not captured)
- Business users describe behaviors ("when I enter a quantity, the price updates automatically") that are not visible in table schema or queries

**Prevention:**
1. Test VBA extraction EARLY (during the probe phase, not after everything else is done)
2. Have a fallback plan ready: Windows VM, cloud Windows instance, or manual extraction via Access
3. If automated extraction fails, the fallback is: open the .accdb in Access on a Windows machine, go to VBA editor (Alt+F11), export all modules as .bas files
4. On Windows, use VBA to export everything: loop through `CurrentProject.AllModules`, `CurrentProject.AllForms`, `CurrentProject.AllReports` and call `Application.SaveAsText` for each
5. Pay special attention to form events: BeforeUpdate (validation), AfterUpdate (cascading calculations), OnClick (workflow actions), OnOpen (initialization), OnFormat (report formatting)

**Detection:** Compare the number of forms to the amount of VBA code. If extraction yields only a few standard modules but there are 10+ forms, form code-behind has been missed.

**Phase mapping:** Phase 1 (Assessment Setup) for testing; Phase 3 (Logic Extraction) for full VBA capture.

**Confidence:** HIGH -- this is the second most common mistake in Access assessments after incomplete relationship extraction.

---

### Pitfall 4: Treating Table Schema as the Complete Data Model

**What goes wrong:** The assessment documents table columns, data types, and explicit foreign keys, then declares the data model "complete." But Access databases built by non-programmers have implicit relationships, lookup fields with hidden join tables, calculated fields in queries, and business rules in form events.

**Why it happens:** Non-programmer Access builders use the visual form designer and drag-and-drop query builder rather than writing SQL DDL. This creates:
- Lookup columns that appear as simple dropdowns but are actually hidden joins with display transformations
- Queries that act as "virtual tables" -- forms and reports reference them instead of base tables
- Form-level validation that enforces business rules not present in the table schema
- Relationships defined in the Access Relationships window that may not have corresponding foreign key constraints in the table definitions
- Integer ID columns that ARE foreign keys but lack declared relationships

**Consequences:**
- Rebuild team creates database schema from assessment, but it is missing critical relationships
- Data integrity rules are not captured -- the rebuilt app allows invalid data
- Lookup field display values vs. stored values are confused
- "Virtual tables" (queries used as data sources) are missed entirely

**Warning signs:**
- Tables have integer columns with no obvious foreign key but that are clearly IDs
- Queries reference other queries (nested query chains)
- Extracted relationship count seems low (fewer than 5 relationships in a database with 15+ tables)
- Form combo boxes show text but store numeric IDs

**Prevention:**
1. Extract the MSysRelationships system table: use `mdb-tables -S` to list system tables, `mdb-export database.accdb MSysRelationships` to extract
2. For every table column of type Long Integer or Integer, check if it is used as a foreign key in any query or relationship
3. For lookup fields: extract column properties (not just definitions) to find `RowSource` -- on Windows: `For Each fld In tdf.Fields: Debug.Print fld.Name, fld.Properties("RowSource")`
4. Document all queries as potential "virtual tables," not just raw SQL
5. Cross-reference integer columns against all queries and the relationships table

**Detection:** Count explicit relationships vs. integer ID columns. If there are many more ID columns than relationships, you are missing implicit relationships.

**Phase mapping:** Phase 2 (Schema Extraction) -- must enumerate all relationship sources, not just table definitions.

**Confidence:** HIGH -- the single most common mistake in Access database assessments.

---

### Pitfall 5: Missing Query Logic That IS the Business Logic

**What goes wrong:** Assessment documents queries as "SQL statements" but fails to recognize that in non-programmer Access databases, queries ARE the business logic layer. Complex pricing calculations, report aggregations, and data transformations live in stacked queries (queries referencing other queries).

**Why it happens:** Non-programmers build logic using the Access Query Design view, creating chains: Query1 joins two tables, Query2 filters Query1, Query3 aggregates Query2, and a report uses Query3. Additionally, Access has query types that do not exist in standard SQL: crosstab queries, parameter queries with input prompts, make-table queries, append queries, delete queries.

**Consequences:**
- Assessment lists queries without mapping dependencies or explaining business purpose
- Rebuild team cannot reconstruct the calculation pipeline
- Calculated fields in queries (IIF statements, Switch expressions, custom functions) contain business rules that look like "just SQL"
- Access-specific query types (crosstab, parameter) are extracted as raw SQL but not classified

**Warning signs:**
- Queries whose FROM clause references other query names, not table names
- Queries with complex IIF/Switch/Choose expressions in SELECT columns
- Queries that call VBA functions (e.g., `SELECT MyPricingFunction([Qty]) AS Price`)
- Multiple queries with similar names suggesting a chain

**Prevention:**
1. Build a query dependency graph: for each query, list which tables and which other queries it references
2. Classify every query by type (SELECT, CROSSTAB, UPDATE, INSERT, DELETE, MAKE-TABLE, UNION, PASS-THROUGH)
3. Document calculated columns in queries separately -- these are business rules
4. Identify queries that call VBA functions -- these are integration points between query and code layers
5. For parameter queries, document the parameters (name, type, prompt text)
6. For each report and form, document which query it uses as its Record Source

**Detection:** If you have more than approximately 5 queries, check for query-to-query references. In a 10-year-old business system, expect 20-50 queries, many chained.

**Phase mapping:** Phase 3 (Query and Logic Extraction) -- queries should be extracted with dependency trees, not as flat lists.

**Confidence:** HIGH -- standard pattern in non-programmer Access databases.

---

### Pitfall 6: Treating the Assessment as Data Migration

**What goes wrong:** Developer extracts ALL data from every table (1,000 customers, 10,000 orders) and produces massive CSV files. The assessment output is 90% raw data and 10% documentation. The rebuild team gets a data dump, not a blueprint.

**Why it happens:** Data extraction is the easiest thing mdbtools does. It feels productive. "I extracted 10,000 rows!" feels like progress but adds no rebuild value beyond the first 10-20 sample rows.

**Consequences:** Assessment output is bloated and hard to navigate. The actual valuable content (schema definitions, business logic, form specifications) is buried under raw data. Data migration is a separate project.

**Warning signs:**
- CSV files exceeding 100 rows in the output
- More disk space used by data exports than by documentation
- Assessment takes hours to review because of raw data volume

**Prevention:**
1. Extract SAMPLE data only (5-10 representative rows per table)
2. Extract ROW COUNTS for volume estimation
3. Do NOT include full data dumps in the assessment
4. If full data export is needed later, it can be done in minutes -- no need to store it in the assessment

**Detection:** If any CSV file in the output exceeds 100 rows, question whether it should be there.

**Phase mapping:** Phase 2 (Schema Extraction) -- set sample limits before extraction begins.

**Confidence:** HIGH -- common scope creep in database assessment projects.

---

## Moderate Pitfalls

---

### Pitfall 7: Assessment Captures Structure but Not Workflow

**What goes wrong:** Assessment documents what exists (tables, queries, forms, reports) but not how it is used. The rebuild team gets a parts list but not an assembly manual. They do not know: What is the daily workflow? In what order are forms used? What triggers what? What is the main menu flow?

**Why it happens:** Workflow is implicit in Access -- it lives in the form navigation flow, macro-driven menu systems, button click events, and the user's muscle memory. None of this appears in a table schema dump. The startup form, main switchboard, and navigation hierarchy encode the application's workflow.

**Consequences:**
- Rebuilt app has the right data model but wrong user experience
- Critical workflows are missed (e.g., "after entering an order, the user always prints an invoice and a shipping label in sequence")
- Form dependencies are lost (form A opens form B with a filter)
- Default values and auto-populated fields are not documented

**Prevention:**
1. Document the startup form and main menu / switchboard
2. For each form, document: what opens it, what it opens, what buttons it has, what those buttons do
3. Map the primary workflows: order entry, invoice printing, inventory update, report generation
4. If possible, watch a user operate the system (even via screen recording) to capture implicit workflow
5. Extract the AutoExec macro if one exists -- it defines startup behavior

**Detection:** After form extraction, if you have a list of forms but cannot describe how a user navigates through them, workflow documentation is missing.

**Phase mapping:** Phase 4 (Forms, Reports, and Workflow Documentation).

**Confidence:** HIGH -- standard oversight in database assessments.

---

### Pitfall 8: Access Date/Time and Currency Types Map Incorrectly

**What goes wrong:** Access uses a proprietary Date/Time format (double-precision floating point representing days since December 30, 1899) and a Currency type (fixed-point 8-byte integer scaled by 10,000). Extraction tools may output these as raw numbers instead of formatted values. Additionally, Thai Buddhist calendar dates (common in Thai systems) add 543 to the Gregorian year.

**Consequences:**
- Order dates are wrong (off by days or centuries)
- Invoice amounts are wrong (currency precision loss)
- If Buddhist calendar is used, all dates appear to be 543 years in the future

**Prevention:**
1. Use explicit date format in mdb-export: `mdb-export -D '%Y-%m-%d %H:%M:%S'`
2. Extract a table with known dates and amounts, verify against the original
3. Check if dates are stored as Gregorian or Buddhist calendar (year 2567 = Gregorian 2024)
4. For currency, verify decimal precision: extract a known price and confirm it matches to the satang (Thai cents)
5. Document the date format convention used throughout the database

**Detection:** Check the first few date values: if they look like raw floats (e.g., `45000`) or Buddhist calendar years (e.g., `2567`), you have a format issue.

**Phase mapping:** Phase 2 (Schema Extraction) -- type mapping must be validated before bulk data extraction.

**Confidence:** MEDIUM -- the date/currency mapping issue is well-known, but whether this specific database uses Buddhist calendar dates requires verification.

---

### Pitfall 9: Not Documenting What COULD NOT Be Extracted

**What goes wrong:** The assessment documents what was extracted but silently omits what could not be extracted. The rebuild team assumes the assessment is complete and does not know to investigate the .accdb file for missing information.

**Prevention:**
1. For every Access object category, explicitly state extraction completeness
2. If forms could not be fully extracted, say so: "Form layout details could NOT be extracted on macOS. Only form names and record sources were captured. Full form inspection requires opening the .accdb in Microsoft Access."
3. Include a "Known Gaps" section in the final assessment

**Phase mapping:** All phases -- each phase should end with a completeness statement.

**Confidence:** HIGH -- this is the difference between a trustworthy assessment and a misleading one.

---

### Pitfall 10: Non-Programmer Database Has Structural Inconsistencies

**What goes wrong:** Developer assumes the Access database follows standard relational design patterns (normalized tables, proper foreign keys, consistent naming conventions). The database was built by a non-programmer over 10 years and has significant structural quirks.

**Why it happens:** Non-programmers add what they need when they need it. There is no schema migration strategy, no naming convention, no code review. Over a decade, the database evolves organically.

**Warning signs:**
- Tables with extremely wide schemas (30+ columns) -- a sign of denormalization
- Tables that look like spreadsheets (row-per-month, column-per-product)
- Duplicate table structures (same columns, different names)
- Text fields storing only numeric data
- Mixed Thai/English naming with no consistent pattern
- Tables with 0 rows (abandoned objects)

**Prevention:**
1. Do not assume normalization. Check for repeated data, denormalized tables, multi-value fields
2. Do not assume foreign keys exist even where they logically should
3. Before detailed extraction, do a triage pass: count rows in every table, identify empty tables
4. For each table, check if any forms or queries reference it -- unreferenced tables may be abandoned
5. Document quirks without judgment -- the goal is accurate documentation, not criticism

**Phase mapping:** Phase 2 (Schema Extraction) -- triage before deep extraction saves significant time.

**Confidence:** HIGH -- universal in non-programmer-built databases of this age.

---

### Pitfall 11: Inconsistent Thai-to-English Translation

**What goes wrong:** The same Thai word is translated differently in different parts of the assessment. Thai business terminology may not have direct English equivalents. Multiple Thai terms might translate to the same English word. Machine translation may fail on business-specific abbreviations, slang, or truncated labels.

**Prevention:**
1. Build a glossary FIRST, before translating anything
2. Keep original Thai alongside all translations (never replace, always annotate)
3. Where Thai terms are ambiguous, document both the literal translation and the functional meaning (e.g., "this field is labeled [Thai] which literally translates to 'type' but in context refers to the product category")
4. Have the business owner validate critical translations (pricing terms, product names, customer categories)
5. Apply the glossary mechanically to all output
6. Review for consistency: search output for English terms that might be duplicates (customer/client, product/item, order/purchase)

**Detection:** If multiple fields translate to similar English names, or if translations do not make business sense, flag for human review.

**Phase mapping:** Phase 5 (Translation) -- but the glossary should be started in Phase 2 during schema extraction.

**Confidence:** HIGH -- specific to this project's Thai-to-English requirement.

---

### Pitfall 12: Overlooking Linked Tables and External Dependencies

**What goes wrong:** The Access database may contain linked tables pointing to external sources (other Access files, Excel spreadsheets, ODBC connections). These appear as normal tables but have no local data.

**Prevention:**
1. Check MSysObjects for Type 6 entries (linked tables)
2. For any linked tables found, document the connection string and source path
3. Flag linked tables prominently -- they represent external dependencies the rebuild must account for
4. If the linked source is unavailable, the table data cannot be extracted

**Phase mapping:** Phase 2 (Schema Extraction) -- check for linked tables in system objects scan.

**Confidence:** MEDIUM -- depends on whether this particular database uses linked tables.

---

### Pitfall 13: Access Macros vs. VBA Confusion

**What goes wrong:** Access has two separate automation systems: Macros (a visual action-based system stored as XML-like action lists) and VBA (Visual Basic for Applications source code). They are different objects stored differently. Extraction might capture one but miss the other, especially if the assessment assumes "macros" means VBA.

**Prevention:**
1. Explicitly extract both: `Application.SaveAsText acMacro` for macros, separate VBA export for code modules
2. Check the Navigation Pane for both "Macros" and "Modules" groups
3. The AutoExec macro (if present) is an Access Macro, not VBA -- it controls startup behavior
4. Embedded macros in forms and reports are separate from standalone macros

**Phase mapping:** Phase 3 (Query and Logic Extraction) -- enumerate both object types explicitly.

**Confidence:** HIGH -- common terminology confusion that leads to missed objects.

---

## Minor Pitfalls

---

### Pitfall 14: Boolean Field Misinterpretation

**What goes wrong:** Access Yes/No fields export as 0/-1, 0/1, or True/False depending on mdbtools version and flags.

**Prevention:** Document the boolean encoding convention (Access uses -1 for True, 0 for False) and apply consistent conversion.

**Phase mapping:** Phase 2 (Schema Extraction).

---

### Pitfall 15: Memo/Long Text Field Truncation

**What goes wrong:** Large text fields (Memo type in Access) may be truncated during CSV export if they contain newlines, commas, or other special characters.

**Prevention:** Use appropriate quoting in mdb-export: `mdb-export -Q` for quoted output. Verify Memo fields contain full content by comparing row-level character counts.

**Phase mapping:** Phase 2 (Schema Extraction).

---

### Pitfall 16: OLE Objects and Attachment Fields

**What goes wrong:** Access can store OLE objects (images, documents, embedded files) and Attachment-type columns (Access 2007+). These binary blobs do not extract cleanly through mdbtools and may contain business assets like product images, document templates, or logos used in reports.

**Prevention:**
- Check for OLE Object and Attachment-type columns in the schema
- If found, document them as "binary data -- requires Access for extraction"
- Note the number of attachments per record if possible
- On Windows, use VBA to extract and save as individual files

**Phase mapping:** Phase 2 (Schema Extraction) -- identify during schema analysis.

**Confidence:** MEDIUM -- depends on whether this database uses OLE/Attachment fields.

---

### Pitfall 17: Underestimating Assessment Scope

**What goes wrong:** The project is scoped as "extract a database" which sounds straightforward. In reality, a 10-year-old Access database with Thai interface, VBA business logic, forms, reports, queries, and relationships requires careful multi-phase extraction to produce a rebuild-quality blueprint.

**Prevention:**
- Scope each extraction phase explicitly: tables (including relationships and lookup fields), queries (including dependency graphs), forms (including event code and workflow), reports (including layout and formatting logic), VBA (including all code-behind), translation (including glossary creation), and final documentation
- Accept that the Windows environment setup alone takes time if not already available
- Build in verification steps: after each extraction phase, validate a sample against the original

**Phase mapping:** All phases -- each phase should have explicit scope boundaries and verification gates.

**Confidence:** HIGH.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Environment Setup | macOS tools cannot extract forms/VBA (Pitfall 1) | Secure Windows environment before starting extraction |
| Environment Setup | Thai encoding broken in extraction pipeline (Pitfall 2) | Validate encoding with sample data before bulk extraction |
| Environment Setup | mdbtools not supporting .accdb features (Pitfall 1) | Run `mdb-ver data/epic_db.accdb` immediately after install |
| Schema Extraction | System tables filtered out (Pitfall 4) | Use `mdb-tables -S` flag explicitly |
| Schema Extraction | Implicit relationships missed (Pitfall 4) | Cross-reference integer columns against queries and MSysRelationships |
| Schema Extraction | Lookup fields hide relationships (Pitfall 4) | Extract column properties, not just definitions |
| Schema Extraction | Date/Currency types wrong (Pitfall 8) | Verify sample dates and amounts against known values |
| Schema Extraction | Structural inconsistencies waste effort (Pitfall 10) | Triage tables by row count and reference count first |
| Schema Extraction | Over-extraction of data (Pitfall 6) | Cap at 10 rows per table, document row counts separately |
| Query/Logic Extraction | Queries ARE the business logic (Pitfall 5) | Build query dependency graph, document calculated columns |
| Query/Logic Extraction | VBA code-behind missed (Pitfall 3) | Extract form/report modules separately from standalone modules |
| Query/Logic Extraction | Macros vs. VBA confusion (Pitfall 13) | Enumerate both object types explicitly |
| Forms/Reports | Workflow not captured (Pitfall 7) | Map navigation flow, button actions, and user journeys |
| Forms/Reports | Expecting full layout from macOS tools (Pitfall 1) | Set expectations: names and bindings only without Windows |
| Translation | Inconsistent translations (Pitfall 11) | Build glossary first, apply mechanically |
| Assessment Synthesis | Missing "what could not be extracted" (Pitfall 9) | Explicit completeness statement per category |
| All Phases | Scope underestimation (Pitfall 17) | Phase-by-phase scope boundaries with verification gates |

---

## The One Thing That Will Bite You Hardest

If there is a single takeaway from this pitfall analysis, it is **Pitfall 1: you cannot fully extract this database on macOS alone.** Every other pitfall is manageable with careful methodology. But without access to a Windows environment with Microsoft Access (or at minimum the Access Runtime), the forms, reports, and VBA modules -- which contain the majority of the business logic in a non-programmer-built system -- are simply inaccessible. The table data and query SQL can be extracted on macOS, but that is roughly half the assessment. Plan for Windows access from the start, or plan the assessment in two explicit tracks with clear documentation of what each track can and cannot deliver.

---

## Sources and Confidence Notes

- mdbtools issue tracker (common user-reported problems with .accdb extraction)
- Access database migration best practices (well-established domain)
- Unicode encoding handling for Thai text (TIS-620/Windows-874 encoding landscape)
- Domain expertise with Microsoft Access database migration and extraction projects
- Web verification tools (WebSearch, WebFetch, Context7) were unavailable during this research session
- Pitfalls marked HIGH confidence are well-established patterns in the Access migration community
- Pitfalls marked MEDIUM confidence could not be verified against current tool documentation
- The Thai encoding and Buddhist calendar issues should be verified empirically during Phase 1
- Recommendation: verify mdbtools and access-parser current .accdb capabilities before finalizing extraction approach

---

*Pitfalls research: 2026-02-14*
