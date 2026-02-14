# Codebase Concerns

**Analysis Date:** 2026-02-14

## Tech Debt

**Legacy Microsoft Access Database:**
- Issue: System built by non-programmer; opaque business logic embedded in VBA modules, queries, and forms with no external documentation
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (15MB)
- Impact: Difficult to modify safely without breaking functionality; no version control on database objects; impossible to review changes systematically; high risk of data corruption if modified incorrectly
- Fix approach: Complete extraction and documentation of all database components (tables, relationships, queries, forms, VBA modules) before any modifications. Extract business logic to exportable format (SQL, Python, or JavaScript). Build reproducible schema and stored procedures.

**Thai-Language Interface Only:**
- Issue: Database interface is entirely in Thai; owner cannot read Thai labels, field names, or form instructions
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all forms and UI elements)
- Impact: Owner cannot audit data directly; modifications require intermediary; workflow changes are blocked; auditing is impossible
- Fix approach: Map all Thai labels to English equivalents. Document field purposes and UI flow in English. Create bilingual interface in any rebuilt system.

**No Database Password/Access Control:**
- Issue: Single 10MB `.accdb` file with no password protection and no external dependencies
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb`
- Impact: Anyone with file access can modify or delete database without authentication; no audit trail of who changed what; no concurrent user conflict resolution
- Fix approach: Implement role-based access control (RBAC) in any replacement system. Add user authentication. Enable transaction logging.

**Single-File Architecture with No Backup Strategy:**
- Issue: Entire business database is a single `.accdb` file; loss or corruption catastrophic
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb`
- Impact: One file corruption = total data loss; no versioning; concurrent write conflicts with multiple users; no point-in-time recovery
- Fix approach: Migrate to server-based database (PostgreSQL, MySQL, SQL Server). Implement automated backups with versioning. Set up transaction logs.

## Known Bugs

**Concurrent Access Conflicts:**
- Symptoms: Potential data corruption or loss when 2-3 concurrent users edit the same tables simultaneously
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all tables, especially Orders and Inventory)
- Trigger: Two users modifying inventory or placing orders at same time
- Workaround: Enforce serial access (one user at a time) or implement file-level locking

**Thai Character Encoding Issues:**
- Symptoms: Data loss or display corruption when exporting/importing; potential issues with non-Thai systems
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all character fields, especially customer and product names)
- Trigger: Export to CSV/Excel; import on non-Thai system; data sync across systems
- Workaround: Ensure UTF-8 encoding on all imports/exports; validate character data after migration

**Formula Dependencies Not Documented:**
- Symptoms: Calculated fields may fail if underlying fields are modified or deleted
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (forms with embedded formulas, ingredient mixing formulas)
- Trigger: Renaming fields; modifying pricing structure; changing discount calculation logic
- Workaround: Before any schema changes, audit all VBA modules and form formulas for dependencies

## Security Considerations

**Unencrypted Sensitive Business Data:**
- Risk: Customer information, pricing, discounts, and order history stored in plain-text `.accdb` file
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb`
- Current mitigation: Physical file security only; no encryption
- Recommendations: Encrypt database at rest. Implement row-level security for multi-user systems. Use HTTPS for any web replacement. Add authentication and authorization controls.

**SQL Injection Risk in Queries:**
- Risk: If VBA code constructs queries dynamically with user input, potential for SQL injection attacks
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all VBA modules with queries)
- Current mitigation: Access database somewhat isolated (no direct network exposure); single-file architecture limits attack surface
- Recommendations: Audit all VBA code for dynamic query construction. Extract business logic to server-side code with parameterized queries. Remove any form-based SQL input fields.

**No Audit Trail:**
- Risk: Cannot track who modified data, when, or what changed
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all tables)
- Current mitigation: None
- Recommendations: Implement audit logging in any replacement system. Track user, timestamp, field, old value, new value for all changes.

**Backup File Access:**
- Risk: No documented backup strategy; if backups exist, they are likely as unencrypted copies
- Files: Unknown location (not in repository)
- Current mitigation: None identified
- Recommendations: Establish secure backup strategy with encryption, off-site storage, and retention policy.

## Performance Bottlenecks

**Large Dataset Queries on Single File:**
- Problem: Database scales to ~10,000 orders and ~1,000 customers; all data in single `.accdb` file; queries may be slow on large result sets
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (Orders and Inventory tables likely)
- Cause: Access database designed for single-user, small-scale use; no indexing strategy documented; file I/O on local machine
- Improvement path: Migrate to server-based database with query optimization, indexing, and connection pooling. Add caching layer for frequently accessed reports.

**No Query Optimization:**
- Problem: Reports may be slow during peak business hours (10-50 orders/day)
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all report queries)
- Cause: Access reports may have unoptimized joins or full table scans
- Improvement path: Audit report queries. Add database indexes. Consider materialized views for summary reports. Profile query performance.

**Export/Import Overhead:**
- Problem: Any data extraction or backup requires file I/O; slow for 15MB+ file
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb`
- Cause: Single-file architecture; no streaming or incremental backup
- Improvement path: Implement server-based replication or log-based backups. Use incremental snapshots.

## Fragile Areas

**VBA Module Dependencies:**
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all VBA modules - not yet extracted)
- Why fragile: Business logic embedded in VBA; interdependencies between modules, forms, and queries unknown; non-programmer code likely lacks error handling; changes in one module can break unrelated functionality
- Safe modification: Extract all VBA code to external files for version control. Document module dependencies. Write tests before modifying any module. Validate all affected forms and reports after changes.
- Test coverage: Gaps - no unit tests; no regression test suite for Access forms and reports

**Pricing and Discount Logic:**
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (Pricing table, Discount calculations, override formulas)
- Why fragile: Discount override logic suggests complex pricing rules; if embedded in forms or queries, changes risk incorrect invoicing or revenue loss
- Safe modification: Extract pricing rules to configuration and code. Write tests for all pricing scenarios. Validate invoices before marking orders shipped.
- Test coverage: Gaps - no tests for discount calculations; no regression tests for pricing changes

**Customer and Inventory Data Consistency:**
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (Customer, Product, Inventory tables)
- Why fragile: Many-to-many relationships (customers to products, products to orders); no documented foreign key constraints in Access; cascading deletes or updates could orphan data
- Safe modification: Before any schema changes, audit referential integrity constraints. Add explicit foreign key validation. Document all relationships.
- Test coverage: Gaps - no tests for referential integrity; no data validation tests

**Shipping Label Generation:**
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (Reports for shipping labels, possibly VBA code)
- Why fragile: Shipping labels likely depend on specific data formats (addresses in Thai); changes to address format or data structure break label output
- Safe modification: Extract label generation logic. Test with real addresses. Validate output format before deployment.
- Test coverage: Gaps - no tests for label formatting; no tests with real Thai address data

## Scaling Limits

**Concurrent User Limitations:**
- Current capacity: 1-3 concurrent users
- Limit: Access file locking breaks after ~5 concurrent users; more than 3 creates risk of data corruption
- Scaling path: Migrate to client-server architecture (web app, API, database). Implement connection pooling. Add load balancing if needed.

**Data Volume Capacity:**
- Current capacity: ~1,000 customers, ~10,000 orders, 8 products, 15MB file
- Limit: Single Access file becomes unstable above 50MB; queries slow above 100,000 records in a single table
- Scaling path: Migrate to server database. Implement archiving for old orders. Add indexing and partitioning for large tables.

**Report Generation Performance:**
- Current capacity: Runs on local machine; reports generate in seconds for current data volume
- Limit: Multi-page reports slow above 1,000 records; concurrent report generation blocks other users
- Scaling path: Move reports to web interface with async generation. Use server-side query optimization. Implement caching.

**Network Availability:**
- Current capacity: File stored locally or on shared drive for 1-3 users
- Limit: Network latency becomes significant above 10 users; file corruption risk increases with network unreliability
- Scaling path: Deploy web application on reliable server. Use database replication for high availability.

## Dependencies at Risk

**Microsoft Access Runtime:**
- Risk: Requires Windows OS and Microsoft Access or Access Runtime; not available on macOS or Linux; licensing costs for multiple machines
- Impact: Blocks cross-platform migration; new users must have Windows machine with Access; cost scales with user count
- Migration plan: Rebuild as web application (React/Vue frontend, Node/Python/Java backend, PostgreSQL database). No runtime dependencies beyond modern browser and server.

**Thai Language Support:**
- Risk: Requires Thai character encoding and fonts on all client machines; issues with data migration to non-Thai systems
- Impact: Blocks cross-platform deployment; limits integration with external systems; data export/import risks character loss
- Migration plan: Ensure UTF-8 support throughout stack. Extract all Thai labels to translation/localization system. Test data integrity across character encodings.

**VBA as Business Logic Transport:**
- Risk: VBA is proprietary to Microsoft; difficult to version control, test, or migrate; expertise rare
- Impact: Knowledge transfer difficult; code review impossible; migration to other platforms requires complete rewrite
- Migration plan: Extract all VBA business logic to Python, JavaScript, or other portable language. Create comprehensive tests. Document algorithms.

## Missing Critical Features

**No User Authentication:**
- Problem: No login system; anyone with file access can view and modify all data
- Blocks: Multi-user systems; role-based access control; audit trails; secure data sharing

**No Audit Logging:**
- Problem: Cannot track who changed what data, when, or why
- Blocks: Compliance audits; fraud detection; data recovery; debugging issues

**No API or Integration:**
- Problem: Database is file-only; cannot integrate with other systems (accounting software, shipping APIs, etc.)
- Blocks: Automated order fulfillment; shipping integration; accounting system sync; external reporting

**No Mobile Access:**
- Problem: Database requires Windows machine with Access; not accessible on mobile devices or tablets
- Blocks: Field sales; warehouse mobile apps; remote order entry

**No Real-Time Collaboration:**
- Problem: File locking prevents concurrent edits; multiple users create conflicts
- Blocks: Team collaboration; simultaneous order entry; real-time inventory updates

## Test Coverage Gaps

**No Database Schema Tests:**
- What's not tested: Table creation, column types, primary/foreign keys, indexes, constraints
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (not yet documented)
- Risk: Schema changes (field renames, type changes) may break dependent VBA code or forms silently
- Priority: High

**No Business Logic Tests:**
- What's not tested: Pricing calculations, discount logic, inventory tracking, order processing
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (VBA modules with business logic)
- Risk: Pricing errors result in revenue loss; discount bugs create inconsistent pricing; inventory bugs cause stockouts or overselling
- Priority: High

**No Form Validation Tests:**
- What's not tested: Form input validation, error messages, field constraints
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all forms)
- Risk: Invalid data enters database; corrupts reports; breaks downstream calculations
- Priority: Medium

**No Report Accuracy Tests:**
- What's not tested: Report calculations, totals, grouping, formatting
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all reports including shipping labels, invoices, inventory reports)
- Risk: Invoices show wrong totals; shipping labels have incorrect data; inventory reports are unreliable
- Priority: High

**No Data Migration Tests:**
- What's not tested: Export/import consistency, character encoding, data type conversion
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (during any extraction or migration)
- Risk: Data loss or corruption during migration; Thai characters corrupted; relationships broken
- Priority: High

**No Concurrent Access Tests:**
- What's not tested: Multiple users editing simultaneously; locking behavior; conflict resolution
- Files: `/Users/jb/Dev/epic_gear/epic-db/data/epic_db.accdb` (all shared tables)
- Risk: Silent data loss when concurrent users modify same records; corrupt state not detected until later
- Priority: High

---

*Concerns audit: 2026-02-14*
