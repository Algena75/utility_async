from dbase.core.config import settings as st

FILL_TABLE = \
"""
COPY {table} FROM '{file}' WITH (FORMAT csv);
"""

CREATE_USER_IF_NOT_EXISTS = \
f"""
DO
$do$
BEGIN
   IF EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = '{st.POSTGRES_USER}') THEN

      RAISE NOTICE 'Role "{st.POSTGRES_USER}" is already exists. Skipping.';
   ELSE
      CREATE ROLE {st.POSTGRES_USER} WITH LOGIN SUPERUSER 
        PASSWORD '{st.POSTGRES_PASSWORD}';
   END IF;
END
$do$;
"""

CREATE_DB_IF_NOT_EXISTS = \
f"""
CREATE DATABASE {st.POSTGRES_DB} OWNER "{st.POSTGRES_USER}";

"""

CREATE_TABLES = \
"""
CREATE TABLE IF NOT EXISTS buildings(
    id SERIAL PRIMARY KEY,
    street TEXT NOT NULL,
    house_number INTEGER NOT NULL,
    bld_number INTEGER,
    CHECK (house_number > 0),
    CHECK (bld_number > 0 AND bld_number < 20),
    UNIQUE (street, house_number, bld_number)
);
CREATE UNIQUE INDEX IF NOT EXISTS bld_number_null_unique_idx ON buildings (street, house_number) WHERE bld_number IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS bld_number_notnull_unique_idx ON buildings (street, house_number, bld_number) WHERE bld_number IS NOT NULL;
CREATE TABLE IF NOT EXISTS apartments(
    id SERIAL PRIMARY KEY,
    building INTEGER REFERENCES buildings ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK (number > 0),
    square NUMERIC (5, 2) NOT NULL CHECK (square > 0),
    UNIQUE (building, number)
);
CREATE TABLE IF NOT EXISTS counters(
    apartment INTEGER REFERENCES apartments ON DELETE CASCADE,
    counter_number VARCHAR(10) NOT NULL PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS periods(
    year integer NOT NULL CHECK(year > 1990 AND year < 2030),
    month integer NOT NULL CHECK(month >= 1 AND month <= 12),
    PRIMARY KEY (month, year)
);
INSERT INTO periods (month, year)
    SELECT month, year
    FROM
        generate_series(1, 12) month,
        generate_series(2019, 2025) year;
CREATE TABLE IF NOT EXISTS counter_values(
    counter_number varchar(10) NOT NULL,
    month integer NOT NULL CHECK(month >= 1 AND month <= 12),
    year integer NOT NULL CHECK(year > 1990 AND year < 2030),
    value NUMERIC (10,3) DEFAULT 0,
    UNIQUE (counter_number, month, year),
    FOREIGN KEY (counter_number) REFERENCES counters (counter_number) ON DELETE CASCADE,
    FOREIGN KEY (month, year) REFERENCES periods (month, year)
);
CREATE TABLE IF NOT EXISTS tariffs(
    tariff_name char(2) NOT NULL,
    value NUMERIC(6, 2) NOT NULL,
    from_date date NOT NULL DEFAULT current_date,
    until_date date,
    CHECK (tariff_name IN ('WA', 'CP')),
    CHECK (from_date > '1990-01-01'),
    CHECK (until_date > from_date)
);
CREATE TABLE IF NOT EXISTS bills(
    apartment INTEGER NOT NULL REFERENCES apartments ON DELETE CASCADE,
    month INTEGER NOT NULL CHECK(month >= 1 AND month <= 12),
    year INTEGER NOT NULL CHECK(year > 1990 AND year < 2030),
    water NUMERIC (7, 2),
    community_property NUMERIC (7, 2),
    total NUMERIC (10, 2),
    UNIQUE (apartment, month, year),
    FOREIGN KEY (month, year) REFERENCES periods (month, year)
);
"""

GET_BUILDINGS = \
"""
SELECT b.*, array(
                  SELECT a.number
                  FROM apartments a
                  WHERE b.id = a.building
                  ) AS apartments 
FROM buildings b;
"""

GET_BUILDING = \
"""
SELECT b.*, a.number, a.square::text, array(
                SELECT c.counter_number
                FROM counters c
                WHERE c.apartment = a.id) AS counters
FROM buildings b
LEFT JOIN apartments a ON b.id=a.building
WHERE b.id = $1
ORDER BY a.number;
"""

GET_BUILDING_ID = \
"""
SELECT b.*
FROM buildings b
WHERE b.street = $1 AND b.house_number = $2 AND b.bld_number = $3;
"""

NEW_BUILDING = \
"""
INSERT INTO buildings (street, house_number, bld_number)
VALUES ($1, $2, $3)
RETURNING *;
"""

NEW_APARTMENT = \
"""
INSERT INTO apartments (building, number, square)
VALUES ($1, $2, $3)
ON CONFLICT ON CONSTRAINT apartments_building_number_key
DO UPDATE SET square = excluded.square
RETURNING *;
"""
