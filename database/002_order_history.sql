CREATE TABLE IF NOT EXISTS demo_customer (
    id text PRIMARY KEY,
    display_name text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS demo_order (
    id text PRIMARY KEY,
    customer_id text NOT NULL REFERENCES demo_customer(id),
    placed_at timestamptz NOT NULL,
    status text NOT NULL CHECK (status IN
        ('confirmed', 'preparing', 'ready', 'dispatched', 'delivered', 'cancelled')),
    total_czk integer NOT NULL CHECK (total_czk >= 0)
);

CREATE TABLE IF NOT EXISTS demo_order_item (
    order_id text NOT NULL REFERENCES demo_order(id),
    pizza_id text NOT NULL REFERENCES pizza(id),
    pizza_name text NOT NULL,
    quantity integer NOT NULL CHECK (quantity > 0),
    unit_price_czk integer NOT NULL CHECK (unit_price_czk > 0),
    PRIMARY KEY (order_id, pizza_id)
);

CREATE INDEX IF NOT EXISTS demo_order_customer_time_idx
    ON demo_order (customer_id, placed_at DESC, id DESC);
