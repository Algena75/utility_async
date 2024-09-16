import asyncpg

from dbase.core.config import settings as st


async def create_database_if_not_exists():
    """Создаём БД, если не существует."""
    try:
        connection = await asyncpg.connect(
            host=st.POSTGRES_SERVER,
            port=st.POSTGRES_PORT,
            user=st.POSTGRES_USER,
            database=st.POSTGRES_DB,
            password=st.POSTGRES_PASSWORD
        )
        print(f'Подключено! Необходимая БД {st.POSTGRES_DB} обнаружена')
        await connection.close()
    except:
        connection = await asyncpg.connect(
            host=st.POSTGRES_SERVER,
            port=st.POSTGRES_PORT,
            user='postgres',
            database='template1',
            password='postgres'
        )
        await connection.execute(CREATE_USER_IF_NOT_EXISTS)
        await connection.execute(CREATE_DB_IF_NOT_EXISTS)
        print('База создана!')
        await connection.close()
        connection = await asyncpg.connect(
            host=st.POSTGRES_SERVER,
            port=st.POSTGRES_PORT,
            user=st.POSTGRES_USER,
            database=st.POSTGRES_DB,
            password=st.POSTGRES_PASSWORD
        )
        await connection.execute(CREATE_TABLES)
        print('Таблицы созданы')
        await connection.close()


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
      CREATE ROLE {st.POSTGRES_USER} LOGIN PASSWORD '{st.POSTGRES_PASSWORD}';
   END IF;
END
$do$;"""

CREATE_DB_IF_NOT_EXISTS = \
f"""
CREATE DATABASE {st.POSTGRES_DB} OWNER '{st.POSTGRES_USER}';"""

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
CREATE TABLE IF NOT EXISTS apartments(
    id SERIAL PRIMARY KEY,
    building INTEGER REFERENCES buildings ON DELETE CASCADE,
    number INTEGER NOT NULL CHECK (number > 0),
    square NUMERIC (5, 2) NOT NULL CHECK (square > 0),
    UNIQUE (building, number)
);
CREATE TABLE IF NOT EXISTS counters(
    apartment INTEGER REFERENCES apartments ON DELETE CASCADE,
    number VARCHAR(10) NOT NULL UNIQUE
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
    counter varchar(10) REFERENCES counters (number),
    month integer NOT NULL CHECK(month >= 1 AND month <= 12),
    year integer NOT NULL CHECK(year > 1990 AND year < 2030),
    value NUMERIC (10,3) DEFAULT 0,
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
    FOREIGN KEY (month, year) REFERENCES periods (month, year)
);
"""
