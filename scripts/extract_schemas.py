"""Extract per-table schema documents for all user tables.

Produces one markdown file per user table in assessment/tables/{table_name}.md
with column definitions, indexes, and sample data.
"""

from datetime import datetime
from pathlib import Path

from tabulate import tabulate

from db_reader import (
    open_db,
    get_column_metadata,
    get_indexes_for_table,
    get_user_tables,
    parse_table,
    strip_null_bytes,
)

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "assessment" / "tables"


def format_sample_value(val, max_len=80):
    """Format a single sample data value for markdown display."""
    if val is None:
        return ""
    if isinstance(val, bytes):
        return f"[Binary: {len(val)} bytes]"
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S")
    s = strip_null_bytes(str(val))
    if len(s) > max_len:
        return s[:max_len] + "..."
    return s


def build_overview_table(table_name, columns, indexes, row_count):
    """Build the Overview properties table."""
    # Find primary key from indexes
    pk_cols = []
    for idx in indexes:
        if idx["type"] == "Primary Key":
            pk_cols.extend(idx["columns"])
    pk_display = ", ".join(pk_cols) if pk_cols else "None detected"

    rows = [
        ["Row Count", f"{row_count:,}"],
        ["Column Count", str(len(columns))],
        ["Index Count", str(len(indexes))],
        ["Primary Key", pk_display],
    ]
    return tabulate(rows, headers=["Property", "Value"], tablefmt="pipe")


def build_column_table(columns):
    """Build the Column Definitions table."""
    rows = []
    has_decimal = False
    for i, col in enumerate(columns, 1):
        max_chars = col["max_chars"]
        max_chars_display = str(max_chars) if max_chars is not None else "-"

        nullable = "Yes" if col["can_be_null"] else "No"
        autonumber = "Yes" if col["is_autonumber"] else "No"
        fixed_len = "Yes" if col["is_fixed_length"] else "No"

        if col["type_code"] == 16:
            has_decimal = True

        rows.append([
            i,
            col["name"],
            col["type_name"],
            col["length_bytes"],
            max_chars_display,
            nullable,
            autonumber,
            fixed_len,
        ])

    headers = [
        "#", "Column Name", "Data Type", "Length (bytes)",
        "Max Chars", "Nullable", "AutoNumber", "Fixed Length",
    ]
    table_str = tabulate(rows, headers=headers, tablefmt="pipe")

    # Build notes
    notes = [
        "- Text columns show max character count (length_bytes / 2 for UTF-16)",
        "- All text columns use Thai collation (code page 1054 / TIS-620)",
    ]
    if has_decimal:
        # Find decimal columns and show precision/scale
        for col in columns:
            if col["type_code"] == 16:
                prec = col.get("precision", "N/A")
                scale = col.get("scale", "N/A")
                notes.append(
                    f"- Decimal columns: precision={prec}, scale={scale}"
                )
                break

    return table_str, "\n".join(notes)


def build_index_table(indexes):
    """Build the Indexes table."""
    if not indexes:
        return "*(No indexes detected)*"

    rows = []
    for idx in indexes:
        col_display = ", ".join(idx["columns"]) if idx["columns"] else "(no columns mapped)"
        rows.append([idx["name"], idx["type"], col_display])

    return tabulate(rows, headers=["Index Name", "Type", "Columns"], tablefmt="pipe")


def build_sample_data(data, max_rows=5):
    """Build the Sample Data table from parsed table data."""
    if not data:
        return "*(Table is empty -- no sample data available)*"

    columns = list(data.keys())
    first_col_vals = data[columns[0]]
    actual_rows = len(first_col_vals)

    if actual_rows == 0:
        return "*(Table is empty -- no sample data available)*"

    num_rows = min(max_rows, actual_rows)
    rows = []
    for i in range(num_rows):
        row = []
        for col in columns:
            val = data[col][i] if i < len(data[col]) else None
            row.append(format_sample_value(val))
        rows.append(row)

    # Clean column headers (strip null bytes)
    display_cols = [strip_null_bytes(str(c)) for c in columns]

    return tabulate(rows, headers=display_cols, tablefmt="pipe")


def extract_schema_for_table(db, table_name):
    """Extract complete schema document for a single table."""
    # Get column metadata
    columns = get_column_metadata(db, table_name)

    # Build column_id_map for index resolution
    column_id_map = {col["column_id"]: col["name"] for col in columns}

    # Get indexes
    indexes = get_indexes_for_table(db, table_name, column_id_map)

    # Get sample data
    data = parse_table(db, table_name)
    if data:
        first_col = next(iter(data.values()))
        row_count = len(first_col)
    else:
        row_count = 0

    # Build document sections
    overview = build_overview_table(table_name, columns, indexes, row_count)
    col_table, col_notes = build_column_table(columns)
    idx_table = build_index_table(indexes)
    sample_data = build_sample_data(data, max_rows=5)

    # Compose full document
    doc = f"""# {table_name}

## Overview

{overview}

## Column Definitions

{col_table}

Notes:
{col_notes}

## Indexes

{idx_table}

## Sample Data (First 5 Rows)

{sample_data}
"""
    return doc, len(columns), len(indexes)


def main():
    db = open_db()
    tables = get_user_tables(db)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Remove .gitkeep if present (being replaced by actual files)
    gitkeep = OUTPUT_DIR / ".gitkeep"
    if gitkeep.exists():
        gitkeep.unlink()

    for table_name in tables:
        print(f"Extracting schema for: {table_name}...", end=" ", flush=True)
        doc, n_cols, n_idx = extract_schema_for_table(db, table_name)

        out_path = OUTPUT_DIR / f"{table_name}.md"
        out_path.write_text(doc, encoding="utf-8")
        print(f"done ({n_cols} columns, {n_idx} indexes)")

    print(f"\nGenerated {len(tables)} schema documents in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
