"""Centralized database access module for epic_db.accdb.

All extraction scripts import from this module to avoid duplicating
file paths, parser initialization, and encoding workarounds.
"""

from pathlib import Path

from access_parser_c import AccessParser
from tabulate import tabulate

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "epic_db.accdb"

# MSysObjects type codes (from Microsoft documentation)
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


def open_db(db_path: Path = DB_PATH) -> AccessParser:
    """Open the Access database. Returns AccessParser instance.

    Wraps initialization with clear error messages for common failures.
    """
    try:
        return AccessParser(str(db_path))
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Database file not found: {db_path}\n"
            f"Expected at: {db_path.resolve()}"
        )
    except ImportError as e:
        raise ImportError(
            f"access-parser import failed: {e}\n"
            "Try: uv pip install access-parser"
        )
    except Exception as e:
        raise RuntimeError(
            f"Failed to open database: {e}\n"
            f"File: {db_path}\n"
            "If 'not a supported database version', try McSash fork:\n"
            "  uv pip install git+https://github.com/McSash/access_parser_c"
        )


def get_catalog(db: AccessParser) -> list[str]:
    """Return user-visible table names from the catalog.

    Note: The catalog as returned by access-parser may include system
    tables (MSys*). Use get_user_tables() for filtered user tables only.
    For the full inventory of all object types, use get_all_objects_from_msys().
    """
    return list(db.catalog.keys())


def get_user_tables(db: AccessParser) -> list[str]:
    """Return only user table names (excludes MSys*, f_*, ~* system tables)."""
    return [
        name for name in db.catalog.keys()
        if not name.startswith("MSys")
        and not name.startswith("~")
        and not name.startswith("f_")
    ]


def parse_table(db: AccessParser, table_name: str) -> dict:
    """Parse a table and return its data as {column_name: [values...]}.

    Works for tables in the catalog. For MSysObjects (system catalog),
    use _read_msys_objects_raw() instead.
    """
    return db.parse_table(table_name)


def _read_msys_objects_raw(db: AccessParser) -> dict:
    """Read the raw MSysObjects system table by accessing the catalog page directly.

    MSysObjects is stored at page offset 2 * page_size. The parser's
    _parse_catalog() method reads this same data to build the catalog,
    but MSysObjects itself is not included in the catalog. This function
    accesses it at the lower level.
    """
    from access_parser_c.access_parser import AccessTable

    catalog_page_offset = 2 * db.page_size
    table_obj = db._tables_with_data[catalog_page_offset]
    access_table = AccessTable(
        table_obj, db.version, db.page_size, db._data_pages, db._table_defs
    )
    return access_table.parse()


def get_all_objects_from_msys(db: AccessParser) -> dict:
    """Read MSysObjects to enumerate every object in the database by type.

    Returns dict of {type_label: [{"name": str, "flags": int}, ...]}.
    Filters out system objects (MSys*) and temp objects (~*).
    Includes an "Unknown" bucket for unrecognized type codes.
    """
    msys = _read_msys_objects_raw(db)

    names = msys.get("Name", [])
    types = msys.get("Type", [])
    flags = msys.get("Flags", [])

    inventory = {}
    for name, obj_type, obj_flags in zip(names, types, flags):
        obj_name = str(name)

        # Skip system objects and temp objects
        if obj_name.startswith("MSys") or obj_name.startswith("~"):
            continue

        type_label = MSYS_TYPES.get(obj_type, "Unknown")
        if type_label not in inventory:
            inventory[type_label] = []

        inventory[type_label].append({
            "name": obj_name,
            "flags": int(obj_flags) if obj_flags is not None else 0,
        })

    return inventory


if __name__ == "__main__":
    print("=" * 60)
    print("Epic DB Reader - Database Summary")
    print("=" * 60)

    # 1. Open the database
    print(f"\nOpening: {DB_PATH}")
    db = open_db()
    print("Database opened successfully.")

    # 2. Print user table names (filtered from catalog)
    tables = get_user_tables(db)
    print(f"\n--- User Tables ({len(tables)}) ---")
    for i, t in enumerate(tables, 1):
        print(f"  {i:3d}. {t}")

    # 3. Print MSysObjects type summary
    print("\n--- MSysObjects Type Summary ---")
    objects = get_all_objects_from_msys(db)
    summary_rows = []
    for type_label, items in sorted(objects.items()):
        summary_rows.append([type_label, len(items)])
    print(tabulate(summary_rows, headers=["Object Type", "Count"], tablefmt="pipe"))

    # 4. Read first table from catalog, print first 3 rows
    if tables:
        first_table = tables[0]
        print(f"\n--- Sample Data: {first_table} (first 3 rows) ---")
        data = parse_table(db, first_table)
        if data:
            columns = list(data.keys())
            # Build rows (transpose from column-oriented to row-oriented)
            num_rows = min(3, len(next(iter(data.values()))))
            rows = []
            for i in range(num_rows):
                row = []
                for col in columns:
                    val = data[col][i] if i < len(data[col]) else ""
                    # Truncate long values for display
                    val_str = str(val)
                    if len(val_str) > 60:
                        val_str = val_str[:57] + "..."
                    row.append(val_str)
                rows.append(row)
            # Truncate column names for display too
            display_cols = [
                c[:30] + "..." if len(str(c)) > 30 else str(c) for c in columns
            ]
            print(tabulate(rows, headers=display_cols, tablefmt="pipe"))
        else:
            print("  (empty table)")
