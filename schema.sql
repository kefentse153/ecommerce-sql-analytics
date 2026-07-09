-- ============================================================
-- E-Commerce Analytics Database — Schema
-- Dialect: SQLite (portable to PostgreSQL/MySQL with minor tweaks
-- noted in README, e.g. AUTOINCREMENT -> SERIAL, TEXT -> VARCHAR)
-- ============================================================

DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id     INTEGER PRIMARY KEY,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL UNIQUE,
    signup_date     DATE NOT NULL,
    city            TEXT,
    state           TEXT,
    region          TEXT NOT NULL CHECK (region IN ('North','South','East','West','Central'))
);

CREATE TABLE categories (
    category_id     INTEGER PRIMARY KEY,
    category_name   TEXT NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id      INTEGER PRIMARY KEY,
    product_name    TEXT NOT NULL,
    category_id     INTEGER NOT NULL REFERENCES categories(category_id),
    unit_price      NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    unit_cost       NUMERIC(10,2) NOT NULL CHECK (unit_cost > 0)
);

CREATE TABLE orders (
    order_id        INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date      DATE NOT NULL,
    order_status    TEXT NOT NULL CHECK (order_status IN ('completed','cancelled','returned'))
);

CREATE TABLE order_items (
    order_item_id   INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    quantity        INTEGER NOT NULL CHECK (quantity > 0),
    unit_price      NUMERIC(10,2) NOT NULL CHECK (unit_price > 0)
);

CREATE TABLE payments (
    payment_id      INTEGER PRIMARY KEY,
    order_id        INTEGER NOT NULL REFERENCES orders(order_id),
    payment_date    DATE NOT NULL,
    amount          NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    payment_method  TEXT NOT NULL CHECK (payment_method IN ('card','eft','wallet','cod'))
);

CREATE TABLE reviews (
    review_id       INTEGER PRIMARY KEY,
    order_item_id   INTEGER NOT NULL REFERENCES order_items(order_item_id),
    rating          INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_date     DATE NOT NULL
);

-- Helpful indexes for the analytical queries in queries.sql
CREATE INDEX idx_orders_customer   ON orders(customer_id);
CREATE INDEX idx_orders_date       ON orders(order_date);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_prod  ON order_items(product_id);
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_payments_order    ON payments(order_id);
