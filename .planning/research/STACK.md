# Technology Stack

**Project:** Epic DB Assessment -- Access Database Extraction & Documentation
**Researched:** 2026-02-14
**Overall confidence:** MEDIUM (versions unverified against live sources; architecture decisions HIGH confidence)

## Important Context

Microsoft Access .accdb files are a binary format with several distinct component types. **No single tool extracts everything.** The extraction stack must be layered:

| Component | Extractable on macOS? | Primary Tool |
|-----------|----------------------|--------------|
| Tables (schema + data) | YES | mdbtools + pandas |
| Relationships | YES | mdbtools (mdb-schema) |
| Queries (SQL) | PARTIAL | mdbtools (mdb-queries) |
| Forms | NO (natively) | access-parser or jackcess |
| Reports | NO (natively) | access-parser or jackcess |
| VBA Modules | NO (natively) | access-parser or jackcess |
| Macros | NO (natively) | access-parser or jackcess |

This is the fundamental challenge: **tables and queries live in well-documented binary structures, but forms, reports, and VBA are stored in proprietary OLE compound document streams** that most open-source tools do not fully parse.

## Recommended Stack

### Layer 1: System-Level Database Access (mdbtools)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| mdbtools | 1.0+ | CLI tools for reading .accdb tables, schema, queries, relationships | The only mature, well-maintained open-source Access reader on macOS. Installable via Homebrew with native arm64 support. Provides `mdb-tables`, `mdb-schema`, `mdb-export`, `mdb-queries`, `mdb-count`. | HIGH |

**Install:** `brew install mdbtools`

**Key capabilities:**
- `mdb-tables` -- list all table names
- `mdb-schema` -- dump full schema (CREATE TABLE statements with types, constraints, relationships)
- `mdb-export` -- export table data as CSV, with delimiter and encoding options
- `mdb-queries` -- list stored queries (SQL text)
- `mdb-count` -- row counts per table

**Limitations:**
- Does NOT extract forms, reports, VBA modules, or macros
- Query extraction may miss some complex Access-specific query types (crosstab, action queries)
- .accdb support was added in mdbtools 0.9+ (the older .mdb-only limitation is gone)

**Confidence:** HIGH -- mdbtools on Homebrew for macOS arm64 is well-established. The .accdb format support has been stable since 0.9.x.

### Layer 2: Python Database Interface (pandas + subprocess)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pandas | >=2.0 | Data manipulation, CSV ingestion, analysis | Standard for tabular data work. Read CSV exports from mdbtools, analyze schema, produce documentation. | HIGH |

**Why pandas + subprocess over pyodbc:**

pyodbc requires an ODBC driver for Access. On macOS arm64, there is **no official Microsoft ODBC driver for Access**. The mdbtools ODBC driver (`libmdbodbc`) exists but is fragile and poorly documented compared to just calling the CLI tools. The subprocess approach (calling `mdb-export`, `mdb-schema`, etc.) is simpler, more reliable, and produces identical results with less configuration overhead.

**Pattern:**
```python
import subprocess
import pandas as pd
from io import StringIO

def export_table(accdb_path: str, table_name: str) -> pd.DataFrame:
    """Export a table from .accdb to a DataFrame via mdbtools."""
    result = subprocess.run(
        ["mdb-export", accdb_path, table_name],
        capture_output=True, text=True, check=True
    )
    return pd.read_csv(StringIO(result.stdout))
```

### Layer 3: Deep Object Extraction (Forms, Reports, VBA)

This is the hardest part. Two viable options exist, and both have tradeoffs.

#### Option A (Recommended): access-parser (Python, pure)

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| access-parser | >=0.0.2 | Parse .accdb binary to extract system catalog entries including forms, reports, VBA | Pure Python, no native dependencies, works on any platform. Parses the Access binary format directly. Can enumerate forms, reports, and extract some metadata. | MEDIUM |

**Install:** `pip install access-parser`

**Key capabilities:**
- Parses Access system tables (MSysObjects, MSysQueries, etc.)
- Can extract table names, query definitions, form names, report names
- Can extract VBA project streams (the binary VBA storage)
- Works with .accdb format

**Limitations:**
- The library is relatively young and lightly maintained
- Form and report extraction gives you metadata and names, not full layout definitions
- VBA extraction produces raw binary VBA project data that needs further parsing
- Documentation is sparse

**Confidence:** MEDIUM -- the library exists and works for basic extraction, but depth of form/report detail extraction needs validation with the actual file.

#### Option B (Fallback): jackcess via Py4J or Jpype

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Jackcess | 4.x | Java library for reading Access databases | Most complete open-source Access parser. Can read tables, queries, relationships, system tables, and some form/report metadata. | MEDIUM |

Jackcess is a Java library and would require a JVM. This adds complexity but Jackcess is significantly more mature than access-parser for deep Access format parsing.

**Why this is the fallback, not primary:**
- Requires JVM installation (adds dependency weight)
- Python-Java bridging (Py4J or JPype) adds fragility
- For this project's scope, mdbtools + access-parser likely covers 90%+ of needs
- Only escalate to Jackcess if access-parser cannot extract VBA or form metadata adequately

### Layer 4: VBA Source Code Extraction

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| oletools | >=0.60 | Extract VBA macros from OLE2 compound documents | Established Python library for VBA extraction from Office files. `olevba` can parse VBA project streams. | HIGH |

**Install:** `pip install oletools`

**Key capabilities:**
- `olevba` extracts VBA source code from Office documents including Access
- Handles the OLE2 compound document format that stores VBA projects
- Outputs readable VBA source code, not just binary streams
- Well-maintained, security-focused (used for malware analysis), but the extraction is exactly what we need

**Important caveat:** oletools works with OLE2 streams. Access .accdb files (2007+ format) store VBA differently than older .mdb files. The .accdb format uses an internal storage mechanism. oletools may need the VBA binary stream extracted first (via access-parser) before it can parse the source. **This needs validation with the actual file.**

**Confidence:** HIGH for the tool's capability, MEDIUM for .accdb-specific VBA extraction workflow.

### Layer 5: Thai-to-English Translation

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Claude API / Claude Code | Current | Translate Thai field names, labels, data to English | Already in the workflow (this project runs on Claude Code). Batch translate extracted Thai text. Far superior to googletrans or similar for contextual business translation. | HIGH |

**No additional translation library needed.** Claude Code is already the execution environment. Thai text extracted from tables, field names, form labels, etc. can be translated in-context during documentation generation.

### Layer 6: Documentation Output

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Markdown | N/A | Documentation format | Human-readable, version-controllable, renders on GitHub, trivial to produce from Python | HIGH |
| json | stdlib | Structured data export | Schema definitions, relationship maps, query metadata -- structured for future programmatic consumption | HIGH |

## Full Recommended Stack Summary

```
System tools:
  mdbtools          (brew install mdbtools)     -- Table/schema/query extraction

Python packages:
  pandas>=2.0       (pip install pandas)        -- Data manipulation
  access-parser     (pip install access-parser)  -- Deep .accdb binary parsing
  oletools>=0.60    (pip install oletools)       -- VBA source extraction

Stdlib (no install):
  subprocess        -- Call mdbtools CLI
  json              -- Structured output
  pathlib           -- File handling
  csv               -- CSV processing
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Table extraction | mdbtools CLI | pyodbc + mdbodbc ODBC driver | ODBC driver setup on macOS arm64 is fragile, poorly documented, and offers no benefit over CLI for batch extraction |
| Table extraction | mdbtools CLI | pyodbc + Microsoft Access ODBC | Microsoft does not provide an Access ODBC driver for macOS. Period. Windows-only. |
| Table extraction | mdbtools CLI | access-parser for tables | access-parser is slower and less mature for table data than mdbtools |
| Deep parsing | access-parser | Jackcess (Java) | Adds JVM dependency. Only worth it if access-parser fails on forms/VBA. Keep as fallback. |
| Deep parsing | access-parser | MDB/ACCDB Viewer (commercial) | Commercial tools exist but add cost and are often Windows-only |
| VBA extraction | oletools | Manual (open in Access on Windows VM) | Automated extraction is preferable; VM is heavy for just VBA extraction |
| Translation | Claude (in-workflow) | googletrans / deep-translator | Claude provides far better contextual translation, especially for business domain Thai |
| Data processing | pandas | polars | Polars is faster but overkill for a ~10MB database. Pandas ecosystem is more mature for this task. |

## What NOT to Use

| Tool | Why Not |
|------|---------|
| **pyodbc** | No Microsoft Access ODBC driver for macOS. The mdbtools ODBC driver exists but is inferior to just calling mdbtools CLI directly. |
| **pypyodbc** | Same problem as pyodbc -- no macOS Access driver. Also unmaintained. |
| **sqlalchemy-access** | Requires pyodbc with Access driver. Does not work on macOS. |
| **msaccessdb** | Abandoned/unmaintained Python package. |
| **Windows VM** | Heavy, slow, unnecessary for this scope. Only consider if ALL other approaches fail for VBA extraction. |
| **LibreOffice Base** | Can open some .mdb files but .accdb support is poor. No programmatic extraction API. |
| **UCanAccess (Java)** | Built on Jackcess but adds JDBC layer. If going Java route, use Jackcess directly. |

## Extraction Capability Matrix

This is the critical decision framework. Each Access component requires a different extraction approach:

| Component | Tool | Extracts What | Completeness | Confidence |
|-----------|------|---------------|--------------|------------|
| **Table schemas** | mdbtools (`mdb-schema`) | Column names, types, constraints, PKs | FULL | HIGH |
| **Table data** | mdbtools (`mdb-export`) | All rows as CSV | FULL | HIGH |
| **Relationships** | mdbtools (`mdb-schema`) | FK relationships, referential integrity rules | FULL | HIGH |
| **Select queries** | mdbtools (`mdb-queries`) | SQL text of stored queries | GOOD | HIGH |
| **Action queries** | mdbtools (`mdb-queries`) | May miss some Access-specific query types | PARTIAL | MEDIUM |
| **Form names** | access-parser | List of form objects | GOOD | MEDIUM |
| **Form layout/fields** | access-parser | Partial -- control names, bound fields, some properties | PARTIAL | LOW |
| **Report names** | access-parser | List of report objects | GOOD | MEDIUM |
| **Report layout** | access-parser | Partial -- similar to forms | PARTIAL | LOW |
| **VBA modules** | oletools + access-parser | VBA source code text | GOOD | MEDIUM |
| **Macros** | access-parser | Macro definitions | PARTIAL | LOW |
| **Table-level validation** | mdbtools (`mdb-schema`) | Validation rules in schema | GOOD | MEDIUM |

### Key Risk: Forms and Reports

Forms and reports are the **hardest components to extract** on macOS without Access. They are stored in proprietary binary format within the .accdb file. The extraction will yield:

- **What we CAN get:** Form/report names, which tables/queries they bind to, control names, some properties
- **What we PROBABLY CANNOT get:** Full visual layout, exact positioning, formatting details, complex event handlers

**Mitigation:** For the assessment goal (blueprint for rebuild), knowing WHAT forms and reports exist and WHAT data they show is more valuable than pixel-perfect layout replication. The extraction should focus on documenting purpose, data bindings, and business logic rather than visual fidelity.

## Installation

```bash
# System tools (one-time)
brew install mdbtools

# Python dependencies (in project venv)
cd /Users/jb/Dev/epic_gear/epic-db
source .venv/bin/activate
pip install pandas access-parser oletools
```

**Verification commands:**
```bash
# Verify mdbtools can read the file
mdb-tables data/epic_db.accdb

# Verify mdbtools version supports .accdb
mdb-ver data/epic_db.accdb

# Quick table count
mdb-tables -1 data/epic_db.accdb | wc -l
```

## Thai/Unicode Considerations

The database contains Thai-language data (UTF-8 or Windows-874/TIS-620 encoding). Key handling notes:

- **mdb-export** outputs UTF-8 by default on modern mdbtools versions. If Thai characters appear garbled, try: `mdb-export -D '%Y-%m-%d' -q '' -R '\n' -e utf-8 data/epic_db.accdb TableName`
- **pandas** handles UTF-8 natively. No special configuration needed.
- **Field names** in Thai will need translation mapping early in the process (create a translation dictionary)
- **access-parser** should handle Unicode, but validate with the actual file

## Version Validation Needed

The following versions need verification at install time (could not verify against live package indices):

| Package | Expected Version | Verify With |
|---------|-----------------|-------------|
| mdbtools | 1.0.0+ | `mdb-ver --version` or `brew info mdbtools` |
| pandas | 2.x | `pip show pandas` |
| access-parser | 0.0.2+ | `pip show access-parser` |
| oletools | 0.60+ | `pip show oletools` |

**Action:** Run these checks after installation. If access-parser version is very old or unmaintained, evaluate Jackcess as fallback.

## Sources

- mdbtools GitHub: https://github.com/mdbtools/mdbtools (HIGH confidence -- well-maintained, 1000+ stars)
- access-parser PyPI: https://pypi.org/project/access-parser/ (MEDIUM confidence -- smaller project, needs validation)
- oletools GitHub: https://github.com/decalage2/oletools (HIGH confidence -- security tool, actively maintained)
- pandas documentation: https://pandas.pydata.org/ (HIGH confidence)
- Training data knowledge of Access binary format internals (MEDIUM confidence -- architecture claims verified against mdbtools docs patterns)

---

*Stack research: 2026-02-14*
*Confidence note: All tool recommendations are based on established knowledge of the Access extraction ecosystem. Specific version numbers should be verified at install time as noted above. The core architecture (mdbtools for tables + access-parser/oletools for deep objects) is HIGH confidence.*
