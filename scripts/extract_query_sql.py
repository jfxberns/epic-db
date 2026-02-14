"""Extract all query SQL from epic_db.accdb using Jackcess via JPype.

Uses the Jackcess Java library (loaded via JPype1) to read query definitions
from the Access database and call toSQLString() on each. This is the only
reliable way to reconstruct Access query SQL on macOS, since MSysQueries
is not accessible via the Python parser.

Output:
  - JSON to stdout (for piping)
  - assessment/queries/_raw_queries.json (for downstream analysis)
  - Summary table to stderr

Usage:
    python scripts/extract_query_sql.py
"""

import json
import os
import sys
from pathlib import Path

from tabulate import tabulate

# Project paths (following established pattern from db_reader.py)
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "epic_db.accdb"
LIB_DIR = Path(__file__).resolve().parent.parent / "lib"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assessment" / "queries"


def start_jvm():
    """Start JVM with Jackcess JARs on classpath."""
    import jpype
    import jpype.imports  # noqa: F401 -- enables Java package imports as Python modules

    if jpype.isJVMStarted():
        return

    # Ensure JAVA_HOME is set for JPype to find the JVM
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        # Try common Homebrew location on macOS ARM
        brew_java = Path("/opt/homebrew/opt/openjdk@11/libexec/openjdk.jdk/Contents/Home")
        if brew_java.exists():
            os.environ["JAVA_HOME"] = str(brew_java)
        else:
            # Try other common locations
            for candidate in [
                Path("/opt/homebrew/opt/openjdk/libexec/openjdk.jdk/Contents/Home"),
                Path("/Library/Java/JavaVirtualMachines/openjdk-11.jdk/Contents/Home"),
            ]:
                if candidate.exists():
                    os.environ["JAVA_HOME"] = str(candidate)
                    break

    # Build classpath from all JARs in lib/
    jars = list(LIB_DIR.glob("*.jar"))
    if not jars:
        raise FileNotFoundError(f"No JAR files found in {LIB_DIR}")

    classpath = [str(j) for j in jars]
    print(f"Starting JVM with {len(jars)} JARs...", file=sys.stderr)
    jpype.startJVM(classpath=classpath)
    print("JVM started successfully.", file=sys.stderr)


def extract_all_queries() -> list[dict]:
    """Extract all query SQL from the Access database using Jackcess.

    Returns list of dicts with: name, type, sql, error, hidden.
    Includes hidden ~sq_c* subqueries (subform data sources).
    """
    import jpype

    start_jvm()

    # Import Java classes after JVM is started
    from com.healthmarketscience.jackcess import DatabaseBuilder
    from java.io import File

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    print(f"Opening database: {DB_PATH}", file=sys.stderr)
    db = DatabaseBuilder.open(File(str(DB_PATH)))

    results = []
    error_count = 0

    for query in db.getQueries():
        name = str(query.getName())
        qtype = str(query.getType())

        try:
            sql = str(query.toSQLString())
            error = None
        except Exception as e:
            sql = None
            error = str(e)
            error_count += 1

        # Check hidden status
        try:
            hidden = bool(query.isHidden())
        except Exception:
            hidden = False

        results.append({
            "name": name,
            "type": qtype,
            "sql": sql,
            "error": error,
            "hidden": hidden,
        })

    db.close()
    print(f"Extracted {len(results)} queries ({error_count} errors).", file=sys.stderr)

    # Shutdown JVM is not needed -- JPype handles cleanup
    return results


def save_results(queries: list[dict]) -> Path:
    """Save extraction results to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "_raw_queries.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(queries, f, ensure_ascii=False, indent=2)
    print(f"Saved to: {output_path}", file=sys.stderr)
    return output_path


def print_summary_table(queries: list[dict]):
    """Print a summary table of extracted queries."""
    rows = []
    for q in queries:
        sql_len = len(q["sql"]) if q["sql"] else 0
        status = "OK" if q["error"] is None else f"ERROR: {q['error'][:50]}"
        rows.append([
            q["name"],
            q["type"],
            sql_len,
            "Yes" if q["hidden"] else "No",
            status,
        ])

    table = tabulate(
        rows,
        headers=["Query Name", "Type", "SQL Length", "Hidden", "Status"],
        tablefmt="pipe",
    )
    print("\n" + table, file=sys.stderr)


if __name__ == "__main__":
    try:
        queries = extract_all_queries()
        output_path = save_results(queries)
        print_summary_table(queries)

        # Also output JSON to stdout for piping
        print(json.dumps(queries, ensure_ascii=False, indent=2))

        # Summary stats
        total = len(queries)
        ok = sum(1 for q in queries if q["error"] is None)
        hidden = sum(1 for q in queries if q["hidden"])
        print(f"\nTotal: {total} queries, {ok} OK, {total - ok} errors, {hidden} hidden", file=sys.stderr)

    except Exception as e:
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        print(f"\nFallback: Query SQL will be extracted on Windows in Plan 03-02", file=sys.stderr)
        print(f"via export_all.vbs (QueryDef.SQL property).", file=sys.stderr)
        sys.exit(1)
