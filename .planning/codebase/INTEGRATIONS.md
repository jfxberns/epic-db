# External Integrations

**Analysis Date:** 2026-02-14

## APIs & External Services

**None detected**
- No external API integrations configured
- No SDK imports or third-party service clients
- Project scope: local data assessment only

## Data Storage

**Databases:**
- Microsoft Access (proprietary `.accdb` format)
  - Location: `data/epic_db.accdb`
  - Client: Access database engine (embedded in file)
  - Connection: File-based, no network connectivity

**File Storage:**
- Local filesystem only
- Data directory: `data/`

**Caching:**
- None configured

## Authentication & Identity

**Auth Provider:**
- None configured
- Access database has no documented password protection
- Single local user access assumed

## Monitoring & Observability

**Error Tracking:**
- None configured

**Logs:**
- None configured
- Access database transaction logs: file-based (automatic Access feature)

## CI/CD & Deployment

**Hosting:**
- Not applicable - Data assessment only
- File-based storage on local disk

**CI Pipeline:**
- None configured

## Environment Configuration

**Required env vars:**
- None detected
- No external service credentials required

**Secrets location:**
- Not applicable - No external services

## Webhooks & Callbacks

**Incoming:**
- None configured

**Outgoing:**
- None configured

## Data Relationships

**Access Database Contents (from documentation):**

**Tables (inferred from system description):**
- Customers (store information, ~1,000 records)
- Orders (~10,000 records)
- Products (8 records)
- Inventory tracking
- Pricing/Discount configurations

**Features in database:**
- Forms for customer order entry
- Reports (inventory status, etc.)
- Printing labels for shipments
- VBA formulas for ingredient mixing calculations
- Discount calculations with override capability
- Printable invoices

**Forms:**
- Multiple data entry forms (Thai-language interface)

**Reports:**
- Inventory status reports
- Order/invoice reports

## Legacy Dependencies

**VBA Modules:**
- Location: Embedded in `data/epic_db.accdb`
- Status: Not extracted
- Contains business logic for:
  - Ingredient formula calculations
  - Pricing and discount logic
  - Report generation
  - Label printing routines

## Migration Considerations

**Current Limitations:**
- Thai-only interface (owner cannot read)
- Single file database (no distributed processing)
- VBA code embedded (not externally version controlled)
- Non-standard format (Microsoft proprietary)

**Data Volume:**
- ~1,000 customers
- ~10,000 orders
- 8 products
- ~10MB total file size
- Suitable for migration to PostgreSQL, MySQL, or modern web framework backend

**No External Integrations to Replicate:**
- Assessment project contains no external API dependencies
- Future web application can be designed without legacy system constraints

---

*Integration audit: 2026-02-14*
