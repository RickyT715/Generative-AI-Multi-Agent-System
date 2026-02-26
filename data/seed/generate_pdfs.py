"""Generate sample company policy PDFs using fpdf2."""

import os

from fpdf import FPDF


class PolicyPDF(FPDF):
    """Custom PDF class with consistent styling."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "TechCorp Inc. - Confidential", align="C", ln=True)
        self.ln(2)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def add_title(self, title):
        self.set_font("Helvetica", "B", 18)
        self.set_text_color(0, 51, 102)
        self.cell(0, 15, title, ln=True, align="C")
        self.ln(5)

    def add_subtitle(self, text):
        self.set_font("Helvetica", "I", 11)
        self.set_text_color(80, 80, 80)
        self.cell(0, 8, text, ln=True, align="C")
        self.ln(8)

    def add_section(self, title):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, title, ln=True)
        self.ln(3)

    def add_subsection(self, title):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(51, 51, 51)
        self.cell(0, 8, title, ln=True)
        self.ln(2)

    def add_body(self, text):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)
        self.ln(4)

    def add_bullet(self, text):
        self.set_font("Helvetica", "", 11)
        self.set_text_color(0, 0, 0)
        self.cell(10)
        self.cell(5, 6, chr(8226))
        self.multi_cell(0, 6, text)
        self.ln(1)


def generate_refund_policy(output_dir):
    """Generate Refund & Returns Policy PDF."""
    pdf = PolicyPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.add_title("Refund & Returns Policy")
    pdf.add_subtitle("Effective Date: January 1, 2026 | Version 3.2")

    pdf.add_section("1. Overview")
    pdf.add_body(
        "TechCorp Inc. is committed to ensuring customer satisfaction with all our products "
        "and services. This Refund and Returns Policy outlines the terms and conditions under "
        "which customers may request refunds, returns, or exchanges for purchased products "
        "and subscription services."
    )

    pdf.add_section("2. Eligibility for Refunds")
    pdf.add_subsection("2.1 Software Subscriptions")
    pdf.add_body(
        "Customers may request a full refund within 30 days of the initial purchase date "
        "for any subscription plan. After the 30-day period, refunds will be prorated based "
        "on the remaining subscription term. Annual subscriptions are eligible for a prorated "
        "refund up to 90 days after purchase."
    )
    pdf.add_bullet("Free trial conversions: Full refund within 14 days of first charge")
    pdf.add_bullet("Monthly plans: Full refund within 30 days, no refund after")
    pdf.add_bullet("Annual plans: Prorated refund within 90 days of purchase")
    pdf.add_bullet("Enterprise plans: Subject to individual contract terms")

    pdf.add_subsection("2.2 One-Time Purchases")
    pdf.add_body(
        "Products purchased as one-time licenses are eligible for a full refund within "
        "14 days of purchase, provided the software has not been activated on more than "
        "one device. Activated licenses may be eligible for a partial refund at TechCorp's "
        "discretion."
    )

    pdf.add_section("3. Refund Process")
    pdf.add_body("To request a refund, customers must follow these steps:")
    pdf.add_bullet("Step 1: Log into your TechCorp account and navigate to Billing > Refund Request")
    pdf.add_bullet("Step 2: Select the product or subscription for which you want a refund")
    pdf.add_bullet("Step 3: Provide a reason for the refund request")
    pdf.add_bullet("Step 4: Submit the request. You will receive a confirmation email within 24 hours")
    pdf.add_bullet("Step 5: Refunds are processed within 5-10 business days to the original payment method")

    pdf.add_section("4. Exceptions and Non-Refundable Items")
    pdf.add_body("The following items and services are non-refundable:")
    pdf.add_bullet("Setup and configuration fees for enterprise deployments")
    pdf.add_bullet("Custom development or integration work")
    pdf.add_bullet("Training sessions that have already been delivered")
    pdf.add_bullet("Domain registration fees")
    pdf.add_bullet("Third-party add-ons purchased through our marketplace")

    pdf.add_section("5. Exchanges and Plan Changes")
    pdf.add_body(
        "Customers may change their subscription plan at any time. When upgrading, the "
        "price difference will be prorated for the current billing period. When downgrading, "
        "the new rate takes effect at the start of the next billing cycle. No refunds are "
        "issued for mid-cycle downgrades, but account credit may be applied."
    )

    pdf.add_section("6. Dispute Resolution")
    pdf.add_body(
        "If a refund request is denied and the customer disagrees with the decision, "
        "they may escalate the matter by contacting our Customer Advocacy team at "
        "advocacy@techcorp.com. Disputes are typically resolved within 15 business days. "
        "For unresolved disputes, customers may seek resolution through binding arbitration "
        "as outlined in our Terms of Service."
    )

    pdf.add_section("7. Contact Information")
    pdf.add_body(
        "For refund inquiries, please contact:\n"
        "Email: billing@techcorp.com\n"
        "Phone: 1-800-TECHCORP (1-800-832-4267)\n"
        "Hours: Monday-Friday, 9:00 AM - 6:00 PM EST\n"
        "Live Chat: Available 24/7 at support.techcorp.com"
    )

    path = os.path.join(output_dir, "refund_policy.pdf")
    pdf.output(path)
    return path


def generate_privacy_policy(output_dir):
    """Generate Privacy Policy PDF."""
    pdf = PolicyPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.add_title("Privacy Policy")
    pdf.add_subtitle("Effective Date: January 1, 2026 | Version 4.1")

    pdf.add_section("1. Introduction")
    pdf.add_body(
        "TechCorp Inc. (\"we\", \"us\", or \"our\") respects your privacy and is committed "
        "to protecting your personal data. This Privacy Policy explains how we collect, use, "
        "disclose, and safeguard your information when you use our products and services. "
        "This policy applies to all TechCorp products, websites, and services."
    )

    pdf.add_section("2. Information We Collect")
    pdf.add_subsection("2.1 Information You Provide")
    pdf.add_bullet("Account information: name, email address, phone number, billing address")
    pdf.add_bullet("Payment information: credit card numbers, billing details (processed by secure third-party)")
    pdf.add_bullet("Profile data: company name, job title, preferences, profile picture")
    pdf.add_bullet("Communications: support tickets, chat messages, feedback, survey responses")
    pdf.add_bullet("Content: files, documents, and data you upload to our services")

    pdf.add_subsection("2.2 Information Collected Automatically")
    pdf.add_bullet("Device information: IP address, browser type, operating system, device identifiers")
    pdf.add_bullet("Usage data: features used, pages visited, time spent, click patterns")
    pdf.add_bullet("Log data: access times, error logs, referring URLs, search queries")
    pdf.add_bullet("Cookies and tracking: session cookies, analytics cookies, preference cookies")

    pdf.add_section("3. How We Use Your Information")
    pdf.add_body("We use collected information for the following purposes:")
    pdf.add_bullet("Provide, maintain, and improve our products and services")
    pdf.add_bullet("Process transactions and send billing notifications")
    pdf.add_bullet("Send technical notices, updates, security alerts, and support messages")
    pdf.add_bullet("Respond to customer service requests and support needs")
    pdf.add_bullet("Monitor and analyze trends, usage, and activities")
    pdf.add_bullet("Detect, investigate, and prevent fraudulent or unauthorized activities")
    pdf.add_bullet("Personalize and improve your experience")
    pdf.add_bullet("Comply with legal obligations and enforce our terms")

    pdf.add_section("4. Data Sharing and Disclosure")
    pdf.add_body("We do not sell your personal information. We may share data with:")
    pdf.add_bullet("Service providers: cloud hosting, payment processing, analytics, email delivery")
    pdf.add_bullet("Business partners: with your consent, for integrated services")
    pdf.add_bullet("Legal requirements: when required by law, regulation, or legal process")
    pdf.add_bullet("Business transfers: in connection with mergers, acquisitions, or asset sales")
    pdf.add_bullet("With your consent: for any other purpose with your explicit permission")

    pdf.add_section("5. Data Retention")
    pdf.add_body(
        "We retain your personal data for as long as your account is active or as needed "
        "to provide services. Specific retention periods:\n\n"
        "Account data: retained for the duration of account activity plus 2 years\n"
        "Transaction records: retained for 7 years for legal and tax compliance\n"
        "Support tickets: retained for 3 years after resolution\n"
        "Usage analytics: retained in anonymized form for up to 5 years\n"
        "Marketing preferences: retained until you opt out\n\n"
        "After the retention period, data is securely deleted or anonymized."
    )

    pdf.add_section("6. Your Rights (GDPR & CCPA)")
    pdf.add_body("Depending on your location, you may have the following rights:")
    pdf.add_bullet("Right to Access: request a copy of your personal data")
    pdf.add_bullet("Right to Rectification: correct inaccurate or incomplete data")
    pdf.add_bullet("Right to Erasure: request deletion of your personal data")
    pdf.add_bullet("Right to Portability: receive your data in a structured, machine-readable format")
    pdf.add_bullet("Right to Object: object to processing of your data for certain purposes")
    pdf.add_bullet("Right to Restrict: request restriction of processing")
    pdf.add_bullet("Right to Withdraw Consent: withdraw consent at any time")

    pdf.add_body(
        "To exercise any of these rights, contact our Data Protection Officer at "
        "dpo@techcorp.com. We will respond to your request within 30 days."
    )

    pdf.add_section("7. Security Measures")
    pdf.add_body(
        "We implement industry-standard security measures to protect your data:\n\n"
        "Encryption: AES-256 encryption at rest, TLS 1.3 in transit\n"
        "Access Controls: role-based access, multi-factor authentication\n"
        "Monitoring: 24/7 security monitoring and intrusion detection\n"
        "Audits: annual third-party security audits and penetration testing\n"
        "Compliance: SOC 2 Type II certified, ISO 27001 compliant"
    )

    pdf.add_section("8. Contact Us")
    pdf.add_body(
        "For privacy-related inquiries:\n"
        "Data Protection Officer: dpo@techcorp.com\n"
        "Privacy Team: privacy@techcorp.com\n"
        "Mail: TechCorp Inc., 100 Innovation Drive, Suite 500, San Francisco, CA 94105"
    )

    path = os.path.join(output_dir, "privacy_policy.pdf")
    pdf.output(path)
    return path


def generate_terms_of_service(output_dir):
    """Generate Terms of Service PDF."""
    pdf = PolicyPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.add_title("Terms of Service")
    pdf.add_subtitle("Effective Date: January 1, 2026 | Version 5.0")

    pdf.add_section("1. Acceptance of Terms")
    pdf.add_body(
        "By accessing or using any TechCorp Inc. product or service, you agree to be bound "
        "by these Terms of Service (\"Terms\"). If you are using our services on behalf of an "
        "organization, you represent that you have the authority to bind that organization to "
        "these Terms. If you do not agree to these Terms, you may not access or use our services."
    )

    pdf.add_section("2. Account Terms")
    pdf.add_bullet("You must be at least 18 years old to create an account")
    pdf.add_bullet("You must provide accurate and complete registration information")
    pdf.add_bullet("You are responsible for maintaining the security of your account credentials")
    pdf.add_bullet("You must notify us immediately of any unauthorized access to your account")
    pdf.add_bullet("One person or entity may not maintain more than one free account")
    pdf.add_bullet("You may not use our services for any illegal or unauthorized purpose")

    pdf.add_section("3. Subscription Plans and Billing")
    pdf.add_subsection("3.1 Plan Types")
    pdf.add_body(
        "TechCorp offers the following subscription tiers:\n\n"
        "Free Tier: Limited features, 1 user, 1GB storage, community support\n"
        "Basic Plan ($9.99/month): Core features, 5 users, 50GB storage, email support\n"
        "Premium Plan ($29.99/month): All features, 25 users, 500GB storage, priority support\n"
        "Enterprise Plan (custom pricing): Unlimited features, unlimited users, custom storage, "
        "dedicated support, SLA guarantees, custom integrations"
    )

    pdf.add_subsection("3.2 Billing and Payment")
    pdf.add_body(
        "Subscriptions are billed in advance on a monthly or annual basis. All fees are "
        "non-refundable except as expressly set forth in our Refund Policy. We reserve the "
        "right to change pricing with 30 days advance notice. Price changes do not affect "
        "current billing periods for existing subscribers."
    )

    pdf.add_section("4. Acceptable Use Policy")
    pdf.add_body("You agree not to use our services to:")
    pdf.add_bullet("Violate any applicable laws, regulations, or third-party rights")
    pdf.add_bullet("Upload or transmit viruses, malware, or other malicious code")
    pdf.add_bullet("Attempt to gain unauthorized access to our systems or other user accounts")
    pdf.add_bullet("Interfere with or disrupt the integrity or performance of our services")
    pdf.add_bullet("Use our services for cryptocurrency mining or similar resource-intensive activities")
    pdf.add_bullet("Scrape, crawl, or spider our services without written permission")
    pdf.add_bullet("Resell or redistribute our services without authorization")
    pdf.add_bullet("Send spam, phishing, or other unsolicited communications through our platform")

    pdf.add_section("5. Intellectual Property")
    pdf.add_body(
        "All TechCorp products, services, logos, and content are protected by intellectual "
        "property laws. You retain ownership of content you upload to our services. By "
        "uploading content, you grant TechCorp a limited license to process, store, and "
        "display your content solely for the purpose of providing our services to you. "
        "This license terminates when you delete your content or close your account."
    )

    pdf.add_section("6. Service Level Agreement")
    pdf.add_body(
        "TechCorp commits to the following service levels for paid plans:\n\n"
        "Uptime: 99.9% monthly uptime guarantee (excluding scheduled maintenance)\n"
        "Support Response Times:\n"
        "  - Critical issues: 1 hour (Enterprise), 4 hours (Premium), 24 hours (Basic)\n"
        "  - High priority: 4 hours (Enterprise), 8 hours (Premium), 48 hours (Basic)\n"
        "  - Normal priority: 8 hours (Enterprise), 24 hours (Premium), 72 hours (Basic)\n\n"
        "If we fail to meet these commitments, affected customers may be eligible for "
        "service credits as described in the SLA addendum."
    )

    pdf.add_section("7. Limitation of Liability")
    pdf.add_body(
        "TO THE MAXIMUM EXTENT PERMITTED BY LAW, TECHCORP SHALL NOT BE LIABLE FOR ANY "
        "INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES, INCLUDING "
        "BUT NOT LIMITED TO LOSS OF PROFITS, DATA, OR BUSINESS OPPORTUNITIES. TECHCORP'S "
        "TOTAL LIABILITY SHALL NOT EXCEED THE AMOUNT PAID BY YOU IN THE 12 MONTHS PRECEDING "
        "THE CLAIM."
    )

    pdf.add_section("8. Termination")
    pdf.add_body(
        "Either party may terminate the agreement at any time. Upon termination:\n\n"
        "Your right to access our services ceases immediately\n"
        "We will retain your data for 30 days, during which you may export it\n"
        "After 30 days, all your data will be permanently deleted\n"
        "Outstanding fees remain payable\n\n"
        "TechCorp may suspend or terminate accounts that violate these Terms, with or "
        "without prior notice depending on the severity of the violation."
    )

    pdf.add_section("9. Governing Law")
    pdf.add_body(
        "These Terms shall be governed by the laws of the State of California, United States, "
        "without regard to conflict of law principles. Any disputes shall be resolved through "
        "binding arbitration in San Francisco, California, under the rules of the American "
        "Arbitration Association."
    )

    pdf.add_section("10. Contact Information")
    pdf.add_body(
        "For questions about these Terms:\n"
        "Email: legal@techcorp.com\n"
        "Mail: TechCorp Inc., 100 Innovation Drive, Suite 500, San Francisco, CA 94105\n"
        "Phone: 1-800-TECHCORP (1-800-832-4267)"
    )

    path = os.path.join(output_dir, "terms_of_service.pdf")
    pdf.output(path)
    return path


def generate_all_pdfs(output_dir="data/documents"):
    """Generate all policy PDF documents."""
    os.makedirs(output_dir, exist_ok=True)

    paths = [
        generate_refund_policy(output_dir),
        generate_privacy_policy(output_dir),
        generate_terms_of_service(output_dir),
    ]

    print(f"  Generated {len(paths)} policy PDFs in {output_dir}/")
    for p in paths:
        print(f"    - {os.path.basename(p)}")

    return paths


if __name__ == "__main__":
    generate_all_pdfs()
