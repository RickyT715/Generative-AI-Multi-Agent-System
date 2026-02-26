"""Generate test files with distinctive, verifiable content for E2E testing."""

import csv
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "test_uploads")


def generate_test_customers_csv(output_dir):
    """Generate test_customers.csv with 5 distinctive customers."""
    path = os.path.join(output_dir, "test_customers.csv")
    rows = [
        {
            "name": "Ziggy Stardust",
            "email": "ziggy@stardust.io",
            "phone": "555-0101",
            "account_type": "business",
            "subscription_tier": "enterprise",
            "join_date": "2024-01-15",
            "address": "42 Nebula Lane, Space City, SC 00001",
            "account_status": "active",
        },
        {
            "name": "Luna Lovecraft",
            "email": "luna@lovecraft.net",
            "phone": "555-0102",
            "account_type": "business",
            "subscription_tier": "premium",
            "join_date": "2024-03-22",
            "address": "7 Moonbeam Ave, Arkham, MA 01001",
            "account_status": "active",
        },
        {
            "name": "Rex Nebula",
            "email": "rex@nebula.com",
            "phone": "555-0103",
            "account_type": "personal",
            "subscription_tier": "basic",
            "join_date": "2024-06-10",
            "address": "99 Galaxy Rd, Cosmos, TX 77001",
            "account_status": "active",
        },
        {
            "name": "Aria Quantum",
            "email": "aria@quantum.org",
            "phone": "555-0104",
            "account_type": "business",
            "subscription_tier": "enterprise",
            "join_date": "2024-02-28",
            "address": "123 Entangle St, Qubit, CA 94001",
            "account_status": "active",
        },
        {
            "name": "Nova Blaze",
            "email": "nova@blaze.io",
            "phone": "555-0105",
            "account_type": "personal",
            "subscription_tier": "free",
            "join_date": "2024-08-01",
            "address": "5 Supernova Blvd, Starfield, WA 98001",
            "account_status": "inactive",
        },
    ]

    fieldnames = [
        "name",
        "email",
        "phone",
        "account_type",
        "subscription_tier",
        "join_date",
        "address",
        "account_status",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Generated {path} ({len(rows)} rows)")
    return path


def generate_test_tickets_csv(output_dir):
    """Generate test_tickets.csv with 5 distinctive tickets."""
    path = os.path.join(output_dir, "test_tickets.csv")
    rows = [
        {
            "customer_id": "1",
            "subject": "Quantum Sync Error on CloudSync Pro",
            "description": "Getting a quantum sync error E-4242 when trying to sync files larger than 2GB through CloudSync Pro.",
            "category": "technical",
            "priority": "high",
            "status": "open",
            "channel": "email",
            "assigned_agent": "Alice Johnson",
        },
        {
            "customer_id": "2",
            "subject": "Warp Drive Billing Discrepancy",
            "description": "I was charged $299.99 instead of the listed $29.99 for my CloudSync Pro subscription. The decimal point seems to have warped.",
            "category": "billing",
            "priority": "critical",
            "status": "open",
            "channel": "phone",
            "assigned_agent": "Bob Smith",
        },
        {
            "customer_id": "3",
            "subject": "Nebula Dashboard Not Loading",
            "description": "The DataFlow Analytics dashboard shows a spinning nebula animation but never loads actual data. Tried clearing cache.",
            "category": "technical",
            "priority": "medium",
            "status": "in_progress",
            "channel": "chat",
            "assigned_agent": "Carol Williams",
        },
        {
            "customer_id": "4",
            "subject": "Request to Upgrade to Galactic Tier",
            "description": "We need to upgrade our subscription from premium to enterprise tier for our team of 50 users.",
            "category": "account",
            "priority": "low",
            "status": "open",
            "channel": "web_form",
            "assigned_agent": "David Brown",
        },
        {
            "customer_id": "5",
            "subject": "StarShield False Positive Blocking API",
            "description": "SecureVault's threat detection is flagging our legitimate API calls as malicious. Need whitelist configuration.",
            "category": "technical",
            "priority": "high",
            "status": "open",
            "channel": "email",
            "assigned_agent": "Eve Davis",
        },
    ]

    fieldnames = [
        "customer_id",
        "subject",
        "description",
        "category",
        "priority",
        "status",
        "channel",
        "assigned_agent",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Generated {path} ({len(rows)} rows)")
    return path


def generate_quantum_backup_pdf(output_dir):
    """Generate quantum_backup_guide.pdf with verifiable product guide content."""
    try:
        from fpdf import FPDF
    except ImportError:
        print("  Warning: fpdf2 not installed. Run: pip install fpdf2")
        return None

    path = os.path.join(output_dir, "quantum_backup_guide.pdf")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(
        0, 15, "Quantum Backup Ultra - Product Guide", new_x="LMARGIN", new_y="NEXT"
    )
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Overview", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        7,
        (
            "Quantum Backup Ultra is our enterprise-grade backup and disaster recovery solution. "
            "It provides real-time continuous data protection with quantum-encrypted storage, "
            "ensuring your critical business data is always safe and recoverable."
        ),
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "System Requirements", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    requirements = [
        "Operating System: Windows 10/11, macOS 12+, or Ubuntu 20.04+",
        "Processor: Intel i5 or AMD Ryzen 5 (minimum)",
        "RAM: 16GB minimum (32GB recommended for large-scale deployments)",
        "Storage: 500MB for installation, plus backup storage space",
        "Network: Broadband internet connection (50 Mbps minimum)",
        "Browser: Chrome 90+, Firefox 88+, or Edge 90+ for web dashboard",
    ]
    for req in requirements:
        pdf.cell(0, 7, f"  - {req}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Pricing", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(
        0,
        7,
        (
            "Quantum Backup Ultra is available at $44.99/month per server for the standard plan. "
            "Enterprise plans with unlimited servers start at $199.99/month. "
            "All plans include 30-day free trial with full feature access."
        ),
    )
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Installation Steps", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    steps = [
        "1. Download the installer from portal.quantumbackup.io/download",
        "2. Run the installer with administrator privileges",
        "3. Enter your license key when prompted (found in your welcome email)",
        "4. Select backup targets (files, databases, or full system)",
        "5. Configure backup schedule (recommended: continuous with hourly snapshots)",
        "6. Set up remote storage endpoint (cloud or on-premises)",
        "7. Run initial backup verification to confirm setup",
    ]
    for step in steps:
        pdf.cell(0, 7, f"  {step}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Key Features", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    features = [
        "Quantum-encrypted data transfer and storage (AES-256 + post-quantum lattice)",
        "Continuous Data Protection (CDP) with sub-second RPO",
        "One-click bare-metal restore for disaster recovery",
        "Deduplication engine achieving up to 95% storage savings",
        "Multi-cloud support: AWS, Azure, GCP, and private cloud",
        "Compliance: SOC 2, HIPAA, GDPR, and FedRAMP certified",
    ]
    for feat in features:
        pdf.cell(0, 7, f"  - {feat}", new_x="LMARGIN", new_y="NEXT")

    pdf.output(path)
    print(f"  Generated {path}")
    return path


def generate_starshield_faq_txt(output_dir):
    """Generate starshield_faq.txt with verifiable FAQ content."""
    path = os.path.join(output_dir, "starshield_faq.txt")
    content = """StarShield Antivirus - Frequently Asked Questions
==================================================

Q: What is StarShield Antivirus?
A: StarShield Antivirus is our next-generation endpoint security solution that uses
AI-powered threat detection to protect your devices from malware, ransomware, phishing,
and zero-day attacks. It operates in real-time with minimal system impact.

Q: How much does StarShield Antivirus cost?
A: StarShield Antivirus is available at $7.99/month per device for individual users.
Business plans start at $5.99/month per device (minimum 10 devices). Annual billing
provides a 20% discount. All plans include a 14-day free trial.

Q: What is the malware detection rate?
A: StarShield achieves a 99.7% detection rate in independent lab testing by AV-Comparatives
(January 2025). This includes a 99.9% detection rate for known threats and a 98.5%
detection rate for zero-day threats using our neural heuristic engine.

Q: What operating systems are supported?
A: StarShield supports Windows 10/11, macOS 12 (Monterey) and later, Ubuntu 20.04+,
Android 11+, and iOS 15+. A lightweight agent is also available for Linux servers.

Q: Does StarShield slow down my computer?
A: No. StarShield uses less than 1% CPU on average during background scanning and
approximately 150MB of RAM. Our Smart Scan technology schedules intensive scans during
idle periods to minimize impact on your workflow.

Q: How do I contact support?
A: You can reach our support team through the following channels:
   - Email: support@starshield.io
   - Phone: 1-800-STAR-SHIELD (1-800-782-7744), available 24/7
   - Live Chat: Available on starshield.io from 6am to 10pm PST
   - Knowledge Base: kb.starshield.io for self-service articles

Q: Can I use StarShield alongside other antivirus software?
A: We recommend using StarShield as your primary antivirus solution. Running multiple
real-time antivirus engines simultaneously can cause conflicts and performance issues.
StarShield will automatically detect other AV software and offer to manage the transition.

Q: How does the AI threat detection work?
A: StarShield uses a multi-layered AI approach: (1) a lightweight neural network on-device
for instant detection, (2) behavioral analysis that monitors process activity patterns,
and (3) cloud-based deep learning models for analyzing suspicious files. This combination
allows us to detect threats that signature-based solutions miss.

Q: What is the refund policy?
A: We offer a full refund within 30 days of purchase, no questions asked. After 30 days,
prorated refunds are available for annual subscriptions. Monthly subscriptions can be
cancelled at any time with no further charges.

Q: Does StarShield include a VPN?
A: The Premium plan ($12.99/month) includes StarShield VPN with servers in 50+ countries.
The standard plan does not include VPN, but you can add it for an additional $4.99/month.
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  Generated {path}")
    return path


def generate_all_test_files():
    """Generate all test files."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("Generating test files for upload testing...\n")
    files = []
    files.append(generate_test_customers_csv(OUTPUT_DIR))
    files.append(generate_test_tickets_csv(OUTPUT_DIR))
    files.append(generate_quantum_backup_pdf(OUTPUT_DIR))
    files.append(generate_starshield_faq_txt(OUTPUT_DIR))

    generated = [f for f in files if f is not None]
    print(f"\nGenerated {len(generated)} test file(s) in {OUTPUT_DIR}")
    return generated


if __name__ == "__main__":
    generate_all_test_files()
