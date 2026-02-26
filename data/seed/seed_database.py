"""Seed SQLite database with generated customer support data."""

import os
import sqlite3

from data.seed.generate_data import generate_all

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
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

CREATE TABLE IF NOT EXISTS products (
    product_id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL(10,2),
    description TEXT
);

CREATE TABLE IF NOT EXISTS tickets (
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
"""


def seed_database(db_path="data/customer_support.db"):
    """Create SQLite database and populate with generated data."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Remove existing database for clean seed
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create tables
    cursor.executescript(SCHEMA)

    # Generate data
    data = generate_all()

    # Insert customers
    cursor.executemany(
        """INSERT INTO customers
           (customer_id, name, email, phone, account_type,
            subscription_tier, join_date, address, account_status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                c["customer_id"], c["name"], c["email"], c["phone"],
                c["account_type"], c["subscription_tier"], c["join_date"],
                c["address"], c["account_status"],
            )
            for c in data["customers"]
        ],
    )

    # Insert products
    cursor.executemany(
        """INSERT INTO products
           (product_id, name, category, price, description)
           VALUES (?, ?, ?, ?, ?)""",
        [
            (
                p["product_id"], p["name"], p["category"],
                p["price"], p["description"],
            )
            for p in data["products"]
        ],
    )

    # Insert tickets
    cursor.executemany(
        """INSERT INTO tickets
           (ticket_id, customer_id, subject, description, category,
            priority, status, channel, assigned_agent,
            created_at, resolved_at, resolution, satisfaction_rating)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                t["ticket_id"], t["customer_id"], t["subject"],
                t["description"], t["category"], t["priority"],
                t["status"], t["channel"], t["assigned_agent"],
                t["created_at"], t["resolved_at"], t["resolution"],
                t["satisfaction_rating"],
            )
            for t in data["tickets"]
        ],
    )

    conn.commit()
    conn.close()

    print(f"  Seeded SQLite database at {db_path}")
    print(f"    - {len(data['customers'])} customers")
    print(f"    - {len(data['products'])} products")
    print(f"    - {len(data['tickets'])} tickets")

    return db_path


if __name__ == "__main__":
    seed_database()
