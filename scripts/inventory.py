"""Generate a complete inventory of every object in epic_db.accdb.

Produces assessment/inventory.md with counts and metadata per object type.
Rerunnable: overwrites the output file each time.

Usage:
    python scripts/inventory.py [--output PATH]
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# Ensure scripts/ is on the path for sibling imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db_reader import (
    DB_PATH,
    MSYS_TYPES,
    _read_msys_objects_raw,
    get_catalog,
    get_user_tables,
    open_db,
    parse_table,
)
from tabulate import tabulate

# Query subtype constants (from MSysQueries Attribute==0 Flag values)
# When MSysQueries is not accessible, the MSysObjects Flags field for
# Type=5 objects may encode the query subtype with these same values.
QUERY_SUBTYPES = {
    0: "SELECT",
    16: "CROSSTAB",
    32: "DELETE",
    48: "UPDATE",
    64: "APPEND",
    80: "MAKE_TABLE",
    96: "DDL",
    112: "PASSTHROUGH",
    128: "UNION",
}

# Additional MSysObjects type codes not in the primary MSYS_TYPES mapping
# These are system/container objects, not user-visible database objects.
SYSTEM_TYPE_LABELS = {
    2: "System Metadata",
    3: "Container",
    8: "Relationship",
    -32757: "Document Property",
    -32758: "Security",
}

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "assessment" / "inventory.md"


def get_table_metadata(db) -> list[dict]:
    """Get metadata for each user table: name, row count, column count.

    Uses the catalog (get_user_tables) for the table list, then parses
    each table to get row/column counts. Tables that fail to parse get
    row_count=-1 as an error indicator.
    """
    tables = get_user_tables(db)
    results = []

    for table_name in sorted(tables):
        try:
            table_data = parse_table(db, table_name)
            if table_data:
                first_col = next(iter(table_data.values()))
                row_count = len(first_col)
                column_count = len(table_data.keys())
            else:
                row_count = 0
                column_count = 0
        except Exception as e:
            print(f"  WARNING: Failed to parse table '{table_name}': {e}")
            row_count = -1
            column_count = 0

        results.append({
            "name": table_name,
            "row_count": row_count,
            "column_count": column_count,
        })

    return results


def get_query_metadata(db) -> list[dict]:
    """Get metadata for each query: name and query type classification.

    Attempts to read MSysQueries for precise type classification. Falls
    back to the Flags field from MSysObjects if MSysQueries is not readable.
    """
    # Get query entries from MSysObjects
    msys = _read_msys_objects_raw(db)
    names = msys.get("Name", [])
    types = msys.get("Type", [])
    flags = msys.get("Flags", [])

    queries = []
    for name, obj_type, obj_flags in zip(names, types, flags):
        obj_name = str(name)
        if obj_type != 5:
            continue
        # Skip system/temp queries
        if obj_name.startswith("MSys") or obj_name.startswith("~"):
            continue

        f_int = int(obj_flags) if obj_flags is not None else 0
        queries.append({
            "name": obj_name,
            "flags": f_int,
        })

    # Try MSysQueries for precise type classification
    msys_queries_data = None
    try:
        msys_queries_data = parse_table(db, "MSysQueries")
    except Exception:
        pass

    if msys_queries_data and "Attribute" in msys_queries_data:
        # MSysQueries accessible -- use it for precise classification
        mq_attrs = msys_queries_data.get("Attribute", [])
        mq_flags = msys_queries_data.get("Flag", [])
        mq_names = msys_queries_data.get("Name1", [])

        # Build lookup: query name -> type from Attribute==0 rows
        query_type_lookup = {}
        for attr, flag, qname in zip(mq_attrs, mq_flags, mq_names):
            if attr == 0:
                qname_str = str(qname)
                flag_int = int(flag) if flag is not None else 0
                query_type_lookup[qname_str] = QUERY_SUBTYPES.get(
                    flag_int, f"Unknown({flag_int})"
                )

        for q in queries:
            q["query_type"] = query_type_lookup.get(q["name"], "Unknown")
        classification_source = "MSysQueries"
    else:
        # Fallback: use MSysObjects Flags field
        # Note: flags=0 is ambiguous -- it's the default and could be SELECT
        # or simply "no type info available". Only non-zero flags are reliable.
        for q in queries:
            if q["flags"] in QUERY_SUBTYPES:
                if q["flags"] == 0:
                    # flags=0 is SELECT by convention, but could also mean
                    # the type info is not encoded in MSysObjects for this query.
                    q["query_type"] = "SELECT"
                else:
                    q["query_type"] = QUERY_SUBTYPES[q["flags"]]
            else:
                q["query_type"] = f"Unknown({q['flags']})"
        classification_source = "MSysObjects Flags (MSysQueries not accessible)"

    return sorted(queries, key=lambda q: q["name"]), classification_source


def get_other_objects(db) -> dict:
    """Get forms, reports, macros, modules, linked tables, and unknowns.

    Returns a dict with lists per category. Linked tables are Type 4 or 6.
    Unknown types are anything not in MSYS_TYPES.
    """
    msys = _read_msys_objects_raw(db)
    names = msys.get("Name", [])
    types = msys.get("Type", [])
    flags = msys.get("Flags", [])

    result = {
        "forms": [],
        "reports": [],
        "macros": [],
        "modules": [],
        "linked_tables": [],
        "relationships": [],
        "unknown": [],
    }

    for name, obj_type, obj_flags in zip(names, types, flags):
        obj_name = str(name)
        f_int = int(obj_flags) if obj_flags is not None else 0

        # Skip system/temp objects
        if obj_name.startswith("MSys") or obj_name.startswith("~"):
            continue

        if obj_type == -32768:
            result["forms"].append({"name": obj_name, "flags": f_int})
        elif obj_type == -32764:
            result["reports"].append({"name": obj_name, "flags": f_int})
        elif obj_type == -32766:
            result["macros"].append({"name": obj_name, "flags": f_int})
        elif obj_type == -32761:
            result["modules"].append({"name": obj_name, "flags": f_int})
        elif obj_type in (4, 6):
            result["linked_tables"].append({
                "name": obj_name,
                "link_type": "ODBC" if obj_type == 4 else "File",
                "flags": f_int,
            })
        elif obj_type == 8:
            result["relationships"].append({"name": obj_name, "flags": f_int})
        elif obj_type not in (1, 5) and obj_type not in SYSTEM_TYPE_LABELS:
            result["unknown"].append({
                "name": obj_name,
                "type_code": obj_type,
                "flags": f_int,
            })

    # Sort each list by name
    for key in result:
        result[key].sort(key=lambda x: x["name"])

    return result


def assess_windows_need(other_objects: dict) -> str:
    """Generate Windows environment assessment text.

    Returns a recommendation string explaining whether Windows is needed.
    """
    has_forms = len(other_objects["forms"]) > 0
    has_reports = len(other_objects["reports"]) > 0
    has_modules = len(other_objects["modules"]) > 0
    has_macros = len(other_objects["macros"]) > 0

    parts = []
    if has_forms:
        parts.append(f"{len(other_objects['forms'])} forms")
    if has_reports:
        parts.append(f"{len(other_objects['reports'])} reports")
    if has_modules:
        parts.append(f"{len(other_objects['modules'])} modules")
    if has_macros:
        parts.append(f"{len(other_objects['macros'])} macros")

    if has_forms or has_reports or has_modules:
        objects_str = ", ".join(parts) if parts else ""
        text = (
            f"**Windows environment IS NEEDED** for full content extraction.\n\n"
            f"This database contains {objects_str} whose content (layouts, controls, "
            f"VBA code, definitions) cannot be extracted on macOS.\n\n"
            f"**What macOS can do:** List names for all object types (shown above), "
            f"extract table schemas and data, enumerate query names and types.\n\n"
            f"**What requires Windows:** Form layouts and controls, report definitions "
            f"and data sources, VBA module code, macro step definitions. These are "
            f"stored as binary blobs requiring Microsoft Access COM Object Model "
            f"(`Application.SaveAsText`).\n\n"
            f"**Recommendation:** Proceed with macOS for Phase 1 (inventory) and "
            f"Phase 2 (schema/query extraction). Set up a Windows environment with "
            f"Microsoft Access for Phase 3 (Logic + Interface extraction)."
        )
    else:
        text = (
            "**Windows environment is NOT needed.** No forms, reports, or modules "
            "were found in the database. All content can be extracted on macOS."
        )

    return text


def cross_validate(db, table_metadata: list[dict], query_metadata: list[dict],
                   other_objects: dict) -> list[str]:
    """Cross-validate inventory completeness.

    Compares catalog table names vs MSysObjects Type=1 names, and checks
    total counts match. Returns a list of findings/discrepancies.
    """
    findings = []

    # 1. Compare catalog tables vs MSysObjects Type=1 tables
    catalog_names = set(get_user_tables(db))

    msys = _read_msys_objects_raw(db)
    names = msys.get("Name", [])
    types = msys.get("Type", [])
    flags = msys.get("Flags", [])

    msys_table_names = set()
    for name, obj_type, obj_flags in zip(names, types, flags):
        obj_name = str(name)
        if obj_type == 1 and not obj_name.startswith("MSys") and not obj_name.startswith("~"):
            msys_table_names.add(obj_name)

    # Tables in catalog but not in MSysObjects
    catalog_only = catalog_names - msys_table_names
    if catalog_only:
        findings.append(
            f"Tables in catalog but NOT in MSysObjects: {sorted(catalog_only)}"
        )

    # Tables in MSysObjects but not in catalog
    msys_only = msys_table_names - catalog_names
    if msys_only:
        # This is expected for system-flagged tables (f_* prefixed)
        user_msys_only = {n for n in msys_only if not n.startswith("f_")}
        system_msys_only = {n for n in msys_only if n.startswith("f_")}
        if user_msys_only:
            findings.append(
                f"Tables in MSysObjects but NOT in catalog (user): {sorted(user_msys_only)}"
            )
        if system_msys_only:
            findings.append(
                f"Tables in MSysObjects but NOT in catalog (system/internal, f_* prefix): "
                f"{len(system_msys_only)} entries (expected -- these are internal Access tables)"
            )

    if not catalog_only and not (msys_table_names - catalog_names - {n for n in msys_only if n.startswith("f_")}):
        findings.append("Catalog vs MSysObjects user tables: MATCH")

    # 2. Check for parse errors
    error_tables = [t for t in table_metadata if t["row_count"] == -1]
    if error_tables:
        findings.append(
            f"Tables with parse errors (row_count=-1): "
            f"{[t['name'] for t in error_tables]}"
        )
    else:
        findings.append("All tables parsed successfully (no row_count=-1 errors)")

    # 3. Total object count
    total_inventory = (
        len(table_metadata)
        + len(query_metadata)
        + len(other_objects["forms"])
        + len(other_objects["reports"])
        + len(other_objects["macros"])
        + len(other_objects["modules"])
    )

    # Count non-system objects from MSysObjects (Types 1, 5, -32768, -32764, -32766, -32761)
    user_types = {1, 5, -32768, -32764, -32766, -32761}
    msys_user_count = 0
    for name, obj_type in zip(names, types):
        obj_name = str(name)
        if obj_type in user_types and not obj_name.startswith("MSys") and not obj_name.startswith("~"):
            # Also exclude f_* system tables from count to match inventory
            if obj_type == 1 and obj_name.startswith("f_"):
                continue
            msys_user_count += 1

    if total_inventory == msys_user_count:
        findings.append(
            f"Total object count: {total_inventory} (matches MSysObjects user object count)"
        )
    else:
        findings.append(
            f"Total object count MISMATCH: inventory={total_inventory}, "
            f"MSysObjects user objects={msys_user_count}"
        )

    return findings


def generate_inventory(db, output_path: Path) -> None:
    """Orchestrate inventory generation and write assessment/inventory.md."""
    print("Generating inventory...")

    # Step 1: Table metadata
    print("  Collecting table metadata...")
    table_metadata = get_table_metadata(db)
    print(f"    Found {len(table_metadata)} user tables")

    # Step 2: Query metadata
    print("  Collecting query metadata...")
    query_metadata, query_source = get_query_metadata(db)
    print(f"    Found {len(query_metadata)} queries (classified via {query_source})")

    # Step 3: Other objects
    print("  Collecting forms, reports, macros, modules...")
    other_objects = get_other_objects(db)
    print(f"    Forms: {len(other_objects['forms'])}")
    print(f"    Reports: {len(other_objects['reports'])}")
    print(f"    Macros: {len(other_objects['macros'])}")
    print(f"    Modules: {len(other_objects['modules'])}")
    print(f"    Linked tables: {len(other_objects['linked_tables'])}")
    print(f"    Relationships: {len(other_objects['relationships'])}")

    # Step 4: Windows assessment
    windows_text = assess_windows_need(other_objects)

    # Step 5: Cross-validate
    print("  Cross-validating...")
    findings = cross_validate(db, table_metadata, query_metadata, other_objects)
    for f in findings:
        print(f"    {f}")

    # Step 6: Build the markdown document
    lines = []
    lines.append("# Epic DB Object Inventory")
    lines.append("")
    lines.append(f"**Generated:** {date.today()}")
    lines.append(f"**Source:** data/epic_db.accdb (Access 2010 format)")
    lines.append("**Generator:** scripts/inventory.py (rerun to regenerate)")
    lines.append("")

    # --- Summary ---
    lines.append("## Summary")
    lines.append("")

    total = (
        len(table_metadata)
        + len(query_metadata)
        + len(other_objects["forms"])
        + len(other_objects["reports"])
        + len(other_objects["macros"])
        + len(other_objects["modules"])
    )

    summary_rows = [
        ["Tables", len(table_metadata)],
        ["Queries", len(query_metadata)],
        ["Forms", len(other_objects["forms"])],
        ["Reports", len(other_objects["reports"])],
        ["Macros", len(other_objects["macros"])],
        ["Modules", len(other_objects["modules"])],
    ]
    lines.append(tabulate(summary_rows, headers=["Object Type", "Count"], tablefmt="pipe"))
    lines.append("")
    lines.append(f"**Total: {total} objects**")
    lines.append("")

    if other_objects["linked_tables"]:
        lines.append(
            f"Additionally: {len(other_objects['linked_tables'])} linked table(s), "
            f"{len(other_objects['relationships'])} relationship(s)"
        )
    elif other_objects["relationships"]:
        lines.append(
            f"Additionally: {len(other_objects['relationships'])} relationship(s) detected"
        )
    lines.append("")

    # --- Tables ---
    lines.append(f"## Tables ({len(table_metadata)})")
    lines.append("")

    if table_metadata:
        table_rows = []
        for t in table_metadata:
            rc = t["row_count"] if t["row_count"] >= 0 else "ERROR"
            table_rows.append([t["name"], rc, t["column_count"]])
        lines.append(
            tabulate(table_rows, headers=["Name", "Row Count", "Columns"], tablefmt="pipe")
        )
    else:
        lines.append("*None found*")
    lines.append("")

    # --- Queries ---
    lines.append(f"## Queries ({len(query_metadata)})")
    lines.append("")

    if query_metadata:
        query_rows = [[q["name"], q["query_type"]] for q in query_metadata]
        lines.append(
            tabulate(query_rows, headers=["Name", "Type"], tablefmt="pipe")
        )
        lines.append("")
        lines.append(f"> Query type classification source: {query_source}")
        if "MSysObjects" in query_source:
            lines.append(
                "> Note: MSysQueries system table was not accessible. Query types are "
                "inferred from MSysObjects Flags field. Flags=0 is classified as SELECT "
                "by convention, but some queries (especially those with names suggesting "
                "UPDATE/INSERT operations) may have different actual types. Precise "
                "classification requires MSysQueries or Windows with Access."
            )
    else:
        lines.append("*None found*")
    lines.append("")

    # --- Forms ---
    lines.append(f"## Forms ({len(other_objects['forms'])})")
    lines.append("")

    if other_objects["forms"]:
        form_rows = [[f["name"]] for f in other_objects["forms"]]
        lines.append(tabulate(form_rows, headers=["Name"], tablefmt="pipe"))
        lines.append("")
        lines.append(
            "> Note: Form content (layouts, controls, VBA code-behind) requires "
            "Windows with Microsoft Access for extraction via `Application.SaveAsText`."
        )
    else:
        lines.append("*None found*")
    lines.append("")

    # --- Reports ---
    lines.append(f"## Reports ({len(other_objects['reports'])})")
    lines.append("")

    if other_objects["reports"]:
        report_rows = [[r["name"]] for r in other_objects["reports"]]
        lines.append(tabulate(report_rows, headers=["Name"], tablefmt="pipe"))
        lines.append("")
        lines.append(
            "> Note: Report content (layouts, data sources, grouping/sorting) requires "
            "Windows with Microsoft Access for extraction via `Application.SaveAsText`."
        )
    else:
        lines.append("*None found*")
    lines.append("")

    # --- Modules ---
    lines.append(f"## Modules ({len(other_objects['modules'])})")
    lines.append("")

    if other_objects["modules"]:
        module_rows = [[m["name"]] for m in other_objects["modules"]]
        lines.append(tabulate(module_rows, headers=["Name"], tablefmt="pipe"))
        lines.append("")
        lines.append(
            "> Note: Module content (VBA code) requires Windows with Microsoft Access "
            "for extraction via `Application.SaveAsText` or VBE COM automation."
        )
    else:
        lines.append("*None found*")
    lines.append("")

    # --- Macros ---
    lines.append(f"## Macros ({len(other_objects['macros'])})")
    lines.append("")

    if other_objects["macros"]:
        macro_rows = [[m["name"]] for m in other_objects["macros"]]
        lines.append(tabulate(macro_rows, headers=["Name"], tablefmt="pipe"))
        lines.append("")
        lines.append(
            "> Note: Macro definitions (action steps) require Windows with Microsoft "
            "Access for extraction via `Application.SaveAsText`."
        )
    else:
        lines.append("*None found*")
    lines.append("")

    # --- Linked Tables ---
    if other_objects["linked_tables"]:
        lines.append(f"## Linked Tables ({len(other_objects['linked_tables'])})")
        lines.append("")
        linked_rows = [
            [lt["name"], lt["link_type"]]
            for lt in other_objects["linked_tables"]
        ]
        lines.append(
            tabulate(linked_rows, headers=["Name", "Link Type"], tablefmt="pipe")
        )
        lines.append("")
        lines.append(
            "> Note: Linked tables reference external data sources. The actual data "
            "resides outside this .accdb file."
        )
        lines.append("")

    # --- Relationships ---
    if other_objects["relationships"]:
        lines.append(f"## Relationships ({len(other_objects['relationships'])})")
        lines.append("")
        lines.append(
            "The following table-to-table relationships were detected in MSysObjects "
            "(Type=8). The Name field contains concatenated table names indicating "
            "a relationship between two tables."
        )
        lines.append("")
        rel_rows = [[r["name"]] for r in other_objects["relationships"]]
        lines.append(tabulate(rel_rows, headers=["Relationship (Table Pair)"], tablefmt="pipe"))
        lines.append("")

    # --- Windows Assessment ---
    lines.append("## Windows Assessment")
    lines.append("")
    lines.append(windows_text)
    lines.append("")

    # --- Cross-Validation ---
    lines.append("## Cross-Validation")
    lines.append("")
    for finding in findings:
        lines.append(f"- {finding}")
    lines.append("")

    # Write the file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    # Print summary to stdout
    print()
    print(
        f"Inventory complete: {len(table_metadata)} tables, "
        f"{len(query_metadata)} queries, {len(other_objects['forms'])} forms, "
        f"{len(other_objects['reports'])} reports, "
        f"{len(other_objects['modules'])} modules, "
        f"{len(other_objects['macros'])} macros = {total} total"
    )
    print(f"Written to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate a complete inventory of every object in epic_db.accdb"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path for inventory markdown (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    db = open_db()
    generate_inventory(db, args.output)


if __name__ == "__main__":
    main()
