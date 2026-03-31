"""DuckDB schema setup and prompt-friendly schema description helpers."""

from __future__ import annotations

from functools import lru_cache

import duckdb


CUSTOMERS = [
	(1, "Alice Johnson", "United States"),
	(2, "Bruno Martins", "Brazil"),
	(3, "Chloe Dubois", "France"),
	(4, "Deepak Sharma", "India"),
	(5, "Elena Petrova", "Germany"),
	(6, "Fatima Hassan", "United Arab Emirates"),
]

ORDERS = [
	(1, 1, 249.99, "2026-01-15"),
	(2, 1, 89.50, "2026-02-03"),
	(3, 2, 540.00, "2026-01-22"),
	(4, 3, 120.75, "2026-02-11"),
	(5, 4, 980.40, "2026-02-18"),
	(6, 4, 310.20, "2026-03-02"),
	(7, 5, 75.25, "2026-03-05"),
	(8, 6, 410.00, "2026-03-12"),
	(9, 2, 199.99, "2026-03-16"),
	(10, 3, 650.10, "2026-03-20"),
]


def _create_tables(connection: duckdb.DuckDBPyConnection) -> None:
	connection.execute(
		"""
		CREATE TABLE customers (
			id INTEGER PRIMARY KEY,
			name VARCHAR NOT NULL,
			country VARCHAR NOT NULL
		)
		"""
	)
	connection.execute(
		"""
		CREATE TABLE orders (
			id INTEGER PRIMARY KEY,
			customer_id INTEGER NOT NULL,
			amount DECIMAL(10, 2) NOT NULL,
			date DATE NOT NULL,
			FOREIGN KEY (customer_id) REFERENCES customers(id)
		)
		"""
	)


def _seed_data(connection: duckdb.DuckDBPyConnection) -> None:
	connection.executemany(
		"INSERT INTO customers (id, name, country) VALUES (?, ?, ?)",
		CUSTOMERS,
	)
	connection.executemany(
		"INSERT INTO orders (id, customer_id, amount, date) VALUES (?, ?, ?, ?)",
		ORDERS,
	)


def _initialize_database(connection: duckdb.DuckDBPyConnection) -> duckdb.DuckDBPyConnection:
	_create_tables(connection)
	_seed_data(connection)
	return connection


@lru_cache(maxsize=1)
def get_connection() -> duckdb.DuckDBPyConnection:
	return _initialize_database(duckdb.connect(database=":memory:"))


def get_schema_description() -> str:
	connection = get_connection()
	columns = connection.execute(
		"""
		SELECT table_name, column_name, data_type
		FROM information_schema.columns
		WHERE table_schema = 'main'
		ORDER BY table_name, ordinal_position
		"""
	).fetchall()

	tables: dict[str, list[str]] = {}
	for table_name, column_name, data_type in columns:
		tables.setdefault(table_name, []).append(f"- {column_name}: {data_type}")

	lines = [
		"Database: DuckDB (in-memory)",
		"",
		"Tables:",
	]

	for table_name, table_columns in tables.items():
		lines.append(f"{table_name}")
		lines.extend(table_columns)
		lines.append("")

	lines.extend(
		[
			"Relationships:",
			"- orders.customer_id references customers.id",
			"",
			"Notes:",
			"- customers stores the customer profile and home country.",
			"- orders stores one row per purchase with order amount and order date.",
		]
	)

	return "\n".join(lines).strip()


__all__ = ["get_connection", "get_schema_description"]