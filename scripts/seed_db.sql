-- Phase 1: Intentional Messiness
-- 1. Ambiguous Keys (customers.customer_id vs orders.cust_id)
-- 2. Denormalization (orders.total_amount vs line_items.qty * unit_price)
-- 3. Nullable Columns (customers.region)

CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    region VARCHAR(100) -- Nullable intentionally
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    cust_id INTEGER REFERENCES customers(customer_id), -- Ambiguous key name
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL -- Denormalized total
);

CREATE TABLE line_items (
    item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_name VARCHAR(255) NOT NULL,
    qty INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL
);

-- Seed Data
-- 100+ customers, 500+ orders, 1500+ line items to test Cartesian Product heuristics

-- Generate Customers
INSERT INTO customers (name, region)
SELECT 
    'Customer ' || i,
    CASE WHEN i % 5 = 0 THEN NULL ELSE 'Region ' || (i % 4) END
FROM generate_series(1, 150) AS i;

-- Generate Orders (Average 4 orders per customer)
INSERT INTO orders (cust_id, order_date, total_amount)
SELECT 
    (random() * 149 + 1)::INT,
    CURRENT_DATE - (random() * 365)::INT,
    0 -- We'll update this later based on line items to keep it consistent initially
FROM generate_series(1, 600) AS i;

-- Generate Line Items (Average 3 items per order)
INSERT INTO line_items (order_id, product_name, qty, unit_price)
SELECT 
    (random() * 599 + 1)::INT,
    'Product ' || (random() * 50)::INT,
    (random() * 10 + 1)::INT,
    (random() * 100 + 10)::DECIMAL(10, 2)
FROM generate_series(1, 1800) AS i;

-- Update the denormalized total_amount in orders
UPDATE orders o
SET total_amount = (
    SELECT COALESCE(SUM(qty * unit_price), 0)
    FROM line_items li
    WHERE li.order_id = o.order_id
);

-- Let's create a specific customer with NO orders to test empty result heuristic
INSERT INTO customers (name, region) VALUES ('Zero Spender', 'North');
