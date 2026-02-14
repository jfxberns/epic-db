# Technology Stack

**Analysis Date:** 2026-02-14

## Languages

**Primary:**
- Not applicable - Data assessment project, no custom source code

**Secondary:**
- Python 3.11 - Virtual environment established for potential future tooling
- VBA - Legacy code embedded in Microsoft Access database (not extracted)

## Runtime

**Environment:**
- Python 3.11.12 (via uv - universal virtualenv manager)
- Virtual environment: `.venv/`

**Package Manager:**
- uv 0.10.0 - Modern Python package manager
- No dependencies installed (baseline environment only)

## Frameworks

**Database:**
- Microsoft Access 2007+ (`.accdb` binary format)

**Build/Dev:**
- None configured

## Key Dependencies

**Critical:**
- None installed - Project is data-only assessment

**Infrastructure:**
- None configured

## Configuration

**Environment:**
- Virtual environment at `/Users/jb/Dev/epic_gear/epic-db/.venv/`
- Python version pinned: 3.11.12
- No `.env` configuration detected
- No external API keys or database connection strings configured

**Build:**
- None configured

## Platform Requirements

**Development:**
- Python 3.11.12 (macOS arm64)
- Microsoft Access or compatible database tool for `epic_db.accdb` inspection
- macOS/Darwin operating system

**Production:**
- Not applicable - Assessment project only
- Data file: `epic_db.accdb` (~10MB)

## Data Files

**Primary Data Asset:**
- Location: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb`
- Type: Microsoft Access Database
- Size: ~10MB
- Content: Legacy RipRoy (Epic Gear) business data including customers, inventory, orders, formulas, pricing, reports

## Project Scope

**Purpose:** Assessment and documentation of existing Access database prior to potential web application migration

**Current System Characteristics:**
- Single-file database (no external integrations)
- Thai-language interface
- 1-3 concurrent users maximum
- No version control on database file
- No backup automation configured

---

*Stack analysis: 2026-02-14*
