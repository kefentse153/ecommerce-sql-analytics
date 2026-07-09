"""
analysis.py
Runs the key analytical queries against ecommerce.db, saves results as CSV
in results/, and produces a few charts in visuals/ for the README.
"""
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

conn = sqlite3.connect(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\ecommerce.db")

plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["font.size"] = 10

# ---------- Q1: monthly revenue trend ----------
q1 = """
WITH monthly_revenue AS (
    SELECT strftime('%Y-%m', p.payment_date) AS month, ROUND(SUM(p.amount), 2) AS revenue
    FROM payments p JOIN orders o ON o.order_id = p.order_id
    WHERE o.order_status = 'completed'
    GROUP BY 1
)
SELECT * FROM monthly_revenue ORDER BY month;
"""
df1 = pd.read_sql(q1, conn)
df1.to_csv(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\results\q1_monthly_revenue.csv", index=False)

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(df1["month"], df1["revenue"], marker="o", color="#2563eb", linewidth=2)
ax.set_title("Monthly Revenue (2024–2025)", fontsize=13, fontweight="bold")
ax.set_ylabel("Revenue (R)")
ax.tick_params(axis="x", rotation=60)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\visuals\monthly_revenue.png", dpi=150)
plt.close(fig)

# ---------- Q4: cohort retention heatmap ----------
q4 = """
WITH cohorts AS (
    SELECT customer_id, strftime('%Y-%m', signup_date) AS cohort_month FROM customers
),
activity AS (
    SELECT DISTINCT o.customer_id, strftime('%Y-%m', o.order_date) AS active_month
    FROM orders o WHERE o.order_status = 'completed'
),
cohort_activity AS (
    SELECT c.cohort_month, a.active_month,
        ((CAST(strftime('%Y', a.active_month||'-01') AS INTEGER) - CAST(strftime('%Y', c.cohort_month||'-01') AS INTEGER))*12
        + (CAST(strftime('%m', a.active_month||'-01') AS INTEGER) - CAST(strftime('%m', c.cohort_month||'-01') AS INTEGER))) AS month_number,
        c.customer_id
    FROM cohorts c JOIN activity a ON a.customer_id = c.customer_id
),
cohort_size AS (
    SELECT cohort_month, COUNT(DISTINCT customer_id) AS num_customers FROM cohorts GROUP BY cohort_month
)
SELECT ca.cohort_month, ca.month_number, COUNT(DISTINCT ca.customer_id) AS retained_customers,
       cs.num_customers AS cohort_size,
       ROUND(100.0*COUNT(DISTINCT ca.customer_id)/cs.num_customers,1) AS retention_pct
FROM cohort_activity ca JOIN cohort_size cs ON cs.cohort_month = ca.cohort_month
WHERE ca.month_number BETWEEN 0 AND 6
GROUP BY ca.cohort_month, ca.month_number
ORDER BY ca.cohort_month, ca.month_number;
"""
df4 = pd.read_sql(q4, conn)
df4.to_csv(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\results\q4_cohort_retention.csv", index=False)

pivot = df4.pivot(index="cohort_month", columns="month_number", values="retention_pct")
pivot = pivot.sort_index().head(12)  # first 12 cohorts, readable heatmap

fig, ax = plt.subplots(figsize=(9, 6))
im = ax.imshow(pivot.values, cmap="Blues", aspect="auto", vmin=0, vmax=100)
ax.set_xticks(range(pivot.shape[1]))
ax.set_xticklabels([f"M{m}" for m in pivot.columns])
ax.set_yticks(range(pivot.shape[0]))
ax.set_yticklabels(pivot.index)
ax.set_title("Cohort Retention (%) by Signup Month", fontsize=13, fontweight="bold")
for i in range(pivot.shape[0]):
    for j in range(pivot.shape[1]):
        val = pivot.values[i, j]
        if pd.notna(val):
            ax.text(j, i, f"{val:.0f}", ha="center", va="center",
                     color="white" if val > 50 else "black", fontsize=8)
fig.colorbar(im, ax=ax, label="Retention %")
fig.tight_layout()
fig.savefig(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\visuals\cohort_retention_heatmap.png", dpi=150)
plt.close(fig)

# ---------- Q6: revenue by region ----------
q6 = """
SELECT c.region, ROUND(SUM(oi.quantity*oi.unit_price),2) AS total_revenue
FROM orders o JOIN customers c ON c.customer_id=o.customer_id
JOIN order_items oi ON oi.order_id=o.order_id
WHERE o.order_status='completed'
GROUP BY c.region ORDER BY total_revenue DESC;
"""
df6 = pd.read_sql(q6, conn)
df6.to_csv(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\results\q6_revenue_by_region.csv", index=False)

fig, ax = plt.subplots(figsize=(7, 4.5))
bars = ax.bar(df6["region"], df6["total_revenue"], color="#0d9488")
ax.set_title("Total Revenue by Region", fontsize=13, fontweight="bold")
ax.set_ylabel("Revenue (R)")
ax.grid(axis="y", alpha=0.3)
for b in bars:
    ax.text(b.get_x() + b.get_width()/2, b.get_height(), f"{b.get_height():,.0f}",
            ha="center", va="bottom", fontsize=8)
fig.tight_layout()
fig.savefig(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\visuals\revenue_by_region.png", dpi=150)
plt.close(fig)

# ---------- Q3: RFM segment distribution (full population, not just top 50) ----------
q3_full = """
WITH last_order AS (
    SELECT customer_id, MAX(order_date) AS last_order_date FROM orders WHERE order_status='completed' GROUP BY customer_id
),
rfm_base AS (
    SELECT o.customer_id,
        CAST(julianday('2025-12-31') - julianday(lo.last_order_date) AS INTEGER) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(oi.quantity*oi.unit_price),2) AS monetary
    FROM orders o JOIN order_items oi ON oi.order_id=o.order_id
    JOIN last_order lo ON lo.customer_id=o.customer_id
    WHERE o.order_status='completed'
    GROUP BY o.customer_id
),
rfm_scored AS (
    SELECT customer_id, recency_days, frequency, monetary,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary ASC) AS m_score
    FROM rfm_base
)
SELECT
    CASE
        WHEN r_score>=3 AND f_score>=3 AND m_score>=3 THEN 'Champions'
        WHEN r_score>=3 AND f_score<=2 THEN 'New / Promising'
        WHEN r_score<=2 AND f_score>=3 AND m_score>=3 THEN 'At Risk (High Value)'
        WHEN r_score<=2 AND f_score<=2 THEN 'Lost / Dormant'
        ELSE 'Needs Attention'
    END AS segment,
    COUNT(*) AS num_customers
FROM rfm_scored
GROUP BY segment
ORDER BY num_customers DESC;
"""
df3 = pd.read_sql(q3_full, conn)
df3.to_csv(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\results\q3_rfm_segment_distribution.csv", index=False)

fig, ax = plt.subplots(figsize=(7, 4.5))
colors = ["#2563eb", "#0d9488", "#f59e0b", "#dc2626", "#7c3aed"]
ax.bar(df3["segment"], df3["num_customers"], color=colors[:len(df3)])
ax.set_title("Customer Distribution by RFM Segment", fontsize=13, fontweight="bold")
ax.set_ylabel("Number of Customers")
ax.tick_params(axis="x", rotation=20)
ax.grid(axis="y", alpha=0.3)
fig.tight_layout()
fig.savefig(r"C:\Users\user\Downloads\files\ecommerce-sql-analytics\ecommerce-sql-analytics\visuals\rfm_segments.png", dpi=150)
plt.close(fig)

print("Done. CSVs in results/, charts in visuals/")
print(df3)
