"""Generate synthetic customer support data using Faker."""

import json
import random
from datetime import timedelta

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)

SUBSCRIPTION_TIERS = ["free", "basic", "premium", "enterprise"]
ACCOUNT_TYPES = ["personal", "business"]
ACCOUNT_STATUSES = ["active", "inactive", "suspended"]
TICKET_STATUSES = ["open", "in_progress", "resolved", "closed"]
TICKET_PRIORITIES = ["low", "medium", "high", "critical"]
TICKET_CHANNELS = ["email", "chat", "phone", "web_form"]
TICKET_CATEGORIES = ["billing", "technical", "account", "complaint"]
AGENTS = [
    "Alice Johnson",
    "Bob Smith",
    "Carol Williams",
    "David Brown",
    "Eve Davis",
]

PRODUCT_CATALOG = [
    (
        "CloudSync Pro",
        "cloud_storage",
        29.99,
        "Enterprise cloud storage and sync solution with 1TB storage",
    ),
    (
        "SecureVault",
        "security",
        49.99,
        "Advanced cybersecurity suite with real-time threat detection",
    ),
    (
        "DataFlow Analytics",
        "analytics",
        79.99,
        "Business intelligence and data analytics platform",
    ),
    (
        "TeamChat Plus",
        "communication",
        12.99,
        "Team messaging and video conferencing tool",
    ),
    (
        "AutoBackup",
        "backup",
        19.99,
        "Automated backup solution for files and databases",
    ),
    ("APIConnect", "developer_tools", 39.99, "API management and integration platform"),
    ("SmartDocs", "productivity", 9.99, "AI-powered document management system"),
    ("NetMonitor", "networking", 59.99, "Network monitoring and performance analytics"),
    (
        "CodeDeploy",
        "developer_tools",
        34.99,
        "CI/CD pipeline and deployment automation",
    ),
    ("MailGuard", "security", 24.99, "Email security and anti-phishing solution"),
    ("CloudSync Basic", "cloud_storage", 9.99, "Basic cloud storage with 100GB space"),
    ("TaskMaster", "productivity", 14.99, "Project management and task tracking tool"),
    ("DataVault", "backup", 44.99, "Enterprise-grade data backup and recovery"),
    ("InsightAI", "analytics", 99.99, "AI-powered predictive analytics platform"),
    (
        "SecureConnect VPN",
        "security",
        15.99,
        "Business VPN with enterprise-level encryption",
    ),
]

TICKET_TEMPLATES = {
    "billing": [
        "I was charged twice for my {product} subscription this month. Please refund the duplicate charge.",
        "Can you explain the charge of ${amount:.2f} on my latest invoice? I don't recognize this.",
        "I need a refund for order #{order_id}. The product didn't meet expectations.",
        "My subscription to {product} was supposed to be ${price:.2f}/month but I'm being charged more.",
        "I want to cancel my {product} subscription and get a prorated refund.",
        "When will my refund for ticket #{ticket_ref} be processed?",
        "I upgraded from {current_tier} to {target_tier} but the pricing seems wrong.",
        "There's a billing discrepancy on my account. I need this resolved immediately.",
    ],
    "technical": [
        "The {product} app keeps crashing when I try to upload files larger than 50MB.",
        "I'm getting error code E-{error_code} when accessing the {product} dashboard.",
        "The sync feature in {product} stopped working after the latest update.",
        "{product} is running extremely slowly. Page loads take over 30 seconds.",
        "I can't connect {product} to our company's SSO provider.",
        "The API endpoint for {product} is returning 500 errors intermittently.",
        "Data export from {product} generates corrupted CSV files.",
        "Two-factor authentication isn't working with {product}. I'm locked out.",
    ],
    "account": [
        "I need to update my email address from {old_email} to {new_email}.",
        "How do I upgrade from {current_tier} to {target_tier}?",
        "I want to add 5 more user seats to my {product} team account.",
        "Can you transfer my account data to a new organization?",
        "I need to reset my password but the reset email isn't arriving.",
        "Please update my billing address to {address}.",
        "I want to merge my two accounts into one.",
        "How do I enable admin access for my team members?",
    ],
    "complaint": [
        "I've been waiting {days} days for a response to ticket #{ticket_ref}. This is unacceptable.",
        "The service quality of {product} has degraded significantly since last month.",
        "Your support team gave me incorrect information about the refund policy.",
        "I've had to contact support {count} times about the same issue with {product}.",
        "The downtime on {product} last week cost our business significant revenue.",
        "Your competitor offers better features at a lower price. I'm considering switching.",
        "The onboarding process for {product} is confusing and poorly documented.",
        "I was promised a feature that still hasn't been delivered after {days} days.",
    ],
}

RESOLUTIONS = {
    "billing": [
        "Refund of ${amount:.2f} processed. Will appear in 5-7 business days.",
        "Invoice adjusted. Credit applied to next billing cycle.",
        "Subscription pricing corrected. Difference refunded.",
        "Billing discrepancy resolved. Account credited.",
    ],
    "technical": [
        "Issue resolved after clearing cache and updating to latest version.",
        "Bug identified and fix deployed. Please try again.",
        "Configuration adjusted. Service restored to normal operation.",
        "Escalated to engineering team. Fix included in next release.",
    ],
    "account": [
        "Account information updated as requested.",
        "Subscription plan upgraded successfully.",
        "Password reset link sent to verified email address.",
        "Account settings modified per customer request.",
    ],
    "complaint": [
        "Escalated to management. Compensation credit applied to account.",
        "Service improvements scheduled. Customer notified of timeline.",
        "Follow-up meeting scheduled with account manager.",
        "Issue acknowledged. Process improvements implemented.",
    ],
}


def generate_customers(n=100):
    """Generate n synthetic customer records."""
    customers = []
    for i in range(1, n + 1):
        customers.append(
            {
                "customer_id": i,
                "name": fake.name(),
                "email": fake.unique.email(),
                "phone": fake.phone_number(),
                "account_type": random.choice(ACCOUNT_TYPES),
                "subscription_tier": random.choice(SUBSCRIPTION_TIERS),
                "join_date": fake.date_between(
                    start_date="-3y", end_date="today"
                ).isoformat(),
                "address": fake.address().replace("\n", ", "),
                "account_status": random.choices(
                    ACCOUNT_STATUSES, weights=[0.8, 0.15, 0.05]
                )[0],
            }
        )
    return customers


def generate_products():
    """Generate product catalog."""
    products = []
    for i, (name, category, price, description) in enumerate(PRODUCT_CATALOG, 1):
        products.append(
            {
                "product_id": i,
                "name": name,
                "category": category,
                "price": price,
                "description": description,
            }
        )
    return products


def generate_tickets(customers, products, n=500):
    """Generate n synthetic support tickets."""
    tickets = []
    for i in range(1, n + 1):
        customer = random.choice(customers)
        product = random.choice(products)
        category = random.choice(TICKET_CATEGORIES)
        status = random.choices(TICKET_STATUSES, weights=[0.15, 0.15, 0.5, 0.2])[0]
        priority = random.choices(TICKET_PRIORITIES, weights=[0.3, 0.4, 0.2, 0.1])[0]

        created_at = fake.date_time_between(start_date="-1y", end_date="now")
        resolved_at = None
        resolution = None
        satisfaction = None

        if status in ("resolved", "closed"):
            resolved_at = created_at + timedelta(hours=random.randint(1, 168))
            resolution = random.choice(RESOLUTIONS[category]).format(
                amount=product["price"]
            )
            satisfaction = random.choices(
                [1, 2, 3, 4, 5], weights=[0.05, 0.1, 0.2, 0.35, 0.3]
            )[0]

        template = random.choice(TICKET_TEMPLATES[category])
        description = template.format(
            product=product["name"],
            amount=product["price"] * random.uniform(1.0, 2.5),
            price=product["price"],
            order_id=random.randint(10000, 99999),
            ticket_ref=random.randint(1, max(1, i - 1)),
            error_code=random.randint(1000, 9999),
            old_email=fake.email(),
            new_email=fake.email(),
            current_tier=random.choice(SUBSCRIPTION_TIERS),
            target_tier=random.choice(SUBSCRIPTION_TIERS),
            address=fake.address().replace("\n", ", "),
            days=random.randint(3, 30),
            count=random.randint(2, 8),
            feature=random.choice(["dashboard", "reports", "settings", "API"]),
            action=random.choice(["login", "upload", "export", "sync"]),
            date=fake.date_this_year().isoformat(),
        )

        subject_prefixes = {
            "billing": [
                "Billing Issue",
                "Refund Request",
                "Invoice Question",
                "Payment Problem",
            ],
            "technical": [
                "Technical Issue",
                "Bug Report",
                "Error",
                "Performance Problem",
            ],
            "account": [
                "Account Update",
                "Account Question",
                "Access Request",
                "Account Change",
            ],
            "complaint": ["Complaint", "Escalation", "Service Issue", "Urgent Concern"],
        }

        tickets.append(
            {
                "ticket_id": i,
                "customer_id": customer["customer_id"],
                "subject": f"{random.choice(subject_prefixes[category])}: {product['name']}",
                "description": description,
                "category": category,
                "priority": priority,
                "status": status,
                "channel": random.choice(TICKET_CHANNELS),
                "assigned_agent": random.choice(AGENTS),
                "created_at": created_at.isoformat(),
                "resolved_at": resolved_at.isoformat() if resolved_at else None,
                "resolution": resolution,
                "satisfaction_rating": satisfaction,
            }
        )
    return tickets


def generate_all():
    """Generate all synthetic data and return as dict."""
    customers = generate_customers(100)
    products = generate_products()
    tickets = generate_tickets(customers, products, 500)

    return {
        "customers": customers,
        "products": products,
        "tickets": tickets,
    }


if __name__ == "__main__":
    data = generate_all()
    print(f"Generated {len(data['customers'])} customers")
    print(f"Generated {len(data['products'])} products")
    print(f"Generated {len(data['tickets'])} tickets")

    # Save to JSON for inspection
    with open("data/seed/generated_data.json", "w") as f:
        json.dump(data, f, indent=2, default=str)
    print("Saved to data/seed/generated_data.json")
