-- =====================================================================
-- 01_schema.sql
-- Transactional schema for the e-commerce dataset (SQLite).
-- =====================================================================
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS customers;
DROP TABLE IF EXISTS products;

CREATE TABLE products (
    product_id    TEXT PRIMARY KEY,
    product_name  TEXT NOT NULL,
    category      TEXT NOT NULL,
    list_price    REAL NOT NULL,
    unit_cost     REAL NOT NULL
);

CREATE TABLE customers (
    customer_id          TEXT PRIMARY KEY,
    signup_date          TEXT NOT NULL,          -- YYYY-MM-DD
    country              TEXT,
    acquisition_channel  TEXT
);

CREATE TABLE orders (
    order_id     TEXT PRIMARY KEY,
    customer_id  TEXT REFERENCES customers (customer_id),   -- NULL = guest checkout
    order_date   TEXT NOT NULL,                              -- YYYY-MM-DD
    status       TEXT NOT NULL CHECK (status IN ('completed', 'cancelled', 'returned'))
);

CREATE TABLE order_items (
    order_item_id  INTEGER PRIMARY KEY,
    order_id       TEXT NOT NULL REFERENCES orders (order_id),
    product_id     TEXT NOT NULL REFERENCES products (product_id),
    quantity       INTEGER NOT NULL CHECK (quantity > 0),
    unit_price     REAL NOT NULL CHECK (unit_price >= 0)
);

CREATE INDEX idx_orders_customer ON orders (customer_id);
CREATE INDEX idx_orders_date     ON orders (order_date);
CREATE INDEX idx_items_order     ON order_items (order_id);
CREATE INDEX idx_items_product   ON order_items (product_id);
