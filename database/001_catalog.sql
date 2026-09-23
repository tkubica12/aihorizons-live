CREATE TABLE IF NOT EXISTS pizza (
    id text PRIMARY KEY,
    name text NOT NULL UNIQUE,
    category text NOT NULL,
    description text NOT NULL,
    price_czk integer NOT NULL CHECK (price_czk > 0),
    available boolean NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS ingredient (
    id text PRIMARY KEY,
    name text NOT NULL UNIQUE,
    allergen_profile_complete boolean NOT NULL,
    profile_note text NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS allergen (
    number integer PRIMARY KEY CHECK (number BETWEEN 1 AND 14),
    name text NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS ingredient_allergen (
    ingredient_id text NOT NULL REFERENCES ingredient(id),
    allergen_number integer NOT NULL REFERENCES allergen(number),
    PRIMARY KEY (ingredient_id, allergen_number)
);

CREATE TABLE IF NOT EXISTS pizza_ingredient (
    pizza_id text NOT NULL REFERENCES pizza(id),
    ingredient_id text NOT NULL REFERENCES ingredient(id),
    grams integer NOT NULL CHECK (grams > 0),
    PRIMARY KEY (pizza_id, ingredient_id)
);

CREATE INDEX IF NOT EXISTS pizza_category_name_idx ON pizza (category, name);
CREATE INDEX IF NOT EXISTS pizza_ingredient_ingredient_idx ON pizza_ingredient (ingredient_id);
