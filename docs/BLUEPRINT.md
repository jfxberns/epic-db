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


### English Alphabetical Index

| English | Thai | Domain | Category |
|---------|------|--------|----------|
| additional_details | รายละเอียดเพิ่มเติม | Financial | column_name |
| address | ที่อยู่ | Customers | column_name |
| already_asked | ถามแล้ว | Customers | enum_value |
| Arunee | อรุณี | Proper Nouns | proper_noun |
| assign_invoice_number | qryกำหนดเลขที่inv | Financial | query_name |
| awaiting_transfer | รอโอน | Orders | enum_value |
| balance_notification_pdf | pdf แจ้งยอด | Orders | report_name |
| bank | ธนาคาร | Orders | column_name |
| bead | เม็ด | Products | enum_value |
| best_sellers_last_3_months | qry_สินค้าที่ขายดีย้อนหลัง 3 เดือน | Orders | query_name |
| bill_end_date | วันที่เปิดบิลสุดท้าย | Orders | form_label |
| bill_end_discount_percent | ส่วนลดท้ายบิล(%) | Orders | column_name |
| bill_start_date | วันที่เปิดบิลเริ่มต้น | Orders | form_label |
| bill_type_preference | เอาบิลอะไร | Customers | column_name |
| box_number | หมายเลขกล่อง | Inventory | column_name |
| business_branch | สาขาสถานประกอบการ | Customers | column_name |
| cash | เงินสด | Orders | enum_value |
| cash_or_individual | สด | Customers | enum_value |
| Chantakan | จันทกานต์ | Proper Nouns | proper_noun |
| closed_sunday | ปิดวันอาทิตย์ | Customers | enum_value |
| combined_multi_order_quantities | ดูจำนวนรวมสินค้าที่สั่งหลายออเดอร์รวมกัน | Orders | query_name |
| customer_points_subform | qry คะแนนรวมลูกค้าแต่ละคน subform | Customers | form_name |
| customer_points_used | คะแนนที่ลูกค้าใช้ไป | Customers | table_name |
| customer_total_points | qry คะแนนรวมลูกค้าแต่ละคน | Customers | query_name |
| data_entry_reviewer | พนักงานตรวจการบันทึกข้อมูล | Financial | column_name |
| data_entry_staff | พนักงานบันทึกข้อมูล | Financial | column_name |
| date | วันที่ | Orders | column_name |
| date_end | วันที่จบ | Orders | form_label |
| date_start | วันที่เริ่ม | Orders | form_label |
| document_number | เลขที่ใบสำคัญ | Inventory | calculated_field |
| end_date | วันที่สุดท้าย | Orders | form_label |
| enter_first_order_to_view | ใส่เลขที่ออเดอร์คนแรกที่จะดู | Customers | form_label |
| enter_first_shop_order | ใส่เลขที่ออเดอร์ร้านแรก | Customers | form_label |
| enter_last_order_to_view | ใส่เลขที่ออเดอร์คนสุดท้ายที่จะดู | Customers | form_label |
| enter_last_shop_order | ใส่เลขที่ออเดอร์ร้านสุดท้าย | Customers | form_label |
| enter_tax_invoice_number | qryใส่เลขที่ใบกำกับ | Financial | query_name |
| FACEBOOK | FACEBOOK | Orders | enum_value |
| facebook_messenger | เฟซบุค แมสเซนเจอร์ | Customers | column_name |
| facebook_name | ชื่อเฟส | Customers | column_name |
| first_name | ชื่อ | Customers | column_name |
| first_order_number | เลขที่ออเดอร์แรก | Orders | form_label |
| frm_salesorder_fishingshop | frm_salesorder_fishingshop | Orders | form_name |
| frm_salesorder_retail | frm_salesorder_retail | Orders | form_name |
| frm_stck_fishingshop | frm_stck_fishingshop | Inventory | form_name |
| goods_issue_form | frm เบิกสินค้า | Inventory | form_name |
| goods_receipt_details | รายละเอียดใบรับเข้าสินค้า | Inventory | report_name |
| goods_receipt_form | frm รับเข้าสินค้า | Inventory | form_name |
| head_office_branch | สาขาสำนักงานใหญ่ | Customers | column_name |
| holidays | วันหยุด | Customers | column_name |
| id | id | Orders | column_name |
| ID | ID | Inventory | column_name |
| inspection_staff | พนักงานตรวจเช็ค | Financial | column_name |
| inv_end | invสุดท้าย | Orders | form_label |
| inv_start | invเริ่มต้น | Orders | form_label |
| invoice_address | ที่อยู่สำหรับออกใบกำกับ | Customers | column_name |
| invoice_date | วันที่inv | Orders | column_name |
| invoice_shop_name | ชื่อร้านสำหรับออกใบกำกับ | Customers | column_name |
| issue_address_labels | rptทำที่อยู่เบิกสินค้า | Inventory | report_name |
| issue_date | วันที่เบิก | Inventory | column_name |
| issue_headers | หัวใบเบิก | Inventory | table_name |
| issue_line_items | สินค้าในแต่ละใบเบิก | Inventory | table_name |
| issue_line_items_subform | สินค้าในแต่ละใบเบิก Subform | Inventory | form_name |
| issue_lookup | qry เจาะจงเลขที่ใบเบิก | Inventory | query_name |
| issue_member_number | หมายเลขสมาชิกที่เบิก | Inventory | column_name |
| issue_number | เลขที่ใบเบิก | Inventory | column_name |
| issue_reason | เหตุผลการเบิก | Inventory | column_name |
| issue_shop_code | รหัสร้านค้าที่เบิก | Inventory | column_name |
| issuing_staff | พนักงานเบิก | Inventory | column_name |
| kasikorn_bank | กสิกร | Orders | enum_value |
| kerry_and_thailand_post | เคอรี่และไปรษณีย์ไทย | Customers | enum_value |
| Khun Tar Thonglueang | คุณต้าร์ทองเหลือง | Proper Nouns | proper_noun |
| large_pack | ซองใหญ่ | Products | enum_value |
| last_name | นามสกุล | Customers | column_name |
| last_order_number | เลขที่ออเดอร์สุดท้าย | Orders | form_label |
| latest_address | ที่อยู่ล่าสุด | Customers | column_name |
| LINE | LINE | Orders | enum_value |
| line_name | ชื่อไลน์ | Customers | column_name |
| line_or_facebook_name | ชื่อไลน์หรือเฟซ | Customers | column_name |
| line_total | ราคารวม | Orders | calculated_field |
| main_menu | หน้าหลัก | Customers | form_name |
| manual_bonus_points | คะแนนคีย์มือเพิ่มให้ | Customers | column_name |
| manual_points_entry | คะแนนคีย์เอง | Orders | column_name |
| member_auto_id | หมายเลขออโต้ | Customers | column_name |
| member_info | ข้อมูลสมาชิก | Customers | table_name |
| member_info_form | frmข้อมูลสมาชิก | Customers | form_name |
| member_number | หมายเลขสมาชิก | Customers | column_name |
| mobile_phone_2 | เบอร์โทรศัพท์2(มือถือ) | Customers | column_name |
| month_end_date | วันที่ท้ายเดือน | Orders | form_label |
| month_start_date | วันที่ต้นเดือน | Orders | form_label |
| monthly_invoice_number | เลขที่invoiceของแต่ละเดือน | Orders | column_name |
| monthly_receipt_number | เลขที่ใบรับเข้าของแต่ละเดือน | Inventory | column_name |
| net_total_incl_vat | ราคาสุทธิรวมภาษีมูลค่าเพิ่ม | Orders | calculated_field |
| notes | หมายเหตุ | Inventory | column_name |
| open_every_day | เปิดทุกวัน | Customers | enum_value |
| order_channel | ช่องทางสั่งซื้อ | Orders | column_name |
| order_detail_subreport | qry เจาะจงหมายเลขออเดอร์ subreport | Orders | report_name |
| order_details | รายละเอียดออเดอร์ | Orders | table_name |
| order_line_items | สินค้าในแต่ละออเดอร์ | Orders | table_name |
| order_line_items_subform | qry สินค้าในแต่ละออเดอร์ Subform | Orders | form_name |
| order_line_items_subform_1 | qry สินค้าในแต่ละออเดอร์ Subform1 | Orders | form_name |
| order_lookup_by_shop_name | หาเลขที่ออเดอร์ถ้ารู้ชื่อร้าน | Orders | form_name |
| order_number | เลขที่ออเดอร์ | Orders | column_name |
| order_staff | พนักงานรับออเดอร์ | Orders | column_name |
| other | อื่นๆ | Orders | enum_value |
| other_notes | หมายเหตุอื่นๆ | Orders | column_name |
| pack | ซอง | Products | enum_value |
| per_shipment | ครั้ง | Products | enum_value |
| phone_number | เบอร์โทรศัพท์ | Customers | column_name |
| piece | ตัว | Products | enum_value |
| please_enter_shop_code | กรุณาระบุรหัสร้านค้า | Orders | form_label |
| points | คะแนน | Orders | calculated_field |
| points_redeemed_1 | คะแนนที่ใช้ครั้งที่1 | Customers | column_name |
| points_redeemed_2 | คะแนนที่ใช้ครั้งที่2 | Customers | column_name |
| points_redeemed_3 | คะแนนที่ใช้ครั้งที่3 | Customers | column_name |
| points_used_1 | คะแนนที่ใช้ครั้งที่ 1 | Customers | column_name |
| points_used_2 | คะแนนที่ใช้ครั้งที่ 2 | Customers | column_name |
| points_used_3 | คะแนนที่ใช้ครั้งที่ 3 | Customers | column_name |
| points_used_4 | คะแนนที่ใช้ครั้งที่ 4 | Customers | column_name |
| points_used_5 | คะแนนที่ใช้ครั้งที่ 5 | Customers | column_name |
| post_shop_payments | qryลงยอดร้านค้า | Financial | query_name |
| pre_vat_after_shop_discount | ราคาก่อนแวทหลังหักส่วนลดร้านค้า | Orders | calculated_field |
| pre_vat_price | ราคาก่อนแวท | Products | column_name |
| preferred_carrier | ขนส่งที่สะดวก | Customers | column_name |
| preferred_contact_channel | ช่องทางติดต่อที่สะดวก | Customers | column_name |
| price | ราคา | Products | column_name |
| price_after_shop_discount | ราคาหลังหักส่วนลดร้านค้า | Orders | calculated_field |
| print_addresses | ปริ้นท์ที่อยู่ | Customers | report_name |
| print_goods_issue | ปรินท์ใบเบิกสินค้า | Inventory | report_name |
| print_retail_addresses | ปริ้นท์ที่อยู่ลูกค้าปลีก | Customers | report_name |
| producer_or_packer | ผู้ผลิต หรือ พนักงานแพ็ค | Inventory | column_name |
| product_and_material_report | qryรายงานสินค้าและวัตุดิบ | Products | query_name |
| product_code | รหัสสินค้า | Products | column_name |
| product_sales_by_date | จำนวนที่ขายของสินค้าแต่ละตัว(ระบุวันที่) | Orders | query_name |
| product_stock | qry สต็อคสินค้า | Inventory | query_name |
| product_stock_form | frm_สต็อคสินค้า | Inventory | form_name |
| products | สินค้า | Products | table_name |
| qry stck subform2 | qry stck subform2 | Inventory | form_name |
| quantity | จำนวน | Orders | column_name |
| quantity_issued | จำนวนเบิก | Inventory | column_name |
| quantity_received | จำนวนรับเข้า | Inventory | column_name |
| quantity_sold | จำนวนขาย | Inventory | calculated_field |
| Rattanaporn | รัตนาพร | Proper Nouns | proper_noun |
| receipt_date | วันที่รับเข้า | Inventory | column_name |
| receipt_headers | หัวใบรับเข้า | Inventory | table_name |
| receipt_line_items | สินค้าในแต่ละใบรับเข้า | Inventory | table_name |
| receipt_line_items_subform | สินค้าในแต่ละใบรับเข้า Subform | Inventory | form_name |
| receipt_lookup | qry เจาะจงเลขที่ใบรับเข้า | Inventory | query_name |
| receipt_number | เลขที่ใบรับเข้า | Inventory | column_name |
| received_large_sticker | ได้สติกเกอร์ใหญ่แล้ว | Customers | column_name |
| received_sticker | ได้สติกเกอร์หรือยัง | Customers | column_name |
| record_created_date | วันที่สร้างข้อมูล | Customers | column_name |
| regular_bill | บิลธรรมดา | Customers | enum_value |
| remaining_points_after_use | qry คะแนนคงเหลือหลังจากใช้แล้ว | Customers | query_name |
| remaining_points_form | คะแนนคงเหลือหลังจากใช้แล้ว | Customers | form_name |
| retail_addresses_by_date | qry ที่อยู่เจาะจงโดยวันที่ (ปลีก) | Customers | query_name |
| retail_customer_bill | บิลลูกค้าปลีก | Orders | report_name |
| retail_invoice_name | ชื่อออกใบกำกับปลีก | Customers | column_name |
| retail_net_total_incl_vat | ราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม | Orders | calculated_field |
| retail_order_line_items | qry สินค้าในแต่ละออเดอร์ปลีก | Orders | query_name |
| retail_order_lookup | qry เจาะจงหมายเลขออเดอร์ปลีก | Orders | query_name |
| retail_order_stock | qry สต็อคสินค้าในแต่ละออเดอร์ปลีก | Inventory | query_name |
| retail_order_transfer_details | qry รายละเอียดการโอนแต่ละออเดอร์ปลีก | Financial | query_name |
| retail_sales_totals | qry ยอดขายลูกค้าปลีก | Orders | query_name |
| retail_tax_id | เลขประจำตัวผู้เสียภาษีปลีก | Customers | column_name |
| retail_tax_invoice | ใบกำกับภาษีลูกค้าปลีก | Orders | report_name |
| retail_tax_invoice_copy | ใบกำกับภาษีลูกค้าปลีก(สำเนา) | Orders | report_name |
| retail_tracking_notification | ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก | Customers | report_name |
| retail_vat | ภาษีมูลค่าเพิ่มปลีก | Orders | calculated_field |
| RipRoy | ริปรอย | Proper Nouns | proper_noun |
| sales_tax_report | รายงานภาษีขาย | Financial | report_name |
| sales_tax_verification | ตรวจภาษีขาย | Financial | report_name |
| sales_tax_verification_by_inv | ตรวจภาษีขายเรียงตามเลขinv | Financial | report_name |
| sequence_number | ลำดับที่ | Products | column_name |
| ship_before_payment | ส่งของให้ก่อน | Orders | enum_value |
| ship_or_pay_first | ส่งของก่อนหรือโอนเงินก่อน | Customers | column_name |
| shop_addresses_by_date | qry ที่อยู่เจาะจงโดยวันที่ (ร้านค้า) | Customers | query_name |
| shop_annual_purchase_totals | qry ยอดซื้อร้านค้าทั้งปี | Orders | query_name |
| shop_auto_id | รหัสร้านค้าออโต้ | Customers | column_name |
| shop_bill | บิลร้านค้า | Orders | report_name |
| shop_bill_verification | ใบตรวจบิลร้านค้า | Orders | report_name |
| shop_code | รหัสร้านค้า | Orders | column_name |
| shop_delivery_note | ใบส่งของร้านค้า | Orders | report_name |
| shop_discount | ส่วนลดร้านค้า | Products | column_name |
| shop_discount_pre_vat | ส่วนลดร้านค้าก่อนแวท | Products | column_name |
| shop_info | ข้อมูลร้านค้า | Customers | table_name |
| shop_name | ชื่อร้าน | Customers | column_name |
| shop_order_line_items | qry สินค้าในแต่ละออเดอร์ร้านค้า | Orders | query_name |
| shop_order_line_items_subform | qry สินค้าในแต่ละออเดอร์ร้านค้า subform | Orders | form_name |
| shop_order_lookup | qry เจาะจงหมายเลขออเดอร์ร้านค้า | Orders | query_name |
| shop_packing_list | ใบจัดสินค้าร้านค้า | Orders | report_name |
| shop_payment_amounts | qryยอดเงินร้านค้า | Orders | query_name |
| shop_phone | เบอร์โทรศัพท์ร้านค้า | Customers | column_name |
| shop_price_incl_vat | ราคาร้านค้ารวมแวท | Products | column_name |
| shop_purchase_totals_per_vendor | qry ดูยอดซื้อร้านค้าแต่ละเจ้า | Orders | query_name |
| shop_sales_totals | qry ยอดขายร้านค้า | Orders | query_name |
| shop_specific_notes | หมายเหตุเฉพาะร้าน | Customers | column_name |
| shop_tax_id | เลขประจำตัวผู้เสียภาษีร้านค้า | Customers | column_name |
| shop_tax_invoice | ใบกำกับภาษีร้านค้า | Orders | report_name |
| shop_tax_invoice_copy | ใบกำกับภาษีร้านค้า(สำเนา) | Orders | report_name |
| shop_tax_invoice_duplicate | Copy of ใบกำกับภาษีร้านค้า | Orders | report_name |
| shop_tracking_notification | ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า | Customers | report_name |
| shop_transfer_details | qry รายละเอียดการโอนเงินร้านค้า | Financial | query_name |
| shops_awaiting_transfer | qry_ร้านค้ารอโอน | Orders | query_name |
| shops_ship_before_payment | qry_ร้านค้าส่งของให้ก่อน | Orders | query_name |
| start_date | วันที่เริ่มต้น | Orders | form_label |
| store_phone | เบอร์ร้าน | Customers | column_name |
| sum_line_total | SumOfราคารวม | Orders | calculated_field |
| sum_net_total_incl_vat | SumOfราคาสุทธิรวมภาษีมูลค่าเพิ่ม | Orders | calculated_field |
| sum_points | SumOfคะแนน | Customers | calculated_field |
| sum_pre_vat_after_bill_end_discount | SumOfราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล | Orders | calculated_field |
| sum_pre_vat_total | SumOfราคารวมก่อนแวท | Orders | calculated_field |
| sum_quantity | SumOfจำนวน | Orders | calculated_field |
| sum_quantity_issued | SumOfจำนวนเบิก | Inventory | calculated_field |
| sum_quantity_received | SumOfจำนวนรับเข้า | Inventory | calculated_field |
| sum_retail_net_total_incl_vat | SumOfราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม | Orders | calculated_field |
| sum_retail_vat | SumOfภาษีมูลค่าเพิ่มปลีก | Orders | calculated_field |
| sum_total_after_bill_end_discount | SumOfราคารวมหลังหักส่วนลดท้ายบิล | Orders | calculated_field |
| sum_total_after_shop_discount | SumOfราคารวมหลังหักส่วนลดร้านค้า | Orders | calculated_field |
| sum_vat | SumOfภาษีมูลค่าเพิ่ม | Orders | calculated_field |
| tax_invoice | ใบกำกับภาษี | Customers | enum_value |
| telephone | โทรศัพท์ | Customers | enum_value |
| total_after_bill_end_discount | ราคารวมหลังหักส่วนลดท้ายบิล | Orders | calculated_field |
| total_after_shop_discount | ราคารวมหลังหักส่วนลดร้านค้า | Orders | calculated_field |
| total_issued_all_products | qry จำนวนเบิกรวม ของสินค้าทุกตัว | Inventory | query_name |
| total_points | คะแนนรวม | Customers | column_name |
| total_pre_vat | ราคารวมก่อนแวท | Orders | calculated_field |
| total_pre_vat_after_bill_end_discount | ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล | Orders | calculated_field |
| total_pre_vat_after_shop_discount | ราคารวมก่อนแวทหลังหักส่วนลดร้านค้า | Orders | calculated_field |
| total_received_all_products | qry จำนวนรับเข้ารวม ของสินค้าทุกตัว | Inventory | query_name |
| total_sold_per_product | qry จำนวนที่ขายของสินค้าแต่ละตัว | Inventory | query_name |
| transfer_date | วันที่โอนเงิน | Orders | column_name |
| transfer_datetime_by_invoice | qry วันที่และเวลาโอนเงินเรียงตามใบกำกับ | Financial | query_name |
| transfer_details | รายละเอียดการโอน | Financial | report_name |
| transfer_details_per_order | rptรายละเอียดการโอนเงินของแต่ละเลขที่ออเดอร์ | Financial | report_name |
| transfer_first_only | โอนเงินก่อนเท่านั้น | Customers | enum_value |
| transfer_time | เวลาโอนเงิน | Orders | column_name |
| unit | หน่วยนับ | Products | column_name |
| unit_value_list | "ซอง";"ตัว";"เม็ด" | Products | query_name |
| vat | ภาษีมูลค่าเพิ่ม | Orders | calculated_field |
| vat_bill_asked | ถามเรื่องบิลแวทยัง | Customers | column_name |
| view_issue_numbers | rptดูเลขทีใบเบิก | Inventory | report_name |
| Wanpen | วันเพ็ญ | Proper Nouns | proper_noun |
| yearly_invoice_number | เลขที่invoiceของปี | Orders | column_name |
| yearly_receipt_number | เลขที่ใบรับเข้าของปี | Inventory | column_name |

### Thai Alphabetical Index

| Thai | English | Domain | Category |
|------|---------|--------|----------|
| "ซอง";"ตัว";"เม็ด" | unit_value_list | Products | query_name |
| Copy of ใบกำกับภาษีร้านค้า | shop_tax_invoice_duplicate | Orders | report_name |
| FACEBOOK | FACEBOOK | Orders | enum_value |
| ID | ID | Inventory | column_name |
| LINE | LINE | Orders | enum_value |
| SumOfคะแนน | sum_points | Customers | calculated_field |
| SumOfจำนวน | sum_quantity | Orders | calculated_field |
| SumOfจำนวนรับเข้า | sum_quantity_received | Inventory | calculated_field |
| SumOfจำนวนเบิก | sum_quantity_issued | Inventory | calculated_field |
| SumOfภาษีมูลค่าเพิ่ม | sum_vat | Orders | calculated_field |
| SumOfภาษีมูลค่าเพิ่มปลีก | sum_retail_vat | Orders | calculated_field |
| SumOfราคารวม | sum_line_total | Orders | calculated_field |
| SumOfราคารวมก่อนแวท | sum_pre_vat_total | Orders | calculated_field |
| SumOfราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล | sum_pre_vat_after_bill_end_discount | Orders | calculated_field |
| SumOfราคารวมหลังหักส่วนลดท้ายบิล | sum_total_after_bill_end_discount | Orders | calculated_field |
| SumOfราคารวมหลังหักส่วนลดร้านค้า | sum_total_after_shop_discount | Orders | calculated_field |
| SumOfราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม | sum_retail_net_total_incl_vat | Orders | calculated_field |
| SumOfราคาสุทธิรวมภาษีมูลค่าเพิ่ม | sum_net_total_incl_vat | Orders | calculated_field |
| frm รับเข้าสินค้า | goods_receipt_form | Inventory | form_name |
| frm เบิกสินค้า | goods_issue_form | Inventory | form_name |
| frm_salesorder_fishingshop | frm_salesorder_fishingshop | Orders | form_name |
| frm_salesorder_retail | frm_salesorder_retail | Orders | form_name |
| frm_stck_fishingshop | frm_stck_fishingshop | Inventory | form_name |
| frm_สต็อคสินค้า | product_stock_form | Inventory | form_name |
| frmข้อมูลสมาชิก | member_info_form | Customers | form_name |
| id | id | Orders | column_name |
| invสุดท้าย | inv_end | Orders | form_label |
| invเริ่มต้น | inv_start | Orders | form_label |
| pdf แจ้งยอด | balance_notification_pdf | Orders | report_name |
| qry stck subform2 | qry stck subform2 | Inventory | form_name |
| qry คะแนนคงเหลือหลังจากใช้แล้ว | remaining_points_after_use | Customers | query_name |
| qry คะแนนรวมลูกค้าแต่ละคน | customer_total_points | Customers | query_name |
| qry คะแนนรวมลูกค้าแต่ละคน subform | customer_points_subform | Customers | form_name |
| qry จำนวนที่ขายของสินค้าแต่ละตัว | total_sold_per_product | Inventory | query_name |
| qry จำนวนรับเข้ารวม ของสินค้าทุกตัว | total_received_all_products | Inventory | query_name |
| qry จำนวนเบิกรวม ของสินค้าทุกตัว | total_issued_all_products | Inventory | query_name |
| qry ดูยอดซื้อร้านค้าแต่ละเจ้า | shop_purchase_totals_per_vendor | Orders | query_name |
| qry ที่อยู่เจาะจงโดยวันที่ (ปลีก) | retail_addresses_by_date | Customers | query_name |
| qry ที่อยู่เจาะจงโดยวันที่ (ร้านค้า) | shop_addresses_by_date | Customers | query_name |
| qry ยอดขายร้านค้า | shop_sales_totals | Orders | query_name |
| qry ยอดขายลูกค้าปลีก | retail_sales_totals | Orders | query_name |
| qry ยอดซื้อร้านค้าทั้งปี | shop_annual_purchase_totals | Orders | query_name |
| qry รายละเอียดการโอนเงินร้านค้า | shop_transfer_details | Financial | query_name |
| qry รายละเอียดการโอนแต่ละออเดอร์ปลีก | retail_order_transfer_details | Financial | query_name |
| qry วันที่และเวลาโอนเงินเรียงตามใบกำกับ | transfer_datetime_by_invoice | Financial | query_name |
| qry สต็อคสินค้า | product_stock | Inventory | query_name |
| qry สต็อคสินค้าในแต่ละออเดอร์ปลีก | retail_order_stock | Inventory | query_name |
| qry สินค้าในแต่ละออเดอร์ Subform | order_line_items_subform | Orders | form_name |
| qry สินค้าในแต่ละออเดอร์ Subform1 | order_line_items_subform_1 | Orders | form_name |
| qry สินค้าในแต่ละออเดอร์ปลีก | retail_order_line_items | Orders | query_name |
| qry สินค้าในแต่ละออเดอร์ร้านค้า | shop_order_line_items | Orders | query_name |
| qry สินค้าในแต่ละออเดอร์ร้านค้า subform | shop_order_line_items_subform | Orders | form_name |
| qry เจาะจงหมายเลขออเดอร์ subreport | order_detail_subreport | Orders | report_name |
| qry เจาะจงหมายเลขออเดอร์ปลีก | retail_order_lookup | Orders | query_name |
| qry เจาะจงหมายเลขออเดอร์ร้านค้า | shop_order_lookup | Orders | query_name |
| qry เจาะจงเลขที่ใบรับเข้า | receipt_lookup | Inventory | query_name |
| qry เจาะจงเลขที่ใบเบิก | issue_lookup | Inventory | query_name |
| qry_ร้านค้ารอโอน | shops_awaiting_transfer | Orders | query_name |
| qry_ร้านค้าส่งของให้ก่อน | shops_ship_before_payment | Orders | query_name |
| qry_สินค้าที่ขายดีย้อนหลัง 3 เดือน | best_sellers_last_3_months | Orders | query_name |
| qryกำหนดเลขที่inv | assign_invoice_number | Financial | query_name |
| qryยอดเงินร้านค้า | shop_payment_amounts | Orders | query_name |
| qryรายงานสินค้าและวัตุดิบ | product_and_material_report | Products | query_name |
| qryลงยอดร้านค้า | post_shop_payments | Financial | query_name |
| qryใส่เลขที่ใบกำกับ | enter_tax_invoice_number | Financial | query_name |
| rptดูเลขทีใบเบิก | view_issue_numbers | Inventory | report_name |
| rptทำที่อยู่เบิกสินค้า | issue_address_labels | Inventory | report_name |
| rptรายละเอียดการโอนเงินของแต่ละเลขที่ออเดอร์ | transfer_details_per_order | Financial | report_name |
| กรุณาระบุรหัสร้านค้า | please_enter_shop_code | Orders | form_label |
| กสิกร | kasikorn_bank | Orders | enum_value |
| ขนส่งที่สะดวก | preferred_carrier | Customers | column_name |
| ข้อมูลร้านค้า | shop_info | Customers | table_name |
| ข้อมูลสมาชิก | member_info | Customers | table_name |
| ข้อมูลสำหรับแจ้งเลขพัสดุร้านค้า | shop_tracking_notification | Customers | report_name |
| ข้อมูลสำหรับแจ้งเลขพัสดุลูกค้าปลีก | retail_tracking_notification | Customers | report_name |
| ครั้ง | per_shipment | Products | enum_value |
| คะแนน | points | Orders | calculated_field |
| คะแนนคงเหลือหลังจากใช้แล้ว | remaining_points_form | Customers | form_name |
| คะแนนคีย์มือเพิ่มให้ | manual_bonus_points | Customers | column_name |
| คะแนนคีย์เอง | manual_points_entry | Orders | column_name |
| คะแนนที่ลูกค้าใช้ไป | customer_points_used | Customers | table_name |
| คะแนนที่ใช้ครั้งที่ 1 | points_used_1 | Customers | column_name |
| คะแนนที่ใช้ครั้งที่ 2 | points_used_2 | Customers | column_name |
| คะแนนที่ใช้ครั้งที่ 3 | points_used_3 | Customers | column_name |
| คะแนนที่ใช้ครั้งที่ 4 | points_used_4 | Customers | column_name |
| คะแนนที่ใช้ครั้งที่ 5 | points_used_5 | Customers | column_name |
| คะแนนที่ใช้ครั้งที่1 | points_redeemed_1 | Customers | column_name |
| คะแนนที่ใช้ครั้งที่2 | points_redeemed_2 | Customers | column_name |
| คะแนนที่ใช้ครั้งที่3 | points_redeemed_3 | Customers | column_name |
| คะแนนรวม | total_points | Customers | column_name |
| คุณต้าร์ทองเหลือง | Khun Tar Thonglueang | Proper Nouns | proper_noun |
| จันทกานต์ | Chantakan | Proper Nouns | proper_noun |
| จำนวน | quantity | Orders | column_name |
| จำนวนขาย | quantity_sold | Inventory | calculated_field |
| จำนวนที่ขายของสินค้าแต่ละตัว(ระบุวันที่) | product_sales_by_date | Orders | query_name |
| จำนวนรับเข้า | quantity_received | Inventory | column_name |
| จำนวนเบิก | quantity_issued | Inventory | column_name |
| ชื่อ | first_name | Customers | column_name |
| ชื่อร้าน | shop_name | Customers | column_name |
| ชื่อร้านสำหรับออกใบกำกับ | invoice_shop_name | Customers | column_name |
| ชื่อออกใบกำกับปลีก | retail_invoice_name | Customers | column_name |
| ชื่อเฟส | facebook_name | Customers | column_name |
| ชื่อไลน์ | line_name | Customers | column_name |
| ชื่อไลน์หรือเฟซ | line_or_facebook_name | Customers | column_name |
| ช่องทางติดต่อที่สะดวก | preferred_contact_channel | Customers | column_name |
| ช่องทางสั่งซื้อ | order_channel | Orders | column_name |
| ซอง | pack | Products | enum_value |
| ซองใหญ่ | large_pack | Products | enum_value |
| ดูจำนวนรวมสินค้าที่สั่งหลายออเดอร์รวมกัน | combined_multi_order_quantities | Orders | query_name |
| ตรวจภาษีขาย | sales_tax_verification | Financial | report_name |
| ตรวจภาษีขายเรียงตามเลขinv | sales_tax_verification_by_inv | Financial | report_name |
| ตัว | piece | Products | enum_value |
| ถามเรื่องบิลแวทยัง | vat_bill_asked | Customers | column_name |
| ถามแล้ว | already_asked | Customers | enum_value |
| ที่อยู่ | address | Customers | column_name |
| ที่อยู่ล่าสุด | latest_address | Customers | column_name |
| ที่อยู่สำหรับออกใบกำกับ | invoice_address | Customers | column_name |
| ธนาคาร | bank | Orders | column_name |
| นามสกุล | last_name | Customers | column_name |
| บิลธรรมดา | regular_bill | Customers | enum_value |
| บิลร้านค้า | shop_bill | Orders | report_name |
| บิลลูกค้าปลีก | retail_customer_bill | Orders | report_name |
| ปรินท์ใบเบิกสินค้า | print_goods_issue | Inventory | report_name |
| ปริ้นท์ที่อยู่ | print_addresses | Customers | report_name |
| ปริ้นท์ที่อยู่ลูกค้าปลีก | print_retail_addresses | Customers | report_name |
| ปิดวันอาทิตย์ | closed_sunday | Customers | enum_value |
| ผู้ผลิต หรือ พนักงานแพ็ค | producer_or_packer | Inventory | column_name |
| พนักงานตรวจการบันทึกข้อมูล | data_entry_reviewer | Financial | column_name |
| พนักงานตรวจเช็ค | inspection_staff | Financial | column_name |
| พนักงานบันทึกข้อมูล | data_entry_staff | Financial | column_name |
| พนักงานรับออเดอร์ | order_staff | Orders | column_name |
| พนักงานเบิก | issuing_staff | Inventory | column_name |
| ภาษีมูลค่าเพิ่ม | vat | Orders | calculated_field |
| ภาษีมูลค่าเพิ่มปลีก | retail_vat | Orders | calculated_field |
| รหัสร้านค้า | shop_code | Orders | column_name |
| รหัสร้านค้าที่เบิก | issue_shop_code | Inventory | column_name |
| รหัสร้านค้าออโต้ | shop_auto_id | Customers | column_name |
| รหัสสินค้า | product_code | Products | column_name |
| รอโอน | awaiting_transfer | Orders | enum_value |
| รัตนาพร | Rattanaporn | Proper Nouns | proper_noun |
| ราคา | price | Products | column_name |
| ราคาก่อนแวท | pre_vat_price | Products | column_name |
| ราคาก่อนแวทหลังหักส่วนลดร้านค้า | pre_vat_after_shop_discount | Orders | calculated_field |
| ราคารวม | line_total | Orders | calculated_field |
| ราคารวมก่อนแวท | total_pre_vat | Orders | calculated_field |
| ราคารวมก่อนแวทหลังหักส่วนลดท้ายบิล | total_pre_vat_after_bill_end_discount | Orders | calculated_field |
| ราคารวมก่อนแวทหลังหักส่วนลดร้านค้า | total_pre_vat_after_shop_discount | Orders | calculated_field |
| ราคารวมหลังหักส่วนลดท้ายบิล | total_after_bill_end_discount | Orders | calculated_field |
| ราคารวมหลังหักส่วนลดร้านค้า | total_after_shop_discount | Orders | calculated_field |
| ราคาร้านค้ารวมแวท | shop_price_incl_vat | Products | column_name |
| ราคาสุทธิปลีกรวมภาษีมูลค่าเพิ่ม | retail_net_total_incl_vat | Orders | calculated_field |
| ราคาสุทธิรวมภาษีมูลค่าเพิ่ม | net_total_incl_vat | Orders | calculated_field |
| ราคาหลังหักส่วนลดร้านค้า | price_after_shop_discount | Orders | calculated_field |
| รายงานภาษีขาย | sales_tax_report | Financial | report_name |
| รายละเอียดการโอน | transfer_details | Financial | report_name |
| รายละเอียดออเดอร์ | order_details | Orders | table_name |
| รายละเอียดเพิ่มเติม | additional_details | Financial | column_name |
| รายละเอียดใบรับเข้าสินค้า | goods_receipt_details | Inventory | report_name |
| ริปรอย | RipRoy | Proper Nouns | proper_noun |
| ลำดับที่ | sequence_number | Products | column_name |
| วันที่ | date | Orders | column_name |
| วันที่inv | invoice_date | Orders | column_name |
| วันที่จบ | date_end | Orders | form_label |
| วันที่ต้นเดือน | month_start_date | Orders | form_label |
| วันที่ท้ายเดือน | month_end_date | Orders | form_label |
| วันที่รับเข้า | receipt_date | Inventory | column_name |
| วันที่สร้างข้อมูล | record_created_date | Customers | column_name |
| วันที่สุดท้าย | end_date | Orders | form_label |
| วันที่เบิก | issue_date | Inventory | column_name |
| วันที่เปิดบิลสุดท้าย | bill_end_date | Orders | form_label |
| วันที่เปิดบิลเริ่มต้น | bill_start_date | Orders | form_label |
| วันที่เริ่ม | date_start | Orders | form_label |
| วันที่เริ่มต้น | start_date | Orders | form_label |
| วันที่โอนเงิน | transfer_date | Orders | column_name |
| วันหยุด | holidays | Customers | column_name |
| วันเพ็ญ | Wanpen | Proper Nouns | proper_noun |
| สด | cash_or_individual | Customers | enum_value |
| สาขาสถานประกอบการ | business_branch | Customers | column_name |
| สาขาสำนักงานใหญ่ | head_office_branch | Customers | column_name |
| สินค้า | products | Products | table_name |
| สินค้าในแต่ละออเดอร์ | order_line_items | Orders | table_name |
| สินค้าในแต่ละใบรับเข้า | receipt_line_items | Inventory | table_name |
| สินค้าในแต่ละใบรับเข้า Subform | receipt_line_items_subform | Inventory | form_name |
| สินค้าในแต่ละใบเบิก | issue_line_items | Inventory | table_name |
| สินค้าในแต่ละใบเบิก Subform | issue_line_items_subform | Inventory | form_name |
| ส่งของก่อนหรือโอนเงินก่อน | ship_or_pay_first | Customers | column_name |
| ส่งของให้ก่อน | ship_before_payment | Orders | enum_value |
| ส่วนลดท้ายบิล(%) | bill_end_discount_percent | Orders | column_name |
| ส่วนลดร้านค้า | shop_discount | Products | column_name |
| ส่วนลดร้านค้าก่อนแวท | shop_discount_pre_vat | Products | column_name |
| หน่วยนับ | unit | Products | column_name |
| หน้าหลัก | main_menu | Customers | form_name |
| หมายเลขกล่อง | box_number | Inventory | column_name |
| หมายเลขสมาชิก | member_number | Customers | column_name |
| หมายเลขสมาชิกที่เบิก | issue_member_number | Inventory | column_name |
| หมายเลขออโต้ | member_auto_id | Customers | column_name |
| หมายเหตุ | notes | Inventory | column_name |
| หมายเหตุอื่นๆ | other_notes | Orders | column_name |
| หมายเหตุเฉพาะร้าน | shop_specific_notes | Customers | column_name |
| หัวใบรับเข้า | receipt_headers | Inventory | table_name |
| หัวใบเบิก | issue_headers | Inventory | table_name |
| หาเลขที่ออเดอร์ถ้ารู้ชื่อร้าน | order_lookup_by_shop_name | Orders | form_name |
| อรุณี | Arunee | Proper Nouns | proper_noun |
| อื่นๆ | other | Orders | enum_value |
| เคอรี่และไปรษณีย์ไทย | kerry_and_thailand_post | Customers | enum_value |
| เงินสด | cash | Orders | enum_value |
| เบอร์ร้าน | store_phone | Customers | column_name |
| เบอร์โทรศัพท์ | phone_number | Customers | column_name |
| เบอร์โทรศัพท์2(มือถือ) | mobile_phone_2 | Customers | column_name |
| เบอร์โทรศัพท์ร้านค้า | shop_phone | Customers | column_name |
| เปิดทุกวัน | open_every_day | Customers | enum_value |
| เฟซบุค แมสเซนเจอร์ | facebook_messenger | Customers | column_name |
| เม็ด | bead | Products | enum_value |
| เลขที่invoiceของปี | yearly_invoice_number | Orders | column_name |
| เลขที่invoiceของแต่ละเดือน | monthly_invoice_number | Orders | column_name |
| เลขที่ออเดอร์ | order_number | Orders | column_name |
| เลขที่ออเดอร์สุดท้าย | last_order_number | Orders | form_label |
| เลขที่ออเดอร์แรก | first_order_number | Orders | form_label |
| เลขที่ใบรับเข้า | receipt_number | Inventory | column_name |
| เลขที่ใบรับเข้าของปี | yearly_receipt_number | Inventory | column_name |
| เลขที่ใบรับเข้าของแต่ละเดือน | monthly_receipt_number | Inventory | column_name |
| เลขที่ใบสำคัญ | document_number | Inventory | calculated_field |
| เลขที่ใบเบิก | issue_number | Inventory | column_name |
| เลขประจำตัวผู้เสียภาษีปลีก | retail_tax_id | Customers | column_name |
| เลขประจำตัวผู้เสียภาษีร้านค้า | shop_tax_id | Customers | column_name |
| เวลาโอนเงิน | transfer_time | Orders | column_name |
| เหตุผลการเบิก | issue_reason | Inventory | column_name |
| เอาบิลอะไร | bill_type_preference | Customers | column_name |
| โทรศัพท์ | telephone | Customers | enum_value |
| โอนเงินก่อนเท่านั้น | transfer_first_only | Customers | enum_value |
| ใบกำกับภาษี | tax_invoice | Customers | enum_value |
| ใบกำกับภาษีร้านค้า | shop_tax_invoice | Orders | report_name |
| ใบกำกับภาษีร้านค้า(สำเนา) | shop_tax_invoice_copy | Orders | report_name |
| ใบกำกับภาษีลูกค้าปลีก | retail_tax_invoice | Orders | report_name |
| ใบกำกับภาษีลูกค้าปลีก(สำเนา) | retail_tax_invoice_copy | Orders | report_name |
| ใบจัดสินค้าร้านค้า | shop_packing_list | Orders | report_name |
| ใบตรวจบิลร้านค้า | shop_bill_verification | Orders | report_name |
| ใบส่งของร้านค้า | shop_delivery_note | Orders | report_name |
| ใส่เลขที่ออเดอร์คนสุดท้ายที่จะดู | enter_last_order_to_view | Customers | form_label |
| ใส่เลขที่ออเดอร์คนแรกที่จะดู | enter_first_order_to_view | Customers | form_label |
| ใส่เลขที่ออเดอร์ร้านสุดท้าย | enter_last_shop_order | Customers | form_label |
| ใส่เลขที่ออเดอร์ร้านแรก | enter_first_shop_order | Customers | form_label |
| ได้สติกเกอร์หรือยัง | received_sticker | Customers | column_name |
| ได้สติกเกอร์ใหญ่แล้ว | received_large_sticker | Customers | column_name |

**Total unique terms: 244**
