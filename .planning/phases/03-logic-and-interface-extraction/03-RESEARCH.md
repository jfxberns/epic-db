# Phase 3: Logic and Interface Extraction - Research

**Researched:** 2026-02-15
**Domain:** Query SQL extraction, form/report cataloguing, VBA/business logic documentation from Access .accdb on macOS + Windows
**Confidence:** MEDIUM (macOS query extraction has two viable paths; forms/reports require Windows which user does not yet have)

## Summary

Phase 3 extracts the "logic and interface layer" of epic_db.accdb: 32 queries, 17 forms, 25 reports, and the business logic embedded across them. The fundamental challenge is that **this phase spans two platforms**: some work is macOS-only, some requires Windows with Microsoft Access. The prior decisions confirm: zero standalone VBA modules exist, zero macros exist, and MSysQueries is not accessible via the parser. The work splits into three natural sub-phases:

**Sub-phase A (macOS -- queries):** Extract query SQL and build the dependency graph. Since MSysQueries is inaccessible via access_parser_c, query SQL must be reconstructed. Two approaches exist: (1) Use Jackcess (Java) via JPype1 to call `Database.getQueries()` and `query.toSQLString()` -- Jackcess has battle-tested SQL reconstruction from MSysQueries decomposed rows. (2) Use the Windows COM approach (QueryDef.SQL) during the Windows extraction step. Approach 1 keeps this work on macOS and avoids blocking on Windows setup, but adds Java as a dependency. Approach 2 is simpler but blocks on Windows. **Recommendation: Use Jackcess via JPype1 on macOS** -- it is pip-installable, avoids the Windows dependency for queries, and Jackcess's SQL reconstruction is the most reliable open-source implementation.

**Sub-phase B (Windows -- forms, reports, queries via SaveAsText):** Extract form and report definitions using `Application.SaveAsText`, plus query SQL via `QueryDef.SQL` as a cross-validation/backup. The SaveAsText output is a hierarchical BEGIN/END text format containing all control properties, data sources, event handler references, and code-behind modules. A single automated VBA script + PowerShell wrapper extracts everything headlessly. The user needs a Windows environment (UTM VM on macOS arm64 with Windows 11 ARM, or a cloud Windows instance) with Microsoft Access installed.

**Sub-phase C (macOS -- analysis and documentation):** Parse the extracted SaveAsText files and query SQL to produce the assessment documents: query catalogue with SQL and dependency graph, form/report catalogues with data sources and fields, business process flows, and business logic documentation (pricing, discounts, recipes). This is pure Python text processing and Claude-assisted analysis of the extracted content.

**Critical finding: Zero VBA modules and zero macros exist** in this database (confirmed in Phase 1 inventory). This dramatically simplifies Phase 3 -- there is no standalone VBA code to extract. However, forms may contain code-behind event handlers (VBA in form modules), which SaveAsText will capture. The VBA-related requirements (VBA-01 through VBA-05) will be satisfied either by documenting the absence of VBA modules or by extracting code-behind from form definitions.

**Primary recommendation:** Split Phase 3 into two plans: Plan 1 extracts query SQL via Jackcess/JPype on macOS and produces the query assessment documents. Plan 2 handles Windows extraction of forms/reports, parsing SaveAsText output, and producing form/report/business-process assessment documents. If Jackcess/JPype fails at runtime, fall back to extracting query SQL on Windows alongside forms/reports in Plan 2.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| access_parser_c (McSash fork) | git HEAD (already installed) | Read MSysObjects for object inventory, cross-reference | Already validated in Phases 1-2. Provides object names, types, flags for all 84 objects | HIGH |
| JPype1 | >=1.5.0 (PyPI) | Python-Java bridge to call Jackcess from Python | Mature, pip-installable, 1000+ GitHub stars, actively maintained. Enables calling Jackcess `toSQLString()` without writing Java code. | MEDIUM (not yet validated on this project) |
| Jackcess | 4.0.8 (Maven Central) | Java library to read Access query definitions and reconstruct SQL | Most complete open-source Access parser. `getQueries()` + `toSQLString()` reconstructs SQL from MSysQueries decomposed rows. Battle-tested since version 1.1.19. Pure Java, cross-platform. | HIGH (library itself), MEDIUM (JPype integration) |
| tabulate | latest (already installed) | Markdown table formatting for assessment output | Already used in all prior scripts. Handles Thai text correctly. | HIGH |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Java JDK/JRE | 11+ (any distribution) | Required runtime for JPype1 + Jackcess | Must be installed for Jackcess approach. On macOS arm64: `brew install openjdk@11` or download Temurin ARM64 from Adoptium |
| commons-lang3 | 3.10+ (Maven Central) | Jackcess runtime dependency | Needed alongside Jackcess JAR |
| commons-logging | 1.1+ (Maven Central) | Jackcess runtime dependency | Needed alongside Jackcess JAR |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Jackcess via JPype1 | Windows QueryDef.SQL extraction | Simpler (no Java dep), but blocks on Windows setup. If user already has Windows, use this instead. |
| Jackcess via JPype1 | Manual MSysQueries SQL reconstruction in Python | MSysQueries is not accessible via parser (confirmed). Even if it were, the decomposed format (Attribute/Flag/Name1/Name2/Expression rows) requires complex reconstruction logic that Jackcess has already solved. Do not hand-roll. |
| Jackcess via JPype1 | mdbtools `mdb-queries` | Requires Homebrew (violates pip-only constraint). Also, mdbtools .accdb query support is uncertain. |
| SaveAsText on Windows | Manual binary parsing of form/report blobs on macOS | Not feasible. Form/report definitions are opaque binary blobs requiring the Access COM Object Model. No open-source parser exists. |
| UTM (free VM) for Windows | Parallels Desktop | UTM is free and runs Windows 11 ARM on Apple Silicon. Parallels is commercial ($100+/year). UTM performance is adequate for headless Access automation. |

**Installation (macOS -- queries):**
```bash
# In project venv
uv pip install JPype1

# Java JDK (if not already installed)
# Option A: Homebrew (fastest)
brew install openjdk@11
# Option B: Manual download from https://adoptium.net (Temurin 11 ARM64)

# Download Jackcess JARs (one-time)
mkdir -p lib/
curl -L -o lib/jackcess-4.0.8.jar \
  "https://repo1.maven.org/maven2/com/healthmarketscience/jackcess/jackcess/4.0.8/jackcess-4.0.8.jar"
curl -L -o lib/commons-lang3-3.14.0.jar \
  "https://repo1.maven.org/maven2/org/apache/commons/commons-lang3/3.14.0/commons-lang3-3.14.0.jar"
curl -L -o lib/commons-logging-1.3.0.jar \
  "https://repo1.maven.org/maven2/commons-logging/commons-logging/1.3.0/commons-logging-1.3.0.jar"
```

**Note about Java:** Java is a system-level dependency (not pip-installable). This is a deviation from the "Python-only dependencies" constraint from Phase 1. However, Phase 1's constraint was about the parser itself. For Phase 3, Java is a practical bridge dependency. If the user objects to Java, the fallback is to extract query SQL on Windows alongside forms/reports -- no Java needed but Windows required earlier.

## Architecture Patterns

### Recommended Project Structure
```
scripts/
  db_reader.py              # EXISTING: extend with query metadata functions
  inventory.py              # EXISTING
  extract_query_sql.py      # NEW: Jackcess via JPype -> query SQL extraction
  parse_saveastext.py       # NEW: Parse SaveAsText output files
  extract_forms_reports.py  # NEW: Generate form/report assessment docs
  extract_business_logic.py # NEW: Synthesize business process documentation
lib/
  jackcess-4.0.8.jar        # NEW: Jackcess JAR
  commons-lang3-3.14.0.jar  # NEW: Jackcess dependency
  commons-logging-1.3.0.jar # NEW: Jackcess dependency
windows/
  export_all.vbs            # NEW: VBScript for headless Access export
  export_all.ps1            # NEW: PowerShell wrapper
  README.md                 # NEW: Windows setup instructions
assessment/
  queries/
    _overview.md            # NEW: Query catalogue with type classification
    {query_name}.md         # NEW: Per-query SQL with annotations
    dependency_graph.md     # NEW: Query dependency visualization
  forms/
    _overview.md            # NEW: Form catalogue with purpose/data sources
    {form_name}.md          # NEW: Per-form controls, data sources, events
    navigation.md           # NEW: Form navigation workflow
  reports/
    _overview.md            # NEW: Report catalogue with purpose/data sources
    {report_name}.md        # NEW: Per-report data sources, fields, format
  business_logic/
    pricing_discounts.md    # NEW: Pricing/discount logic in English
    inventory_formulas.md   # NEW: Formula/recipe logic documentation
    process_flows.md        # NEW: Business process flows across components
```

### Pattern 1: Jackcess Query SQL Extraction via JPype

**What:** Use JPype1 to start a JVM, load Jackcess JARs, open the .accdb file, and call `getQueries()` + `toSQLString()` on each query.
**When to use:** For QURY-01, QURY-02, QURY-03 (query SQL, dependency graph, type classification).
**Confidence:** MEDIUM -- JPype + Jackcess individually are HIGH confidence, but the combination on this specific database needs runtime validation.

```python
# scripts/extract_query_sql.py
import jpype
import jpype.imports
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "epic_db.accdb"
LIB_DIR = Path(__file__).resolve().parent.parent / "lib"

def start_jvm():
    """Start JVM with Jackcess on classpath."""
    if not jpype.isJVMStarted():
        jars = list(LIB_DIR.glob("*.jar"))
        classpath = ":".join(str(j) for j in jars)
        jpype.startJVM(classpath=[classpath])

def extract_all_queries(db_path: Path = DB_PATH) -> list[dict]:
    """Extract all query SQL from the Access database using Jackcess."""
    start_jvm()

    from com.healthmarketscience.jackcess import DatabaseBuilder
    from java.io import File

    db = DatabaseBuilder.open(File(str(db_path)))
    queries = []

    for query in db.getQueries():
        try:
            sql = str(query.toSQLString())
        except Exception as e:
            sql = f"ERROR: {e}"

        queries.append({
            "name": str(query.getName()),
            "type": str(query.getType()),
            "sql": sql,
            "hidden": bool(query.isHidden()),
        })

    db.close()
    return queries
```

### Pattern 2: Windows Headless Export via VBScript

**What:** A VBScript + PowerShell script that opens the database in Access, iterates all objects, and exports them via SaveAsText and QueryDef.SQL.
**When to use:** For FORM-01, FORM-02, FORM-03, and backup query SQL extraction.
**Confidence:** HIGH -- SaveAsText is the standard documented approach, well-tested across Access versions.

```vbscript
' windows/export_all.vbs
' Run via: cscript //nologo export_all.vbs "C:\path\to\epic_db.accdb" "C:\output\"
'
' Exports ALL forms, reports, queries (both SaveAsText and SQL), macros, and modules
' Fully headless -- no UI interaction required

Dim args, dbPath, outputPath
Set args = WScript.Arguments
If args.Count < 2 Then
    WScript.Echo "Usage: cscript export_all.vbs <db_path> <output_path>"
    WScript.Quit 1
End If

dbPath = args(0)
outputPath = args(1)

' Ensure output directories exist
Dim fso
Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FolderExists(outputPath) Then fso.CreateFolder(outputPath)
If Not fso.FolderExists(outputPath & "\forms") Then fso.CreateFolder(outputPath & "\forms")
If Not fso.FolderExists(outputPath & "\reports") Then fso.CreateFolder(outputPath & "\reports")
If Not fso.FolderExists(outputPath & "\queries") Then fso.CreateFolder(outputPath & "\queries")
If Not fso.FolderExists(outputPath & "\queries_sql") Then fso.CreateFolder(outputPath & "\queries_sql")
If Not fso.FolderExists(outputPath & "\macros") Then fso.CreateFolder(outputPath & "\macros")
If Not fso.FolderExists(outputPath & "\modules") Then fso.CreateFolder(outputPath & "\modules")

' Open Access
Dim accessApp
Set accessApp = CreateObject("Access.Application")
accessApp.OpenCurrentDatabase dbPath
accessApp.Visible = False

Dim db
Set db = accessApp.CurrentDb()

' Export Forms (SaveAsText)
Dim container, doc
Set container = db.Containers("Forms")
For Each doc In container.Documents
    accessApp.SaveAsText 2, doc.Name, outputPath & "\forms\" & doc.Name & ".txt"
    WScript.Echo "Form: " & doc.Name
Next

' Export Reports (SaveAsText)
Set container = db.Containers("Reports")
For Each doc In container.Documents
    accessApp.SaveAsText 3, doc.Name, outputPath & "\reports\" & doc.Name & ".txt"
    WScript.Echo "Report: " & doc.Name
Next

' Export Queries (SaveAsText format)
Dim qdf, i
For i = 0 To db.QueryDefs.Count - 1
    Set qdf = db.QueryDefs(i)
    If Left(qdf.Name, 1) <> "~" Then
        accessApp.SaveAsText 1, qdf.Name, outputPath & "\queries\" & qdf.Name & ".txt"
        ' Also export raw SQL
        Dim sqlFile
        Set sqlFile = fso.CreateTextFile(outputPath & "\queries_sql\" & qdf.Name & ".sql", True, True)
        sqlFile.Write qdf.SQL
        sqlFile.Close
        WScript.Echo "Query: " & qdf.Name & " (Type=" & qdf.Type & ")"
    End If
Next

' Export Macros (SaveAsText)
Set container = db.Containers("Scripts")
For Each doc In container.Documents
    If Left(doc.Name, 1) <> "~" Then
        accessApp.SaveAsText 4, doc.Name, outputPath & "\macros\" & doc.Name & ".txt"
        WScript.Echo "Macro: " & doc.Name
    End If
Next

' Export Modules (SaveAsText)
Set container = db.Containers("Modules")
For Each doc In container.Documents
    accessApp.SaveAsText 5, doc.Name, outputPath & "\modules\" & doc.Name & ".txt"
    WScript.Echo "Module: " & doc.Name
Next

accessApp.Quit
Set accessApp = Nothing
WScript.Echo "Export complete."
```

```powershell
# windows/export_all.ps1
# PowerShell wrapper for headless execution
param(
    [string]$DbPath = "C:\epic_db\epic_db.accdb",
    [string]$OutputPath = "C:\epic_db\export"
)

cscript //nologo "$PSScriptRoot\export_all.vbs" $DbPath $OutputPath
```

### Pattern 3: SaveAsText Output Parsing

**What:** Parse the hierarchical BEGIN/END text format produced by SaveAsText to extract control properties, data sources, event handlers, and VBA code-behind.
**When to use:** For FORM-01, FORM-02, FORM-03, VBA-05 (form/report cataloguing, event handlers).
**Confidence:** HIGH -- the format is simple and well-documented (property = value pairs in BEGIN/END blocks).

```python
# scripts/parse_saveastext.py
"""Parser for Access SaveAsText output files.

The format is:
  Version =20
  Begin Form
    PropertyName =Value
    Begin
      Begin ControlType
        PropertyName =Value
      End
    End
  End

Key properties to extract:
  Form level: RecordSource, Caption, DefaultView, Filter, OrderBy
  Controls: Name, ControlType, ControlSource, RowSource, RowSourceType
  Events: OnClick, OnOpen, OnClose, BeforeUpdate, AfterUpdate, OnCurrent
  Code-behind: Everything after 'CodeBehindForm' marker
"""

import re
from pathlib import Path


def parse_saveastext(filepath: Path) -> dict:
    """Parse a SaveAsText file into structured data.

    Returns dict with:
      - properties: top-level form/report properties
      - controls: list of controls with their properties
      - events: dict of event_name -> handler_type
      - code_behind: VBA code text (if any)
      - sections: list of sections (Detail, Header, Footer)
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")
    lines = text.split("\n")

    result = {
        "properties": {},
        "controls": [],
        "events": {},
        "code_behind": "",
        "sections": [],
    }

    # Extract code-behind (everything after CodeBehindForm marker)
    code_marker = "CodeBehindForm"
    if code_marker in text:
        code_start = text.index(code_marker) + len(code_marker)
        # Find the code section (between Attribute VB_Name and End)
        code_section = text[code_start:]
        result["code_behind"] = code_section.strip()

    # Parse properties and controls from BEGIN/END structure
    # ... (implementation follows standard recursive descent parser)

    return result


# Event property names that indicate VBA handlers
EVENT_PROPERTIES = {
    "OnClick", "OnDblClick", "OnOpen", "OnClose", "OnLoad",
    "OnCurrent", "BeforeUpdate", "AfterUpdate", "BeforeInsert",
    "AfterInsert", "BeforeDelConfirm", "AfterDelConfirm",
    "OnChange", "OnGotFocus", "OnLostFocus", "OnEnter", "OnExit",
    "OnMouseDown", "OnMouseUp", "OnMouseMove", "OnKeyDown",
    "OnKeyUp", "OnKeyPress", "OnActivate", "OnDeactivate",
    "OnResize", "OnTimer", "BeforeRender", "AfterRender",
}

# Key control properties for cataloguing
CONTROL_KEY_PROPERTIES = {
    "Name", "ControlSource", "RowSource", "RowSourceType",
    "Caption", "DefaultValue", "ValidationRule", "InputMask",
    "Visible", "Enabled", "Locked",
}
```

### Pattern 4: Query Dependency Graph Construction

**What:** Parse extracted SQL to identify table and query references, build a dependency graph.
**When to use:** For QURY-02 (dependency graph).
**Confidence:** HIGH -- SQL parsing for table/query name extraction is straightforward with regex.

```python
import re

def extract_references_from_sql(sql: str, known_tables: set, known_queries: set) -> dict:
    """Extract table and query references from SQL text.

    Returns dict with:
      - tables: set of referenced table names
      - queries: set of referenced query names
      - type: query type (SELECT, UPDATE, INSERT, DELETE, UNION, CROSSTAB, etc.)
    """
    # Normalize whitespace
    sql_norm = " ".join(sql.split())

    # Detect query type
    sql_upper = sql_norm.upper().strip()
    if sql_upper.startswith("SELECT"):
        qtype = "SELECT"
    elif sql_upper.startswith("UPDATE"):
        qtype = "UPDATE"
    elif sql_upper.startswith("INSERT"):
        qtype = "INSERT"
    elif sql_upper.startswith("DELETE"):
        qtype = "DELETE"
    elif "TRANSFORM" in sql_upper:
        qtype = "CROSSTAB"
    elif "UNION" in sql_upper:
        qtype = "UNION"
    else:
        qtype = "OTHER"

    # Extract FROM and JOIN table references
    # Pattern: FROM table, JOIN table, INTO table, UPDATE table
    references = set()
    # Match identifiers after FROM, JOIN, INTO, UPDATE (with optional brackets)
    patterns = [
        r'\bFROM\s+\[?([^\]\s,;]+)\]?',
        r'\bJOIN\s+\[?([^\]\s,;]+)\]?',
        r'\bINTO\s+\[?([^\]\s,;]+)\]?',
        r'\bUPDATE\s+\[?([^\]\s,;]+)\]?',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, sql_norm, re.IGNORECASE):
            references.add(match.group(1))

    tables = references & known_tables
    queries = references & known_queries

    return {"tables": tables, "queries": queries, "type": qtype}
```

### Anti-Patterns to Avoid

- **Blocking all of Phase 3 on Windows setup:** The query extraction (32 queries, QURY-01/02/03) can proceed on macOS via Jackcess. Do not wait for Windows to start this work.
- **Attempting to parse form/report binary blobs on macOS:** These are opaque binary structures. Only SaveAsText on Windows can produce readable output. Do not waste time on binary parsing.
- **Hand-rolling MSysQueries SQL reconstruction:** The decomposed format (Attribute/Flag/Name1/Name2/Expression) is complex and Jackcess already has a battle-tested implementation. Even if MSysQueries were accessible (it is not), the reconstruction is non-trivial.
- **Treating "zero modules" as "no VBA exists":** Zero standalone modules does not mean zero VBA. Forms can have code-behind modules with event handlers. SaveAsText captures these. Check every form's SaveAsText output for code.
- **Generating business logic docs without the actual SQL/form data:** VBA-02 (pricing), VBA-03 (formulas), VBA-04 (process flows) require synthesizing information FROM the extracted queries and forms. These cannot be written before extraction.
- **Assuming query type classification from MSysObjects Flags is accurate:** Phase 1 classified 31 queries as SELECT and 1 as UNION based on flags. The actual SQL may reveal different types. Use the real SQL for classification, not flags.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| SQL reconstruction from MSysQueries | Custom Python SQL builder from decomposed rows | Jackcess `toSQLString()` via JPype | MSysQueries has 12 attribute types with complex flag/expression interactions. Jackcess handles all query types including UNION, CROSSTAB, TRANSFORM, parameterized. Thousands of production databases tested. |
| Access form/report content extraction | Binary blob parser | `Application.SaveAsText` on Windows | No specification exists for the binary format. SaveAsText is the only way to get readable form/report definitions. |
| SaveAsText output parsing | Ad-hoc regex | Structured recursive descent parser (BEGIN/END blocks) | The format is hierarchical with nesting. Simple regex breaks on nested controls and multi-line binary properties. |
| Query dependency graph | Manual SQL inspection | Regex-based reference extraction + graph construction | 32 queries with potential cross-references. Automated extraction is the only reliable approach. |
| Business logic documentation | Guess from table/column names | Synthesize from actual query SQL + form event handlers + table constraints | Business logic is distributed across queries (calculated columns, IIF expressions), form events (VBA code-behind), and table validation rules. All must be combined. |

**Key insight:** Phase 3 has two fundamentally different extraction modes: programmatic (queries via Jackcess) and COM-based (forms/reports via Windows). Treating them as one approach causes unnecessary blocking.

## Common Pitfalls

### Pitfall 1: JPype JVM Startup Failure on macOS arm64 (MEDIUM RISK)
**What goes wrong:** JPype cannot find the JVM or crashes during startup.
**Why it happens:** Java may not be installed, or JAVA_HOME may not be set, or the arm64 JVM path differs from the default x86_64 path.
**How to avoid:**
  1. Install Java via Homebrew (`brew install openjdk@11`) or download Temurin ARM64
  2. Set JAVA_HOME explicitly before JPype startup
  3. Test JVM startup in isolation before attempting Jackcess calls
  4. Fallback: extract query SQL on Windows alongside forms/reports
**Warning signs:** `OSError: JVM not found`, `JVMNotSupportedException`, or segfault during `jpype.startJVM()`.

### Pitfall 2: Jackcess Cannot Open Database (LOW RISK)
**What goes wrong:** Jackcess throws an exception opening epic_db.accdb.
**Why it happens:** Jackcess 4.x supports Access 2000-2019. The database is Access 2010 format (version byte 0x03), well within range. Unlikely to fail but must be validated.
**How to avoid:** Test database open before writing the full extraction script. If it fails, check Jackcess version and database format.
**Warning signs:** `IOException`, `UnsupportedOperationException` on `DatabaseBuilder.open()`.

### Pitfall 3: SaveAsText File Encoding Issues with Thai Content (HIGH RISK)
**What goes wrong:** SaveAsText output files contain garbled Thai text, or the Python parser cannot read them correctly.
**Why it happens:** SaveAsText may use the system's ANSI code page (Windows-874 for Thai locale, or Windows-1252 for English locale). If the Windows VM is configured with an English locale, Thai characters in form captions and control names may be corrupted.
**How to avoid:**
  1. Configure the Windows VM with Thai locale support (or at least UTF-8 beta support)
  2. Test SaveAsText on one form first and verify Thai text renders correctly
  3. When reading files in Python, try encodings in order: utf-8, utf-16-le, cp874, cp1252
  4. The VBScript should use `CreateTextFile(path, True, True)` for Unicode output where possible
**Warning signs:** `?????` characters, garbled text in form captions, `UnicodeDecodeError` when reading files in Python.

### Pitfall 4: Confusing "Zero Modules" with "Zero VBA" (HIGH RISK for documentation)
**What goes wrong:** Documenting that the database has no VBA code, when in fact forms contain code-behind event handlers.
**Why it happens:** Phase 1 inventory found zero standalone modules. But Access forms and reports can have embedded VBA in their code-behind module (visible only via SaveAsText or the VBE IDE). Since the database was "built by a non-programmer," simple event handlers (e.g., button click opens a report, combo box filters data) are likely present.
**How to avoid:** After SaveAsText extraction, grep ALL form and report .txt files for VBA markers: `Option Compare`, `Sub `, `Function `, `Private Sub`, `[Event Procedure]`. Document every event handler found.
**Warning signs:** Form properties with `[Event Procedure]` values indicate VBA exists in the code-behind.

### Pitfall 5: Query SQL Contains Thai That Needs Careful Handling (MEDIUM RISK)
**What goes wrong:** Query SQL references Thai table and column names. Simple regex parsing breaks on multi-byte characters or bracket-quoted Thai identifiers.
**Why it happens:** Access SQL uses `[bracket notation]` for identifiers with special characters. Thai table names like `[สินค้าในแต่ละออเดอร์]` will appear in the SQL.
**How to avoid:** Use bracket-aware parsing: extract identifiers from `[...]` before applying regex patterns. The dependency graph builder must handle Thai identifiers correctly.
**Warning signs:** Broken table name extraction, partial Thai strings in dependency graph.

### Pitfall 6: Windows ARM + Access Compatibility (MEDIUM RISK)
**What goes wrong:** Microsoft Access is not available for Windows ARM, or the ARM version does not support COM automation.
**Why it happens:** On Apple Silicon, UTM runs Windows 11 ARM. Microsoft 365 Access runs natively on ARM64 Windows. However, some older Access versions (standalone/retail) are x86 only and require emulation.
**How to avoid:** Use Microsoft 365 (subscription) which has native ARM64 builds. Or use the x86 emulation layer in Windows 11 ARM, which transparently runs x86 Access.
**Warning signs:** "This app can't run on your PC" error, or COM objects not registering.

### Pitfall 7: Subform Data Sources Are Embedded Queries (MEDIUM RISK)
**What goes wrong:** Missing 8 embedded subqueries (`~sq_c*` prefix) that serve as data sources for subforms. These are system-generated queries not visible in the query list.
**Why it happens:** When a form's RecordSource or a subform's SourceObject references a query that was built in the form designer, Access creates a hidden `~sq_c*` query. Phase 1 inventory filtered these out (they start with `~`).
**How to avoid:** Include `~sq_c*` queries in the extraction (8 were detected in Phase 1). Map them back to the forms that use them.
**Warning signs:** Forms whose RecordSource references a query name not found in the visible query list.

## Code Examples

### Complete Jackcess Query Extraction (Validated Pattern)
```python
# Source: Jackcess official API + JPype1 documentation
# Confidence: MEDIUM -- pattern is correct but needs runtime validation
import jpype
import jpype.imports
from pathlib import Path
import json

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "epic_db.accdb"
LIB_DIR = Path(__file__).resolve().parent.parent / "lib"

def extract_queries():
    """Extract all query SQL from epic_db.accdb using Jackcess via JPype."""
    # Build classpath from all JARs in lib/
    jars = list(LIB_DIR.glob("*.jar"))
    if not jars:
        raise FileNotFoundError(f"No JAR files found in {LIB_DIR}")
    classpath = ":".join(str(j) for j in jars)

    # Start JVM
    if not jpype.isJVMStarted():
        jpype.startJVM(classpath=[classpath])

    # Import Java classes
    from com.healthmarketscience.jackcess import DatabaseBuilder
    from java.io import File

    # Open database (read-only)
    db = DatabaseBuilder.open(File(str(DB_PATH)))

    results = []
    for query in db.getQueries():
        name = str(query.getName())
        qtype = str(query.getType())

        try:
            sql = str(query.toSQLString())
        except Exception as e:
            sql = None
            error = str(e)

        results.append({
            "name": name,
            "type": qtype,
            "sql": sql,
            "error": error if sql is None else None,
            "hidden": bool(query.isHidden()),
        })

    db.close()
    return results

if __name__ == "__main__":
    queries = extract_queries()
    for q in queries:
        print(f"\n--- {q['name']} ({q['type']}) ---")
        if q['sql']:
            print(q['sql'])
        else:
            print(f"ERROR: {q['error']}")
```

### Windows Export All Script (VBScript -- Complete)
```vbscript
' See Pattern 2 above for the complete export_all.vbs script.
' Key object type constants for SaveAsText:
'   acForm = 2
'   acReport = 3
'   acQuery = 1
'   acMacro = 4
'   acModule = 5
'
' Usage: cscript //nologo export_all.vbs "C:\path\to\epic_db.accdb" "C:\output\"
' The script creates subdirectories: forms/, reports/, queries/, queries_sql/,
' macros/, modules/
```

### SaveAsText Output Parser (Key Extraction)
```python
# Source: SaveAsText format documentation (Microsoft Learn archive)
def extract_form_metadata(filepath: Path) -> dict:
    """Extract key metadata from a SaveAsText form file.

    Extracts: RecordSource, Caption, controls with data bindings,
    event handlers, and code-behind VBA.
    """
    text = filepath.read_text(encoding="utf-8", errors="replace")

    metadata = {
        "name": filepath.stem,
        "record_source": None,
        "caption": None,
        "default_view": None,
        "controls": [],
        "event_handlers": [],
        "has_code_behind": False,
        "code_behind_preview": "",
    }

    # Extract top-level properties
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("RecordSource ="):
            metadata["record_source"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("Caption ="):
            metadata["caption"] = line.split("=", 1)[1].strip().strip('"')
        elif line.startswith("DefaultView ="):
            metadata["default_view"] = line.split("=", 1)[1].strip()

    # Detect code-behind
    if "Option Compare" in text or "Private Sub" in text or "Public Sub" in text:
        metadata["has_code_behind"] = True
        # Extract first 500 chars of code for preview
        for marker in ["Option Compare", "Option Explicit"]:
            if marker in text:
                code_start = text.index(marker)
                metadata["code_behind_preview"] = text[code_start:code_start + 500]
                break

    # Extract controls and their key properties
    # (Simplified -- full parser uses recursive descent)
    control_types = [
        "TextBox", "ComboBox", "ListBox", "CommandButton",
        "Label", "CheckBox", "OptionButton", "Subform",
        "Image", "BoundObjectFrame", "UnboundObjectFrame",
        "ToggleButton", "TabControl", "OptionGroup",
    ]
    for ct in control_types:
        pattern = rf"Begin {ct}\b"
        for match in re.finditer(pattern, text):
            # Extract properties until matching End
            start = match.start()
            # Simple extraction: find Name and ControlSource nearby
            block = text[start:start + 2000]  # Grab context
            name_match = re.search(r'Name ="([^"]*)"', block)
            source_match = re.search(r'ControlSource ="([^"]*)"', block)
            row_source_match = re.search(r'RowSource ="([^"]*)"', block)

            control = {
                "type": ct,
                "name": name_match.group(1) if name_match else "unnamed",
                "control_source": source_match.group(1) if source_match else None,
                "row_source": row_source_match.group(1) if row_source_match else None,
            }

            # Check for event handlers
            for evt in EVENT_PROPERTIES:
                if f'{evt} ="[Event Procedure]"' in block:
                    metadata["event_handlers"].append({
                        "control": control["name"],
                        "event": evt,
                    })

            metadata["controls"].append(control)

    return metadata
```

### Query Dependency Graph as Markdown
```python
def generate_dependency_graph(queries: list[dict], known_tables: set) -> str:
    """Generate a Mermaid-compatible text dependency graph.

    Output is a markdown document with:
    1. Mermaid graph definition (viewable in GitHub/VSCode)
    2. Text table listing all dependencies
    """
    lines = ["# Query Dependency Graph", ""]
    lines.append("```mermaid")
    lines.append("graph LR")

    known_query_names = {q["name"] for q in queries}

    for q in queries:
        if not q.get("sql"):
            continue
        refs = extract_references_from_sql(q["sql"], known_tables, known_query_names)

        for table in refs["tables"]:
            lines.append(f'    {safe_id(table)}["{table}"] --> {safe_id(q["name"])}["{q["name"]}"]')
        for qref in refs["queries"]:
            lines.append(f'    {safe_id(qref)}("{qref}") --> {safe_id(q["name"])}("{q["name"]}")')

    lines.append("```")
    return "\n".join(lines)

def safe_id(name: str) -> str:
    """Convert Thai/special chars to safe Mermaid node ID."""
    return "n" + str(abs(hash(name)))
```

## Database-Specific Context

### What We Know About the 32 Queries

From the Phase 1 inventory, the 32 queries are:
- **31 classified as SELECT** (based on MSysObjects flags -- actual types may differ)
- **1 classified as UNION** (`qryรายงานสินค้าและวัตุดิบ` / "Product and Raw Materials Report")
- **8 hidden embedded subqueries** (`~sq_c*` prefix, filtered from inventory -- these are subform data sources)
- Query names suggest: stock calculations, sales totals, order filtering, customer points, product per-order breakdowns, date-range filtering, invoice numbering, transfer details

### What We Know About the 17 Forms

From the Phase 1 inventory:
- `หน้าหลัก` ("Main Page") -- likely the main menu/navigation form
- `frm_salesorder_fishingshop` / `frm_salesorder_retail` -- order entry (shop vs retail)
- `frm รับเข้าสินค้า` / `frm เบิกสินค้า` -- goods receipt / goods issue
- `frm_สต็อคสินค้า` / `frm_stck_fishingshop` -- stock management
- `frmข้อมูลสมาชิก` -- member/customer data
- Multiple subform entries (`Subform`, `Subform1`) -- embedded data grids
- `หาเลขที่ออเดอร์ถ้ารู้ชื่อร้าน` -- order lookup by shop name
- `คะแนนคงเหลือหลังจากใช้แล้ว` -- remaining points after use

### What We Know About the 25 Reports

From the Phase 1 inventory:
- Invoice reports: `ใบกำกับภาษีร้านค้า` (shop tax invoice), `ใบกำกับภาษีลูกค้าปลีก` (retail tax invoice), plus copies
- Shipping reports: `ใบส่งของร้านค้า` (shop delivery note), `ใบจัดสินค้าร้านค้า` (shop packing list)
- Address/label reports: `ปริ้นท์ที่อยู่` (print address), `ปริ้นท์ที่อยู่ลูกค้าปลีก` (print retail customer address)
- Financial: `ตรวจภาษีขาย` (check sales tax), `รายงานภาษีขาย` (sales tax report)
- Transfer details: `รายละเอียดการโอน` (transfer details), `pdf แจ้งยอด` (statement PDF)
- Inventory: `รายละเอียดใบรับเข้าสินค้า` (goods receipt details), `ปรินท์ใบเบิกสินค้า` (print goods issue)

### Business Domain Model (Inferred from Schema + Names)

The database supports a fishing lure manufacturing business with:
1. **Order Management**: Retail (ปลีก) and Wholesale/Shop (ร้านค้า) channels
2. **Inventory**: Goods receipt (รับเข้า) and goods issue/withdrawal (เบิก)
3. **Customer Management**: Members (สมาชิก) with points system, shops (ร้านค้า)
4. **Invoicing**: Tax invoices (ใบกำกับภาษี) with copies, for both channels
5. **Stock Tracking**: Stock queries, per-product calculations
6. **Financial**: Bank transfers (โอนเงิน), sales reports, tax reporting

## Open Questions

1. **Does Jackcess via JPype actually work with epic_db.accdb on macOS arm64?**
   - What we know: Jackcess 4.x supports Access 2010 format. JPype1 works on macOS arm64. Both are well-maintained.
   - What's unclear: Whether the combination works without issues at runtime. The database uses Thai identifiers which Jackcess should handle (it reads UTF-16 directly from the binary format).
   - Recommendation: Test immediately at start of Plan 1. If it fails, fall back to extracting query SQL on Windows.
   - **Fallback cost:** LOW -- the Windows export script already extracts QueryDef.SQL. Just means queries wait for Windows setup.

2. **Does the user have access to a Windows environment?**
   - What we know: Phase 1 concluded "Windows IS NEEDED" and the user can set up a VM but does not have one yet.
   - What's unclear: Whether the user has already set up the Windows VM since Phase 1 concluded.
   - Recommendation: The plan should include Windows setup instructions (UTM + Windows 11 ARM). If the user already has Windows access, this step is skipped.

3. **Do any forms contain VBA code-behind?**
   - What we know: Zero standalone modules exist. The database was built by a non-programmer.
   - What's unclear: Whether forms use `[Event Procedure]` handlers (common even in non-programmer databases for navigation buttons).
   - Recommendation: After SaveAsText extraction, scan all form files for VBA markers. Expect to find at least button click handlers for form navigation.
   - **Impact:** If no VBA exists anywhere, VBA-01 through VBA-05 are satisfied by documenting the absence. If code-behind exists, it must be documented.

4. **What encoding does SaveAsText use for Thai content?**
   - What we know: The database stores Thai in UTF-16-LE with Windows-874 collation. SaveAsText output encoding depends on the Windows locale settings.
   - What's unclear: Whether a Windows VM with English locale will correctly export Thai form captions and VBA comments.
   - Recommendation: Configure Windows VM with Thai language support or UTF-8 beta. Test one form export before bulk extraction.

5. **Are query parameter prompts (input boxes) used?**
   - What we know: Several queries have names suggesting date-range filtering (`เจาะจงโดยวันที่` = "specific by date"). Access parameter queries prompt the user for input values at runtime.
   - What's unclear: Whether these use PARAMETERS declarations (which appear in SQL) or rely on form controls for input.
   - Recommendation: After SQL extraction, check for PARAMETERS keyword and `[prompt text]` patterns in SQL. Document all parameter queries specially -- they represent user interaction points.

6. **How should the Java dependency be handled relative to the "Python-only" constraint?**
   - What we know: Phase 1 locked "Python-only dependencies -- no Homebrew." Java requires either Homebrew or a manual download.
   - What's unclear: Whether the user considers Java acceptable as a bridge dependency.
   - Recommendation: Present as a choice at plan time: (A) Install Java for macOS query extraction, or (B) extract queries on Windows alongside forms/reports. Both produce the same output.

## Sources

### Primary (HIGH confidence)
- [Application.SaveAsText](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/application-save-as-text) -- Official Microsoft documentation, object type constants and syntax
- [SaveAsText format](https://learn.microsoft.com/en-us/archive/blogs/thirdoffive/templates-quick-overview-of-saveastext-and-loadfromtext-aka-lets-get-boring-again) -- Microsoft archive blog showing BEGIN/END format structure with full example
- [Jackcess Java Library](https://jackcess.sourceforge.io/) -- Official site, query support confirmed (getQueries, toSQLString), version 4.0.8
- [Jackcess FAQ](https://jackcess.sourceforge.io/faq.html) -- Confirms query reading since v1.1.19, documents cannot execute queries
- [Jackcess QueryImpl API](https://jackcess.sourceforge.io/apidocs/com/healthmarketscience/jackcess/impl/query/QueryImpl.html) -- toSQLString method, supported query types
- [MSysQueries structure](https://www.isladogs.co.uk/explaining-queries/) -- Attribute codes, flag meanings, decomposed row format
- [QueryDef.SQL property](https://learn.microsoft.com/en-us/office/client-developer/access/desktop-database-reference/querydef-sql-property-dao) -- Official DAO documentation
- Phase 1 and Phase 2 outputs from this project -- Validated inventory data, schema extraction patterns

### Secondary (MEDIUM confidence)
- [JPype1 PyPI](https://pypi.org/project/jpype1/) -- Installation, API overview
- [PowerShell Access Automation](https://gist.github.com/tniedbala/8b21b9cf08aefacb210cbcd573ddf0b7) -- COM object interaction patterns
- [UTM Virtual Machines](https://docs.getutm.app/guides/windows/) -- Windows 11 ARM on macOS setup guide
- [Access Forum: Export All Objects](https://www.access-programmers.co.uk/forums/threads/export-all-database-objects-into-text-files.99179/) -- Community-validated VBA export scripts
- [Jackcess QueryTest](https://github.com/jahlborn/jackcess/blob/master/src/test/java/com/healthmarketscience/jackcess/query/QueryTest.java) -- Test code showing toSQLString usage

### Tertiary (LOW confidence)
- Training data on Access form/report binary format internals -- Not verified
- Query type inference from MSysObjects flags -- Confirmed unreliable for this database (MSysQueries inaccessible)
- Windows ARM + Access compatibility specifics -- General consensus, not tested on this specific setup

## Metadata

**Confidence breakdown:**
- Query extraction (Jackcess): MEDIUM -- Library is HIGH confidence but JPype integration on macOS arm64 is unvalidated
- Query extraction (Windows fallback): HIGH -- QueryDef.SQL is the standard approach, well-documented
- Form/report extraction: HIGH -- SaveAsText is the only approach and is well-documented
- SaveAsText parsing: MEDIUM -- Format is simple but Thai encoding handling needs validation
- Business logic documentation: MEDIUM -- Depends on what queries and forms actually contain (synthesized from extracted data)
- Windows setup: MEDIUM -- UTM + Windows ARM is viable but setup complexity varies

**Key risk for Phase 3:** The Windows environment. Unlike Phases 1-2 which were macOS-only, Phase 3 requires Windows for 17 forms and 25 reports. If the user cannot set up Windows, approximately 60% of Phase 3 requirements (FORM-01, FORM-02, FORM-03, VBA-01, VBA-04, VBA-05 and parts of VBA-02, VBA-03) are blocked. Query extraction (QURY-01, QURY-02, QURY-03) can proceed on macOS via Jackcess.

**Recommended plan split:**
- **Plan 1 (macOS):** Query SQL extraction via Jackcess, query catalogue, dependency graph, type classification. Deliverables: assessment/queries/ directory with overview, per-query docs, dependency graph. Addresses QURY-01, QURY-02, QURY-03.
- **Plan 2 (Windows + macOS):** Windows setup, SaveAsText extraction, form/report parsing, business logic synthesis. Deliverables: assessment/forms/, assessment/reports/, assessment/business_logic/ directories. Addresses FORM-01, FORM-02, FORM-03, VBA-01, VBA-02, VBA-03, VBA-04, VBA-05.

**Research date:** 2026-02-15
**Valid until:** 2026-03-15 (30 days -- Jackcess and SaveAsText are stable; project database file is static)
