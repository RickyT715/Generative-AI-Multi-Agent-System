"""Unit tests for the file processing pipeline (no LLM/API calls needed)."""

import os
import sqlite3
import tempfile

import pytest

from src.processing.file_processor import (
    detect_csv_table,
    insert_csv_to_sqlite,
    validate_csv_data,
)


class TestDetectCsvTable:
    """Tests for auto-detecting which table a CSV maps to."""

    def test_detect_customers(self):
        headers = ["name", "email", "phone", "account_type", "subscription_tier"]
        assert detect_csv_table(headers) == "customers"

    def test_detect_customers_minimal(self):
        headers = ["name", "email"]
        assert detect_csv_table(headers) == "customers"

    def test_detect_products(self):
        headers = ["name", "category", "price", "description"]
        assert detect_csv_table(headers) == "products"

    def test_detect_tickets(self):
        headers = [
            "customer_id",
            "subject",
            "description",
            "category",
            "priority",
            "status",
        ]
        assert detect_csv_table(headers) == "tickets"

    def test_detect_unknown(self):
        headers = ["foo", "bar", "baz"]
        assert detect_csv_table(headers) is None

    def test_detect_case_insensitive(self):
        headers = ["Name", "EMAIL", "Phone"]
        assert detect_csv_table(headers) == "customers"

    def test_detect_with_extra_columns(self):
        headers = ["name", "email", "phone", "extra_col", "another"]
        assert detect_csv_table(headers) == "customers"


class TestValidateCsvData:
    """Tests for CSV data validation."""

    def test_valid_customers(self):
        rows = [
            {"name": "Alice", "email": "alice@example.com"},
            {"name": "Bob", "email": "bob@example.com"},
        ]
        is_valid, errors = validate_csv_data(rows, "customers")
        assert is_valid
        assert errors == []

    def test_missing_required_field(self):
        rows = [
            {"name": "Alice", "email": ""},
        ]
        is_valid, errors = validate_csv_data(rows, "customers")
        assert not is_valid
        assert len(errors) == 1
        assert "email" in errors[0]

    def test_valid_products(self):
        rows = [
            {"name": "Widget", "category": "tools", "price": "9.99"},
        ]
        is_valid, errors = validate_csv_data(rows, "products")
        assert is_valid

    def test_invalid_price(self):
        rows = [
            {"name": "Widget", "category": "tools", "price": "not-a-number"},
        ]
        is_valid, errors = validate_csv_data(rows, "products")
        assert not is_valid
        assert "numeric" in errors[0]

    def test_valid_tickets(self):
        rows = [
            {"customer_id": "1", "subject": "Help", "description": "Need help"},
        ]
        is_valid, errors = validate_csv_data(rows, "tickets")
        assert is_valid

    def test_invalid_customer_id_in_ticket(self):
        rows = [
            {"customer_id": "abc", "subject": "Help", "description": "Need help"},
        ]
        is_valid, errors = validate_csv_data(rows, "tickets")
        assert not is_valid
        assert "integer" in errors[0]

    def test_unknown_table(self):
        is_valid, errors = validate_csv_data([], "nonexistent")
        assert not is_valid
        assert "Unknown table" in errors[0]


class TestInsertCsvToSqlite:
    """Tests for CSV insertion into SQLite with auto-ID."""

    @pytest.fixture()
    def temp_db(self):
        """Create a temporary SQLite database with the schema."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.executescript("""
            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(20),
                account_type VARCHAR(50),
                subscription_tier VARCHAR(50),
                join_date DATE,
                address TEXT,
                account_status VARCHAR(50)
            );
            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                name VARCHAR(255),
                category VARCHAR(100),
                price DECIMAL(10,2),
                description TEXT
            );
            CREATE TABLE tickets (
                ticket_id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                subject VARCHAR(255),
                description TEXT,
                category VARCHAR(100),
                priority VARCHAR(50),
                status VARCHAR(50),
                channel VARCHAR(50),
                assigned_agent VARCHAR(100),
                created_at TIMESTAMP,
                resolved_at TIMESTAMP,
                resolution TEXT,
                satisfaction_rating INTEGER
            );
        """)
        conn.commit()
        conn.close()

        yield path

        os.unlink(path)

    def test_insert_customers(self, temp_db):
        rows = [
            {"name": "Alice", "email": "alice@example.com", "phone": "555-0001"},
            {"name": "Bob", "email": "bob@example.com", "phone": "555-0002"},
        ]
        inserted = insert_csv_to_sqlite(rows, "customers", db_path=temp_db)
        assert inserted == 2

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id, name FROM customers ORDER BY customer_id")
        results = cursor.fetchall()
        conn.close()

        assert len(results) == 2
        assert results[0] == (1, "Alice")
        assert results[1] == (2, "Bob")

    def test_auto_id_continues(self, temp_db):
        """IDs should continue from existing max."""
        # Pre-insert a row
        conn = sqlite3.connect(temp_db)
        conn.execute(
            "INSERT INTO customers (customer_id, name, email) VALUES (100, 'Pre', 'pre@x.com')"
        )
        conn.commit()
        conn.close()

        rows = [{"name": "New", "email": "new@x.com"}]
        insert_csv_to_sqlite(rows, "customers", db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT customer_id FROM customers WHERE name = 'New'")
        new_id = cursor.fetchone()[0]
        conn.close()

        assert new_id == 101

    def test_insert_products(self, temp_db):
        rows = [
            {
                "name": "Widget",
                "category": "tools",
                "price": "9.99",
                "description": "A widget",
            },
        ]
        inserted = insert_csv_to_sqlite(rows, "products", db_path=temp_db)
        assert inserted == 1

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT product_id, name, price FROM products")
        result = cursor.fetchone()
        conn.close()

        assert result[0] == 1
        assert result[1] == "Widget"

    def test_insert_with_missing_optional_fields(self, temp_db):
        """Missing optional fields should become NULL."""
        rows = [{"name": "Minimal", "email": "min@x.com"}]
        insert_csv_to_sqlite(rows, "customers", db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT phone, account_type FROM customers WHERE name = 'Minimal'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result[0] is None
        assert result[1] is None
