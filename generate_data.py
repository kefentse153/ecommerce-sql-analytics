"""
generate_data.py
Generates a realistic synthetic e-commerce dataset and loads it into
ecommerce.db (SQLite). Designed so the analytical queries in queries.sql
have real patterns to find: seasonality, churn, repeat buyers, regional
skew, category performance differences.

Run:  python generate_data.py
"""

import sqlite3
import random
from datetime import date, timedelta
from faker import Faker

random.seed(42)
fake = Faker()
Faker.seed(42)

DB_PATH = "ecommerce.db"
START_DATE = date(2024, 1, 1)
END_DATE = date(2025, 12, 31)
N_CUSTOMERS = 2000
N_PRODUCTS_PER_CATEGORY = 8

REGIONS = ["North", "South", "East", "West", "Central"]
CATEGORIES = [
    "Electronics", "Home & Kitchen", "Fashion", "Beauty & Personal Care",
    "Sports & Outdoors", "Books & Stationery", "Toys & Games", "Groceries"
]
PAYMENT_METHODS = ["card", "eft", "wallet", "cod"]

# category -> (min_price, max_price, cost_ratio range)
CATEGORY_PRICE_RANGE = {
    "Electronics": (400, 15000),
    "Home & Kitchen": (100, 4000),
    "Fashion": (80, 1500),
    "Beauty & Personal Care": (50, 900),
    "Sports & Outdoors": (100, 3500),
    "Books & Stationery": (30, 500),
    "Toys & Games": (50, 1200),
    "Groceries": (20, 400),
}


def random_date(start, end):
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))


def seasonal_weight(d: date) -> float:
    """November/December (Black Friday + festive season) and July winter sales spike."""
    if d.month in (11, 12):
        return 2.2
    if d.month == 7:
        return 1.4
    if d.month in (1, 2):
        return 0.7  # post-holiday slump
    return 1.0


def build():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    with open("schema.sql") as f:
        cur.executescript(f.read())

    # ---------------- categories ----------------
    for i, name in enumerate(CATEGORIES, start=1):
        cur.execute("INSERT INTO categories VALUES (?,?)", (i, name))

    # ---------------- products ----------------
    product_id = 1
    products = []  # (id, category_id)
    for cat_id, cat_name in enumerate(CATEGORIES, start=1):
        lo, hi = CATEGORY_PRICE_RANGE[cat_name]
        for _ in range(N_PRODUCTS_PER_CATEGORY):
            price = round(random.uniform(lo, hi), 2)
            cost = round(price * random.uniform(0.45, 0.75), 2)
            name = f"{fake.word().capitalize()} {cat_name.split(' ')[0]} {random.choice(['Pro','Lite','Max','Basic','Plus'])}"
            cur.execute(
                "INSERT INTO products VALUES (?,?,?,?,?)",
                (product_id, name, cat_id, price, cost),
            )
            products.append((product_id, cat_id, price))
            product_id += 1

    # ---------------- customers ----------------
    customers = []
    for cid in range(1, N_CUSTOMERS + 1):
        signup = random_date(START_DATE, END_DATE - timedelta(days=30))
        region = random.choices(REGIONS, weights=[0.28, 0.22, 0.18, 0.20, 0.12])[0]
        cur.execute(
            "INSERT INTO customers VALUES (?,?,?,?,?,?,?,?)",
            (
                cid,
                fake.first_name(),
                fake.last_name(),
                f"user{cid}_{fake.free_email()}",
                signup.isoformat(),
                fake.city(),
                fake.state(),
                region,
            ),
        )
        # customer "type" drives repeat-purchase behaviour -> makes cohort/RFM meaningful
        r = random.random()
        if r < 0.12:
            cust_type = "power"      # frequent repeat buyers
        elif r < 0.40:
            cust_type = "regular"    # a few orders
        elif r < 0.70:
            cust_type = "occasional" # 1-2 orders
        else:
            cust_type = "one_and_done"  # single order, often never returns
        customers.append((cid, signup, cust_type))

    # ---------------- orders / order_items / payments / reviews ----------------
    order_id = 1
    order_item_id = 1
    payment_id = 1
    review_id = 1

    type_order_count = {
        "power": (8, 20),
        "regular": (3, 7),
        "occasional": (1, 2),
        "one_and_done": (1, 1),
    }

    for cid, signup, cust_type in customers:
        lo, hi = type_order_count[cust_type]
        n_orders = random.randint(lo, hi)

        for _ in range(n_orders):
            candidate = random_date(signup, END_DATE)
            # bias toward seasonal months using rejection sampling
            if random.random() > seasonal_weight(candidate) / 2.2:
                candidate = random_date(signup, END_DATE)
            order_date = candidate

            status = random.choices(
                ["completed", "cancelled", "returned"], weights=[0.90, 0.05, 0.05]
            )[0]

            cur.execute(
                "INSERT INTO orders VALUES (?,?,?,?)",
                (order_id, cid, order_date.isoformat(), status),
            )

            n_items = random.randint(1, 4)
            order_total = 0.0
            chosen_products = random.sample(products, k=min(n_items, len(products)))
            item_ids_this_order = []
            for pid, cat_id, price in chosen_products:
                qty = random.randint(1, 3)
                # small price jitter to simulate discounts/promo pricing
                unit_price = round(price * random.uniform(0.85, 1.0), 2)
                cur.execute(
                    "INSERT INTO order_items VALUES (?,?,?,?,?)",
                    (order_item_id, order_id, pid, qty, unit_price),
                )
                order_total += qty * unit_price
                item_ids_this_order.append(order_item_id)
                order_item_id += 1

            if status != "cancelled":
                cur.execute(
                    "INSERT INTO payments VALUES (?,?,?,?,?)",
                    (
                        payment_id,
                        order_id,
                        order_date.isoformat(),
                        round(order_total, 2),
                        random.choice(PAYMENT_METHODS),
                    ),
                )
                payment_id += 1

            # ~35% of items get a review, skewed positive (typical for retail)
            for item_id in item_ids_this_order:
                if random.random() < 0.35:
                    rating = random.choices([1, 2, 3, 4, 5], weights=[4, 6, 12, 33, 45])[0]
                    review_date = order_date + timedelta(days=random.randint(1, 21))
                    if review_date > END_DATE:
                        review_date = END_DATE
                    cur.execute(
                        "INSERT INTO reviews VALUES (?,?,?,?)",
                        (review_id, item_id, rating, review_date.isoformat()),
                    )
                    review_id += 1

            order_id += 1

    conn.commit()

    # quick sanity counts
    for tbl in ["customers", "categories", "products", "orders", "order_items", "payments", "reviews"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        print(f"{tbl:15s}: {n:,}")

    conn.close()


if __name__ == "__main__":
    build()
