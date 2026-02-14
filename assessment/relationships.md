# Database Relationships

## Summary

- 14 total relationships in MSysRelationships
- 8 table-to-table relationships (user-defined foreign keys)
- 4 table-to-query relationships (lookup/derived)
- 2 system relationships (excluded from analysis)

## Table-to-Table Relationships

| Relationship Name                     | Source Table           | Source Column   | Referenced Table   | Referenced Column   | Integrity             |
|:--------------------------------------|:-----------------------|:----------------|:-------------------|:--------------------|:----------------------|
| ข้อมูลร้านค้ารายละเอียดออเดอร์        | รายละเอียดออเดอร์      | รหัสร้านค้า     | ข้อมูลร้านค้า      | รหัสร้านค้า         | None (UI lookup only) |
| ข้อมูลสมาชิกรายละเอียดออเดอร์         | รายละเอียดออเดอร์      | เบอร์โทรศัพท์   | ข้อมูลสมาชิก       | เบอร์โทรศัพท์       | NO_INTEGRITY          |
| รายละเอียดออเดอร์สินค้าในแต่ละออเดอร์ | สินค้าในแต่ละออเดอร์   | เลขที่ออเดอร์   | รายละเอียดออเดอร์  | เลขที่ออเดอร์       | NO_INTEGRITY          |
| สินค้าสินค้าในแต่ละใบเบิก             | สินค้าในแต่ละใบเบิก    | สินค้า          | สินค้า             | สินค้า              | NO_INTEGRITY          |
| สินค้าสินค้าในแต่ละใบรับเข้า          | สินค้าในแต่ละใบรับเข้า | สินค้า          | สินค้า             | สินค้า              | NO_INTEGRITY          |
| สินค้าสินค้าในแต่ละออเดอร์            | สินค้าในแต่ละออเดอร์   | สินค้า          | สินค้า             | สินค้า              | NO_INTEGRITY          |
| หัวใบเบิกสินค้าในแต่ละใบเบิก          | สินค้าในแต่ละใบเบิก    | เลขที่ใบเบิก    | หัวใบเบิก          | เลขที่ใบเบิก        | NO_INTEGRITY          |
| หัวใบรับเข้าสินค้าในแต่ละใบรับเข้า    | สินค้าในแต่ละใบรับเข้า | เลขที่ใบรับเข้า | หัวใบรับเข้า       | เลขที่ใบรับเข้า     | NO_INTEGRITY          |

### Referential Integrity Detail

- "ข้อมูลร้านค้ารายละเอียดออเดอร์": รายละเอียดออเดอร์.รหัสร้านค้า -> ข้อมูลร้านค้า.รหัสร้านค้า -- UI lookup only (no integrity constraints)
- "ข้อมูลสมาชิกรายละเอียดออเดอร์": รายละเอียดออเดอร์.เบอร์โทรศัพท์ -> ข้อมูลสมาชิก.เบอร์โทรศัพท์ -- No integrity check (orphans allowed)
- "รายละเอียดออเดอร์สินค้าในแต่ละออเดอร์": สินค้าในแต่ละออเดอร์.เลขที่ออเดอร์ -> รายละเอียดออเดอร์.เลขที่ออเดอร์ -- No integrity check (orphans allowed)
- "สินค้าสินค้าในแต่ละใบเบิก": สินค้าในแต่ละใบเบิก.สินค้า -> สินค้า.สินค้า -- No integrity check (orphans allowed)
- "สินค้าสินค้าในแต่ละใบรับเข้า": สินค้าในแต่ละใบรับเข้า.สินค้า -> สินค้า.สินค้า -- No integrity check (orphans allowed)
- "สินค้าสินค้าในแต่ละออเดอร์": สินค้าในแต่ละออเดอร์.สินค้า -> สินค้า.สินค้า -- No integrity check (orphans allowed)
- "หัวใบเบิกสินค้าในแต่ละใบเบิก": สินค้าในแต่ละใบเบิก.เลขที่ใบเบิก -> หัวใบเบิก.เลขที่ใบเบิก -- No integrity check (orphans allowed)
- "หัวใบรับเข้าสินค้าในแต่ละใบรับเข้า": สินค้าในแต่ละใบรับเข้า.เลขที่ใบรับเข้า -> หัวใบรับเข้า.เลขที่ใบรับเข้า -- No integrity check (orphans allowed)

## Table-to-Query Relationships

| Relationship Name                                 | Source                       | Source Column   | Referenced Query/Table           | Referenced Column   | Flags                        |
|:--------------------------------------------------|:-----------------------------|:----------------|:---------------------------------|:--------------------|:-----------------------------|
| qry คะแนนคงเหลือหลังจากใช้แล้รายละเอียดออเดอร์    | รายละเอียดออเดอร์            | หมายเลขสมาชิก   | qry คะแนนคงเหลือหลังจากใช้แล้ว   | หมายเลขสมาชิก       | CASCADE_UPDATES              |
| qry คะแนนรวมลูกค้าแต่ละคนqry สินค้าในแต่ละออเดอร์ | qry สินค้าในแต่ละออเดอร์ปลีก | หมายเลขสมาชิก   | qry คะแนนรวมลูกค้าแต่ละคน        | หมายเลขสมาชิก       | CASCADE_UPDATES, QUERY_BASED |
| qry สต็อคสินค้าสินค้า                             | สินค้า                       | สินค้า          | qry สต็อคสินค้า                  | สินค้า.สินค้า       | CASCADE_UPDATES              |
| จำนวนที่ขายของสินค้าแต่ละตัวสินค้า                | สินค้า                       | สินค้า          | qry จำนวนที่ขายของสินค้าแต่ละตัว | สินค้า              | CASCADE_UPDATES              |

Note: These relationships reference queries rather than tables directly. The actual table dependencies are resolved through the query definitions (Phase 3).

## System Relationships

Excluded: MSysNavPaneGroupCategoriesMSysNavPaneGroups, MSysNavPaneGroupsMSysNavPaneGroupToObjects

## Notes

- grbit=0 means no referential integrity enforced (relationship exists for UI lookup purposes only)
- Relationships flagged NO_INTEGRITY (0x100) allow orphaned records
- QUERY_BASED (0x2000000) relationships depend on query definitions for resolution
- CASCADE_UPDATES propagates primary key changes to foreign key columns
- CASCADE_DELETES removes child records when parent record is deleted
- Default values and validation rules are stored in field property blobs (not extractable on macOS -- deferred to Phase 3 Windows extraction if needed)
