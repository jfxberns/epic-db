"""Extract cross-table data profiling and abandoned table analysis.

Produces assessment/data_profile.md with per-table column profiles,
fill rate analysis, relationship cross-reference, and abandoned table detection.
"""

from pathlib import Path

from tabulate import tabulate

from db_reader import (
    open_db,
    get_relationships,
    get_user_tables,
    parse_table,
    strip_null_bytes,
)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "assessment" / "data_profile.md"


def compute_column_profiles(data, max_sample_rows=1000):
    """Compute per-column fill rate, distinct count, and sample values.

    Args:
        data: dict of {col_name: [values...]} from parse_table
        max_sample_rows: max rows to scan for distinct value estimation

    Returns: dict of {col_name: {fill_rate, distinct_count, samples}}
    """
    if not data:
        return {}

    columns = list(data.keys())
    first_col_vals = data[columns[0]]
    row_count = len(first_col_vals)

    profiles = {}
    for col_name in columns:
        values = data[col_name]
        clean_name = strip_null_bytes(str(col_name))

        # Count non-null, non-empty values
        non_empty = 0
        for v in values:
            if v is None:
                continue
            if isinstance(v, bytes):
                non_empty += 1  # bytes count as non-empty
                continue
            s = str(v)
            if s not in ("", "None"):
                non_empty += 1

        fill_rate = non_empty / row_count if row_count > 0 else 0

        # Distinct value estimate from first N rows
        sample_slice = values[:max_sample_rows]
        distinct_set = set()
        for v in sample_slice:
            if v is None:
                distinct_set.add(None)
            elif isinstance(v, bytes):
                distinct_set.add(v)
            else:
                distinct_set.add(str(v))
        distinct_count = len(distinct_set)

        # Sample values (3 non-empty, truncated)
        samples = []
        for v in values:
            if v is None:
                continue
            if isinstance(v, bytes):
                samples.append("[Binary]")
            else:
                s = strip_null_bytes(str(v))
                if s and s != "None":
                    samples.append(s[:60] if len(s) > 60 else s)
            if len(samples) >= 3:
                break

        profiles[clean_name] = {
            "fill_rate": fill_rate,
            "distinct_count": distinct_count,
            "samples": samples,
        }

    return profiles


def compute_relationship_counts(relationships, user_tables):
    """Count incoming and outgoing relationships per table.

    Returns: dict of {table_name: {"in": N, "out": N}}
    """
    counts = {t: {"in": 0, "out": 0} for t in user_tables}

    for rel in relationships:
        src = rel["source_table"]
        ref = rel["ref_table"]

        if src in counts:
            counts[src]["out"] += 1
        if ref in counts:
            counts[ref]["in"] += 1

    return counts


def detect_abandoned_signals(row_count, avg_fill_rate, rel_count):
    """Detect abandoned table signals.

    Returns: list of signal strings
    """
    signals = []
    if row_count == 0:
        signals.append("ZERO_ROWS")
    if avg_fill_rate < 0.10 and row_count > 0:
        signals.append("VERY_LOW_FILL")
    if rel_count == 0:
        signals.append("NO_RELATIONSHIPS")
    return signals


def classify_status(signals):
    """Classify table status based on signal count."""
    if len(signals) >= 2:
        return "Likely Abandoned"
    elif len(signals) == 1:
        return "Review"
    else:
        return "Active"


def main():
    db = open_db()
    tables = get_user_tables(db)
    relationships = get_relationships(db)
    rel_counts = compute_relationship_counts(relationships, tables)

    # Profile each table
    all_profiles = {}
    table_summaries = []

    for table_name in tables:
        print(f"Profiling: {table_name}...", end=" ", flush=True)

        data = parse_table(db, table_name)
        if data:
            first_col = next(iter(data.values()))
            row_count = len(first_col)
        else:
            row_count = 0

        col_profiles = compute_column_profiles(data)
        all_profiles[table_name] = {
            "row_count": row_count,
            "column_count": len(col_profiles),
            "profiles": col_profiles,
        }

        # Compute average fill rate
        if col_profiles:
            fill_rates = [p["fill_rate"] for p in col_profiles.values()]
            avg_fill = sum(fill_rates) / len(fill_rates)
        else:
            avg_fill = 0

        all_profiles[table_name]["avg_fill_rate"] = avg_fill

        # Relationship info
        rc = rel_counts.get(table_name, {"in": 0, "out": 0})
        total_rels = rc["in"] + rc["out"]

        # Abandoned detection
        signals = detect_abandoned_signals(row_count, avg_fill, total_rels)
        status = classify_status(signals)
        all_profiles[table_name]["signals"] = signals
        all_profiles[table_name]["status"] = status
        all_profiles[table_name]["rel_in"] = rc["in"]
        all_profiles[table_name]["rel_out"] = rc["out"]

        table_summaries.append({
            "name": table_name,
            "rows": row_count,
            "cols": len(col_profiles),
            "avg_fill": avg_fill,
            "rel_display": f"{rc['in']} in / {rc['out']} out",
            "status": status,
        })

        print(f"({row_count} rows, avg fill {avg_fill:.0%})")

    # Calculate totals
    total_rows = sum(s["rows"] for s in table_summaries)

    # Build document
    doc_parts = []

    # Header
    doc_parts.append("# Data Profile Summary\n")

    # Overview table
    doc_parts.append("## Overview\n")
    overview_rows = []
    for s in table_summaries:
        overview_rows.append([
            s["name"],
            f"{s['rows']:,}",
            s["cols"],
            f"{s['avg_fill']:.0%}",
            s["rel_display"],
            s["status"],
        ])
    overview_headers = ["Table", "Rows", "Columns", "Avg Fill Rate", "Relationships", "Status"]
    doc_parts.append(tabulate(overview_rows, headers=overview_headers, tablefmt="pipe"))
    doc_parts.append(f"\nTotal: {total_rows:,} rows across {len(tables)} tables\n")

    # Abandoned Table Analysis
    doc_parts.append("## Abandoned Table Analysis\n")

    # Likely Abandoned
    doc_parts.append("### Likely Abandoned\n")
    abandoned_found = False
    for table_name in tables:
        info = all_profiles[table_name]
        if info["status"] == "Likely Abandoned":
            abandoned_found = True
            doc_parts.append(f"#### {table_name}\n")
            doc_parts.append(f"- **Signals:** {', '.join(info['signals'])}")

            # Build evidence
            evidence_parts = []
            if "ZERO_ROWS" in info["signals"]:
                evidence_parts.append("Table contains 0 rows")
            if "VERY_LOW_FILL" in info["signals"]:
                evidence_parts.append(f"Average fill rate is only {info['avg_fill_rate']:.0%}")
            if "NO_RELATIONSHIPS" in info["signals"]:
                evidence_parts.append("Table does not appear in any relationship (source or reference)")
            doc_parts.append(f"- **Evidence:** {'; '.join(evidence_parts)}")
            doc_parts.append(f"- **Recommendation:** Safe to exclude from rebuild -- empty table with no relationships\n")

    if not abandoned_found:
        doc_parts.append("No tables identified as likely abandoned.\n")

    # Under Review
    doc_parts.append("### Under Review\n")
    review_found = False
    for table_name in tables:
        info = all_profiles[table_name]
        if info["status"] == "Review":
            review_found = True
            signal = info["signals"][0]
            # Brief explanation
            if signal == "ZERO_ROWS":
                explanation = "0 rows but has relationship connections"
            elif signal == "VERY_LOW_FILL":
                explanation = f"Very low fill rate ({info['avg_fill_rate']:.0%}) despite having data"
            elif signal == "NO_RELATIONSHIPS":
                explanation = "Not referenced in any relationship but contains data"
            else:
                explanation = signal
            doc_parts.append(f"- **{table_name}**: {signal} -- {explanation}")

    if not review_found:
        doc_parts.append("No tables under review.\n")

    # Active Tables
    doc_parts.append("\n### Active Tables\n")
    doc_parts.append("All remaining tables show healthy data patterns (non-zero rows, relationships present, reasonable fill rates).\n")

    # Per-Table Column Profiles
    doc_parts.append("## Per-Table Column Profiles\n")
    for table_name in tables:
        info = all_profiles[table_name]
        doc_parts.append(f"### {table_name} ({info['row_count']:,} rows)\n")

        if not info["profiles"]:
            doc_parts.append("*(No column data available)*\n")
            continue

        profile_rows = []
        for col_name, profile in info["profiles"].items():
            samples_display = ", ".join(profile["samples"]) if profile["samples"] else "-"
            # Truncate combined samples to 80 chars
            if len(samples_display) > 80:
                samples_display = samples_display[:80] + "..."
            profile_rows.append([
                col_name,
                f"{profile['fill_rate']:.0%}",
                profile["distinct_count"],
                samples_display,
            ])
        profile_headers = ["Column", "Fill Rate", "Distinct Values", "Sample Values"]
        doc_parts.append(tabulate(profile_rows, headers=profile_headers, tablefmt="pipe"))
        doc_parts.append("")

    # Notes
    doc_parts.append("## Notes\n")
    doc_parts.append("- Fill rate = (non-null, non-empty values) / total rows")
    doc_parts.append("- Distinct values estimated from first 1000 rows where applicable")
    doc_parts.append("- \"Relationships\" count includes both incoming (referenced by other tables) and outgoing (references other tables)")
    doc_parts.append("- Abandoned detection uses multiple signals -- single-signal tables may still be active")
    doc_parts.append("")

    # Write output
    doc = "\n".join(doc_parts)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(doc, encoding="utf-8")
    print(f"\nWritten to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
