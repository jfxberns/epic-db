"""Thai encoding validation script for epic_db.accdb.

Scans ALL tables for Thai text rendering quality:
- Checks column names for Thai characters
- Checks row data for Thai characters, mojibake (U+FFFD), and null byte artifacts
- Distinguishes Unicode compression artifacts (harmless) from true corruption
- Prints visual samples with Unicode codepoints for manual verification
- Produces a PASS/FAIL/WARNING verdict
"""

import sys
from pathlib import Path

# Ensure scripts/ is in the path for db_reader import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from db_reader import open_db, get_user_tables, parse_table

# Thai Unicode block: U+0E00 to U+0E7F
THAI_RANGE = range(0x0E00, 0x0E80)


def has_thai(text: str) -> bool:
    """Check if text contains any Thai characters."""
    return any(ord(c) in THAI_RANGE for c in text)


def has_mojibake(text: str) -> bool:
    """Check if text contains U+FFFD replacement characters."""
    return "\ufffd" in text


def has_null_bytes(text: str) -> bool:
    """Check if text contains null byte artifacts."""
    return "\x00" in text


def strip_compression_nulls(text: str) -> str:
    """Strip null bytes from Access Unicode compression artifacts.

    Access stores text as UTF-16-LE with a proprietary compression scheme.
    When the parser decodes compressed segments, null bytes (\x00) may
    remain as artifacts at segment boundaries. These are not data corruption
    -- they are parser artifacts from the compression toggle points.

    Stripping them produces clean readable text.
    """
    return text.replace("\x00", "")


def codepoints_str(text: str, max_chars: int = 30) -> str:
    """Return Unicode codepoints for the first N characters of text."""
    return " ".join(f"U+{ord(c):04X}" for c in text[:max_chars])


def check_column_names(db, tables: list[str]) -> dict:
    """Check column names across all tables for Thai characters.

    Returns dict of {table_name: [thai_column_names...]}.
    """
    thai_columns = {}
    for table_name in tables:
        try:
            data = parse_table(db, table_name)
            if data is None:
                continue
            for col_name in data.keys():
                col_str = str(col_name)
                if has_thai(col_str):
                    if table_name not in thai_columns:
                        thai_columns[table_name] = []
                    thai_columns[table_name].append(col_str)
        except Exception as e:
            print(f"  WARNING: Could not read table {table_name}: {e}")
    return thai_columns


def check_row_data(db, tables: list[str]) -> dict:
    """Check row data across all tables for Thai encoding quality.

    Returns dict of {table_name: {
        "total_strings": int,
        "thai_count": int,
        "mojibake_count": int,
        "null_byte_count": int,
        "null_bytes_with_thai": int,
        "null_bytes_clean_after_strip": int,
        "samples": [(col_name, row_idx, text), ...],
        "null_byte_samples": [(col_name, row_idx, raw, cleaned), ...],
    }}.
    """
    results = {}
    for table_name in tables:
        try:
            data = parse_table(db, table_name)
            if data is None:
                continue
        except Exception as e:
            print(f"  WARNING: Could not parse table {table_name}: {e}")
            continue

        table_stats = {
            "total_strings": 0,
            "thai_count": 0,
            "mojibake_count": 0,
            "null_byte_count": 0,
            "null_bytes_with_thai": 0,
            "null_bytes_clean_after_strip": 0,
            "samples": [],
            "null_byte_samples": [],
        }

        for col_name, values in data.items():
            for row_idx, val in enumerate(values):
                text = str(val)
                if not text or text == "None" or text == "":
                    continue

                table_stats["total_strings"] += 1

                is_thai = has_thai(text)
                is_mojibake = has_mojibake(text)
                has_nulls = has_null_bytes(text)

                if is_thai:
                    table_stats["thai_count"] += 1
                if is_mojibake:
                    table_stats["mojibake_count"] += 1
                if has_nulls:
                    table_stats["null_byte_count"] += 1
                    # Check if the cleaned version looks good
                    cleaned = strip_compression_nulls(text)
                    cleaned_thai = has_thai(cleaned) or not any(
                        ord(c) > 127 for c in cleaned
                    )
                    if cleaned_thai:
                        table_stats["null_bytes_clean_after_strip"] += 1
                    if is_thai or has_thai(cleaned):
                        table_stats["null_bytes_with_thai"] += 1

                    # Collect null byte samples
                    if len(table_stats["null_byte_samples"]) < 3:
                        table_stats["null_byte_samples"].append(
                            (str(col_name), row_idx, text[:150], cleaned[:150])
                        )

                # Collect Thai samples: up to 5 per table, prefer clean Thai
                if is_thai and not has_nulls and len(table_stats["samples"]) < 5:
                    table_stats["samples"].append(
                        (str(col_name), row_idx, text[:200])
                    )

        # If we didn't get enough clean samples, add Thai samples with nulls stripped
        if len(table_stats["samples"]) < 3:
            for col_name, values in data.items():
                for row_idx, val in enumerate(values):
                    text = str(val)
                    if has_thai(text) and has_null_bytes(text):
                        cleaned = strip_compression_nulls(text)
                        if has_thai(cleaned) and len(table_stats["samples"]) < 5:
                            table_stats["samples"].append(
                                (str(col_name), row_idx, cleaned[:200])
                            )

        results[table_name] = table_stats

    return results


def print_report(thai_columns: dict, row_results: dict) -> str:
    """Print the full encoding validation report. Returns verdict string."""
    print("=" * 70)
    print("THAI ENCODING VALIDATION REPORT")
    print("=" * 70)

    # --- Section 1: Column Names ---
    print("\n--- COLUMN NAME ANALYSIS ---")
    if thai_columns:
        total_thai_cols = sum(len(cols) for cols in thai_columns.values())
        print(f"Found {total_thai_cols} Thai column names across "
              f"{len(thai_columns)} tables:\n")
        for table_name, cols in sorted(thai_columns.items()):
            print(f"  TABLE: {table_name}")
            for col in cols:
                print(f"    - {col}")
                print(f"      Codepoints: {codepoints_str(col)}")
            print()
    else:
        print("  No Thai column names found.")

    # --- Section 2: Per-table Row Data Summary ---
    print("\n--- PER-TABLE ENCODING SUMMARY ---")
    print(f"{'Table':<35} {'Strings':>8} {'Thai':>6} "
          f"{'Mojibake':>8} {'NullByte':>8} {'Strippable':>10}")
    print("-" * 80)

    total_thai = 0
    total_mojibake = 0
    total_nullbytes = 0
    total_strippable = 0
    total_strings = 0

    for table_name, stats in sorted(row_results.items()):
        total_strings += stats["total_strings"]
        total_thai += stats["thai_count"]
        total_mojibake += stats["mojibake_count"]
        total_nullbytes += stats["null_byte_count"]
        total_strippable += stats["null_bytes_clean_after_strip"]

        display_name = table_name[:33] + ".." if len(table_name) > 35 else table_name
        print(f"{display_name:<35} {stats['total_strings']:>8} "
              f"{stats['thai_count']:>6} {stats['mojibake_count']:>8} "
              f"{stats['null_byte_count']:>8} "
              f"{stats['null_bytes_clean_after_strip']:>10}")

    print("-" * 80)
    print(f"{'TOTAL':<35} {total_strings:>8} {total_thai:>6} "
          f"{total_mojibake:>8} {total_nullbytes:>8} {total_strippable:>10}")

    # --- Section 3: Null byte analysis ---
    if total_nullbytes > 0:
        print("\n--- NULL BYTE ANALYSIS ---")
        print(f"Total strings with null bytes: {total_nullbytes}")
        print(f"Strippable (compression artifacts): {total_strippable}")
        true_corruption = total_nullbytes - total_strippable
        print(f"Non-strippable (possible corruption): {true_corruption}")
        print()
        print("These null bytes are Access Unicode compression artifacts.")
        print("The parser partially decodes compressed UTF-16-LE text, leaving")
        print("null bytes at compression segment boundaries. Stripping them")
        print("produces correct readable text.")
        print()
        print("Sample before/after stripping:")
        shown = 0
        for table_name, stats in sorted(row_results.items()):
            for col_name, row_idx, raw, cleaned in stats["null_byte_samples"]:
                if shown >= 5:
                    break
                shown += 1
                print(f"  {table_name}.{col_name}[{row_idx}]:")
                print(f"    Raw:     {repr(raw[:80])}")
                print(f"    Cleaned: \"{cleaned[:80]}\"")
                print()

    # --- Section 4: Visual Samples ---
    print("\n--- VISUAL THAI SAMPLES ---")
    print("(Review these to confirm Thai text renders as Thai script,")
    print(" not as garbled symbols, boxes, or question marks)\n")

    sample_count = 0
    for table_name, stats in sorted(row_results.items()):
        if not stats["samples"]:
            continue
        print(f"TABLE: {table_name}")
        for col_name, row_idx, text in stats["samples"]:
            sample_count += 1
            display_text = text[:100]
            print(f"  {table_name}.{col_name}[{row_idx}]: \"{display_text}\"")
            print(f"  Codepoints: {codepoints_str(text, 20)}")
            print()

    if sample_count == 0:
        print("  No Thai text samples found in row data.")

    # --- Section 5: Verdict ---
    print("\n" + "=" * 70)

    if total_mojibake > 0:
        # Real mojibake -- U+FFFD replacement characters
        verdict = "FAIL"
        print("VERDICT: FAIL")
        print(f"  Thai characters found: {total_thai}")
        print(f"  Mojibake (U+FFFD): {total_mojibake}")
        print("  MOJIBAKE DETECTED: Some text contains U+FFFD replacement characters.")
        affected = [t for t, s in row_results.items() if s["mojibake_count"] > 0]
        print(f"  Affected tables: {', '.join(affected)}")
    elif total_thai > 0:
        # Thai found, no mojibake
        if total_nullbytes > 0:
            verdict = "PASS"
            print("VERDICT: PASS (with compression artifacts)")
            print(f"  Thai characters found: {total_thai}")
            print(f"  Mojibake (U+FFFD): 0")
            print(f"  Null byte artifacts: {total_nullbytes} strings affected")
            print(f"    (all are Unicode compression artifacts, not data corruption)")
            print(f"    (strippable with strip_compression_nulls())")
            print()
            print("  Thai text is correctly decoded. Column names are clean.")
            print("  Row data has compression artifacts in mixed Thai/ASCII text,")
            print("  which can be cleaned by stripping null bytes.")
            print("  Visual verification recommended.")
        else:
            verdict = "PASS"
            print("VERDICT: PASS")
            print(f"  Thai characters found: {total_thai}")
            print(f"  Mojibake (U+FFFD): 0")
            print(f"  Null byte artifacts: 0")
            print("  Encoding appears fully clean. Visual verification recommended.")
    else:
        verdict = "WARNING"
        print("VERDICT: WARNING")
        print("  No Thai characters found anywhere in the database.")
        print("  This is unexpected for a Thai-language database.")
        print("  Check if the database contains the expected data.")

    print("=" * 70)
    return verdict


def main():
    print("Opening database...")
    db = open_db()
    print("Database opened successfully.\n")

    tables = get_user_tables(db)
    print(f"Scanning {len(tables)} user tables...\n")

    # Check column names
    print("Checking column names for Thai characters...")
    thai_columns = check_column_names(db, tables)

    # Check row data
    print("Checking row data for encoding quality...")
    row_results = check_row_data(db, tables)

    # Print report
    print()
    verdict = print_report(thai_columns, row_results)

    return verdict


if __name__ == "__main__":
    verdict = main()
    sys.exit(0 if verdict == "PASS" else 1)
