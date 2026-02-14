"""Centralized database access module for epic_db.accdb.

All extraction scripts import from this module to avoid duplicating
file paths, parser initialization, and encoding workarounds.
"""

from io import BytesIO
from pathlib import Path

from access_parser_c import AccessParser
from access_parser_c.access_parser import AccessTable, TableObj
from access_parser_c.parsing_primitives import TDEF_HEADER, parse_table_head
from construct import Array, Int8ul, Int16ul, Int32ul, PaddedString, Struct
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


# --- Schema extraction functions (Phase 2) ---

# Access internal type codes -> human-readable names
TYPE_NAMES = {
    1: "Yes/No",
    2: "Byte",
    3: "Integer",
    4: "Long Integer",
    5: "Currency",
    6: "Single",
    7: "Double",
    8: "Date/Time",
    9: "Binary",
    10: "Short Text",
    11: "OLE Object",
    12: "Long Text (Memo)",
    15: "GUID",
    16: "Decimal",
    18: "Complex",
}


def strip_null_bytes(s):
    """Strip null byte compression artifacts from Access strings.

    Access stores text with Unicode compression that introduces \\x00 bytes.
    This helper consolidates the stripping pattern for reuse.
    """
    if isinstance(s, str):
        return s.replace("\x00", "")
    return str(s)


def _get_access_table(db: AccessParser, table_name: str) -> AccessTable | None:
    """Get an AccessTable instance for a user table by name.

    Handles the catalog lookup and fallback to _table_defs for tables
    without data pages (empty tables).
    """
    page_num = db.catalog.get(table_name)
    if not page_num:
        return None
    table_offset = page_num * db.page_size
    table_obj = db._tables_with_data.get(table_offset)
    if not table_obj:
        table_def = db._table_defs.get(table_offset)
        if table_def:
            table_obj = TableObj(offset=table_offset, val=table_def)
        else:
            return None
    return AccessTable(
        table_obj, db.version, db.page_size, db._data_pages, db._table_defs
    )


def get_column_metadata(db: AccessParser, table_name: str) -> list[dict]:
    """Extract column metadata from the binary table definition.

    Accesses AccessTable.columns to get type, length, nullable, autonumber
    flags per column -- information that parse_table() does not expose.

    Returns list of dicts with: name, type_code, type_name, length_bytes,
    max_chars (for text types), can_be_null, is_autonumber, is_fixed_length,
    column_id, column_index. Text columns also include collation; Decimal
    columns include precision and scale when available.
    """
    access_table = _get_access_table(db, table_name)
    if not access_table:
        return []

    columns = []
    for i, col in access_table.columns.items():
        col_info = {
            "name": col.col_name_str,
            "type_code": col.type,
            "type_name": TYPE_NAMES.get(col.type, f"Unknown({col.type})"),
            "length_bytes": col.length,
            "max_chars": col.length // 2 if col.type in (10, 12) else None,
            "can_be_null": col.column_flags.can_be_null,
            "is_autonumber": col.column_flags.autonumber,
            "is_fixed_length": col.column_flags.fixed_length,
            "column_id": col.column_id,
            "column_index": col.column_index,
        }

        # Text columns: extract collation info
        if col.type in (10, 12) and hasattr(col, "various") and col.various:
            v = dict(col.various)
            v.pop("_io", None)
            col_info["collation"] = v.get("collation", None)

        # Decimal columns: extract precision and scale
        if col.type == 16 and hasattr(col, "various") and col.various:
            v = dict(col.various)
            v.pop("_io", None)
            col_info["precision"] = v.get("prec", None)
            col_info["scale"] = v.get("scale", None)

        columns.append(col_info)

    return columns


def get_relationships(db: AccessParser) -> list[dict]:
    """Read MSysRelationships system table for column-level FK detail.

    MSysRelationships is at catalog Id=5, offset = 5 * page_size.
    It is NOT in the filtered catalog but IS readable via direct offset.

    Returns list of dicts with: name, source_table, source_column,
    ref_table, ref_column, grbit, enforce_ri, cascade_updates,
    cascade_deletes, no_integrity.  All string values have null bytes stripped.
    """
    rels_offset = 5 * db.page_size
    table_obj = db._tables_with_data.get(rels_offset)
    if not table_obj:
        return []

    access_table = AccessTable(
        table_obj, db.version, db.page_size, db._data_pages, db._table_defs
    )
    data = access_table.parse()
    if not data or "szRelationship" not in data:
        return []

    relationships = []
    for i in range(len(data["szRelationship"])):
        grbit = data["grbit"][i]
        relationships.append(
            {
                "name": strip_null_bytes(data["szRelationship"][i]),
                "source_table": strip_null_bytes(data["szObject"][i]),
                "source_column": strip_null_bytes(data["szColumn"][i]),
                "ref_table": strip_null_bytes(data["szReferencedObject"][i]),
                "ref_column": strip_null_bytes(data["szReferencedColumn"][i]),
                "grbit": grbit,
                "enforce_ri": bool(grbit & 0x001),
                "cascade_updates": bool(grbit & 0x002),
                "cascade_deletes": bool(grbit & 0x004),
                "no_integrity": bool(grbit & 0x100),
            }
        )

    return relationships


def get_indexes_for_table(
    db: AccessParser, table_name: str, column_id_map: dict
) -> list[dict]:
    """Parse index definitions from the binary table definition.

    Manually navigates past real_index + columns + column_names in the
    merged table data to reach REAL_INDEX2, ALL_INDEXES, and INDEX_NAME
    structures. The parser (access_parser_c) skips these because they
    cause errors on SOME databases, but they work on epic_db.accdb.

    Args:
        db: AccessParser instance
        table_name: name of the table
        column_id_map: dict mapping column_id -> column_name
            (build from get_column_metadata results before calling)

    Returns: list of index dicts with name, type, and column names.
    """
    page_num = db.catalog.get(table_name)
    if not page_num:
        return []
    table_offset = page_num * db.page_size

    table_obj = db._tables_with_data.get(table_offset)
    if not table_obj:
        table_def = db._table_defs.get(table_offset)
        if table_def:
            table_obj = TableObj(offset=table_offset, val=table_def)
        else:
            return []

    # Parse header to get counts
    table_header = parse_table_head(table_obj.value, version=db.version)
    merged_data = table_obj.value[table_header.tdef_header_end :]

    # Handle multi-page table definitions (follow next_page_ptr chain)
    if table_header.TDEF_header.next_page_ptr:
        next_ptr = table_header.TDEF_header.next_page_ptr
        while next_ptr:
            next_page = db._table_defs.get(next_ptr * db.page_size)
            if not next_page:
                break
            ph = TDEF_HEADER.parse(next_page)
            merged_data += next_page[ph.header_end :]
            next_ptr = ph.next_page_ptr

    stream = BytesIO(merged_data)

    # Skip real_index entries (12 bytes each for Access 2010 / v4)
    stream.read(table_header.real_index_count * 12)

    # Skip column entries (25 bytes each for v4)
    stream.read(table_header.column_count * 25)

    # Skip column_names (variable length: 2-byte length prefix + name bytes)
    for _ in range(table_header.column_count):
        name_len = Int16ul.parse_stream(stream)
        stream.read(name_len)

    remaining = merged_data[stream.tell() :]

    if table_header.real_index_count == 0 and table_header.index_count == 0:
        return []

    # Parse REAL_INDEX2 (52 bytes each, contains col_id -> index mapping)
    REAL_INDEX2 = Struct(
        "unknown_b1" / Int32ul,
        "unk_struct"
        / Array(10, Struct("col_id" / Int16ul, "idx_flags" / Int8ul)),
        "runk" / Int32ul,
        "first_index_page" / Int32ul,
        "flags" / Int16ul,
        "unknown_b3" / Int32ul,
        "unknown_b4" / Int32ul,
    )
    ri2_entry_size = 52
    ri2_list = Array(table_header.real_index_count, REAL_INDEX2).parse(remaining)
    remaining = remaining[table_header.real_index_count * ri2_entry_size :]

    # Parse ALL_INDEXES (28 bytes each, contains idx_type: 0=Regular, 1=PK, 2=FK)
    ALL_INDEXES = Struct(
        "unknown_c1" / Int32ul,
        "idx_num" / Int32ul,
        "idx_col_num" / Int32ul,
        "unkc2" / Int8ul,
        "unkc3" / Int32ul,
        "unkc4" / Int32ul,
        "unkc5" / Int16ul,
        "idx_type" / Int8ul,
        "unknown_c6" / Int32ul,
    )
    idx_entry_size = 28
    all_idx = Array(table_header.index_count, ALL_INDEXES).parse(remaining)
    remaining = remaining[table_header.index_count * idx_entry_size :]

    # Parse INDEX_NAME (variable length, UTF-16 encoded names)
    INDEX_NAME = Struct(
        "name_len" / Int16ul,
        "name" / PaddedString(lambda x: x.name_len, encoding="utf16"),
    )
    idx_names = Array(table_header.index_count, INDEX_NAME).parse(remaining)

    IDX_TYPE_MAP = {0: "Regular", 1: "Primary Key", 2: "Foreign Key"}

    indexes = []
    for i, (idx_def, idx_name) in enumerate(zip(all_idx, idx_names)):
        # Map columns from REAL_INDEX2 via idx_num
        col_names = []
        ri_idx = idx_def.idx_num
        if ri_idx < len(ri2_list):
            for entry in ri2_list[ri_idx].unk_struct:
                if entry.col_id != 0xFFFF:  # 65535 = unused slot
                    col_name = column_id_map.get(
                        entry.col_id, f"col_id_{entry.col_id}"
                    )
                    col_names.append(col_name)

        indexes.append(
            {
                "name": strip_null_bytes(idx_name.name),
                "type": IDX_TYPE_MAP.get(idx_def.idx_type, f"Unknown({idx_def.idx_type})"),
                "columns": col_names,
            }
        )

    return indexes


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
