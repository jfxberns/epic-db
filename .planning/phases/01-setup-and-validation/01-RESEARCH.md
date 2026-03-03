# Phase 1: Setup and Validation - Research

**Researched:** 2026-02-14
**Domain:** Python extraction of Microsoft Access .accdb on macOS arm64, Thai encoding validation
**Confidence:** MEDIUM (primary tool verified, but Thai encoding and system table access need runtime validation)

## Summary

Reading epic_db.accdb on macOS arm64 with pip-only dependencies restricts us to pure-Python parsers. The primary tool is **access-parser** (Claroty, v0.0.6, PyPI, corporate-backed, 88 GitHub stars, 6 contributors). It parses the .accdb binary format directly and can read both user tables and system tables including MSysObjects. It does NOT parse queries, forms, reports, VBA modules, or macros as structured objects -- it only parses table-like data structures.

**The database file (`epic_db.accdb`) has been verified as Access version 0x03** (Access 2010 format, 15MB, "Standard ACE DB" header). This version is within access-parser's explicitly supported range. The post-2010 compatibility issue (#35) does not apply.

Access stores all text internally as UTF-16-LE with an optional proprietary compression scheme. Thai characters (U+0E00-U+0E7F) are fully representable. However, access-parser has **documented, unfixed encoding bugs** (GitHub issues #21 and #26) where compressed Unicode text is not properly decoded. PR #33 ("Text parsing overhaul") addresses these but remains **unmerged** as of Feb 2026. If Thai text is broken at runtime, the mitigation path is: (1) apply the community patch from issue #21/PR #33, (2) try the McSash fork (access_parser_c), or (3) manually decode UTF-16-LE compressed segments. Thai encoding validation is a hard blocker -- it must pass before proceeding.

The complete object inventory is achievable on macOS by reading the MSysObjects system table directly via `db.parse_table("MSysObjects")`. This table contains rows for every object in the database with type codes: 1=table, 5=query, -32768=form, -32764=report, -32766=macro, -32761=module. Object **names** are accessible for all types. Object **content** (form layouts, VBA code, report definitions) requires Windows with Microsoft Access -- these are stored as binary blobs that only the Access COM Object Model can interpret. The user's Windows threshold decision applies: if names are listable on macOS, the inventory phase is viable; content extraction is deferred to Windows if/when needed.

**Primary recommendation:** Use access-parser as the sole parser. Read MSysObjects for the full object inventory. Validate Thai encoding on the very first table read. Accept that form/report/VBA **content** requires Windows. For queries, list names and types from MSysObjects; defer SQL reconstruction to Phase 2.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Python-only dependencies -- no Homebrew. Everything must install via pip/uv into the project venv
- Mix tools if needed -- use different tools per object type rather than requiring one tool to handle everything
- Validation bar: tool must successfully read ALL tables and queries (not just one sample) before we commit to it
- Inventory as a Markdown document in `assessment/` top-level folder
- Include brief metadata per object: row counts for tables, query type (SELECT/UPDATE/etc.), module line counts where available
- Extraction scripts should be kept as clean, reusable tools -- not throwaway code. The .accdb may need re-extraction
- Subfolders per object type within assessment/ (tables/, queries/, etc.)
- User can set up a Windows VM but does not have one now
- Claude decides when to recommend Windows vs. keep trying macOS -- based on what tool validation reveals
- Windows threshold: if macOS tools cannot even LIST forms/reports/VBA names, Windows is needed. If names are accessible but detail is not, that's still macOS-viable
- If Windows is needed, scripts must be fully automated/headless -- user runs one command, gets output files
- Correct Thai rendering is a BLOCKER -- do not proceed to Phase 2 if encoding is broken (mojibake)
- Both column/field names AND row data must render Thai correctly
- User can spot-check some Thai but cannot read it fluently -- validation should include visual output the user can verify with help
- No known reference values yet -- user can check the database to get test values if needed
- **access-parser is the PRIMARY and ONLY parser** (user decision: pyaccdb dropped due to security concerns)

### Claude's Discretion
- Specific tool selection and evaluation order
- When to recommend Windows vs. exhaust macOS options
- Encoding detection and fix strategy
- Script architecture and module organization
- Assessment directory internal structure beyond the top-level convention

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard | Confidence |
|---------|---------|---------|--------------|------------|
| access-parser | 0.0.6 (PyPI, Jan 2025) | Primary .accdb binary parser -- reads table data and system tables from .accdb format | Pure Python, pip-installable, corporate-backed (Claroty security), 88 GitHub stars, 49 commits, 6 contributors. Only actively maintained pure-Python .accdb parser on PyPI. | HIGH (tool exists and installs), MEDIUM (encoding bugs documented) |
| tabulate | latest (PyPI) | Markdown table formatting for inventory output | Standard Python library for generating formatted markdown tables. Handles alignment and escaping correctly. | HIGH |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| oletools | >=0.60 (PyPI) | Attempt VBA extraction from .accdb binary | Try early in validation. Official docs do NOT list .accdb as supported, but some community usage suggests partial support. If it fails, confirms Windows is needed for VBA. Worth a quick test -- costs nothing. |
| JPype1 | latest (PyPI) | Java-Python bridge for Jackcess | Only if query SQL reconstruction from MSysQueries proves too complex to do manually in Phase 2. Enables calling Jackcess `toSQLString()` from Python. NOT needed for Phase 1 inventory. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| access-parser | access_parser_c (McSash fork) | Fork with potential encoding fixes. Install via `pip install git+https://github.com/McSash/access_parser_c`. 34 commits, no PyPI release. Less documented but may handle Unicode compression better. Try only if access-parser Thai encoding is broken. |
| access-parser | mdbtools (system binary) | Requires Homebrew -- violates Python-only constraint. Mature and reliable but not pip-installable. |
| access-parser | mdb-parser (PyPI) | This is just a Python wrapper around the mdbtools C binary. Requires mdbtools installed via Homebrew. Violates pip-only constraint. Discontinued (no releases in 12+ months). |
| tabulate | Custom string formatting | Error-prone for alignment and special characters. tabulate is battle-tested. |

**Installation:**
```bash
# In project venv
pip install access-parser tabulate

# Optional: test VBA extraction (may not work with .accdb)
pip install oletools
```

**If Thai encoding is broken with access-parser:**
```bash
# Option 1: Try the McSash fork
pip install git+https://github.com/McSash/access_parser_c

# Option 2: Apply community patches from issue #21 / PR #33 manually
# (See Pitfall 1 below for details)
```

## Architecture Patterns

### Recommended Project Structure
```
epic-db/
  data/
    epic_db.accdb              # Source database (read-only, NEVER modified)
  scripts/
    db_reader.py               # Core: open DB, read tables, handle encoding
    inventory.py               # Enumerate all objects from MSysObjects
    validate_encoding.py       # Thai encoding validation (blocker check)
    extract_tables.py          # Extract table schemas and row counts
    extract_queries.py         # Extract query definitions from MSysQueries
  assessment/
    inventory.md               # Master inventory of all objects with counts
    tables/                    # Per-table schema and sample data (Phase 2+)
    queries/                   # Per-query definitions (Phase 2+)
    forms/                     # Form names, metadata (content requires Windows)
    reports/                   # Report names, metadata (content requires Windows)
    modules/                   # Module names (content requires Windows)
    macros/                    # Macro names (content requires Windows)
  .venv/                       # Python virtual environment (already exists)
```

### Pattern 1: Centralized DB Access Module

**What:** Wrap database access in a module that all scripts import.
**When to use:** Always -- avoids duplicating the file path, parser initialization, and encoding workarounds.

```python
# scripts/db_reader.py
from pathlib import Path
from access_parser import AccessParser

DB_PATH = Path(__file__).parent.parent / "data" / "epic_db.accdb"

def open_db(db_path: Path = DB_PATH) -> AccessParser:
    """Open the Access database. Returns AccessParser instance."""
    return AccessParser(str(db_path))

def get_user_tables(db: AccessParser) -> list[str]:
    """Get user table names from catalog (excludes system tables)."""
    return list(db.catalog.keys())

def parse_system_table(db: AccessParser, table_name: str) -> dict:
    """Read a system table directly, bypassing catalog filter."""
    return db.parse_table(table_name)
```

### Pattern 2: MSysObjects Full Inventory

**What:** Read MSysObjects to enumerate every object in the database by type.
**When to use:** For the complete inventory requirement (SETUP-04).

```python
# Object type constants from MSysObjects.Type column
MSYS_OBJECT_TYPES = {
    1: "Table (Local)",
    4: "Table (Linked ODBC)",
    5: "Query",
    6: "Table (Linked)",
    -32768: "Form",
    -32764: "Report",
    -32766: "Macro",
    -32761: "Module",
}

def build_inventory(db):
    """Build complete inventory from MSysObjects."""
    msys = db.parse_table("MSysObjects")
    names = msys.get("Name", [])
    types = msys.get("Type", [])
    flags = msys.get("Flags", [])

    inventory = {}
    for name, obj_type, obj_flags in zip(names, types, flags):
        obj_name = str(name)
        # Skip system objects and temp objects
        if obj_name.startswith("MSys") or obj_name.startswith("~"):
            continue
        if obj_type in MSYS_OBJECT_TYPES:
            type_label = MSYS_OBJECT_TYPES[obj_type]
            if type_label not in inventory:
                inventory[type_label] = []
            inventory[type_label].append({
                "name": obj_name,
                "type": obj_type,
                "flags": obj_flags,
            })
    return inventory
```

### Pattern 3: Thai Encoding Validation

**What:** Test Thai text extraction early and produce visual output for user verification.
**When to use:** Immediately after parser setup -- this is a blocker.

```python
THAI_UNICODE_RANGE = range(0x0E00, 0x0E80)  # Thai block in Unicode

def validate_thai_encoding(text: str, label: str = "") -> dict:
    """Check if text contains properly rendered Thai characters."""
    has_thai = any(ord(c) in THAI_UNICODE_RANGE for c in str(text))
    has_replacement = "\ufffd" in str(text)
    has_null_artifacts = "\x00" in str(text)

    result = {
        "label": label,
        "text": str(text),
        "has_thai": has_thai,
        "has_replacement_chars": has_replacement,
        "has_null_artifacts": has_null_artifacts,
        "likely_valid": has_thai and not has_replacement and not has_null_artifacts,
    }
    return result

def print_encoding_report(results: list[dict]):
    """Print Thai encoding validation report for user visual check."""
    print("=" * 60)
    print("THAI ENCODING VALIDATION REPORT")
    print("=" * 60)
    for r in results:
        status = "PASS" if r["likely_valid"] else "FAIL"
        print(f"\n[{status}] {r['label']}")
        print(f"  Text: {r['text'][:100]}")
        if r["has_thai"]:
            # Show Unicode codepoints for verification
            codepoints = [f"U+{ord(c):04X}" for c in r["text"][:20]]
            print(f"  Codepoints: {' '.join(codepoints)}")
        if not r["likely_valid"]:
            if r["has_replacement_chars"]:
                print("  WARNING: Contains replacement characters (U+FFFD)")
            if r["has_null_artifacts"]:
                print("  WARNING: Contains null bytes -- possible encoding issue")
            if not r["has_thai"]:
                print("  WARNING: No Thai characters detected in expected Thai field")
```

### Pattern 4: Row Count Collection

**What:** Get row counts for every user table by parsing tables.
**When to use:** For inventory metadata (table row counts).

```python
def get_row_count(db, table_name: str) -> int:
    """Get row count for a table. Parses the full table (memory concern for large tables)."""
    try:
        table_data = db.parse_table(table_name)
        # table_data is defaultdict(list) -- all columns have same length
        if table_data:
            first_col = next(iter(table_data.values()))
            return len(first_col)
        return 0
    except Exception as e:
        return -1  # Indicate parse failure
```

**Note:** access-parser loads the entire table into memory. For the ~15MB database this should be fine, but track memory usage.

### Anti-Patterns to Avoid

- **Relying on `db.catalog` for the full inventory:** `catalog` only returns Type=1 (user tables). It explicitly filters out system tables and all non-table objects. Use `db.parse_table("MSysObjects")` to get everything.
- **Assuming oletools can extract VBA from .accdb:** The official olevba documentation does NOT list .accdb as a supported format. It may work, it may not -- test it, but have a plan for failure.
- **Trying to parse form/report/VBA content from .accdb binary on macOS:** These are stored as opaque binary blobs requiring the Access COM Object Model. Enumerate names from MSysObjects only; do not attempt content extraction.
- **Assuming MSysQueries contains plain SQL text:** MSysQueries stores queries as decomposed component rows (attribute/flag/name1/name2/expression). SQL reconstruction is complex. For Phase 1, just list query names and types from MSysObjects.
- **Ignoring encoding validation until later:** Thai encoding bugs in access-parser are documented and unresolved in the main branch. Test encoding on the very first table read.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| .accdb binary parsing | Custom binary parser | access-parser | Undocumented binary format, version-specific quirks, compression, page structures |
| UTF-16-LE compressed text decoding | Custom decompressor | access-parser (or patch from issue #21) | Access uses proprietary compression (FF FE header, toggle mode). Community has working implementations |
| SQL reconstruction from MSysQueries | Custom SQL builder | Jackcess via JPype (Phase 2 if needed) OR documented attribute table | MSysQueries decomposition is complex; Jackcess has battle-tested toSQLString() |
| Markdown table formatting | String concatenation | tabulate with `tablefmt="pipe"` | Handles alignment, escaping, Unicode correctly |
| Object type enumeration | Manual database exploration | MSysObjects system table with type constants | MSysObjects is the authoritative, complete source |

**Key insight:** The .accdb format has no public specification from Microsoft. All open-source parsers are reverse-engineered from the mdbtools project's documentation efforts. Reusing established code avoids re-discovering format quirks.

## Common Pitfalls

### Pitfall 1: Unicode Compression Mishandling (HIGH RISK)
**What goes wrong:** Thai text appears as mojibake, garbled characters, empty strings, or characters from wrong scripts (e.g., Korean appearing in Swedish text per issue #26).
**Why it happens:** Access stores text as UTF-16-LE with a proprietary compression scheme. When the `FF FE` BOM marker is present, text toggles between compressed (single-byte + implicit null padding) and uncompressed (raw UTF-16-LE) segments. access-parser v0.0.6 has known bugs handling this compression -- issues #21, #26 are open, and PR #33 (the fix) is NOT merged.
**How to avoid:**
  1. Test Thai text extraction on the very first table read during setup.
  2. If broken, apply the community fix: PR #33 contains a "text parsing overhaul" that correctly handles Unicode compression based on the Jackcess Java implementation.
  3. Alternative: install the McSash fork (`pip install git+https://github.com/McSash/access_parser_c`) which may include encoding fixes.
  4. Last resort: post-process text manually using the known compression scheme (FF FE header, null-byte-delimited segments, expand compressed segments by doubling data length to restore UTF-16-LE padding, decode as UTF-16-LE).
**Warning signs:** Characters like `\x00\x38` instead of proper text, garbage characters appended to table/column names, `\ufffd` replacement characters, `UnicodeDecodeError` exceptions, strings that are half-correct and half-garbled.

### Pitfall 2: System Tables Filtered from Catalog
**What goes wrong:** The `db.catalog` property shows only user tables, making it appear the database has fewer objects than it actually does. MSysObjects, MSysQueries, and all non-table objects are invisible.
**Why it happens:** access-parser's `_parse_catalog()` method explicitly filters to `Type == 1` (user tables) and excludes system table flags. This is by design for the common case but hides the full inventory.
**How to avoid:** Use `db.parse_table("MSysObjects")` to read the system catalog directly. This returns all rows including all object types.
**Warning signs:** Inventory shows only tables and no queries, forms, reports, modules, or macros.

### Pitfall 3: Confusing "Can List Names" with "Can Extract Content"
**What goes wrong:** Seeing form/report/module names in MSysObjects and assuming their content (layouts, code, properties) can also be extracted on macOS.
**Why it happens:** MSysObjects stores metadata (names, types, flags, timestamps) for ALL objects. But form layouts, report definitions, and VBA code are stored in separate binary structures that only the Access COM Object Model can interpret. No open-source tool on macOS can parse these binary blobs.
**How to avoid:** In the inventory, clearly mark each object category with its extraction status:
  - Tables: name + schema + data (full extraction on macOS)
  - Queries: name + type (from MSysObjects); SQL reconstruction possible but complex (Phase 2)
  - Forms: name only (content requires Windows)
  - Reports: name only (content requires Windows)
  - Modules: name only (content requires Windows)
  - Macros: name only (content requires Windows)
**Warning signs:** Attempting to read form/report binary data and getting opaque byte sequences or parse errors.

### Pitfall 4: MSysQueries Does Not Contain Plain SQL
**What goes wrong:** Expecting to find SQL strings in MSysQueries, but finding rows of attribute/flag/name1/name2/expression tuples that do not resemble SQL.
**Why it happens:** Access decomposes queries into components: one row per join, one per selected field, one per WHERE condition, one per ORDER BY clause. Each row has an Attribute code (1=query type, 5=table, 6=field, 7=join, 8=where, 11=order by) and corresponding Flag/Name values. This is NOT plain SQL.
**How to avoid:** For Phase 1, do NOT attempt SQL reconstruction. Just enumerate query names and types from MSysObjects (Type=5). The Flags field in MSysObjects for queries encodes the query subtype:
  - Flag values 0=Select, 16=Crosstab, 32=Delete, 48=Update, 64=Append, 80=Make Table, 96=DDL, 112=Pass-through, 128=Union
  Defer full SQL reconstruction to Phase 2 where Jackcess via JPype can be used if needed.
**Warning signs:** Reading MSysQueries and seeing cryptic numeric rows instead of SQL strings.

### Pitfall 5: oletools Does Not Support .accdb (Likely)
**What goes wrong:** Running olevba against the .accdb file and getting no output, errors, or misleading results.
**Why it happens:** The official olevba documentation lists Word, Excel, PowerPoint, and Publisher as supported formats. Access .accdb is NOT in the supported format list. The .accdb format stores VBA differently than OLE2 compound documents that oletools was built for.
**How to avoid:** Test oletools quickly as an opportunistic check. If it extracts VBA, great. If not, do not debug -- accept that VBA content extraction requires Windows with Access installed. Do not waste time on this.
**Warning signs:** Empty output, "Not a supported format" errors, binary gibberish.

### Pitfall 6: access-parser Memory Usage
**What goes wrong:** access-parser parses the entire file into memory rather than streaming pages on demand. For a 15MB database this is likely fine, but could be slow if there are very large tables.
**Why it happens:** The library's architecture reads all pages upfront (noted in comparisons with other libraries).
**How to avoid:** Monitor memory usage during parsing. If table parsing is slow, parse tables selectively rather than calling `print_database()` which parses everything. Get row counts table-by-table.
**Warning signs:** Long parse times, high memory usage, Python process slowdown.

## Code Examples

### Opening the Database and Checking Version
```python
# Step 1: Verify the database version before parsing
import struct

def check_accdb_version(db_path: str) -> dict:
    """Read the .accdb file header to determine version."""
    with open(db_path, "rb") as f:
        header = f.read(0x20)
    magic = header[:4]
    signature = header[4:20].decode("ascii", errors="replace").rstrip("\x00")
    version_byte = header[0x14]

    VERSION_MAP = {
        0: "Access 2000 (Jet 4.0)",
        1: "Access 2002-2003 (Jet 4.0)",
        2: "Access 2007",
        3: "Access 2010",
        6: "Access 2013+ (may not be supported by access-parser)",
    }
    return {
        "signature": signature,
        "version_byte": version_byte,
        "version_name": VERSION_MAP.get(version_byte, f"Unknown ({version_byte})"),
        "supported": version_byte <= 3,
    }

# epic_db.accdb confirmed: version_byte=3, signature="Standard ACE DB"
```

### Complete Object Inventory from MSysObjects
```python
# Source: MSysObjects type reference (devhut.net, isladogs.co.uk, Microsoft Q&A)
from access_parser import AccessParser

OBJECT_TYPES = {
    1: "Table",
    4: "Linked Table (ODBC)",
    5: "Query",
    6: "Linked Table",
    -32768: "Form",
    -32764: "Report",
    -32766: "Macro",
    -32761: "Module",
}

def build_full_inventory(db_path: str) -> dict:
    """Build complete inventory of all database objects."""
    db = AccessParser(db_path)
    msys = db.parse_table("MSysObjects")

    names = msys.get("Name", [])
    types = msys.get("Type", [])
    flags = msys.get("Flags", [])

    inventory = {label: [] for label in OBJECT_TYPES.values()}
    for name, obj_type, obj_flags in zip(names, types, flags):
        obj_name = str(name)
        # Skip system and temp objects
        if obj_name.startswith("MSys") or obj_name.startswith("~"):
            continue
        if obj_type in OBJECT_TYPES:
            inventory[OBJECT_TYPES[obj_type]].append({
                "name": obj_name,
                "flags": obj_flags,
            })
    return inventory
```

### Extracting Query Subtypes
```python
# Source: isladogs.co.uk/explaining-queries/ (MSysQueries Attribute/Flag reference)
QUERY_SUBTYPES = {
    0: "SELECT",
    16: "CROSSTAB",
    32: "DELETE",
    48: "UPDATE",
    64: "APPEND (INSERT INTO)",
    80: "MAKE TABLE (SELECT INTO)",
    96: "DATA DEFINITION (DDL)",
    112: "PASS-THROUGH",
    128: "UNION",
}

def classify_queries(inventory_queries: list[dict]) -> list[dict]:
    """Add query subtype classification based on flags."""
    for q in inventory_queries:
        # The flags field from MSysObjects for Type=5 objects
        # encodes the query subtype
        base_flag = q["flags"] & ~0x08  # Remove hidden bit
        q["subtype"] = QUERY_SUBTYPES.get(base_flag, f"Unknown ({q['flags']})")
    return inventory_queries
```

### Thai Encoding Validation Script
```python
def validate_thai_on_table(db, table_name: str, max_rows: int = 5) -> list[dict]:
    """Extract sample rows and check for Thai character rendering."""
    THAI_RANGE = range(0x0E00, 0x0E80)
    results = []

    try:
        table = db.parse_table(table_name)
    except Exception as e:
        return [{"label": f"PARSE ERROR: {table_name}", "text": str(e),
                 "has_thai": False, "likely_valid": False}]

    for col_name, values in table.items():
        for i, val in enumerate(values[:max_rows]):
            text = str(val)
            has_thai = any(ord(c) in THAI_RANGE for c in text)
            if has_thai or i == 0:  # Always show first row + any Thai
                results.append({
                    "label": f"{table_name}.{col_name}[{i}]",
                    "text": text[:200],
                    "has_thai": has_thai,
                    "has_replacement_chars": "\ufffd" in text,
                    "has_null_artifacts": "\x00" in text,
                    "likely_valid": has_thai and "\ufffd" not in text and "\x00" not in text,
                })
    return results
```

### Generating Markdown Inventory
```python
from tabulate import tabulate
from pathlib import Path

def write_inventory_md(inventory: dict, row_counts: dict, output_path: Path):
    """Write inventory as formatted markdown document."""
    lines = [
        "# Epic DB Object Inventory",
        "",
        f"**Generated:** {__import__('datetime').date.today()}",
        f"**Source:** data/epic_db.accdb (Access 2010 format, 15MB)",
        "",
        "## Summary",
        "",
    ]

    # Summary table
    summary_rows = []
    for obj_type, objects in inventory.items():
        summary_rows.append([obj_type, len(objects)])
    lines.append(tabulate(summary_rows, headers=["Object Type", "Count"],
                          tablefmt="pipe"))
    lines.append("")

    # Detailed sections per type
    for obj_type, objects in inventory.items():
        lines.append(f"\n## {obj_type}s ({len(objects)})")
        lines.append("")
        if not objects:
            lines.append("*None found*")
            continue

        if obj_type == "Table":
            headers = ["Name", "Row Count"]
            rows = [[o["name"], row_counts.get(o["name"], "?")] for o in objects]
        elif obj_type == "Query":
            headers = ["Name", "Type"]
            rows = [[o["name"], o.get("subtype", "?")] for o in objects]
        else:
            headers = ["Name"]
            rows = [[o["name"]] for o in objects]

        lines.append(tabulate(rows, headers=headers, tablefmt="pipe"))
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
```

## Windows Fallback Strategy

### When Windows is Needed (Claude's Discretion, Researched)

Based on research, the Windows threshold is clear:

| What | macOS Can Do | Requires Windows |
|------|-------------|-----------------|
| Table names | YES (MSysObjects) | -- |
| Table schema + data | YES (access-parser) | -- |
| Query names + types | YES (MSysObjects) | -- |
| Query SQL text | PARTIAL (MSysQueries decomposed) | Full SQL via COM |
| Form names | YES (MSysObjects) | -- |
| Form layout/controls/VBA | NO | YES (SaveAsText) |
| Report names | YES (MSysObjects) | -- |
| Report layout/data source | NO | YES (SaveAsText) |
| Module names | YES (MSysObjects) | -- |
| Module VBA code | NO (oletools unlikely) | YES (SaveAsText/VBE) |
| Macro names | YES (MSysObjects) | -- |
| Macro definitions | NO | YES (SaveAsText) |

**Recommendation:** macOS is sufficient for Phase 1 (inventory with names, types, table row counts, and Thai encoding validation). Windows is needed starting in Phase 3 (Logic+Interface) for VBA code, form layouts, and report definitions.

### Automated Windows Export Script

If Windows is needed, the following VBA script exports everything headlessly. This can be placed in the .accdb file or a separate .accdb and invoked via command line:

```vba
' ExportAll.bas -- Run via: msaccess.exe /x ExportAll epic_db.accdb
Public Sub ExportAll()
    Dim db As Database
    Dim d As Document
    Dim c As Container
    Dim i As Integer
    Dim sPath As String

    Set db = CurrentDb()
    sPath = CurrentProject.Path & "\export\"

    ' Ensure output directory exists
    MkDir sPath

    ' Export Forms
    Set c = db.Containers("Forms")
    For Each d In c.Documents
        Application.SaveAsText acForm, d.Name, sPath & "Form_" & d.Name & ".txt"
    Next d

    ' Export Reports
    Set c = db.Containers("Reports")
    For Each d In c.Documents
        Application.SaveAsText acReport, d.Name, sPath & "Report_" & d.Name & ".txt"
    Next d

    ' Export Macros
    Set c = db.Containers("Scripts")
    For Each d In c.Documents
        Application.SaveAsText acMacro, d.Name, sPath & "Macro_" & d.Name & ".txt"
    Next d

    ' Export Modules
    Set c = db.Containers("Modules")
    For Each d In c.Documents
        Application.SaveAsText acModule, d.Name, sPath & "Module_" & d.Name & ".txt"
    Next d

    ' Export Queries
    For i = 0 To db.QueryDefs.Count - 1
        Application.SaveAsText acQuery, db.QueryDefs(i).Name, _
            sPath & "Query_" & db.QueryDefs(i).Name & ".txt"
    Next i

    MsgBox "Export complete: " & sPath
    Application.Quit
End Sub
```

**PowerShell wrapper for headless invocation:**
```powershell
$access = New-Object -ComObject Access.Application
$access.OpenCurrentDatabase("C:\path\to\epic_db.accdb")
$access.Run "ExportAll"
$access.Quit
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| mdbtools (C/Homebrew) for .accdb on macOS | Pure Python parsers (access-parser) | 2021-2025 | No system dependencies; pip-installable; cross-platform |
| pyodbc + Access ODBC driver (Windows only) | Pure Python binary parsers | 2021-2025 | Cross-platform Access reading possible |
| oletools for VBA extraction from .accdb | Windows COM (Application.SaveAsText) | Ongoing | oletools does not officially support .accdb; COM is the reliable path |

**Deprecated/outdated approaches (do NOT use):**
- **mdbtools for .accdb:** Requires Homebrew (violates constraint). Also, .accdb support is secondary to .mdb support.
- **mdb-parser (PyPI):** Wrapper around mdbtools C binary. Requires mdbtools installed. Discontinued.
- **pyodbc on macOS:** No Access ODBC driver exists for macOS. Full stop.
- **pyaccdb:** Dropped from consideration per user decision (security concerns: unaudited code, personal git host, not on PyPI, 15 commits).

## Open Questions

1. **Does access-parser correctly decode Thai text from epic_db.accdb?**
   - What we know: access-parser has documented Unicode compression bugs (issues #21, #26). PR #33 with fixes is NOT merged. The database is Access 2010 format (version 0x03), which is within the supported range.
   - What's unclear: Whether Thai text in this specific database triggers the compression bugs. Some databases may not use compression for Thai text.
   - Recommendation: Test immediately during setup. If broken, apply PR #33 patches or try McSash fork. This is the #1 risk for Phase 1.

2. **Can access-parser successfully read MSysObjects from this database?**
   - What we know: The `parse_table("MSysObjects")` call should work since MSysObjects is stored as a regular table in the binary format.
   - What's unclear: Whether the specific MSysObjects structure in Access 2010 format matches what access-parser expects. The column names (Name, Type, Flags) should be standard.
   - Recommendation: Test during setup. If MSysObjects is unreadable, the entire inventory approach needs rethinking.

3. **Does oletools produce any VBA output from this .accdb?**
   - What we know: olevba's official supported formats do NOT include .accdb. However, the tool may still produce partial results.
   - What's unclear: Whether running olevba against epic_db.accdb produces anything useful.
   - Recommendation: Quick test (5 minutes). If it works, document it. If not, confirm Windows is needed for VBA and move on.

4. **How many queries exist, and can their types be determined from MSysObjects flags?**
   - What we know: MSysObjects stores Type=5 for queries. The Flags field should encode query subtypes (SELECT/UPDATE/etc.).
   - What's unclear: Whether the flag encoding matches the documented values. The documentation references are from Access 2003-era sources.
   - Recommendation: Test during inventory generation. Cross-reference a few query names with known behavior if possible.

5. **Are there linked tables in this database?**
   - What we know: MSysObjects Type=4 (ODBC linked) and Type=6 (linked) indicate external table links.
   - What's unclear: Whether epic_db.accdb has any linked tables. The project description says "no external dependencies."
   - Recommendation: Check during inventory. Flag prominently if found.

## Verified Facts

These were confirmed during this research session (not just training data):

| Fact | How Verified | Confidence |
|------|-------------|------------|
| epic_db.accdb is Access 2010 format (version byte 0x03) | Binary header inspection of the actual file | HIGH |
| File size is 15MB | `ls -lh` on the actual file | HIGH |
| File signature is "Standard ACE DB" | Binary header inspection | HIGH |
| access-parser version is 0.0.6, released Jan 2025 | GitHub repo, PyPI page | HIGH |
| access-parser has 88 GitHub stars, 49 commits, 6 contributors | GitHub repo page | HIGH |
| PR #33 (encoding fix) is NOT merged | GitHub PR page | HIGH |
| Issues #21 and #26 (encoding bugs) are OPEN | GitHub issues page | HIGH |
| oletools does NOT list .accdb in supported formats | Official olevba wiki documentation | HIGH |
| MSysObjects Type codes: 1=table, 5=query, -32768=form, -32764=report, -32766=macro, -32761=module | Multiple authoritative Access documentation sources | HIGH |
| MSysQueries stores decomposed components, not SQL text | isladogs.co.uk detailed analysis | HIGH |
| Access stores text as UTF-16-LE with optional compression | Microsoft Learn documentation | HIGH |
| mdb-parser (PyPI) wraps mdbtools C binary (requires Homebrew) | Package documentation and source code | HIGH |
| Python 3.11.12 available in project venv | pyvenv.cfg inspection | HIGH |

## Sources

### Primary (HIGH confidence)
- [access-parser GitHub](https://github.com/claroty/access_parser) - README, source code, API, version info
- [access-parser GitHub Issue #21](https://github.com/claroty/access_parser/issues/21) - TYPE_TEXT Unicode Decoding bug, community fix
- [access-parser GitHub Issue #26](https://github.com/claroty/access_parser/issues/26) - Character encoding in table names/values
- [access-parser GitHub Issue #35](https://github.com/claroty/access_parser/issues/35) - Post-2010 database version support
- [access-parser GitHub PR #33](https://github.com/claroty/access_parser/pull/33) - Text parsing overhaul (unmerged)
- [MSysObjects type reference](https://www.devhut.net/ms-access-listing-of-database-objects/) - Complete type codes for all object types
- [MSysQueries structure](https://www.isladogs.co.uk/explaining-queries/) - Attribute/flag decomposition, query type encoding
- [Microsoft Learn - Unicode compression](https://learn.microsoft.com/en-us/office/vba/access/concepts/miscellaneous/about-compressing-the-data-in-a-text-memo-or-hyperlink-field) - How Access stores compressed text
- [oletools olevba wiki](https://github.com/decalage2/oletools/wiki/olevba) - Supported file formats (does NOT include .accdb)
- [Access export VBA](https://www.access-programmers.co.uk/forums/threads/export-all-database-objects-into-text-files.99179/) - Application.SaveAsText approach
- Binary inspection of actual epic_db.accdb file header - Version confirmation

### Secondary (MEDIUM confidence)
- [access_parser_c (McSash fork)](https://github.com/McSash/access_parser_c) - Alternative with potential encoding fixes
- [Claroty team blog](https://www.claroty.com/team82/research/open-source-accessdb-parser-for-microsoft-access-db) - Library origin story and purpose
- [mdb-parser PyPI](https://pypi.org/project/mdb-parser/) - Confirmed wrapper around mdbtools binary
- [access-parser Snyk analysis](https://snyk.io/advisor/python/access-parser) - Package health, maintenance status

### Tertiary (LOW confidence)
- WebSearch results on oletools .accdb compatibility - Conflicting claims, no official confirmation
- WebSearch results on Thai encoding in Access - General information, not specific to this database
- Training data on Access binary format internals - Architecture-level claims, not verified against current tool versions

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - access-parser is the sole viable pure-Python option. It installs and is maintained, but has known unfixed encoding bugs that directly affect our Thai text requirement. Runtime validation is essential.
- Architecture: HIGH - MSysObjects structure and type codes are well-documented across multiple authoritative sources. The approach of reading system tables for inventory is standard.
- Pitfalls: HIGH - All pitfalls are documented in GitHub issues with reproducible examples or confirmed from official documentation. The encoding risk is the most critical.
- Windows fallback: HIGH - Application.SaveAsText is the standard documented approach for exporting Access objects. COM automation via PowerShell is well-established.

**Key risk for Phase 1:** Thai encoding. If access-parser cannot decode Thai text correctly, the entire pipeline is blocked until the encoding is fixed (via patches, fork, or manual decoding). This risk has HIGH probability based on the open encoding issues, but the mitigation paths are well-documented.

**Research date:** 2026-02-14
**Updated:** 2026-02-14 - Full rewrite with verified findings. Database version confirmed (0x03 = Access 2010). PR #33 status confirmed (unmerged). oletools .accdb support confirmed (NOT listed). pyaccdb excluded per user decision.
**Valid until:** 2026-03-14 (30 days -- access-parser release cadence is slow)
