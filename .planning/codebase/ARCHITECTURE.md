# Architecture

**Analysis Date:** 2026-02-14

## Pattern Overview

**Overall:** Data Assessment & Documentation Pattern

**Key Characteristics:**
- Monolithic Microsoft Access database with embedded business logic
- Single-file architecture (`.accdb` binary database)
- Thai-language interface with embedded VBA modules
- Legacy system with low concurrency requirements (1-3 concurrent users)
- Assessment-focused structure: extracting and documenting existing system rather than new development

## Layers

**Data Layer:**
- Purpose: Persistent storage of all business data and forms
- Location: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb`
- Contains: Database tables, relationships, queries, forms, reports
- Depends on: Microsoft Access runtime (Windows platform dependency)
- Used by: All application logic, UI forms, reporting systems

**Business Logic Layer:**
- Purpose: VBA modules implementing pricing, discounts, formulas, calculations
- Location: Embedded within `epic_db.accdb` as VBA modules
- Contains: Formulas for ingredient mixing, discount calculations, pricing logic, validation rules
- Depends on: Data layer for table access
- Used by: Forms, reports, and automated calculations

**Presentation Layer:**
- Purpose: User interaction through Access forms and reports
- Location: Embedded forms and reports within `epic_db.accdb`
- Contains: Order entry forms, customer management forms, printable reports, shipping labels
- Depends on: Business logic layer and data layer
- Used by: End users (1-3 concurrent maximum)

**Assessment/Documentation Layer:**
- Purpose: Project documentation and system evaluation
- Location: `/Users/jb/Dev/epic_gear/epic-db/docs/`
- Contains: Overview documentation, feasibility analysis notes
- Depends on: Data layer analysis results
- Used by: Project stakeholders for rebuild decision

## Data Flow

**Order Processing Flow:**

1. End user opens order entry form in Access application
2. Form captures customer selection, product selection, quantities
3. VBA modules apply business rules: pricing lookup, discount calculation, total computation
4. Data written to Orders table with customer and product relationships
5. Query retrieves related invoice data from Orders/Customers/Products tables
6. Invoice report rendered and printed
7. Shipping label report generated with order data

**Inventory Management Flow:**

1. User accesses inventory forms
2. Product quantities updated in inventory tracking tables
3. Formula module calculates raw material requirements based on finished goods orders
4. Inventory status report queries current levels and flags low stock

**Report & Analytics Flow:**

1. User requests report (inventory status, order history, etc.)
2. Query retrieves filtered/aggregated data from multiple tables
3. Report layout applies formatting and calculations
4. Output to printer or screen

**State Management:**
- State maintained entirely within Access database tables
- No external state management
- Single file guarantees ACID properties at Access level
- No distributed state concerns (monolithic architecture)

## Key Abstractions

**Customer Database:**
- Purpose: Central registry of store/customer information
- Examples: Customers table in `epic_db.accdb`
- Pattern: Normalized table with one record per customer, containing contact and business information

**Product Catalog:**
- Purpose: Manage ~8 products with associated pricing
- Examples: Products table in `epic_db.accdb`
- Pattern: Master data table with one-to-many relationships to Orders and Inventory

**Orders & Invoicing:**
- Purpose: Track customer orders and generate printable invoices
- Examples: Orders table, line items relationships, Invoice reports in `epic_db.accdb`
- Pattern: Header-detail relationship with calculated totals and tax/discount application

**Pricing & Discounts:**
- Purpose: Apply volume discounts and customer-specific pricing overrides
- Examples: VBA pricing calculation modules, Discount tables in `epic_db.accdb`
- Pattern: Rule-based discount engine with override capability per customer

**Formulas & Recipes:**
- Purpose: Map finished products to raw material requirements
- Examples: Formula VBA modules in `epic_db.accdb`
- Pattern: Calculation modules executed during inventory planning

**Inventory Management:**
- Purpose: Track stock levels and raw material requirements
- Examples: Inventory tables, Formula calculation modules in `epic_db.accdb`
- Pattern: Periodic update via formulas based on order volume

## Entry Points

**End User Entry Point:**
- Location: `epic_db.accdb` - default startup form in Access application
- Triggers: User launches the Access application file
- Responsibilities: Present main menu, route to order entry, inventory, reporting, or admin functions

**Reporting Entry Point:**
- Location: Access Reports within `epic_db.accdb`
- Triggers: User selects report from menu
- Responsibilities: Query data, apply formatting, generate printable output (invoices, shipping labels, inventory reports)

**Form Entry Point (Order Processing):**
- Location: Order entry form within `epic_db.accdb`
- Triggers: User selects "New Order" from main menu
- Responsibilities: Capture order data, apply pricing/discounts via VBA modules, persist to Orders table

## Error Handling

**Strategy:** Basic validation at form level, limited error recovery

**Patterns:**
- Form-level validation on required fields using Access validation rules
- VBA error handling within pricing/discount modules (approach unclear - likely basic Try/Catch or subroutine guards)
- Data integrity via Access referential integrity constraints (foreign keys)
- No structured exception logging or retry mechanisms
- User-facing error messages via Access message boxes

## Cross-Cutting Concerns

**Logging:** Not detected - legacy Access application with no structured logging

**Validation:**
- Field-level validation rules in table/form definitions
- Required field constraints
- Referential integrity enforcement via foreign keys

**Authentication:**
- None detected - single workgroup environment, no user login required
- File-level access control only (Windows file permissions or Access database password - currently none)

---

*Architecture analysis: 2026-02-14*
