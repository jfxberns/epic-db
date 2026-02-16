# Business Process Flows

**Generated:** 2026-02-16
**Source:** Synthesized from query SQL, form catalogues, report catalogues, and table schemas
**Cross-references:** [Query Overview](../queries/_overview.md), [Form Catalogue](../forms/_overview.md), [Report Catalogue](../reports/_overview.md), [Relationships](../relationships.md)

## Overview

Epic Gear's Access database manages a fishing tackle wholesale/retail business with four core process flows:

1. **Order Management** -- two sales channels (shop/wholesale and retail) with distinct pricing
2. **Inventory Management** -- goods receipt, goods issue, and calculated stock levels
3. **Customer/Member Management** -- member registration, loyalty points accumulation and redemption
4. **Financial Reporting** -- tax invoices, bank transfers, sales tax reports

The system uses a shared order table (`รายละเอียดออเดอร์`) as the central hub, with the `ธนาคาร` (bank) field doubling as a payment status indicator.

---

## 1. Order Management Flow

### Overview

Orders are created through two separate form interfaces depending on the sales channel:

| Channel | Form | Pricing Query | Status |
|:--------|:-----|:--------------|:-------|
| Shop/Wholesale (ร้านค้า) | `frm_salesorder_fishingshop` | `qry สินค้าในแต่ละออเดอร์ร้านค้า` | CORRUPT -- not exported |
| Retail (ปลีก) | `frm_salesorder_retail` | `qry สินค้าในแต่ละออเดอร์ปลีก` | CORRUPT -- not exported |

Both forms are among the 4 corrupt VBA forms that could not be exported via SaveAsText. Their structure is inferred from subquery SQL, report record sources, and table relationships.

### Step-by-Step: Shop Order

1. **Order creation**: User opens `frm_salesorder_fishingshop`, enters order header fields into `รายละเอียดออเดอร์`:
   - `เลขที่ออเดอร์` (order number, AutoNumber primary key)
   - `รหัสร้านค้า` (shop code, FK to `ข้อมูลร้านค้า`)
   - `วันที่` (order date)
   - `ช่องทางสั่งซื้อ` (order channel: LINE, FACEBOOK, etc.)
   - `พนักงานรับออเดอร์` (staff who took the order)
   - `ส่วนลดท้ายบิล(%)` (bill-end discount percentage)

2. **Line item entry**: Subform `frm_stck_fishingshop` writes to `สินค้าในแต่ละออเดอร์`:
   - `สินค้า` (product name, FK to `สินค้า`)
   - `จำนวน` (quantity)
   - The subform also shows current stock via `qry สต็อคสินค้า` (Expr1 = current stock level)

3. **Pricing calculation**: `qry สินค้าในแต่ละออเดอร์ร้านค้า` computes:
   - Line price after shop discount: `[ราคา] - [ส่วนลดร้านค้า]`
   - Line total: `[ราคาหลังหักส่วนลดร้านค้า] * [จำนวน]`
   - After bill-end discount: `* (1 - ([ส่วนลดท้ายบิล(%)] / 100))`
   - Pre-VAT base: `[ราคาก่อนแวท] - [ส่วนลดร้านค้าก่อนแวท]`
   - VAT: `[ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล] * 0.07`
   - Net total: pre-VAT base after discounts + VAT

4. **Payment tracking**: `ธนาคาร` field in `รายละเอียดออเดอร์` acts as payment status:
   - `"กสิกร"` (Kasikorn Bank) = paid via bank transfer
   - `"ส่งของให้ก่อน"` = goods shipped before payment (credit)
   - `"รอโอน"` = awaiting payment transfer
   - `"เงินสด"` = cash payment

5. **Invoice generation**: `qryใส่เลขที่ใบกำกับ` and `qryกำหนดเลขที่inv` assign sequential invoice numbers (`เลขที่invoiceของปี`)

6. **Report printing**: From the shop order form, reports are opened using `[Forms]![frm_salesorder_fishingshop]![เลขที่ออเดอร์]` as filter:
   - `บิลร้านค้า` / `บิลร้านค้า1` / `บิลร้านค้า3` -- shop bill variants
   - `ใบกำกับภาษีร้านค้า` / `ใบกำกับภาษีร้านค้า(สำเนา)` -- tax invoices (original + copy)
   - `ใบส่งของร้านค้า` -- delivery note
   - `pdf แจ้งยอด` -- balance notification
   - `Copy of ใบกำกับภาษีร้านค้า` -- additional tax invoice copy

### Step-by-Step: Retail Order

1. **Order creation**: User opens `frm_salesorder_retail`, enters header into `รายละเอียดออเดอร์`:
   - `เบอร์โทรศัพท์` (phone number, FK to `ข้อมูลสมาชิก`)
   - Same date, channel, staff fields as shop orders

2. **Line item entry**: Subform `qry สินค้าในแต่ละออเดอร์ Subform1` writes to `สินค้าในแต่ละออเดอร์`
   - Stock subform `frm_stck_retail` shows current stock via `qry สต็อคสินค้าในแต่ละออเดอร์ปลีก`

3. **Pricing calculation**: `qry สินค้าในแต่ละออเดอร์ปลีก` computes (simpler than shop):
   - Line total: `[ราคา] * [จำนวน]`
   - Points earned: `[ราคารวม] / 100` (1 point per 100 baht)
   - Pre-VAT total: `[ราคาก่อนแวท] * [จำนวน]`
   - VAT: `[ราคารวมก่อนแวท] * 0.07`
   - Net total: pre-VAT + VAT

4. **Points display**: Subform `qry คะแนนรวมลูกค้าแต่ละคน subform` (embedded in order detail form `รายละเอียดออเดอร์`) shows the customer's accumulated points in real time

5. **Report printing**: Retail reports use `[Forms]![frm_salesorder_retail]![เลขที่ออเดอร์]`:
   - `บิลลูกค้าปลีก` -- retail bill
   - `ใบกำกับภาษีลูกค้าปลีก` / `ใบกำกับภาษีลูกค้าปลีก(สำเนา)` -- retail tax invoices

### Component Map: Order Management

```
Forms (entry)               Tables (storage)                  Queries (logic)                     Reports (output)
-----------------           ------------------                -----------------                   -----------------
frm_salesorder_fishingshop  รายละเอียดออเดอร์ (509 rows)       qry สินค้าในแต่ละออเดอร์ร้านค้า     บิลร้านค้า
  |- frm_stck_fishingshop   สินค้าในแต่ละออเดอร์ (7,073 rows)  qry ยอดขายร้านค้า                   ใบกำกับภาษีร้านค้า
                            ข้อมูลร้านค้า (735 rows)           qry ยอดซื้อร้านค้าทั้งปี             ใบกำกับภาษีร้านค้า(สำเนา)
                            สินค้า (186 rows)                  qryยอดเงินร้านค้า                   ใบส่งของร้านค้า
                                                               qry_ร้านค้ารอโอน                    pdf แจ้งยอด
                                                               qry_ร้านค้าส่งของให้ก่อน

frm_salesorder_retail       รายละเอียดออเดอร์ (shared)         qry สินค้าในแต่ละออเดอร์ปลีก         บิลลูกค้าปลีก
  |- frm_stck_retail        สินค้าในแต่ละออเดอร์ (shared)      qry ยอดขายลูกค้าปลีก                ใบกำกับภาษีลูกค้าปลีก
  |- qry สินค้าฯ Subform1   ข้อมูลสมาชิก (2,150 rows)         qry คะแนนรวมลูกค้าแต่ละคน           ใบกำกับภาษีลูกค้าปลีก(สำเนา)
                            สินค้า (shared)                   qry คะแนนคงเหลือหลังจากใช้แล้ว
```

---

## 2. Inventory Flow

### Overview

Inventory is tracked through three movement types: goods receipt (inbound), goods issue (outbound withdrawal), and sales (outbound via orders). Stock level is a calculated value, not a stored balance.

### Step-by-Step: Goods Receipt

1. **Receipt entry**: User opens `frm รับเข้าสินค้า` (goods receipt form):
   - Header data into `หัวใบรับเข้า` (165 rows):
     - `เลขที่ใบรับเข้า` (receipt number)
     - `วันที่รับเข้า` (receipt date)
     - `ผู้ผลิต หรือ พนักงานแพ็ค` (producer or packing staff)
     - `พนักงานตรวจเช็ค` (inspection staff)
     - `พนักงานบันทึกข้อมูล` (data entry staff)

2. **Line items**: Subform `สินค้าในแต่ละใบรับเข้า Subform` writes to `สินค้าในแต่ละใบรับเข้า` (514 rows):
   - `สินค้า` (product, FK to `สินค้า`)
   - `จำนวนรับเข้า` (quantity received)
   - `หมายเลขกล่อง` (box number)
   - `หน่วยนับ` (unit, looked up from `สินค้า`)

3. **Verification**: `qry เจาะจงเลขที่ใบรับเข้า` retrieves receipt details filtered by current form's receipt number (`[Forms]![frm รับเข้าสินค้า]![เลขที่ใบรับเข้า]`)

4. **Report**: `รายละเอียดใบรับเข้าสินค้า` prints the receipt document

### Step-by-Step: Goods Issue

1. **Issue entry**: User opens `frm เบิกสินค้า` (goods issue form):
   - Header data into `หัวใบเบิก` (3,391 rows):
     - `เลขที่ใบเบิก` (issue number)
     - `วันที่เบิก` (issue date)
     - `เหตุผลการเบิก` (reason for issue)
     - `พนักงานเบิก` (issuing staff)
     - `พนักงานตรวจเช็ค` (inspection staff)
     - `หมายเลขสมาชิกที่เบิก` / `รหัสร้านค้าที่เบิก` (member or shop receiving goods)

2. **Line items**: Subform `สินค้าในแต่ละใบเบิก Subform` writes to `สินค้าในแต่ละใบเบิก` (15,293 rows):
   - `สินค้า` (product)
   - `จำนวนเบิก` (quantity issued)
   - `หมายเหตุ` (notes)

3. **Verification**: `qry เจาะจงเลขที่ใบเบิก` retrieves issue details filtered by `[Forms]![frm เบิกสินค้า]![เลขที่ใบเบิก]`

4. **Reports**:
   - `ปรินท์ใบเบิกสินค้า` -- goods issue print document
   - `rptดูเลขทีใบเบิก` -- list of issue numbers
   - `rptทำที่อยู่เบิกสินค้า` -- address labels for shipment of issued goods

### Stock Level Calculation

The key query `qry สต็อคสินค้า` calculates current stock as:

```sql
Nz([SumOfจำนวนรับเข้า], 0) - Nz([SumOfจำนวน], 0) - Nz([SumOfจำนวนเบิก], 0)
```

**In English:** `Stock = Total Received - Total Sold - Total Issued`

This query combines three sub-queries:

| Sub-Query | Source Table | Aggregation |
|:----------|:------------|:------------|
| `qry จำนวนรับเข้ารวม ของสินค้าทุกตัว` | `สินค้าในแต่ละใบรับเข้า` | `Sum(จำนวนรับเข้า)` per product |
| `qry จำนวนที่ขายของสินค้าแต่ละตัว` | `สินค้าในแต่ละออเดอร์` | `Sum(จำนวน)` per product |
| `qry จำนวนเบิกรวม ของสินค้าทุกตัว` | `สินค้าในแต่ละใบเบิก` | `Sum(จำนวนเบิก)` per product |

The `Nz()` function handles products with no receipts, sales, or issues (returns 0 instead of NULL).

The stock form `frm_สต็อคสินค้า` (exported, 15 controls) displays this calculated stock level with product details and unit information.

### Combined Inventory Report

`qryรายงานสินค้าและวัตุดิบ` (UNION query) provides a chronological view of all inventory movements:

```
UNION ALL of:
  1. Goods receipts: product, date, receipt number, จำนวนรับเข้า, NULL, NULL
  2. Goods issues:   product, date, issue number,   NULL, จำนวนเบิก, NULL
  3. Sales:          product, date, order number,    NULL, NULL, จำนวนขาย
ORDER BY วันที่
```

This produces a single timeline of all stock movements per product, with `IIf(False, 0, Null)` as column placeholders to align the UNION columns.

### Component Map: Inventory

```
Forms (entry)           Tables (storage)                      Queries (logic)                       Reports (output)
--------------          ------------------                    -----------------                     -----------------
frm รับเข้าสินค้า       หัวใบรับเข้า (165 rows)                qry จำนวนรับเข้ารวม ของสินค้าทุกตัว    รายละเอียดใบรับเข้าสินค้า
  |- สินค้าในแต่ละใบ     สินค้าในแต่ละใบรับเข้า (514 rows)      qry เจาะจงเลขที่ใบรับเข้า
     รับเข้า Subform

frm เบิกสินค้า          หัวใบเบิก (3,391 rows)                 qry จำนวนเบิกรวม ของสินค้าทุกตัว       ปรินท์ใบเบิกสินค้า
  |- สินค้าในแต่ละใบ     สินค้าในแต่ละใบเบิก (15,293 rows)      qry เจาะจงเลขที่ใบเบิก                rptดูเลขทีใบเบิก
     เบิก Subform                                                                                    rptทำที่อยู่เบิกสินค้า

frm_สต็อคสินค้า         สินค้า (186 rows)                      qry สต็อคสินค้า                        (no dedicated report)
                                                              qry จำนวนที่ขายของสินค้าแต่ละตัว
                                                              qryรายงานสินค้าและวัตุดิบ (UNION)
```

---

## 3. Customer/Member Management Flow

### Overview

The system manages retail customers as "members" (`สมาชิก`) with a loyalty points program. Shop customers (`ร้านค้า`) are managed separately as business entities with different data fields.

### Retail Customer (Member) Registration

The form `frmข้อมูลสมาชิก` (not in exported set -- one of the 10 forms not exported due to Windows limitations, not VBA corruption) writes to `ข้อมูลสมาชิก` (2,150 rows):

| Field | Purpose |
|:------|:--------|
| `หมายเลขสมาชิก` | Member number (manually assigned) |
| `เบอร์โทรศัพท์` | Phone number (**primary key** -- used as member identifier) |
| `ชื่อ` / `นามสกุล` | First/last name |
| `ที่อยู่ล่าสุด` | Latest shipping address |
| `ชื่อไลน์หรือเฟซ` | LINE or Facebook contact name |
| `ชื่อออกใบกำกับปลีก` | Name for tax invoice |
| `เลขประจำตัวผู้เสียภาษีปลีก` | Tax ID for invoice |

**Notable design:** Phone number is the primary key, meaning customers are uniquely identified by phone. Orders are linked to customers via `รายละเอียดออเดอร์.เบอร์โทรศัพท์`.

### Shop Customer Registration

Shop data is in `ข้อมูลร้านค้า` (735 rows) with richer business fields:

| Field | Purpose |
|:------|:--------|
| `รหัสร้านค้า` | Shop code (primary key) |
| `ชื่อร้าน` | Shop name |
| `ที่อยู่` / `ที่อยู่สำหรับออกใบกำกับ` | Shipping / invoice addresses |
| `เบอร์โทรศัพท์ร้านค้า` / `เบอร์ร้าน` | Phone numbers |
| `ชื่อเฟส` / `ชื่อไลน์` | Social media contacts |
| `วันหยุด` | Shop holidays (for delivery planning) |
| `ขนส่งที่สะดวก` | Preferred shipping carrier |
| `ชื่อร้านสำหรับออกใบกำกับ` | Name for tax invoice |
| `เลขประจำตัวผู้เสียภาษีร้านค้า` | Tax ID |
| `สาขาสถานประกอบการ` / `สาขาสำนักงานใหญ่` | Branch office info |
| `หมายเหตุเฉพาะร้าน` | Shop-specific notes |
| `เอาบิลอะไร` | Which bill type the shop wants |
| `ช่องทางติดต่อที่สะดวก` | Preferred contact channel |

### Loyalty Points System

See [Pricing and Discounts](./pricing_discounts.md) for detailed points calculation formulas.

**Summary flow:**

1. Customer places retail order
2. `qry สินค้าในแต่ละออเดอร์ปลีก` calculates: `points = [ราคารวม] / 100`
3. `qry คะแนนรวมลูกค้าแต่ละคน` sums all points per member
4. Points are redeemed manually (3 fixed redemption slots in `ข้อมูลสมาชิก`)
5. `qry คะแนนคงเหลือหลังจากใช้แล้ว` shows remaining balance
6. Shown in real-time on retail order form via embedded subform

### Component Map: Customer Management

```
Forms (entry)            Tables (storage)              Queries (logic)                     Reports (output)
--------------           ------------------            -----------------                   -----------------
frmข้อมูลสมาชิก          ข้อมูลสมาชิก (2,150 rows)     qry คะแนนรวมลูกค้าแต่ละคน           (no dedicated report)
  (not exported)         คะแนนที่ลูกค้าใช้ไป (0 rows)  qry คะแนนคงเหลือหลังจากใช้แล้ว

หาเลขที่ออเดอร์ถ้ารู้     ข้อมูลร้านค้า (735 rows)      (lookup queries)                    ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า
ชื่อร้าน (lookup form)                                                                    ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก
                                                                                          ปริ้นท์ที่อยู่ลูกค้าปลีก

คะแนนคงเหลือหลังจาก     (reads ข้อมูลสมาชิก)           qry คะแนนคงเหลือหลังจากใช้แล้ว     (display-only form)
ใช้แล้ว (standalone)
```

---

## 4. Financial Reporting Flow

### Overview

Financial reporting covers bank transfers, sales tax reports, and invoice management. These are primarily read-only queries and reports that aggregate data from the order and product tables.

### Bank Transfer Tracking

Multiple queries track payment status:

| Query | Purpose | Filter |
|:------|:--------|:-------|
| `qry รายละเอียดการโอนเงินร้านค้า` | Shop transfer details with amounts | Bank = "กสิกร" or "ส่งของให้ก่อน", filtered by date range |
| `qry รายละเอียดการโอนแต่ละออเดอร์ปลีก` | Retail order transfer amounts | Order number range |
| `qry วันที่และเวลาโอนเงินเรียงตามใบกำกับ` | Transfer times sorted by invoice | Invoice number range, Bank = "กสิกร" |
| `qry_ร้านค้ารอโอน` | Shops with pending transfers | Bank = "รอโอน" (awaiting transfer) |
| `qry_ร้านค้าส่งของให้ก่อน` | Shops shipped before payment | Bank = "ส่งของให้ก่อน" (advance shipment) |
| `qryยอดเงินร้านค้า` | Shop payment amounts per order | (no date filter) |
| `qryลงยอดร้านค้า` | Post shop payment records | Bank = "ส่งของให้ก่อน" |

### Sales Tax Reporting

Two tax report record sources aggregate shop and retail pricing data together:

- `รายงานภาษีขาย` -- Sales tax report, grouped by order, filtered by invoice number range (`invเริ่มต้น` to `invสุดท้าย`)
- `ตรวจภาษีขายเรียงตามเลขinv` -- Sales tax verification sorted by invoice number (same structure, different invoice range prompt)

Both reports LEFT JOIN `qry สินค้าในแต่ละออเดอร์ร้านค้า` and `qry สินค้าในแต่ละออเดอร์ปลีก` to get both shop and retail totals per order, then GROUP BY order to produce per-order subtotals:

| Aggregated Field | Source |
|:-----------------|:-------|
| `SumOfราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล` | Shop: pre-VAT after all discounts |
| `SumOfภาษีมูลค่าเพิ่ม` | Shop VAT amount |
| `SumOfราคาสุทธิรวมภาษีมูลค่าเพิ่ม` | Shop net total incl. VAT |
| `SumOfราคารวมก่อนแวท` | Retail: pre-VAT total |
| `SumOfภาษีมูลค่าเพิ่มปลีก` | Retail VAT amount |
| `SumOfราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม` | Retail net total incl. VAT |

### Shipping and Address Reports

| Report | Data Source | Purpose |
|:-------|:-----------|:--------|
| `ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า` | `qry ที่อยู่เจาะจงโดยวันที่ (ร้านค้า)` | Shop tracking number notifications |
| `ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก` | `qry ที่อยู่เจาะจงโดยวันที่ (ปลีก)` | Retail tracking number notifications |
| `ปริ้นท์ที่อยู่ลูกค้าปลีก` | `qry ที่อยู่เจาะจงโดยวันที่ (ปลีก)` | Retail address labels |
| `rptทำที่อยู่เบิกสินค้า` | Direct SQL on `หัวใบเบิก` + `ข้อมูลร้านค้า` | Goods issue shipping labels |

The address queries accept order number range parameters (e.g., `[ใส่เลขที่ออเดอร์คนแรกที่จะดู]` to `[ใส่เลขที่ออเดอร์คนสุดท้ายที่จะดู]`), allowing batch printing of shipping labels for a range of orders.

### Invoice Number Management

Invoice numbers are managed through two queries:

1. `qryใส่เลขที่ใบกำกับ` -- Shows orders with their invoice numbers, filtered by bank type and date range, for manual invoice number assignment
2. `qryกำหนดเลขที่inv` -- Shows orders with their invoice numbers, filtered by invoice number range, for review/correction

The `รายละเอียดออเดอร์` table stores two invoice number fields:
- `เลขที่invoiceของแต่ละเดือน` (monthly invoice number, Integer)
- `เลขที่invoiceของปี` (yearly invoice number, Short Text like "6612-010")

### Component Map: Financial Reporting

```
Tables (data)                Queries (aggregation)                     Reports (output)
--------------               -----------------------                   -----------------
รายละเอียดออเดอร์             qry รายละเอียดการโอนเงินร้านค้า            รายงานภาษีขาย
ข้อมูลร้านค้า                 qry รายละเอียดการโอนแต่ละออเดอร์ปลีก       ตรวจภาษีขายเรียงตามเลขinv
ข้อมูลสมาชิก                  qry วันที่และเวลาโอนเงินเรียงตามใบกำกับ    rptรายละเอียดการโอนเงินฯ
qry สินค้าฯ ร้านค้า           qry_ร้านค้ารอโอน                          ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า
qry สินค้าฯ ปลีก              qry_ร้านค้าส่งของให้ก่อน                   ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก
                              qryใส่เลขที่ใบกำกับ                       ปริ้นท์ที่อยู่ลูกค้าปลีก
                              qryกำหนดเลขที่inv
```

---

## 5. Utility and Analytics Queries

Several queries serve analytical or utility purposes outside the main flows:

| Query | Purpose | Parameters |
|:------|:--------|:-----------|
| `qry_สินค้าที่ขายดีย้อนหลัง 3 เดือน` | Best-selling products in last 3 months | Uses `DateAdd("m", -3, Date())` |
| `จำนวนที่ขายของสินค้าแต่ละตัว(ระบุวันที่)` | Quantity sold per product by date and shop | Date range + shop name |
| `ดูจำนวนรวมสินค้าที่สั่งหลายออเดอร์รวมกัน` | Combined product quantities across multiple orders | Order number range |
| `qry ดูยอดซื้อร้านค้าแต่ละเจ้า` | Purchase totals per shop | Shop code |
| `qry ยอดซื้อร้านค้าทั้งปี` | Annual purchase totals per shop | (none) |
| `"ซอง";"ตัว";"เม็ด"` | Value list for product unit types | (none) |

---

## Gaps and Limitations

### Unexported Components

| Component | Reason | Impact on Documentation |
|:----------|:-------|:------------------------|
| `frm_salesorder_fishingshop` | Corrupt VBA | Order entry flow inferred from queries/reports |
| `frm_salesorder_retail` | Corrupt VBA | Same as above |
| `frm_stck_fishingshop` | Corrupt VBA | Stock subform structure inferred from subquery SQL |
| `qry stck subform2` | Corrupt VBA | Unknown purpose; no subquery SQL found |
| `frmข้อมูลสมาชิก` | Not exported (not in SaveAsText set) | Member form fields inferred from table schema |
| `หน้าหลัก` (Main Menu) | Not exported | Navigation structure unknown |
| 14 reports not exported | SaveAsText not run for all | Report structure inferred from subquery SQL |

### No VBA Code-Behind Found

All 7 exported forms and 11 exported reports have **zero VBA code-behind**. The 4 corrupt forms that could not be exported are the ones most likely to contain VBA code (they are the main data entry forms). This means:

- VBA-01 (code inventory): No VBA found in exported components
- VBA-05 (VBA complexity assessment): Cannot be assessed without the corrupt forms

### No Main Navigation Form

The `หน้าหลัก` (Main Menu) form exists in the database but was not in the Windows export set. Form-to-form navigation is inferred from subform nesting and query form references only.
