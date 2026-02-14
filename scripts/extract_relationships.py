"""Extract relationships from epic_db.accdb and produce assessment/relationships.md.

Reads MSysRelationships via db_reader.get_relationships(), classifies them
into table-to-table, table-to-query, and system categories, and writes a
formatted markdown document with integrity flag explanations.
"""

from pathlib import Path

from tabulate import tabulate

from db_reader import get_relationships, get_user_tables, open_db, strip_null_bytes

ASSESSMENT_DIR = Path(__file__).resolve().parent.parent / "assessment"


def classify_relationships(rels: list[dict], user_tables: list[str]) -> dict:
    """Classify relationships into table-to-table, table-to-query, and system.

    Args:
        rels: list of relationship dicts from get_relationships()
        user_tables: list of user table names

    Returns: dict with keys 'table_to_table', 'table_to_query', 'system',
             each containing a list of relationship dicts.
    """
    user_table_set = set(user_tables)

    classified = {
        "table_to_table": [],
        "table_to_query": [],
        "system": [],
    }

    for rel in rels:
        name = rel["name"]

        # System relationships (MSysNavPane*)
        if name.startswith("MSysNavPane"):
            classified["system"].append(rel)
            continue

        source = rel["source_table"]
        ref = rel["ref_table"]

        # Both sides are user tables -> table-to-table
        if source in user_table_set and ref in user_table_set:
            classified["table_to_table"].append(rel)
        else:
            # One or both sides reference a query -> table-to-query
            classified["table_to_query"].append(rel)

    return classified


def format_integrity_flags(rel: dict) -> str:
    """Format integrity flags as a human-readable string."""
    flags = []
    if rel["enforce_ri"]:
        flags.append("ENFORCE_RI")
    if rel["cascade_updates"]:
        flags.append("CASCADE_UPDATES")
    if rel["cascade_deletes"]:
        flags.append("CASCADE_DELETES")
    if rel["no_integrity"]:
        flags.append("NO_INTEGRITY")

    grbit = rel["grbit"]
    if grbit & 0x1000:
        flags.append("INHERITED")
    if grbit & 0x2000000:
        flags.append("QUERY_BASED")

    if not flags:
        if grbit == 0:
            return "None (UI lookup only)"
        return f"grbit={grbit}"

    return ", ".join(flags)


def format_integrity_detail(rel: dict) -> str:
    """Format a detailed integrity explanation for one relationship."""
    parts = []
    parts.append(
        f'"{rel["name"]}": {rel["source_table"]}.{rel["source_column"]} '
        f'-> {rel["ref_table"]}.{rel["ref_column"]}'
    )

    flags_desc = []
    if rel["enforce_ri"]:
        flags_desc.append("Referential integrity enforced")
    if rel["cascade_updates"]:
        flags_desc.append("Cascade updates on PK change")
    if rel["cascade_deletes"]:
        flags_desc.append("Cascade deletes on PK removal")
    if rel["no_integrity"]:
        flags_desc.append("No integrity check (orphans allowed)")
    if rel["grbit"] & 0x2000000:
        flags_desc.append("Query-based (resolved via query definition)")

    if rel["grbit"] == 0:
        flags_desc.append("UI lookup only (no integrity constraints)")

    return " -- ".join(parts) + " -- " + "; ".join(flags_desc)


def generate_markdown(classified: dict, total_count: int) -> str:
    """Generate the complete relationships.md content."""
    t2t = classified["table_to_table"]
    t2q = classified["table_to_query"]
    sys_rels = classified["system"]

    lines = []
    lines.append("# Database Relationships")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- {total_count} total relationships in MSysRelationships")
    lines.append(
        f"- {len(t2t)} table-to-table relationships (user-defined foreign keys)"
    )
    lines.append(f"- {len(t2q)} table-to-query relationships (lookup/derived)")
    lines.append(f"- {len(sys_rels)} system relationships (excluded from analysis)")
    lines.append("")

    # --- Table-to-Table Relationships ---
    lines.append("## Table-to-Table Relationships")
    lines.append("")

    if t2t:
        t2t_rows = []
        for rel in t2t:
            t2t_rows.append(
                [
                    rel["name"],
                    rel["source_table"],
                    rel["source_column"],
                    rel["ref_table"],
                    rel["ref_column"],
                    format_integrity_flags(rel),
                ]
            )
        lines.append(
            tabulate(
                t2t_rows,
                headers=[
                    "Relationship Name",
                    "Source Table",
                    "Source Column",
                    "Referenced Table",
                    "Referenced Column",
                    "Integrity",
                ],
                tablefmt="pipe",
            )
        )
        lines.append("")

        # Referential Integrity Detail
        lines.append("### Referential Integrity Detail")
        lines.append("")
        for rel in t2t:
            lines.append(f"- {format_integrity_detail(rel)}")
        lines.append("")
    else:
        lines.append("No table-to-table relationships found.")
        lines.append("")

    # --- Table-to-Query Relationships ---
    lines.append("## Table-to-Query Relationships")
    lines.append("")

    if t2q:
        t2q_rows = []
        for rel in t2q:
            t2q_rows.append(
                [
                    rel["name"],
                    rel["source_table"],
                    rel["source_column"],
                    rel["ref_table"],
                    rel["ref_column"],
                    format_integrity_flags(rel),
                ]
            )
        lines.append(
            tabulate(
                t2q_rows,
                headers=[
                    "Relationship Name",
                    "Source",
                    "Source Column",
                    "Referenced Query/Table",
                    "Referenced Column",
                    "Flags",
                ],
                tablefmt="pipe",
            )
        )
        lines.append("")
        lines.append(
            "Note: These relationships reference queries rather than tables "
            "directly. The actual table dependencies are resolved through "
            "the query definitions (Phase 3)."
        )
        lines.append("")
    else:
        lines.append("No table-to-query relationships found.")
        lines.append("")

    # --- System Relationships ---
    lines.append("## System Relationships")
    lines.append("")
    if sys_rels:
        sys_names = [rel["name"] for rel in sys_rels]
        lines.append(f"Excluded: {', '.join(sys_names)}")
    else:
        lines.append("None found.")
    lines.append("")

    # --- Notes ---
    lines.append("## Notes")
    lines.append("")
    lines.append(
        "- grbit=0 means no referential integrity enforced "
        "(relationship exists for UI lookup purposes only)"
    )
    lines.append(
        "- Relationships flagged NO_INTEGRITY (0x100) allow orphaned records"
    )
    lines.append(
        "- QUERY_BASED (0x2000000) relationships depend on query "
        "definitions for resolution"
    )
    lines.append(
        "- CASCADE_UPDATES propagates primary key changes to foreign key columns"
    )
    lines.append(
        "- CASCADE_DELETES removes child records when parent record is deleted"
    )
    lines.append(
        "- Default values and validation rules are stored in field property "
        "blobs (not extractable on macOS -- deferred to Phase 3 Windows "
        "extraction if needed)"
    )
    lines.append("")

    return "\n".join(lines)


def main():
    """Main entry point: extract relationships and write assessment document."""
    print("Opening database...")
    db = open_db()

    print("Reading relationships from MSysRelationships...")
    rels = get_relationships(db)
    print(f"  Found {len(rels)} total relationships")

    print("Getting user table list for classification...")
    user_tables = get_user_tables(db)
    print(f"  {len(user_tables)} user tables")

    print("Classifying relationships...")
    classified = classify_relationships(rels, user_tables)
    print(f"  Table-to-table: {len(classified['table_to_table'])}")
    print(f"  Table-to-query: {len(classified['table_to_query'])}")
    print(f"  System: {len(classified['system'])}")

    print("Generating markdown...")
    md = generate_markdown(classified, len(rels))

    output_path = ASSESSMENT_DIR / "relationships.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(md, encoding="utf-8")
    print(f"Written to: {output_path}")
    print("Done.")


if __name__ == "__main__":
    main()
