"""Comprehensive tests for synthetic data generation and PDF creation."""

import os
import sqlite3
import tempfile


class TestCustomerGeneration:
    """Test customer data generation in detail."""

    def test_customer_count(self):
        from data.seed.generate_data import generate_customers

        assert len(generate_customers(1)) == 1
        assert len(generate_customers(50)) == 50
        assert len(generate_customers(100)) == 100

    def test_customer_fields(self):
        from data.seed.generate_data import generate_customers

        customers = generate_customers(5)
        required_fields = [
            "customer_id",
            "name",
            "email",
            "phone",
            "account_type",
            "subscription_tier",
            "join_date",
            "address",
            "account_status",
        ]
        for c in customers:
            for field in required_fields:
                assert field in c, f"Missing field: {field}"

    def test_customer_ids_sequential(self):
        from data.seed.generate_data import generate_customers

        customers = generate_customers(10)
        ids = [c["customer_id"] for c in customers]
        assert ids == list(range(1, 11))

    def test_customer_unique_emails(self):
        from data.seed.generate_data import generate_customers

        customers = generate_customers(20)
        emails = [c["email"] for c in customers]
        assert len(emails) == len(set(emails))

    def test_customer_valid_account_types(self):
        from data.seed.generate_data import ACCOUNT_TYPES, generate_customers

        customers = generate_customers(50)
        for c in customers:
            assert c["account_type"] in ACCOUNT_TYPES

    def test_customer_valid_tiers(self):
        from data.seed.generate_data import SUBSCRIPTION_TIERS, generate_customers

        customers = generate_customers(50)
        for c in customers:
            assert c["subscription_tier"] in SUBSCRIPTION_TIERS

    def test_customer_valid_statuses(self):
        from data.seed.generate_data import ACCOUNT_STATUSES, generate_customers

        customers = generate_customers(50)
        for c in customers:
            assert c["account_status"] in ACCOUNT_STATUSES


class TestProductGeneration:
    """Test product catalog generation."""

    def test_product_count(self):
        from data.seed.generate_data import generate_products

        products = generate_products()
        assert len(products) == 15

    def test_product_fields(self):
        from data.seed.generate_data import generate_products

        products = generate_products()
        for p in products:
            assert "product_id" in p
            assert "name" in p
            assert "category" in p
            assert "price" in p
            assert "description" in p

    def test_product_prices_positive(self):
        from data.seed.generate_data import generate_products

        products = generate_products()
        for p in products:
            assert p["price"] > 0

    def test_product_ids_sequential(self):
        from data.seed.generate_data import generate_products

        products = generate_products()
        ids = [p["product_id"] for p in products]
        assert ids == list(range(1, 16))


class TestTicketGeneration:
    """Test support ticket generation."""

    def test_ticket_count(self):
        from data.seed.generate_data import (
            generate_customers,
            generate_products,
            generate_tickets,
        )

        c = generate_customers(10)
        p = generate_products()
        tickets = generate_tickets(c, p, 100)
        assert len(tickets) == 100

    def test_ticket_fields(self):
        from data.seed.generate_data import (
            generate_customers,
            generate_products,
            generate_tickets,
        )

        c = generate_customers(5)
        p = generate_products()
        tickets = generate_tickets(c, p, 10)
        required = [
            "ticket_id",
            "customer_id",
            "subject",
            "description",
            "category",
            "priority",
            "status",
            "channel",
            "assigned_agent",
            "created_at",
        ]
        for t in tickets:
            for field in required:
                assert field in t, f"Missing field: {field}"

    def test_ticket_valid_categories(self):
        from data.seed.generate_data import (
            TICKET_CATEGORIES,
            generate_customers,
            generate_products,
            generate_tickets,
        )

        c = generate_customers(10)
        p = generate_products()
        tickets = generate_tickets(c, p, 100)
        for t in tickets:
            assert t["category"] in TICKET_CATEGORIES

    def test_ticket_valid_priorities(self):
        from data.seed.generate_data import (
            TICKET_PRIORITIES,
            generate_customers,
            generate_products,
            generate_tickets,
        )

        c = generate_customers(10)
        p = generate_products()
        tickets = generate_tickets(c, p, 100)
        for t in tickets:
            assert t["priority"] in TICKET_PRIORITIES

    def test_ticket_valid_statuses(self):
        from data.seed.generate_data import (
            TICKET_STATUSES,
            generate_customers,
            generate_products,
            generate_tickets,
        )

        c = generate_customers(10)
        p = generate_products()
        tickets = generate_tickets(c, p, 100)
        for t in tickets:
            assert t["status"] in TICKET_STATUSES

    def test_ticket_customer_ids_valid(self):
        from data.seed.generate_data import (
            generate_customers,
            generate_products,
            generate_tickets,
        )

        c = generate_customers(10)
        p = generate_products()
        tickets = generate_tickets(c, p, 50)
        valid_ids = {cust["customer_id"] for cust in c}
        for t in tickets:
            assert t["customer_id"] in valid_ids

    def test_resolved_tickets_have_resolution(self):
        from data.seed.generate_data import (
            generate_customers,
            generate_products,
            generate_tickets,
        )

        c = generate_customers(10)
        p = generate_products()
        tickets = generate_tickets(c, p, 200)
        for t in tickets:
            if t["status"] in ("resolved", "closed"):
                assert t["resolved_at"] is not None
                assert t["resolution"] is not None


class TestGenerateAll:
    """Test the full data generation pipeline."""

    def test_generate_all(self):
        from data.seed.generate_data import generate_all

        data = generate_all()
        assert "customers" in data
        assert "products" in data
        assert "tickets" in data
        assert len(data["customers"]) == 100
        assert len(data["products"]) == 15
        assert len(data["tickets"]) == 500


class TestSeedDatabase:
    """Test database seeding."""

    def test_seed_creates_db(self):
        from data.seed.seed_database import seed_database

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            seed_database(db_path)
            assert os.path.exists(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM customers")
            assert cursor.fetchone()[0] == 100

            cursor.execute("SELECT COUNT(*) FROM products")
            assert cursor.fetchone()[0] == 15

            cursor.execute("SELECT COUNT(*) FROM tickets")
            assert cursor.fetchone()[0] == 500

            conn.close()
        finally:
            try:
                os.unlink(db_path)
            except PermissionError:
                pass

    def test_seed_schema_correct(self):
        from data.seed.seed_database import seed_database

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            seed_database(db_path)

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check customers table columns
            cursor.execute("PRAGMA table_info(customers)")
            columns = {row[1] for row in cursor.fetchall()}
            assert "customer_id" in columns
            assert "name" in columns
            assert "email" in columns

            # Check tickets table columns
            cursor.execute("PRAGMA table_info(tickets)")
            columns = {row[1] for row in cursor.fetchall()}
            assert "ticket_id" in columns
            assert "customer_id" in columns
            assert "category" in columns

            conn.close()
        finally:
            try:
                os.unlink(db_path)
            except PermissionError:
                pass


class TestPDFGeneration:
    """Test PDF generation."""

    def test_generate_refund_policy(self):
        from data.seed.generate_pdfs import generate_refund_policy

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_refund_policy(tmpdir)
            assert os.path.exists(path)
            assert path.endswith(".pdf")
            assert os.path.getsize(path) > 0

    def test_generate_privacy_policy(self):
        from data.seed.generate_pdfs import generate_privacy_policy

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_privacy_policy(tmpdir)
            assert os.path.exists(path)
            assert path.endswith(".pdf")
            assert os.path.getsize(path) > 0

    def test_generate_terms_of_service(self):
        from data.seed.generate_pdfs import generate_terms_of_service

        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_terms_of_service(tmpdir)
            assert os.path.exists(path)
            assert path.endswith(".pdf")
            assert os.path.getsize(path) > 0

    def test_generate_all_pdfs(self):
        from data.seed.generate_pdfs import generate_all_pdfs

        with tempfile.TemporaryDirectory() as tmpdir:
            paths = generate_all_pdfs(tmpdir)
            assert len(paths) == 3
            for p in paths:
                assert os.path.exists(p)
                assert os.path.getsize(p) > 1000  # non-trivial file
