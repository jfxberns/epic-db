# Phase 1: Setup and Validation - Research

**Researched:** 2026-02-14
**Domain:** Python extraction of Microsoft Access .accdb on macOS arm64, Thai encoding
**Confidence:** MEDIUM (key libraries verified, but encoding and system table access need runtime validation)

## Summary

Reading an .accdb file on macOS arm64 without Homebrew narrows the field to pure-Python parsers. Two credible options exist: **access-parser** (Claroty, pip-installable, more widely used) and **pyaccdb** (newer, more efficient, better text decompression, but not on PyPI). Both parse the binary .accdb format directly and can read user tables and system tables (MSysObjects, MSysQueries). Neither library natively reconstructs query SQL from MSysQueries -- that requires either custom parsing of the MSysQueries attribute/flag/expression columns, or using Jackcess (Java) via JPype to call `toSQLString()`.

Microsoft Access stores all text internally as UTF-16-LE, with an optional compression scheme. Thai characters are fully representable in UTF-16-LE and should decode correctly. However, access-parser has documented encoding bugs (GitHub issues #21 and #26) where compressed Unicode text is not properly decoded. pyaccdb implements the compression/decompression algorithm correctly (modeled after Jackcess). This makes pyaccdb the safer choice for Thai text, though access-parser can be used as a fallback with potential manual patching.

Forms, reports, VBA modules, and macros are NOT stored as parseable table data in .accdb files -- they are stored in binary blobs that require the Access Object Model (COM automation) to extract. Their **names** can be read from MSysObjects (Type=-32768 for forms, -32764 for reports, -32766 for macros, -32761 for modules), but their **content** (layout, code, properties) requires Windows with Access installed. This is the expected Windows threshold.

**Primary recommendation:** Use pyaccdb as the primary parser (install from git), access-parser as fallback. Read MSysObjects to inventory all object types. Read MSysQueries to extract query definitions. Accept that form/report/VBA content extraction requires Windows.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Claude's discretion on which tool to try first (mdbtools, access-parser, or other Python libraries)
- Python-only dependencies -- no Homebrew. Everything must install via pip/uv into the project venv
- Mix tools if needed -- use different tools per object type rather than requiring one tool to handle everything
- Validation bar: tool must successfully read ALL tables and queries (not just one sample) before we commit to it
- Inventory as a Markdown document in `assessment/` top-level folder
- Include brief metadata per object: row counts for tables, query type (SELECT/UPDATE/etc.), module line counts where available
- Extraction scripts should be kept as clean, reusable tools -- not throwaway code. The .accdb may need re-extraction
- Subfolders per object type within assessment/ (tables/, queries/, etc.)
- User can set up a Windows VM but doesn't have one now
- Claude decides when to recommend Windows vs. keep trying macOS -- based on what tool validation reveals
- Windows threshold: if macOS tools can't even LIST forms/reports/VBA names, Windows is needed. If names are accessible but detail isn't, that's still macOS-viable
- If Windows is needed, scripts must be fully automated/headless -- user runs one command, gets output files
- Correct Thai rendering is a BLOCKER -- do not proceed to Phase 2 if encoding is broken (mojibake)
- Both column/field names AND row data must render Thai correctly
- User can spot-check some Thai but cannot read it fluently -- validation should include visual output the user can verify with help
- No known reference values yet -- user can check the database to get test values if needed

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

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pyaccdb | latest (git, ~Nov 2025) | Primary .accdb binary parser | Pure Python, no dependencies, correct UTF-16-LE text decompression (models Jackcess algorithm), efficient page-level reading via MSysObjects, cross-platform |
| access-parser | 0.0.6 (PyPI, Jan 2025) | Fallback .accdb parser | Pip-installable, wider adoption (88 GitHub stars), provides catalog and parse_table API. Has known encoding bugs but works for ASCII/Latin text |
| tabulate | latest (PyPI) | Markdown table formatting | Standard for generating formatted markdown tables in assessment output |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| JPype1 | latest (PyPI) | Java-Python bridge | Only if query SQL reconstruction from MSysQueries proves too complex to do manually; enables calling Jackcess `toSQLString()` from Python |
| jackcess (Java JAR) | 4.0.x | Access database Java library | Only needed with JPype for query SQL reconstruction; has `Database.getQueries()` and `Query.toSQLString()` API |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pyaccdb | access-parser alone | Pip-installable but has encoding bugs (#21, #26) that affect non-ASCII text; parses entire file into memory |
| pyaccdb | access_parser_c (McSash fork) | Fork of access-parser with potential fixes, but limited documentation on what was changed; install via `pip install git+https://github.com/McSash/access_parser_c` |
| pyaccdb | mdbtools (system binary) | Requires Homebrew or compilation from source -- violates Python-only constraint. Also limited .accdb support (primarily Jet 3/4 = .mdb) |
| Custom MSysQueries parsing | Jackcess via JPype | JPype adds Java dependency; custom parsing is feasible since MSysQueries structure is documented |

**Installation:**
```bash
# Primary parser (from git -- not on PyPI)
pip install git+https://yingtongli.me/git/RunasSudo/pyaccdb.git

# Fallback parser (from PyPI)
pip install access-parser

# Markdown table formatting
pip install tabulate
```

If the yingtongli.me git URL is unreachable, pyaccdb can be cloned manually and installed locally:
```bash
git clone https://yingtongli.me/git/RunasSudo/pyaccdb.git /tmp/pyaccdb
pip install /tmp/pyaccdb
```

## Architecture Patterns

### Recommended Project Structure
```
epic-db/
├── data/
│   └── epic_db.accdb          # Source database (read-only, never modified)
├── scripts/
│   ├── db_reader.py           # Core: open DB, read tables, handle encoding
│   ├── inventory.py           # Enumerate all objects from MSysObjects
│   ├── extract_tables.py      # Extract table schemas and sample data
│   ├── extract_queries.py     # Extract query definitions from MSysQueries
│   └── validate_encoding.py   # Thai encoding validation script
├── assessment/
│   ├── inventory.md           # Master inventory of all objects with counts
│   ├── tables/                # Per-table schema and sample data
│   ├── queries/               # Per-query SQL definition
│   ├── forms/                 # Form names (content requires Windows)
│   ├── reports/               # Report names (content requires Windows)
│   ├── modules/               # Module names (content requires Windows)
│   └── macros/                # Macro names (content requires Windows)
└── .venv/                     # Python virtual environment
```

### Pattern 1: Layered DB Access with Fallback

**What:** Wrap database access in a module that tries pyaccdb first, falls back to access-parser if pyaccdb fails on a specific table.
**When to use:** Always -- the tools are immature and may fail on edge cases.

```python
# scripts/db_reader.py
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "epic_db.accdb"

def open_db_pyaccdb(db_path=DB_PATH):
    """Open database with pyaccdb (preferred -- better encoding)."""
    from pyaccdb import Database
    with open(db_path, 'rb') as f:
        return Database(f)

def open_db_access_parser(db_path=DB_PATH):
    """Open database with access-parser (fallback)."""
    from access_parser import AccessParser
    return AccessParser(str(db_path))

def get_table_names(db):
    """Get user table names from MSysObjects."""
    msys = db.get_table_by_name('MSysObjects')
    tables = []
    for row in msys.get_rows():
        obj_type = row.get_field_value('Type')
        obj_name = row.get_field_value('Name')
        if obj_type == 1 and not str(obj_name).startswith('MSys'):
            tables.append(str(obj_name))
    return tables
```

### Pattern 2: MSysObjects Inventory Query

**What:** Read the MSysObjects system table to enumerate all database objects by type.
**When to use:** For the complete inventory requirement (SETUP-04).

```python
# Object type constants from MSysObjects
MSYS_TYPES = {
    1: "Table (Local)",
    4: "Table (Linked ODBC)",
    5: "Query",
    6: "Table (Linked)",
    -32768: "Form",
    -32764: "Report",
    -32766: "Macro",
    -32761: "Module",
}

# Query subtype flags (from MSysObjects.Flags when Type=5)
QUERY_FLAGS = {
    0: "Select",
    16: "Crosstab",
    32: "Delete",
    48: "Update",
    64: "Append",
    80: "Make Table",
    96: "Data Definition",
    112: "Pass-through",
    128: "Union",
}
```

### Pattern 3: Thai Encoding Validation

**What:** Display sample rows with Thai text alongside hex dumps for visual verification.
**When to use:** For encoding validation (SETUP-02).

```python
def validate_thai_text(text, label=""):
    """Check if text contains Thai characters and print for visual verification."""
    thai_range = range(0x0E00, 0x0E80)  # Thai Unicode block
    has_thai = any(ord(c) in thai_range for c in str(text))
    # Check for common mojibake patterns
    has_mojibake = any(ord(c) > 0xFFFF or '\ufffd' in str(text) for c in str(text))

    print(f"[{label}] Text: {text}")
    print(f"  Contains Thai: {has_thai}")
    print(f"  Suspected mojibake: {has_mojibake}")
    print(f"  Hex: {text.encode('utf-8').hex() if isinstance(text, str) else 'N/A'}")
    return has_thai and not has_mojibake
```

### Anti-Patterns to Avoid

- **Parsing the entire file when you only need metadata:** access-parser loads everything into memory. pyaccdb reads only necessary pages. For inventory-only operations, pyaccdb is dramatically faster.
- **Assuming system tables are hidden:** Both libraries can read MSysObjects and MSysQueries -- they are regular tables in the .accdb binary format, just flagged as system tables in the catalog.
- **Trying to extract form/report/VBA content on macOS:** These are binary blobs requiring the Access COM Object Model. Do not waste time trying to parse them from the binary file; enumerate names only.
- **Hardcoding table names:** Use MSysObjects to discover tables dynamically. The database may contain tables not visible in the default Access navigation pane.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| .accdb binary parsing | Custom binary parser for Access format | pyaccdb or access-parser | The .accdb format is undocumented, complex, and version-specific. These libraries reverse-engineer it correctly |
| UTF-16-LE compressed text decoding | Custom decompression for Access text fields | pyaccdb's decompress_text() | Access uses a proprietary compression scheme (FF FE header, toggle between compressed/uncompressed modes). pyaccdb implements this correctly per Jackcess reference |
| Query SQL reconstruction from MSysQueries | Custom SQL builder from attribute/flag/expression columns | Jackcess via JPype (if needed) OR manual parsing using documented attribute table | MSysQueries stores queries as decomposed components (type, tables, fields, joins, where, order by). Jackcess has a battle-tested toSQLString() implementation |
| Markdown inventory formatting | String concatenation for tables | tabulate library with `tablefmt="pipe"` | Handles alignment, escaping, and edge cases correctly |
| Object type enumeration | Manual exploration of tables | MSysObjects system table query | MSysObjects is the authoritative source for all objects with type codes |

**Key insight:** The .accdb format has no public specification from Microsoft. All parsers are reverse-engineered. Using established libraries avoids re-discovering format quirks that took years to identify.

## Common Pitfalls

### Pitfall 1: Unicode Compression Mishandling
**What goes wrong:** Thai text appears as mojibake, garbled characters, or empty strings. Column names with Thai characters are corrupted.
**Why it happens:** Access stores text with a proprietary compression scheme. When the `FF FE` BOM marker is present, text alternates between compressed (single-byte with implicit null padding) and uncompressed (raw UTF-16-LE) segments. Libraries that don't handle this correctly produce garbled output.
**How to avoid:** Use pyaccdb which implements the decompression algorithm correctly (modeled after Jackcess ColumnImpl.java line 1584). If using access-parser, check for the fix from GitHub issue #21 (user JStooke's patch) and apply it if not merged.
**Warning signs:** Characters like `\x00\x38` where an ellipsis should be, extra characters appended to table names (e.g., "Konsert" becomes "Konsert+garbage"), `\ufffd` replacement characters.

### Pitfall 2: System Tables Filtered from Catalog
**What goes wrong:** MSysObjects, MSysQueries, and other system tables don't appear in the table listing, making it impossible to enumerate all database objects.
**Why it happens:** access-parser explicitly filters system tables from its `catalog` property using `SYSTEM_TABLE_FLAGS`. pyaccdb accesses MSysObjects directly at page 2 (fixed location).
**How to avoid:** With access-parser, use `parse_table("MSysObjects")` directly rather than relying on `catalog`. With pyaccdb, use `database.get_table_by_name('MSysObjects')` or the built-in `get_msysobjects()` method.
**Warning signs:** Catalog shows fewer tables than expected, no system tables visible.

### Pitfall 3: Confusing "Can List Names" with "Can Extract Content"
**What goes wrong:** Assuming that because you can see form/report/module names in MSysObjects, you can also extract their content (layouts, code, properties) on macOS.
**Why it happens:** MSysObjects stores metadata (names, types, flags) for all objects, but form layouts, report definitions, and VBA code are stored as binary blobs in separate internal structures that require the Access COM Object Model to interpret.
**How to avoid:** Clearly separate the inventory (names and types from MSysObjects -- doable on macOS) from content extraction (form layouts, VBA code -- requires Windows + Access). The Windows threshold per user decision: if names are listable, macOS is viable for the inventory phase.
**Warning signs:** Attempting to read form/report data and getting raw bytes or parsing errors.

### Pitfall 4: MSysQueries Does Not Store Plain SQL Text
**What goes wrong:** Expecting to find SQL strings directly in MSysQueries, but finding decomposed components instead.
**Why it happens:** Access stores queries as rows of attribute/flag/name1/name2/expression tuples, not as SQL text. Each row represents one component of the query (e.g., one joined table, one selected field, one WHERE condition).
**How to avoid:** Either reconstruct SQL from the components using the documented attribute meanings (Attribute 1=type, 5=table, 6=field, 7=join, 8=where, 11=order by), or use Jackcess via JPype which has `toSQLString()`. For this phase, just listing query names and types from MSysObjects (Type=5) with their flag-based subtype is sufficient.
**Warning signs:** Reading MSysQueries and seeing cryptic rows with numeric attributes instead of SQL.

### Pitfall 5: access-parser Versions After Access 2010
**What goes wrong:** access-parser fails to parse the database or produces errors.
**Why it happens:** GitHub issue #35 reports "Database versions after 2010 are not supported." The .accdb format has evolved across Access versions.
**How to avoid:** Try pyaccdb first. If both fail, check the database version (stored in the file header) and report it. The epic_db.accdb format version should be identified early in the validation process.
**Warning signs:** Parsing errors mentioning page types, overflow offsets, or unsupported versions.

### Pitfall 6: File Locking and Binary Mode
**What goes wrong:** Database file cannot be opened or produces corrupt reads.
**Why it happens:** Not opening in binary mode ('rb'), or the file being locked by another process.
**How to avoid:** Always open .accdb files in binary mode. pyaccdb requires `open('file.accdb', 'rb')`. Do not use text mode.
**Warning signs:** UnicodeDecodeError on file open, truncated data, IOError.

## Code Examples

### Opening the Database and Listing Tables (pyaccdb)
```python
# Source: pyaccdb README and blog post (yingtongli.me/blog/2025/11/22/pyaccdb.html)
from pyaccdb import Database

with open('data/epic_db.accdb', 'rb') as f:
    db = Database(f)

    # Get a specific table
    table = db.get_table_by_name('MSysObjects')

    # Read column definitions
    for col in table.columns:
        print(f"Column: {col.name}, Type: {col.col_type}")

    # Read rows
    for row in table.get_rows():
        obj_name = row.get_field_value('Name')
        obj_type = row.get_field_value('Type')
        obj_flags = row.get_field_value('Flags')
        print(f"{obj_name}: type={obj_type}, flags={obj_flags}")
```

### Opening the Database and Listing Tables (access-parser fallback)
```python
# Source: access-parser README (github.com/claroty/access_parser)
from access_parser import AccessParser

db = AccessParser("data/epic_db.accdb")

# List user tables
print(db.catalog)  # dict of {table_name: table_id}

# Parse a specific table
table_data = db.parse_table("MSysObjects")
# table_data is defaultdict(list): table_data[column_name][row_index]

# Access system table for inventory
names = table_data.get('Name', [])
types = table_data.get('Type', [])
flags = table_data.get('Flags', [])

for name, obj_type, flag in zip(names, types, flags):
    print(f"{name}: type={obj_type}, flags={flag}")
```

### Complete Object Inventory from MSysObjects
```python
# Source: MSysObjects type reference (devhut.net/ms-access-listing-of-database-objects/)
MSYS_TYPES = {
    1: "Table",
    5: "Query",
    -32768: "Form",
    -32764: "Report",
    -32766: "Macro",
    -32761: "Module",
}

def build_inventory(db):
    """Build complete inventory of all database objects."""
    msys = db.get_table_by_name('MSysObjects')
    inventory = {label: [] for label in MSYS_TYPES.values()}

    for row in msys.get_rows():
        obj_type = row.get_field_value('Type')
        obj_name = str(row.get_field_value('Name'))
        obj_flags = row.get_field_value('Flags')

        if obj_type in MSYS_TYPES:
            # Skip system/temp objects
            if obj_name.startswith('MSys') or obj_name.startswith('~'):
                continue
            inventory[MSYS_TYPES[obj_type]].append({
                'name': obj_name,
                'flags': obj_flags,
            })

    return inventory
```

### Extracting Query Type from Flags
```python
# Source: isladogs.co.uk/explaining-queries/ and devhut.net
def get_query_type(flags):
    """Determine query type from MSysObjects.Flags value."""
    # Mask out hidden bit (bit 3 = hidden)
    base_flag = flags & ~0x8  # Remove hidden flag
    QUERY_TYPES = {
        0: "Select",
        16: "Crosstab",
        32: "Delete",
        48: "Update",
        64: "Append",
        80: "Make Table",
        96: "Data Definition",
        112: "Pass-through",
        128: "Union",
    }
    return QUERY_TYPES.get(base_flag, f"Unknown ({flags})")
```

### Thai Text Validation
```python
def print_thai_validation(table_name, rows, columns, max_rows=5):
    """Print sample data for Thai encoding visual verification."""
    print(f"\n=== Thai Encoding Check: {table_name} ===")
    THAI_BLOCK = range(0x0E00, 0x0E80)

    for i, row in enumerate(rows[:max_rows]):
        for col in columns:
            value = str(row.get_field_value(col.name))
            has_thai = any(ord(c) in THAI_BLOCK for c in value)
            if has_thai:
                print(f"  Row {i}, {col.name}: {value}")
                # Print first few code points for verification
                codepoints = [f"U+{ord(c):04X}" for c in value[:20]]
                print(f"    Codepoints: {' '.join(codepoints)}")
```

### Generating Markdown Inventory
```python
from tabulate import tabulate

def write_inventory_markdown(inventory, output_path):
    """Write inventory as formatted markdown."""
    lines = ["# Epic DB Object Inventory\n"]

    for obj_type, objects in inventory.items():
        lines.append(f"\n## {obj_type}s ({len(objects)})\n")
        if objects:
            headers = ["Name", "Flags/Subtype"]
            rows = [[obj['name'], obj.get('subtype', obj['flags'])]
                    for obj in objects]
            lines.append(tabulate(rows, headers=headers, tablefmt="pipe"))
            lines.append("")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| mdbtools (C binary, Homebrew) for .mdb/.accdb on macOS | Pure Python parsers (pyaccdb, access-parser) | 2023-2025 | No system dependencies needed; install via pip; cross-platform |
| pyodbc + Access ODBC driver (Windows only) | Pure Python binary parsers | 2023-2025 | Cross-platform Access reading without Windows/ODBC |
| access-parser as only pure-Python option | pyaccdb (Nov 2025) as more correct alternative | Nov 2025 | Better text decompression, efficient page-level reading, system table awareness |
| Manual MSysQueries parsing for SQL reconstruction | Jackcess 4.x Query.toSQLString() (Java) | ~2020+ | Reliable SQL reconstruction from decomposed query components |

**Deprecated/outdated:**
- **mdbtools for .accdb:** mdbtools primarily supports Jet 3/4 (.mdb). Its .accdb support is experimental/limited. Do not rely on it for .accdb files.
- **pyodbc on macOS for Access:** There is no Access ODBC driver for macOS. pyodbc is Windows-only for Access databases.
- **mdb-parser (PyPI):** This is a Python wrapper around the mdbtools C binary -- inherits all mdbtools limitations and requires the binary installed.

## Open Questions

1. **pyaccdb API completeness for MSysQueries**
   - What we know: pyaccdb can read any table by name including system tables. MSysQueries is a regular table.
   - What's unclear: Whether pyaccdb correctly decodes all column types in MSysQueries (especially Expression column which may contain binary data). The library is very new (15 commits, Nov 2025).
   - Recommendation: Try reading MSysQueries with pyaccdb first. If it fails, fall back to access-parser. If both fail on MSysQueries specifically, use Jackcess via JPype.

2. **Database version of epic_db.accdb**
   - What we know: The file is confirmed as "Microsoft Access Database" by `file` command. Access versions (2007, 2010, 2013, 2016, 2019) use slightly different .accdb internal formats.
   - What's unclear: Which version created this database. access-parser has a known issue with versions after 2010 (#35).
   - Recommendation: Check the version early (it's in the file header). If version > 2010, pyaccdb is strongly preferred.

3. **pyaccdb git repository stability**
   - What we know: pyaccdb is hosted on yingtongli.me personal git, not GitHub or PyPI. It has 15 commits.
   - What's unclear: Long-term availability of the git URL. No tagged releases.
   - Recommendation: Vendor the dependency (download and include in project) if the git install fails. The library is small and has zero dependencies.

4. **Query SQL reconstruction complexity**
   - What we know: MSysQueries stores queries as decomposed attribute rows. The attribute meanings are documented. Jackcess can reconstruct SQL.
   - What's unclear: How many queries are in epic_db.accdb and how complex they are. Simple SELECTs are easy to reconstruct; UNION/crosstab queries are harder.
   - Recommendation: For Phase 1 inventory, just list query names and types. Defer full SQL reconstruction to Phase 2 (extraction). If SQL reconstruction is needed, evaluate JPype+Jackcess vs. manual parsing based on query complexity.

5. **Are there linked tables in this database?**
   - What we know: MSysObjects Type=4 (ODBC linked) and Type=6 (linked) indicate external table links.
   - What's unclear: Whether epic_db.accdb has linked tables. If it does, those links point to external data sources that may not be available.
   - Recommendation: Check for Type 4 and 6 objects during inventory. Flag them clearly in the assessment.

## Sources

### Primary (HIGH confidence)
- [pyaccdb repository](https://yingtongli.me/git/RunasSudo/pyaccdb/src/branch/master) - Source code review of database.py, table.py, util.py; text decompression algorithm
- [pyaccdb blog post](https://yingtongli.me/blog/2025/11/22/pyaccdb.html) - Features, comparison with access-parser, architecture
- [access-parser GitHub](https://github.com/claroty/access_parser) - README, source code (access_parser.py), API
- [access-parser GitHub Issue #21](https://github.com/claroty/access_parser/issues/21) - TYPE_TEXT Unicode Decoding bug and fix
- [access-parser GitHub Issue #26](https://github.com/claroty/access_parser/issues/26) - Character encoding problems in table names and field values
- [access-parser GitHub Issue #35](https://github.com/claroty/access_parser/issues/35) - Database versions after 2010 not supported
- [Jackcess Query API](https://jackcess.sourceforge.io/apidocs/com/healthmarketscience/jackcess/query/Query.html) - Query interface, toSQLString(), supported query types
- [MSysObjects Type reference](https://www.devhut.net/ms-access-listing-of-database-objects/) - Complete type and flags values
- [MSysQueries structure](https://www.isladogs.co.uk/explaining-queries/) - Attribute meanings, flag values, query reconstruction rules
- [Microsoft Learn](https://social.msdn.microsoft.com/Forums/office/en-US/c3af535e-8931-4938-a552-fd1d5187411f/what-character-set-is-access-using) - Access uses UTF-16 (UCS-2) internally

### Secondary (MEDIUM confidence)
- [mdbtools FAQ](https://mdbtools.github.io/faq/) - Confirmed Jet 3/4 only support, query extraction listed as future goal
- [Microsoft Q&A on query extraction](https://learn.microsoft.com/en-us/answers/questions/5377406/extract-queries-from-ms-access-db-using-python) - Confirmed VBA/COM required for full query extraction
- [cavo789/vbs_access_export](https://github.com/cavo789/vbs_access_export) - VBScript for Windows-based export of forms, macros, modules, reports

### Tertiary (LOW confidence)
- [access_parser_c (McSash fork)](https://github.com/McSash/access_parser_c) - Fork with potential fixes, but changes not documented
- WebSearch results on Thai encoding (TIS-620, Windows-874) - Not directly relevant since Access stores text as UTF-16-LE internally

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM - pyaccdb is very new (15 commits, Nov 2025) and not on PyPI; access-parser has known encoding bugs. Both are functional but neither is battle-tested. Runtime validation essential.
- Architecture: HIGH - MSysObjects structure is well-documented across multiple authoritative sources. Object type codes are consistent across all references.
- Pitfalls: HIGH - Encoding bugs are documented in GitHub issues with reproducible examples. System table filtering is confirmed in source code review. MSysQueries structure is documented by multiple Access experts.

**Research date:** 2026-02-14
**Valid until:** 2026-03-14 (30 days -- libraries are slow-moving, but pyaccdb is very new)
