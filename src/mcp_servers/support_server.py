"""FastMCP server exposing customer support tools."""

import os
import sqlite3
from datetime import datetime

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("CustomerSupport")

DB_PATH = os.getenv("SQLITE_DB_PATH", "data/customer_support.db")


def _get_connection():
    """Get a SQLite connection."""
    return sqlite3.connect(DB_PATH)


@mcp.tool()
def lookup_customer(customer_name: str) -> str:
    """Look up a customer by name and return their profile summary.

    Args:
        customer_name: Full or partial name of the customer to look up.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM customers WHERE name LIKE ?",
        (f"%{customer_name}%",),
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()

    if not rows:
        return f"No customer found matching '{customer_name}'"

    results = []
    for row in rows:
        customer = dict(zip(columns, row, strict=False))
        results.append(
            f"Customer ID: {customer['customer_id']}\n"
            f"Name: {customer['name']}\n"
            f"Email: {customer['email']}\n"
            f"Phone: {customer['phone']}\n"
            f"Account Type: {customer['account_type']}\n"
            f"Subscription: {customer['subscription_tier']}\n"
            f"Status: {customer['account_status']}\n"
            f"Join Date: {customer['join_date']}"
        )

    return "\n\n---\n\n".join(results)


@mcp.tool()
def get_ticket_history(customer_id: int) -> str:
    """Get support ticket history for a customer.

    Args:
        customer_id: The ID of the customer to look up tickets for.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM tickets WHERE customer_id = ? ORDER BY created_at DESC",
        (customer_id,),
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    conn.close()

    if not rows:
        return f"No tickets found for customer ID {customer_id}"

    results = []
    for row in rows:
        ticket = dict(zip(columns, row, strict=False))
        results.append(
            f"Ticket #{ticket['ticket_id']}: {ticket['subject']}\n"
            f"  Category: {ticket['category']} | Priority: {ticket['priority']}\n"
            f"  Status: {ticket['status']} | Channel: {ticket['channel']}\n"
            f"  Created: {ticket['created_at']}\n"
            f"  Agent: {ticket['assigned_agent']}"
        )

    return f"Found {len(rows)} tickets:\n\n" + "\n\n".join(results)


@mcp.tool()
def create_ticket(
    customer_id: int,
    subject: str,
    description: str,
    priority: str = "medium",
    category: str = "general",
) -> str:
    """Create a new support ticket for a customer.

    Args:
        customer_id: The ID of the customer creating the ticket.
        subject: Brief subject line for the ticket.
        description: Detailed description of the issue.
        priority: Priority level (low, medium, high, critical).
        category: Ticket category (billing, technical, account, complaint).
    """
    conn = _get_connection()
    cursor = conn.cursor()

    # Verify customer exists
    cursor.execute("SELECT name FROM customers WHERE customer_id = ?", (customer_id,))
    customer = cursor.fetchone()
    if not customer:
        conn.close()
        return f"Error: Customer ID {customer_id} not found"

    cursor.execute(
        """INSERT INTO tickets
           (customer_id, subject, description, category, priority,
            status, channel, assigned_agent, created_at)
           VALUES (?, ?, ?, ?, ?, 'open', 'chat', 'AI Assistant', ?)""",
        (
            customer_id,
            subject,
            description,
            category,
            priority,
            datetime.now().isoformat(),
        ),
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return (
        f"Ticket #{ticket_id} created successfully!\n"
        f"  Customer: {customer[0]} (ID: {customer_id})\n"
        f"  Subject: {subject}\n"
        f"  Priority: {priority}\n"
        f"  Category: {category}\n"
        f"  Status: open"
    )


if __name__ == "__main__":
    mcp.run()
