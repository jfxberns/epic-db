# Short Description of Epic DB Project


# Project Brief: RipRoy Access Database Assessment

## Background

Epic Gear is a small fishing lure manufacturer in Samut Prakan, Thailand (RipRoy brand). Operations run on a ~10-year-old Microsoft Access database (`epic_db.accdb`) with Thai-language interface and data.

## Current System

- **Users:** 1-3 concurrent users maximum
- **Volume:** 10-50 orders/day, ~2 inventory updates/week
- **Data:** ~1,000 customers, ~10,000 orders, 8 products
- **File:** Single 10MB `.accdb` file, no password, no external dependencies
- **Features:** Customer DB, inventory, orders, invoices, formulas, pricing/discounts, reports, shipping labels
  
## Exisitng Features

- Database of customers; stores that buy RipRoy products 
- Inventory tracking
- Product 
- Orders from customers that list all products 
- Printable invoices to give to customers
- Formulas for mixing the ingredients from raw materials
- Pricing for each product
- Discounts for customers based on volume, ability to add overrides on discount rate
- Forms to fill out to customer orders
- Reports such as inventory status
- Printing of labels for shipments
- and more. 

## Pain Points

- Thai-only interface (owner cannot read Thai)
- Built by non-programmer; difficult to modify safely
- Clunky but functional

## Assessment Goal

**Extract all components** from `epic_db.accdb` to evaluate:

1. What data/logic exists
2. Feasibility of rebuilding as web app vs. starting fresh
3. Rough effort estimate

## Deliverable

Documentation of extracted:

- Database tables and relationships
- Forms, reports, queries
- VBA modules and business logic
- Assessment of rebuild feasibility

