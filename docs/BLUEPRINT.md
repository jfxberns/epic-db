# Epic Gear (RipRoy) Database Rebuild Blueprint

> Complete specification for rebuilding the Access database as a modern application.
> Generated from epic_db.accdb assessment -- no need to reference the original file.

## Table of Contents

[Placeholder -- will be finalized in Plan 03]

## Executive Summary

Epic Gear (RipRoy) is a fishing lure manufacturing and distribution business based in Samut Prakan, Thailand. Their operations are managed through a single Microsoft Access 2010 database (`epic_db.accdb`) that has been in use for approximately 10 years.

**What the system does:**

The database manages the complete order-to-cash cycle for two sales channels -- wholesale (shop/fishing store) and retail (individual customers). It tracks products, orders with dual-channel pricing, inventory movements (goods receipt and goods issue), customer/member information with a loyalty points program, payment status, and tax invoicing. The system serves 1-3 concurrent users processing 10-50 orders per day.

**Scale:**

| Metric | Count |
|--------|-------|
| Tables | 10 |
| User queries | 33 |
| Hidden system queries | 29 |
| Forms | 17 (4 corrupt) |
| Reports | 25 (11 exported) |
| Products | 186 |
| Shop customers | 735 |
| Retail members | 2,150 |
| Orders | 509 |
| Order line items | 7,073 |
| Goods issue records | 15,293 |
| Total rows | ~30,000 |

**Key findings:**

- **Zero VBA code** -- all business logic is implemented in SQL query calculated columns (11 distinct formulas identified)
- **4 corrupt forms** -- the two main order entry forms (`frm_salesorder_fishingshop`, `frm_salesorder_retail`) and two stock subforms cannot be exported but are well-documented through their subquery SQL and report references
- **Calculated stock** -- inventory levels are never stored; stock is recalculated on every query as `received - sold - issued`
- **No referential integrity** -- all foreign key relationships use `NO_INTEGRITY`, allowing orphaned records
- **Bilingual requirement** -- all Thai terms have been mapped to English equivalents with Thai preserved for the bilingual UI rebuild
- **1 abandoned table** -- `customer_points_used` (0 rows, no relationships) can be excluded from rebuild

**Rebuild recommendation summary:**

The system's simplicity (zero VBA, all SQL logic, 10 tables) makes it an excellent candidate for a modern web application rebuild. The complete absence of VBA code means all business logic can be directly translated to application-layer SQL or ORM queries. Detailed rebuild assessment with technology recommendations and effort estimates is provided in a later section.

## Buddhist Era (BE) Date Convention

The Thai calendar uses Buddhist Era (BE), which is 543 years ahead of the Common Era (CE).

**Formula:** CE = BE - 543

**Example:** BE 2567 = CE 2024

All date values stored in the database use the standard `Date/Time` data type, which Access stores internally as CE. However, the Access UI displays dates in BE format per the system's Thai locale settings. Date values shown in this blueprint (from sample data extraction) are already converted to CE format. The rebuild should support both BE display (for Thai UI) and CE storage.

## Thai-English Glossary

This glossary is the single source of truth for all Thai-to-English translations used throughout this blueprint. Every subsequent section references these translations for consistency.

**Translation rules applied:**
- Business-equivalent translations (not literal)
- All translated names use `snake_case`
- Proper nouns transliterated only (e.g., RipRoy, Rattanaporn)
- Already-English names kept as-is (e.g., `frm_salesorder_fishingshop`, `ID`)
- Buddhist Era date values preserved as-is

### By Business Domain

#### Products

| Thai | English | Category | Notes |
|------|---------|----------|-------|
| สินค้า | products | table_name | Product master table; also used as column name (product name/FK) |
| รหัสสินค้า | product_code | column_name | Unique product identifier (e.g., POLLYLI'LRR30) |
| ราคา | price | column_name | Retail price, VAT-inclusive (baht) |
| ราคาก่อนแวท | pre_vat_price | column_name | Price before 7% VAT |
| ส่วนลดร้านค้า | shop_discount | column_name | Per-product shop discount amount (fixed baht, not %) |
| ส่วนลดร้านค้าก่อนแวท | shop_discount_pre_vat | column_name | Shop discount amount before VAT |
| ราคาร้านค้ารวมแวท | shop_price_incl_vat | column_name | Shop price including VAT (stored as Decimal) |
| หน่วยนับ | unit | column_name | Unit of measure (e.g., large_pack, KG, per_shipment) |
| ลำดับที่ | sequence_number | column_name | AutoNumber sort order |
| "ซอง";"ตัว";"เม็ด" | unit_value_list | query_name | Value list query for product unit types |
| qryรายงานสินค้าและวัตุดิบ | product_and_material_report | query_name | UNION query combining all inventory movements |
| ซองใหญ่ | large_pack | enum_value | Unit type: large pack/bag |
| ครั้ง | per_shipment | enum_value | Unit type: per shipment/occurrence |
| ตัว | piece | enum_value | Unit type: individual piece |
| เม็ด | bead | enum_value | Unit type: bead/pellet |
| ซอง | pack | enum_value | Unit type: pack/sachet |

#### Orders

| Thai | English | Category | Notes |
|------|---------|----------|-------|
| รายละเอียดออเดอร์ | order_details | table_name | Order header table (509 rows) |
| สินค้าในแต่ละออเดอร์ | order_line_items | table_name | Order line items (7,073 rows) |
| เลขที่ออเดอร์ | order_number | column_name | PK of order_details (AutoNumber) |
| เลขที่invoiceของแต่ละเดือน | monthly_invoice_number | column_name | Monthly sequential invoice number |
| เลขที่invoiceของปี | yearly_invoice_number | column_name | Yearly invoice code (e.g., 6612-010) |
| วันที่ | date | column_name | Order date |
| วันที่โอนเงิน | transfer_date | column_name | Bank transfer payment date |
| วันที่inv | invoice_date | column_name | Invoice issue date |
| เวลาโอนเงิน | transfer_time | column_name | Bank transfer time (stored as text, e.g., 14.35) |
| ช่องทางสั่งซื้อ | order_channel | column_name | How order was placed (LINE, FACEBOOK, etc.) |
| ธนาคาร | bank | column_name | Payment method / status enum field |
| พนักงานรับออเดอร์ | order_staff | column_name | Staff member who took the order |
| คะแนนคีย์เอง | manual_points_entry | column_name | Manually keyed points (order level) |
| หมายเหตุอื่นๆ | other_notes | column_name | Order-level miscellaneous notes |
| รหัสร้านค้า | shop_code | column_name | FK to shop_info (e.g., RT789) |
| ส่วนลดท้ายบิล(%) | bill_end_discount_percent | column_name | Bill-end discount as percentage (0-34%) |
| จำนวน | quantity | column_name | Order line item quantity |
| id | id | column_name | Already English -- AutoNumber PK of order_line_items |
| qry สินค้าในแต่ละออเดอร์ร้านค้า | shop_order_line_items | query_name | Shop order pricing with 2-tier discounts |
| qry สินค้าในแต่ละออเดอร์ปลีก | retail_order_line_items | query_name | Retail order pricing with points calculation |
| qry ยอดขายร้านค้า | shop_sales_totals | query_name | Shop sales totals by date range |
| qry ยอดขายลูกค้าปลีก | retail_sales_totals | query_name | Retail customer sales totals |
| qry เจาะจงหมายเลขออเดอร์ร้านค้า | shop_order_lookup | query_name | Look up specific shop order by number |
| qry เจาะจงหมายเลขออเดอร์ปลีก | retail_order_lookup | query_name | Look up specific retail order by number |
| qry_ร้านค้ารอโอน | shops_awaiting_transfer | query_name | Shops with pending bank transfers |
| qry_ร้านค้าส่งของให้ก่อน | shops_ship_before_payment | query_name | Shops receiving goods before payment |
| qry_สินค้าที่ขายดีย้อนหลัง 3 เดือน | best_sellers_last_3_months | query_name | Best-selling products over last 3 months |
| qry ดูยอดซื้อร้านค้าแต่ละเจ้า | shop_purchase_totals_per_vendor | query_name | Purchase totals per shop vendor |
| qry ยอดซื้อร้านค้าทั้งปี | shop_annual_purchase_totals | query_name | Annual shop purchase totals |
| qryยอดเงินร้านค้า | shop_payment_amounts | query_name | Shop payment amounts per order |
| ดูจำนวนรวมสินค้าที่สั่งหลายออเดอร์รวมกัน | combined_multi_order_quantities | query_name | Combined product quantities across multiple orders |
| จำนวนที่ขายของสินค้าแต่ละตัว(ระบุวันที่) | product_sales_by_date | query_name | Quantity sold per product filtered by date range |
| ราคาหลังหักส่วนลดร้านค้า | price_after_shop_discount | calculated_field | Unit price minus per-product shop discount |
| ราคารวมหลังหักส่วนลดร้านค้า | total_after_shop_discount | calculated_field | Line total after shop discount |
| ราคารวมหลังหักส่วนลดท้ายบิล | total_after_bill_end_discount | calculated_field | Line total after bill-end discount (VAT-inclusive) |
| ราคาก่อนแวทหลังหักส่วนลดร้านค้า | pre_vat_after_shop_discount | calculated_field | Pre-VAT unit price after shop discount |
| ราคารวมก่อนแวทหลังหักส่วนลดร้านค้า | total_pre_vat_after_shop_discount | calculated_field | Pre-VAT line total after shop discount |
| ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล | total_pre_vat_after_bill_end_discount | calculated_field | Pre-VAT total after all discounts |
| ภาษีมูลค่าเพิ่ม | vat | calculated_field | Value Added Tax amount (7%) -- shop channel |
| ราคาสุทธิรวมภาษีมูลค่าเพิ่ม | net_total_incl_vat | calculated_field | Net total including VAT -- shop channel |
| ราคารวม | line_total | calculated_field | Line total (price x quantity) -- retail |
| ราคารวมก่อนแวท | total_pre_vat | calculated_field | Pre-VAT line total -- retail |
| ภาษีมูลค่าเพิ่มปลีก | retail_vat | calculated_field | VAT amount -- retail channel |
| ราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม | retail_net_total_incl_vat | calculated_field | Net total including VAT -- retail |
| คะแนน | points | calculated_field | Loyalty points earned (line_total / 100) |
| SumOfราคารวมหลังหักส่วนลดร้านค้า | sum_total_after_shop_discount | calculated_field | Aggregate: sum of totals after shop discount |
| SumOfราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล | sum_pre_vat_after_bill_end_discount | calculated_field | Aggregate: sum of pre-VAT after all discounts |
| SumOfภาษีมูลค่าเพิ่ม | sum_vat | calculated_field | Aggregate: sum of shop VAT |
| SumOfราคาสุทธิรวมภาษีมูลค่าเพิ่ม | sum_net_total_incl_vat | calculated_field | Aggregate: sum of shop net total |
| SumOfราคารวม | sum_line_total | calculated_field | Aggregate: sum of retail line totals |
| SumOfราคารวมก่อนแวท | sum_pre_vat_total | calculated_field | Aggregate: sum of retail pre-VAT |
| SumOfภาษีมูลค่าเพิ่มปลีก | sum_retail_vat | calculated_field | Aggregate: sum of retail VAT |
| SumOfราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม | sum_retail_net_total_incl_vat | calculated_field | Aggregate: sum of retail net total |
| SumOfราคารวมหลังหักส่วนลดท้ายบิล | sum_total_after_bill_end_discount | calculated_field | Aggregate: sum of totals after bill-end discount |
| SumOfจำนวน | sum_quantity | calculated_field | Aggregate: total quantity sold |
| frm_salesorder_fishingshop | frm_salesorder_fishingshop | form_name | Already English -- Shop order entry form (CORRUPT) |
| frm_salesorder_retail | frm_salesorder_retail | form_name | Already English -- Retail order entry form (CORRUPT) |
| qry สินค้าในแต่ละออเดอร์ Subform | order_line_items_subform | form_name | Retail order line items subform |
| qry สินค้าในแต่ละออเดอร์ร้านค้า subform | shop_order_line_items_subform | form_name | Shop order line items subform |
| qry สินค้าในแต่ละออเดอร์ Subform1 | order_line_items_subform_1 | form_name | Retail order line items subform variant |
| หาเลขที่ออเดอร์ถ้ารู้ชื่อร้าน | order_lookup_by_shop_name | form_name | Order search by shop name |
| กสิกร | kasikorn_bank | enum_value | Payment: Kasikorn Bank transfer |
| รอโอน | awaiting_transfer | enum_value | Payment status: awaiting bank transfer |
| ส่งของให้ก่อน | ship_before_payment | enum_value | Payment status: goods shipped on credit |
| เงินสด | cash | enum_value | Payment: cash |
| LINE | LINE | enum_value | Already English -- order channel |
| FACEBOOK | FACEBOOK | enum_value | Already English -- order channel |
| อื่นๆ | other | enum_value | Order channel: other |
| บิลร้านค้า | shop_bill | report_name | Shop order bill |
| บิลลูกค้าปลีก | retail_customer_bill | report_name | Retail customer bill |
| ใบกำกับภาษีร้านค้า | shop_tax_invoice | report_name | Shop tax invoice (original) |
| ใบกำกับภาษีร้านค้า(สำเนา) | shop_tax_invoice_copy | report_name | Shop tax invoice (copy) |
| Copy of ใบกำกับภาษีร้านค้า | shop_tax_invoice_duplicate | report_name | Additional copy of shop tax invoice |
| ใบกำกับภาษีลูกค้าปลีก | retail_tax_invoice | report_name | Retail customer tax invoice (original) |
| ใบกำกับภาษีลูกค้าปลีก(สำเนา) | retail_tax_invoice_copy | report_name | Retail customer tax invoice (copy) |
| ใบส่งของร้านค้า | shop_delivery_note | report_name | Shop delivery/packing slip |
| ใบจัดสินค้าร้านค้า | shop_packing_list | report_name | Shop order packing list |
| ใบตรวจบิลร้านค้า | shop_bill_verification | report_name | Shop bill verification document |
| pdf แจ้งยอด | balance_notification_pdf | report_name | Balance notification (PDF format) |
| qry เจาะจงหมายเลขออเดอร์ subreport | order_detail_subreport | report_name | Order-specific detail subreport |
| วันที่เริ่มต้น | start_date | form_label | Parameter prompt: start date for date range filter |
| วันที่สุดท้าย | end_date | form_label | Parameter prompt: end date for date range filter |
| เลขที่ออเดอร์แรก | first_order_number | form_label | Parameter prompt: first order number in range |
| เลขที่ออเดอร์สุดท้าย | last_order_number | form_label | Parameter prompt: last order number in range |
| กรุณาระบุรหัสร้านค้า | please_enter_shop_code | form_label | Parameter prompt: enter shop code for lookup |
| invเริ่มต้น | inv_start | form_label | Parameter prompt: starting invoice number |
| invสุดท้าย | inv_end | form_label | Parameter prompt: ending invoice number |
| วันที่เปิดบิลเริ่มต้น | bill_start_date | form_label | Parameter prompt: bill opening start date |
| วันที่เปิดบิลสุดท้าย | bill_end_date | form_label | Parameter prompt: bill opening end date |
| วันที่ต้นเดือน | month_start_date | form_label | Parameter prompt: month start date |
| วันที่ท้ายเดือน | month_end_date | form_label | Parameter prompt: month end date |
| วันที่เริ่ม | date_start | form_label | Parameter prompt: date range start |
| วันที่จบ | date_end | form_label | Parameter prompt: date range end |

#### Inventory

| Thai | English | Category | Notes |
|------|---------|----------|-------|
| หัวใบรับเข้า | receipt_headers | table_name | Goods receipt header (165 rows) |
| สินค้าในแต่ละใบรับเข้า | receipt_line_items | table_name | Goods receipt line items (514 rows) |
| หัวใบเบิก | issue_headers | table_name | Goods issue/withdrawal header (3,391 rows) |
| สินค้าในแต่ละใบเบิก | issue_line_items | table_name | Goods issue line items (15,293 rows) |
| เลขที่ใบรับเข้า | receipt_number | column_name | PK of receipt_headers (AutoNumber) |
| เลขที่ใบรับเข้าของแต่ละเดือน | monthly_receipt_number | column_name | Monthly sequential receipt number |
| เลขที่ใบรับเข้าของปี | yearly_receipt_number | column_name | Yearly receipt identifier |
| วันที่รับเข้า | receipt_date | column_name | Date goods were received |
| ผู้ผลิต หรือ พนักงานแพ็ค | producer_or_packer | column_name | Producer name or packing staff |
| เลขที่ใบเบิก | issue_number | column_name | PK of issue_headers (AutoNumber) |
| วันที่เบิก | issue_date | column_name | Date goods were issued/withdrawn |
| เหตุผลการเบิก | issue_reason | column_name | Reason for goods withdrawal |
| พนักงานเบิก | issuing_staff | column_name | Staff who performed the issue |
| หมายเลขสมาชิกที่เบิก | issue_member_number | column_name | Member receiving issued goods |
| รหัสร้านค้าที่เบิก | issue_shop_code | column_name | Shop receiving issued goods |
| จำนวนรับเข้า | quantity_received | column_name | Quantity received in receipt line |
| หมายเลขกล่อง | box_number | column_name | Box/carton identifier |
| จำนวนเบิก | quantity_issued | column_name | Quantity issued/withdrawn |
| ID | ID | column_name | Already English -- AutoNumber PK of line item tables |
| หมายเหตุ | notes | column_name | General notes field (used in multiple tables) |
| SumOfจำนวนรับเข้า | sum_quantity_received | calculated_field | Aggregate: total quantity received per product |
| SumOfจำนวนเบิก | sum_quantity_issued | calculated_field | Aggregate: total quantity issued per product |
| จำนวนขาย | quantity_sold | calculated_field | Alias used in UNION query for sales quantity |
| เลขที่ใบสำคัญ | document_number | calculated_field | Alias used in UNION query for receipt/issue/order number |
| qry สต็อคสินค้า | product_stock | query_name | Current stock levels (received - sold - issued) |
| qry สต็อคสินค้าในแต่ละออเดอร์ปลีก | retail_order_stock | query_name | Stock levels for products in retail orders |
| qry จำนวนรับเข้ารวม ของสินค้าทุกตัว | total_received_all_products | query_name | Total quantity received per product |
| qry จำนวนเบิกรวม ของสินค้าทุกตัว | total_issued_all_products | query_name | Total quantity issued per product |
| qry จำนวนที่ขายของสินค้าแต่ละตัว | total_sold_per_product | query_name | Total quantity sold per product |
| qry เจาะจงเลขที่ใบรับเข้า | receipt_lookup | query_name | Look up specific goods receipt |
| qry เจาะจงเลขที่ใบเบิก | issue_lookup | query_name | Look up specific goods issue |
| frm รับเข้าสินค้า | goods_receipt_form | form_name | Goods receipt entry form |
| frm เบิกสินค้า | goods_issue_form | form_name | Goods issue/withdrawal form |
| frm_สต็อคสินค้า | product_stock_form | form_name | Stock level display form |
| frm_stck_fishingshop | frm_stck_fishingshop | form_name | Already English -- Shop stock subform (CORRUPT) |
| qry stck subform2 | qry stck subform2 | form_name | Already English -- Stock subform variant (CORRUPT) |
| สินค้าในแต่ละใบรับเข้า Subform | receipt_line_items_subform | form_name | Receipt line items subform |
| สินค้าในแต่ละใบเบิก Subform | issue_line_items_subform | form_name | Issue line items subform |
| ปรินท์ใบเบิกสินค้า | print_goods_issue | report_name | Print goods issue document |
| rptดูเลขทีใบเบิก | view_issue_numbers | report_name | View goods issue number listing |
| rptทำที่อยู่เบิกสินค้า | issue_address_labels | report_name | Address labels for goods issue shipments |
| รายละเอียดใบรับเข้าสินค้า | goods_receipt_details | report_name | Goods receipt detail report |

#### Customers

| Thai | English | Category | Notes |
|------|---------|----------|-------|
| ข้อมูลร้านค้า | shop_info | table_name | Shop/wholesale customer master (735 rows) |
| ข้อมูลสมาชิก | member_info | table_name | Retail customer/member master (2,150 rows) |
| คะแนนที่ลูกค้าใช้ไป | customer_points_used | table_name | Abandoned points usage table (0 rows) |
| รหัสร้านค้าออโต้ | shop_auto_id | column_name | AutoNumber surrogate key for shops |
| ชื่อร้าน | shop_name | column_name | Shop/store name |
| เบอร์โทรศัพท์ร้านค้า | shop_phone | column_name | Shop primary phone number |
| เบอร์โทรศัพท์2(มือถือ) | mobile_phone_2 | column_name | Shop secondary mobile phone |
| เบอร์ร้าน | store_phone | column_name | Shop landline phone |
| ช่องทางติดต่อที่สะดวก | preferred_contact_channel | column_name | Preferred method of contact |
| ชื่อเฟส | facebook_name | column_name | Facebook profile name |
| เฟซบุค แมสเซนเจอร์ | facebook_messenger | column_name | Facebook Messenger contact |
| ชื่อไลน์ | line_name | column_name | LINE messaging app name |
| วันหยุด | holidays | column_name | Shop closed days (for delivery planning) |
| ขนส่งที่สะดวก | preferred_carrier | column_name | Preferred shipping carrier |
| ที่อยู่ | address | column_name | Shipping address |
| หมายเหตุเฉพาะร้าน | shop_specific_notes | column_name | Notes specific to this shop |
| ชื่อร้านสำหรับออกใบกำกับ | invoice_shop_name | column_name | Shop name for tax invoice |
| ที่อยู่สำหรับออกใบกำกับ | invoice_address | column_name | Address for tax invoice |
| เลขประจำตัวผู้เสียภาษีร้านค้า | shop_tax_id | column_name | Shop tax identification number |
| สาขาสำนักงานใหญ่ | head_office_branch | column_name | Head office branch number |
| สาขาสถานประกอบการ | business_branch | column_name | Business establishment branch |
| ได้สติกเกอร์ใหญ่แล้ว | received_large_sticker | column_name | Whether shop received promotional large sticker |
| วันที่สร้างข้อมูล | record_created_date | column_name | Date the shop record was created |
| เอาบิลอะไร | bill_type_preference | column_name | Which bill type the shop wants |
| ถามเรื่องบิลแวทยัง | vat_bill_asked | column_name | Whether shop has been asked about VAT billing |
| ส่งของก่อนหรือโอนเงินก่อน | ship_or_pay_first | column_name | Shop's payment terms preference |
| หมายเลขออโต้ | member_auto_id | column_name | AutoNumber surrogate key for members |
| หมายเลขสมาชิก | member_number | column_name | Member number (manually assigned) |
| ชื่อ | first_name | column_name | Customer first name |
| นามสกุล | last_name | column_name | Customer last name |
| เบอร์โทรศัพท์ | phone_number | column_name | Phone number (PK for members, FK in orders) |
| ชื่อไลน์หรือเฟซ | line_or_facebook_name | column_name | LINE or Facebook contact name |
| ที่อยู่ล่าสุด | latest_address | column_name | Most recent shipping address |
| เลขประจำตัวผู้เสียภาษีปลีก | retail_tax_id | column_name | Retail customer tax ID |
| ได้สติกเกอร์หรือยัง | received_sticker | column_name | Whether member received promotional sticker |
| คะแนนรวม | total_points | column_name | Total accumulated points (stored, possibly redundant) |
| คะแนนคีย์มือเพิ่มให้ | manual_bonus_points | column_name | Points manually added by staff |
| คะแนนที่ใช้ครั้งที่1 | points_redeemed_1 | column_name | First redemption amount |
| คะแนนที่ใช้ครั้งที่2 | points_redeemed_2 | column_name | Second redemption amount |
| คะแนนที่ใช้ครั้งที่3 | points_redeemed_3 | column_name | Third redemption amount |
| ชื่อออกใบกำกับปลีก | retail_invoice_name | column_name | Name for retail tax invoice |
| คะแนนที่ใช้ครั้งที่ 1 | points_used_1 | column_name | Abandoned table: first redemption slot |
| คะแนนที่ใช้ครั้งที่ 2 | points_used_2 | column_name | Abandoned table: second redemption slot |
| คะแนนที่ใช้ครั้งที่ 3 | points_used_3 | column_name | Abandoned table: third redemption slot |
| คะแนนที่ใช้ครั้งที่ 4 | points_used_4 | column_name | Abandoned table: fourth redemption slot |
| คะแนนที่ใช้ครั้งที่ 5 | points_used_5 | column_name | Abandoned table: fifth redemption slot |
| SumOfคะแนน | sum_points | calculated_field | Aggregate: total points earned per member |
| qry คะแนนรวมลูกค้าแต่ละคน | customer_total_points | query_name | Sum total loyalty points per customer |
| qry คะแนนคงเหลือหลังจากใช้แล้ว | remaining_points_after_use | query_name | Remaining points after redemptions |
| qry ที่อยู่เจาะจงโดยวันที่ (ปลีก) | retail_addresses_by_date | query_name | Retail addresses filtered by order date range |
| qry ที่อยู่เจาะจงโดยวันที่ (ร้านค้า) | shop_addresses_by_date | query_name | Shop addresses filtered by order date range |
| frmข้อมูลสมาชิก | member_info_form | form_name | Member registration form (not exported) |
| คะแนนคงเหลือหลังจากใช้แล้ว | remaining_points_form | form_name | Remaining points display form |
| qry คะแนนรวมลูกค้าแต่ละคน subform | customer_points_subform | form_name | Points display subform |
| หน้าหลัก | main_menu | form_name | Main navigation menu form (not exported) |
| ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า | shop_tracking_notification | report_name | Shop shipping tracking notification |
| ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก | retail_tracking_notification | report_name | Retail shipping tracking notification |
| ปริ้นท์ที่อยู่ลูกค้าปลีก | print_retail_addresses | report_name | Print retail customer address labels |
| ปริ้นท์ที่อยู่ | print_addresses | report_name | Print addresses (general) |
| โทรศัพท์ | telephone | enum_value | Preferred contact: telephone |
| เปิดทุกวัน | open_every_day | enum_value | Shop holiday: open daily |
| ปิดวันอาทิตย์ | closed_sunday | enum_value | Shop holiday: closed Sundays |
| เคอรี่และไปรษณีย์ไทย | kerry_and_thailand_post | enum_value | Carrier: Kerry Express and Thailand Post |
| ใบกำกับภาษี | tax_invoice | enum_value | Bill type: tax invoice |
| บิลธรรมดา | regular_bill | enum_value | Bill type: regular bill |
| ถามแล้ว | already_asked | enum_value | VAT billing: already asked |
| โอนเงินก่อนเท่านั้น | transfer_first_only | enum_value | Payment terms: transfer before shipping only |
| สด | cash_or_individual | enum_value | Invoice name value: cash sale / individual |
| ใส่เลขที่ออเดอร์คนแรกที่จะดู | enter_first_order_to_view | form_label | Parameter prompt for retail address query |
| ใส่เลขที่ออเดอร์คนสุดท้ายที่จะดู | enter_last_order_to_view | form_label | Parameter prompt for retail address query |
| ใส่เลขที่ออเดอร์ร้านแรก | enter_first_shop_order | form_label | Parameter prompt for shop address query |
| ใส่เลขที่ออเดอร์ร้านสุดท้าย | enter_last_shop_order | form_label | Parameter prompt for shop address query |

#### Financial

| Thai | English | Category | Notes |
|------|---------|----------|-------|
| qry รายละเอียดการโอนเงินร้านค้า | shop_transfer_details | query_name | Shop bank transfer details with amounts |
| qry รายละเอียดการโอนแต่ละออเดอร์ปลีก | retail_order_transfer_details | query_name | Retail order bank transfer details |
| qry วันที่และเวลาโอนเงินเรียงตามใบกำกับ | transfer_datetime_by_invoice | query_name | Transfer date/time sorted by invoice number |
| qryกำหนดเลขที่inv | assign_invoice_number | query_name | Assign invoice number sequence |
| qryใส่เลขที่ใบกำกับ | enter_tax_invoice_number | query_name | Enter tax invoice numbers for orders |
| qryลงยอดร้านค้า | post_shop_payments | query_name | Post shop payment records |
| รายงานภาษีขาย | sales_tax_report | report_name | Sales tax summary report |
| ตรวจภาษีขาย | sales_tax_verification | report_name | Sales tax verification report |
| ตรวจภาษีขายเรียงตามเลขinv | sales_tax_verification_by_inv | report_name | Sales tax verification sorted by invoice number |
| รายละเอียดการโอน | transfer_details | report_name | Bank transfer details report |
| rptรายละเอียดการโอนเงินของแต่ละเลขที่ออเดอร์ | transfer_details_per_order | report_name | Bank transfer details per order number |
| พนักงานตรวจเช็ค | inspection_staff | column_name | Staff who performed inspection/verification |
| พนักงานบันทึกข้อมูล | data_entry_staff | column_name | Staff who entered data into the system |
| พนักงานตรวจการบันทึกข้อมูล | data_entry_reviewer | column_name | Staff who reviewed the data entry |
| รายละเอียดเพิ่มเติม | additional_details | column_name | Additional details / supplementary notes |

#### Proper Nouns (Transliterations)

| Thai | English | Category | Notes |
|------|---------|----------|-------|
| ริปรอย | RipRoy | proper_noun | Company brand name (Epic Gear) |
| รัตนาพร | Rattanaporn | proper_noun | Staff name -- appears as order_staff, issuing_staff, etc. |
| จันทกานต์ | Chantakan | proper_noun | Staff name |
| อรุณี | Arunee | proper_noun | Staff name |
| วันเพ็ญ | Wanpen | proper_noun | Staff name |
| คุณต้าร์ทองเหลือง | Khun Tar Thonglueang | proper_noun | Producer/packer name |
