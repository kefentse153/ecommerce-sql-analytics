# E-Commerce SQL Analytics

A complete, runnable SQL analytics project built on a synthetic e-commerce dataset (2,000 customers, ~7,500 orders, 2024–2025). It goes from raw relational schema to business insight, using CTEs, window functions, and cohort/RFM analysis techniques used in real analyst roles.

## The business problem

An e-commerce company wants to understand three things:
1. Is revenue actually growing, and is growth seasonal or unstable?
2. Which customers are most valuable, and which are at risk of churning?
3. Which products and regions are driving (or dragging on) performance?

This project answers all three using SQL alone, with a thin Python layer only for data generation and charting.

## Project structure

```
ecommerce-sql-analytics/
├── schema.sql              # DDL: 7 tables, keys, constraints, indexes
├── generate_data.py         # Generates the synthetic dataset (Faker + seeded randomness)
├── ecommerce.db              # SQLite database, ready to query out of the box
├── data/                    # Raw tables exported as CSV (for BI tools / re-import)
├── queries/
│   └── queries.sql          # 10 annotated analytical queries
├── analysis.py               # Runs key queries, exports charts + result CSVs
├── visuals/                  # PNG charts referenced below
├── results/                   # CSV output of each headline query
└── test_queries.py           # Sanity-check script — runs every query and confirms it executes
```

## Setup

```bash
git clone <this-repo>
cd ecommerce-sql-analytics
pip install faker pandas matplotlib

# rebuild the database from scratch (optional — ecommerce.db is already included)
python generate_data.py

# run all queries against it as a smoke test
python test_queries.py

# regenerate charts and result CSVs
python analysis.py
```

Or just open `ecommerce.db` directly in [DB Browser for SQLite](https://sqlitebrowser.org/) or `sqlite3 ecommerce.db` and run anything in `queries/queries.sql`.

**Dialect note:** written for SQLite for portability (no server setup needed to run this repo). All queries use standard ANSI SQL window functions and CTEs that port directly to PostgreSQL and MySQL 8+; the one exception (`QUALIFY`) is documented inline in `queries.sql` with the portable alternative already in place.

## Schema

Seven tables: `customers`, `categories`, `products`, `orders`, `order_items`, `payments`, `reviews`. Standard normalized retail schema — one order has many order items, one order item can have one review, payments track actual settled amounts separately from order line items (so cancelled orders never generate a payment).

```
customers ─┬─< orders ─┬─< order_items >─ products ─> categories
           │            ├─< payments
           │            
           └── (region, signup_date drive cohort/regional analysis)

order_items ─< reviews
```

## Key queries and what they answer

| # | Query | Technique | Business question |
|---|-------|-----------|---|
| 1 | Monthly revenue & MoM growth | `LAG()` window function | Is revenue growing month over month? |
| 2 | Customer lifetime value & repeat rate | Aggregation, conditional counts | What's a customer worth, and do they come back? |
| 3 | RFM segmentation | `NTILE()`, CASE-based scoring | Who are our best customers vs. who's churning? |
| 4 | Cohort retention | Self-join on month offset | Do customers from a given signup month keep buying? |
| 5 | Top products per category | `RANK()`, running `SUM() OVER()` | What are the category leaders, and how concentrated is revenue? |
| 6 | Revenue & AOV by region | Aggregation | Which regions drive the business? |
| 7 | Product margin ranking | Derived columns, joins | What's profitable, not just what sells? |
| 8 | Return rate by category | Conditional aggregation | Where are the quality/fulfillment problems? |
| 9 | Churn-risk customer list | Date arithmetic | Who hasn't ordered in 90+ days? (operational, actionable) |
| 10 | Review rating by category | 4-table join, `HAVING` | Where is customer satisfaction weakest? |

Full queries with comments live in [`queries/queries.sql`](queries/queries.sql).

## Findings

**Revenue is real but seasonal, not just growing.** Monthly revenue climbs from roughly R4,500 in January 2024 to nearly R9.9 million by December 2025, but the growth isn't smooth — November and December spike sharply (Black Friday and festive season effect built into the simulation), while January and February consistently dip below trend.

![Monthly revenue](visuals/monthly_revenue.png)

**Regional revenue is concentrated, not evenly spread.** The North region generates roughly R17.5 million in revenue — nearly 40% more than the second-highest region (South, ~R12.6 million) — while Central lags at under R6.2 million. That's a 2.8x gap between the strongest and weakest region.

![Revenue by region](visuals/revenue_by_region.png)

**Customer value is healthy but churn risk is concentrated.** Average customer lifetime value is roughly R30,575 across 3.5 orders on average, and 53% of customers make more than one purchase — a solid repeat rate for retail. But RFM segmentation shows the customer base splits almost evenly between high performers and risk: 558 customers are "Champions" (recent, frequent, high-spend), while 645 are "Lost/Dormant." That's a near 1:1 ratio of best customers to written-off customers, which is the kind of split that should drive a re-engagement campaign, not just a loyalty program.

![RFM segments](visuals/rfm_segments.png)

**Retention drops off hard after the first month.** The cohort heatmap shows most signup cohorts losing the majority of active customers by month 1–2, with a small stable core still purchasing at month 6. This is the standard retail retention curve — steep early drop-off, then a long flatter tail of loyal repeat buyers.

![Cohort retention](visuals/cohort_retention_heatmap.png)

**Books & Stationery has the highest return rate** among all categories at 5.4%, worth a closer look at product descriptions or packaging for that line.

## Recommendations

- **Prioritize win-back campaigns for the "Lost/Dormant" and "At Risk (High Value)" RFM segments** — combined they're roughly as large as the Champions segment, and the "At Risk" group has already proven they'll spend.
- **Investigate the Central region's underperformance** rather than assuming it's just smaller — compare AOV and repeat rate there against North to see if it's a demand problem or a fulfillment/marketing gap.
- **Build the November/December seasonal spike into inventory and staffing planning**, and use the January/February dip as a window for retention campaigns rather than acquisition spend.

## Why SQLite for this

No server setup required — clone and run. Every query here is written in portable ANSI SQL (CTEs, window functions, standard joins) so it drops into PostgreSQL or MySQL 8+ with no rewrites beyond date-function syntax, which is called out inline in `queries.sql`.

## Possible extensions

- Port to PostgreSQL and add a `dbt` layer for the CTEs as documented models
- Connect a BI tool (Metabase, Superset) directly to `ecommerce.db` for a live dashboard
- Add a `customers_ltv_prediction` notebook using the RFM features as inputs to a simple churn model
