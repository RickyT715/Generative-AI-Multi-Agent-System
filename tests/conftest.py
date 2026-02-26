"""Shared test fixtures."""

import os
import sqlite3
import tempfile

import pytest


@pytest.fixture
def fake_llm():
    """Create a FakeListChatModel for testing without API keys."""
    from langchain_community.chat_models import FakeListChatModel

    return FakeListChatModel(
        responses=["This is a test response from the fake LLM."]
    )


@pytest.fixture
def fake_llm_with_routing():
    """Create a fake LLM that returns structured routing responses."""
    from langchain_community.chat_models import FakeListChatModel

    return FakeListChatModel(
        responses=['{"datasource": "sql_agent"}']
    )


@pytest.fixture
def temp_sqlite_db():
    """Create a temporary SQLite database with test data."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE,
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
            customer_id INTEGER REFERENCES customers(customer_id),
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

        INSERT INTO customers VALUES
            (1, 'John Doe', 'john@example.com', '555-0101', 'personal', 'premium', '2024-01-15', '123 Main St', 'active'),
            (2, 'Jane Smith', 'jane@example.com', '555-0102', 'business', 'enterprise', '2023-06-20', '456 Oak Ave', 'active'),
            (3, 'Bob Wilson', 'bob@example.com', '555-0103', 'personal', 'free', '2025-03-10', '789 Pine Rd', 'inactive');

        INSERT INTO products VALUES
            (1, 'CloudSync Pro', 'cloud_storage', 29.99, 'Enterprise cloud storage'),
            (2, 'SecureVault', 'security', 49.99, 'Cybersecurity suite');

        INSERT INTO tickets VALUES
            (1, 1, 'Billing Issue', 'Charged twice for subscription', 'billing', 'high', 'open', 'email', 'Alice', '2025-01-10', NULL, NULL, NULL),
            (2, 1, 'Login Problem', 'Cannot access dashboard', 'technical', 'medium', 'resolved', 'chat', 'Bob', '2025-01-05', '2025-01-06', 'Password reset', 5),
            (3, 2, 'Refund Request', 'Want refund for last month', 'billing', 'low', 'closed', 'phone', 'Carol', '2025-01-01', '2025-01-03', 'Refund processed', 4);
    """)

    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)
