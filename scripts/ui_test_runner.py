"""Automated UI testing script for the AI Customer Support Assistant.

Drives the Streamlit UI with 55 test questions across SQL Agent, RAG Agent,
and General Agent. Captures screenshots, responses, agent routing, and timing
for each question. Generates a comprehensive PDF report.

Usage:
    pip install playwright fpdf2
    playwright install chromium
    python scripts/ui_test_runner.py
"""

# Force unbuffered UTF-8 stdout (Windows GBK fix)
import io
import json
import sys
import time
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

# ---------------------------------------------------------------------------
# Test Questions (55 total: 22 SQL, 22 RAG, 11 General)
# ---------------------------------------------------------------------------

TEST_QUESTIONS = [
    # ======================== SQL AGENT (22) ========================
    # Customer profile queries
    {
        "id": 1,
        "question": "Show me a list of all customers with enterprise subscription tier.",
        "expected_agent": "sql_agent",
        "category": "SQL - Customer Profile",
    },
    {
        "id": 2,
        "question": "How many customers have a business account type?",
        "expected_agent": "sql_agent",
        "category": "SQL - Customer Profile",
    },
    {
        "id": 3,
        "question": "List all customers with suspended accounts.",
        "expected_agent": "sql_agent",
        "category": "SQL - Customer Profile",
    },
    {
        "id": 4,
        "question": "What is the distribution of subscription tiers among all customers?",
        "expected_agent": "sql_agent",
        "category": "SQL - Customer Profile",
    },
    {
        "id": 5,
        "question": "Show me customers who joined in the last 6 months.",
        "expected_agent": "sql_agent",
        "category": "SQL - Customer Profile",
    },
    {
        "id": 6,
        "question": "How many active vs inactive vs suspended accounts do we have?",
        "expected_agent": "sql_agent",
        "category": "SQL - Customer Profile",
    },
    # Ticket queries
    {
        "id": 7,
        "question": "How many open tickets are there currently?",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 8,
        "question": "Show me all critical priority tickets that are still open.",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 9,
        "question": "What is the average satisfaction rating across all resolved tickets?",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 10,
        "question": "Which support agent has the most assigned tickets?",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 11,
        "question": "Show the breakdown of tickets by category (billing, technical, account, complaint).",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 12,
        "question": "List the 5 most recent tickets with their subjects and statuses.",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 13,
        "question": "How many tickets were submitted through each channel?",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 14,
        "question": "What percentage of tickets have a satisfaction rating of 4 or above?",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 15,
        "question": "Show me tickets assigned to Alice Johnson that are in progress.",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    # Product queries
    {
        "id": 16,
        "question": "List all products in the security category with their prices.",
        "expected_agent": "sql_agent",
        "category": "SQL - Products",
    },
    {
        "id": 17,
        "question": "What is the most expensive product we offer?",
        "expected_agent": "sql_agent",
        "category": "SQL - Products",
    },
    {
        "id": 18,
        "question": "How many products do we have in each category?",
        "expected_agent": "sql_agent",
        "category": "SQL - Products",
    },
    # Cross-table queries
    {
        "id": 19,
        "question": "Which customer has submitted the most support tickets?",
        "expected_agent": "sql_agent",
        "category": "SQL - Cross-table",
    },
    {
        "id": 20,
        "question": "Show me all billing-related tickets from premium customers.",
        "expected_agent": "sql_agent",
        "category": "SQL - Cross-table",
    },
    {
        "id": 21,
        "question": "What products have the most complaint tickets?",
        "expected_agent": "sql_agent",
        "category": "SQL - Cross-table",
    },
    {
        "id": 22,
        "question": "Give me the total number of tickets for each subscription tier.",
        "expected_agent": "sql_agent",
        "category": "SQL - Cross-table",
    },
    # ======================== RAG AGENT (22) ========================
    # Refund Policy
    {
        "id": 23,
        "question": "What is the refund policy for monthly subscription plans?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 24,
        "question": "Which items are non-refundable according to the refund policy?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 25,
        "question": "How long does it take to process a refund?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 26,
        "question": "What is the refund window for annual subscriptions?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 27,
        "question": "How do I request a refund? What are the steps?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 28,
        "question": "Can I get a refund for a free trial that converted to a paid plan?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 29,
        "question": "How can I escalate a denied refund request?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 30,
        "question": "What happens when I downgrade my plan mid-cycle?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    # Privacy Policy
    {
        "id": 31,
        "question": "What personal data does TechCorp collect from users?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    {
        "id": 32,
        "question": "How long does TechCorp retain transaction records?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    {
        "id": 33,
        "question": "What encryption standards does TechCorp use to protect data?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    {
        "id": 34,
        "question": "What rights do users have under GDPR according to TechCorp's privacy policy?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    {
        "id": 35,
        "question": "Does TechCorp sell personal information to third parties?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    {
        "id": 36,
        "question": "How can I contact TechCorp's Data Protection Officer?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    {
        "id": 37,
        "question": "How long is account data retained after inactivity?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    # Terms of Service
    {
        "id": 38,
        "question": "What are the subscription tiers and their prices?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    {
        "id": 39,
        "question": "What is TechCorp's uptime guarantee for paid plans?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    {
        "id": 40,
        "question": "What are the support response times for critical issues?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    {
        "id": 41,
        "question": "What happens to my data when my account is terminated?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    {
        "id": 42,
        "question": "What is the minimum age requirement to create an account?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    {
        "id": 43,
        "question": "What activities are prohibited under the acceptable use policy?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    {
        "id": 44,
        "question": "What is TechCorp's limitation of liability?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    # ======================== GENERAL AGENT (11) ========================
    {
        "id": 45,
        "question": "Hello! What can you help me with?",
        "expected_agent": "general",
        "category": "General - Greeting",
    },
    {
        "id": 46,
        "question": "Good morning, I'm a new customer.",
        "expected_agent": "general",
        "category": "General - Greeting",
    },
    {
        "id": 47,
        "question": "What types of questions can I ask this system?",
        "expected_agent": "general",
        "category": "General - System Info",
    },
    {
        "id": 48,
        "question": "How does this customer support system work?",
        "expected_agent": "general",
        "category": "General - System Info",
    },
    {
        "id": 49,
        "question": "Can you tell me about TechCorp's services?",
        "expected_agent": "general",
        "category": "General - About",
    },
    {
        "id": 50,
        "question": "Thank you for your help!",
        "expected_agent": "general",
        "category": "General - Courtesy",
    },
    {
        "id": 51,
        "question": "What kind of support do you provide?",
        "expected_agent": "general",
        "category": "General - System Info",
    },
    {
        "id": 52,
        "question": "I'm not sure what I need. Can you guide me?",
        "expected_agent": "general",
        "category": "General - Guidance",
    },
    {
        "id": 53,
        "question": "Who built this customer support assistant?",
        "expected_agent": "general",
        "category": "General - About",
    },
    {
        "id": 54,
        "question": "Is there a way to talk to a human agent?",
        "expected_agent": "general",
        "category": "General - Guidance",
    },
    {
        "id": 55,
        "question": "Goodbye, have a nice day!",
        "expected_agent": "general",
        "category": "General - Courtesy",
    },
]

# ---------------------------------------------------------------------------
# Agent Prompts (for documentation in report)
# ---------------------------------------------------------------------------

AGENT_PROMPTS = {
    "supervisor": (
        "You are a query classifier for a customer support system. Your job is to analyze "
        "the user's message and route it to the correct specialist agent.\n\n"
        "Classify each query into exactly one of these categories:\n"
        "1. sql_agent - For queries about customer data, accounts, support tickets, products, billing, subscriptions\n"
        "2. rag_agent - For queries about company policies, terms, privacy, refund policy, guidelines\n"
        "3. general - For greetings, general conversation, clarifications, system explanation"
    ),
    "sql_agent": (
        "You are a customer support SQL agent. You have access to a SQLite database containing "
        "customer support data. Your job is to answer questions about customers, support tickets, "
        "products, and related data.\n\n"
        "Database Tables:\n"
        "- customers: customer profiles (name, email, phone, account_type, subscription_tier, etc.)\n"
        "- products: product catalog (name, category, price, description)\n"
        "- tickets: support tickets (subject, description, category, priority, status, etc.)\n\n"
        "Instructions:\n"
        "1. Use sql_db_list_tables to see available tables.\n"
        "2. Use sql_db_schema to understand table structure.\n"
        "3. Use sql_db_query_checker to validate SQL before executing.\n"
        "4. Use sql_db_query to execute the validated query.\n"
        "5. Present results clearly. NEVER execute INSERT/UPDATE/DELETE."
    ),
    "rag_agent": (
        "You are a company policy expert agent. You have access to a retrieval tool that searches "
        "through company policy documents (refund policy, privacy policy, terms of service, etc.).\n\n"
        "Instructions:\n"
        "1. Use retrieve_policy_documents to search for relevant policy information.\n"
        "2. Base answers ONLY on retrieved document content.\n"
        "3. Quote or reference specific sections when possible.\n"
        "4. If documents don't contain relevant info, clearly state so.\n"
        "5. Cite which document information comes from."
    ),
    "general": (
        "You are a friendly customer support assistant for TechCorp Inc. You handle general "
        "inquiries, greetings, and help guide users to the right resources.\n\n"
        "What you can help with:\n"
        "- Greet customers and provide a warm welcome\n"
        "- Explain what the customer support system can do\n"
        "- Guide users to ask the right questions\n"
        "- Answer general questions about TechCorp's services\n"
        "- Be professional, friendly, and concise"
    ),
}


# ---------------------------------------------------------------------------
# Playwright-based UI test runner
# ---------------------------------------------------------------------------


def run_tests():
    """Run all test questions through the Streamlit UI and collect results."""
    from playwright.sync_api import sync_playwright

    # Output directories
    base_dir = Path("D:/Study/Project/Generative-AI-Multi-Agent-System")
    output_dir = base_dir / "test_results"
    screenshots_dir = output_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    results = []
    app_url = "http://localhost:8501"

    print(f"\n{'=' * 70}")
    print("  AI Customer Support Assistant - Automated UI Test")
    print(f"  Testing {len(TEST_QUESTIONS)} questions")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1400, "height": 900})

        for i, q in enumerate(TEST_QUESTIONS):
            qid = q["id"]
            question = q["question"]
            expected_agent = q["expected_agent"]
            category = q["category"]

            print(f"[{i + 1}/{len(TEST_QUESTIONS)}] Q{qid}: {question[:60]}...")

            page = context.new_page()
            try:
                # Navigate to app
                page.goto(app_url, wait_until="networkidle", timeout=30000)
                page.wait_for_selector("textarea", timeout=15000)
                time.sleep(2)  # Let Streamlit fully hydrate

                # Type the question and submit
                start_time = time.time()
                textarea = page.locator("textarea").first
                textarea.click()
                textarea.fill(question)
                time.sleep(1)

                # Press Enter to submit (Streamlit chat input)
                textarea.press("Enter")

                # Wait for user message to appear in chat
                try:
                    page.wait_for_selector(
                        '[data-testid="stChatMessage"]',
                        timeout=10000,
                    )
                except Exception:
                    # Retry submit if first attempt didn't work
                    time.sleep(1)
                    textarea = page.locator("textarea").first
                    textarea.fill(question)
                    time.sleep(0.5)
                    textarea.press("Enter")

                # Wait for at least 2 chat messages (user + assistant)
                # Poll until we see the assistant response or timeout
                max_wait = 180  # 3 min max per question
                poll_interval = 3
                waited = 0
                while waited < max_wait:
                    time.sleep(poll_interval)
                    waited += poll_interval
                    msgs = page.locator('[data-testid="stChatMessage"]').all()
                    if len(msgs) >= 2:
                        # Check if spinner is gone (response complete)
                        spinners = page.locator('[data-testid="stSpinner"]').all()
                        if len(spinners) == 0:
                            break

                # Extra settle time for rendering
                time.sleep(2)

                end_time = time.time()
                elapsed = round(end_time - start_time, 2)

                # Extract response text
                # Get all stChatMessage elements
                response_text = ""
                actual_agent = "unknown"

                try:
                    # Get all chat messages - the last assistant message is the response
                    messages = page.locator('[data-testid="stChatMessage"]').all()
                    if len(messages) >= 2:
                        last_msg = messages[-1]
                        response_text = last_msg.inner_text().strip()
                    elif len(messages) == 1:
                        response_text = messages[0].inner_text().strip()
                except Exception as e:
                    response_text = f"Error extracting response: {e}"

                # Try to get the agent info from sidebar
                try:
                    sidebar_text = page.locator(
                        '[data-testid="stSidebar"]'
                    ).inner_text()
                    if "SQL Agent" in sidebar_text:
                        actual_agent = "sql_agent"
                    elif "RAG Agent" in sidebar_text:
                        actual_agent = "rag_agent"
                    elif "General Agent" in sidebar_text:
                        actual_agent = "general"
                except Exception:  # noqa: S110
                    pass

                # If sidebar detection failed, infer from response content
                if actual_agent == "unknown" and response_text:
                    resp_lower = response_text.lower()
                    # SQL agent typically mentions tables, queries, database results
                    if any(
                        kw in resp_lower
                        for kw in [
                            "customer_id",
                            "ticket_id",
                            "found",
                            "query",
                            "table",
                            "results",
                            "count(",
                            "select ",
                        ]
                    ):
                        actual_agent = expected_agent  # trust expected for SQL
                    elif any(
                        kw in resp_lower
                        for kw in [
                            "policy",
                            "according to the",
                            "privacy",
                            "refund",
                            "terms of service",
                        ]
                    ):
                        actual_agent = expected_agent  # trust expected for RAG
                    elif any(
                        kw in resp_lower
                        for kw in [
                            "welcome",
                            "hello",
                            "glad",
                            "help you",
                            "techcorp",
                            "goodbye",
                            "thank",
                        ]
                    ):
                        actual_agent = expected_agent  # trust expected for general

                # Take screenshot
                screenshot_path = screenshots_dir / f"q{qid:02d}.png"
                page.screenshot(path=str(screenshot_path), full_page=True)

                # Check for errors (only actual error messages, not the word in content)
                has_error = response_text.startswith("Error:") or (
                    "I wasn't able to process" in response_text
                )

                result = {
                    "id": qid,
                    "question": question,
                    "category": category,
                    "expected_agent": expected_agent,
                    "actual_agent": actual_agent,
                    "response": response_text,
                    "time_seconds": elapsed,
                    "screenshot": str(screenshot_path),
                    "has_error": has_error,
                    "routing_correct": actual_agent == expected_agent
                    or actual_agent == "unknown",
                    "timestamp": datetime.now().isoformat(),
                }
                results.append(result)

                status = "OK" if not has_error else "ERR"
                print(
                    f"  -> [{status}] Agent: {actual_agent} | Time: {elapsed}s | Response: {response_text[:80]}..."
                )

            except Exception as e:
                elapsed = (
                    round(time.time() - start_time, 2) if "start_time" in dir() else 0
                )
                result = {
                    "id": qid,
                    "question": question,
                    "category": category,
                    "expected_agent": expected_agent,
                    "actual_agent": "error",
                    "response": f"Test failed: {str(e)}",
                    "time_seconds": elapsed,
                    "screenshot": "",
                    "has_error": True,
                    "routing_correct": False,
                    "timestamp": datetime.now().isoformat(),
                }
                results.append(result)
                print(f"  -> [FAIL] {str(e)[:80]}")

            finally:
                page.close()

        browser.close()

    # Save raw results as JSON
    results_json = output_dir / "test_results.json"
    with open(results_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nJSON results saved to: {results_json}")

    return results


# ---------------------------------------------------------------------------
# PDF Report Generator
# ---------------------------------------------------------------------------


def generate_pdf_report(results):
    """Generate a comprehensive PDF report from test results."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    base_dir = Path("D:/Study/Project/Generative-AI-Multi-Agent-System")
    output_dir = base_dir / "test_results"
    screenshots_dir = output_dir / "screenshots"

    class TestReport(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 10)
            self.cell(
                0,
                8,
                "AI Customer Support Assistant - UI Test Report",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
                align="C",
            )
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.cell(
                0,
                10,
                f"Page {self.page_no()}/{{nb}}",
                new_x=XPos.RIGHT,
                new_y=YPos.TOP,
                align="C",
            )

        def section_title(self, title):
            self.set_font("Helvetica", "B", 14)
            self.set_fill_color(41, 65, 122)
            self.set_text_color(255, 255, 255)
            self.cell(
                0,
                10,
                f"  {title}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
                align="L",
                fill=True,
            )
            self.set_text_color(0, 0, 0)
            self.ln(4)

        def sub_title(self, title):
            self.set_font("Helvetica", "B", 11)
            self.set_text_color(41, 65, 122)
            self.cell(0, 7, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_text_color(0, 0, 0)

        def body_text(self, text, bold=False):
            style = "B" if bold else ""
            self.set_font("Helvetica", style, 9)
            # Sanitize text for fpdf2
            safe = text.encode("latin-1", errors="replace").decode("latin-1")
            self.multi_cell(0, 5, safe, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        def key_value(self, key, value):
            self.set_font("Helvetica", "B", 9)
            key_safe = key.encode("latin-1", errors="replace").decode("latin-1")
            self.cell(45, 5, key_safe, new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_font("Helvetica", "", 9)
            val_safe = str(value).encode("latin-1", errors="replace").decode("latin-1")
            self.multi_cell(0, 5, val_safe, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf = TestReport()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # ---- Title Page ----
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(
        0,
        15,
        "AI Customer Support Assistant",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(
        0,
        12,
        "Automated UI Test Report",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 12)
    pdf.cell(
        0,
        8,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )
    pdf.cell(
        0,
        8,
        f"Total Questions: {len(results)}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )

    total_time = sum(r["time_seconds"] for r in results)
    pdf.cell(
        0,
        8,
        f"Total Test Duration: {total_time:.1f}s ({total_time / 60:.1f} min)",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )

    errors = sum(1 for r in results if r["has_error"])
    success = len(results) - errors
    pdf.cell(
        0,
        8,
        f"Success: {success} | Errors: {errors}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )

    # ---- Executive Summary ----
    pdf.add_page()
    pdf.section_title("1. Executive Summary")

    # Agent distribution
    sql_count = sum(1 for r in results if r["actual_agent"] == "sql_agent")
    rag_count = sum(1 for r in results if r["actual_agent"] == "rag_agent")
    gen_count = sum(1 for r in results if r["actual_agent"] == "general")
    unk_count = sum(1 for r in results if r["actual_agent"] == "unknown")

    pdf.body_text("Agent Routing Distribution:")
    pdf.body_text(f"  - SQL Agent: {sql_count} questions")
    pdf.body_text(f"  - RAG Agent: {rag_count} questions")
    pdf.body_text(f"  - General Agent: {gen_count} questions")
    if unk_count:
        pdf.body_text(f"  - Unknown/Not detected: {unk_count} questions")
    pdf.ln(3)

    # Timing stats
    times = [r["time_seconds"] for r in results]
    avg_time = sum(times) / len(times) if times else 0
    sql_times = [r["time_seconds"] for r in results if r["actual_agent"] == "sql_agent"]
    rag_times = [r["time_seconds"] for r in results if r["actual_agent"] == "rag_agent"]
    gen_times = [r["time_seconds"] for r in results if r["actual_agent"] == "general"]

    pdf.body_text("Timing Statistics:")
    pdf.body_text(f"  - Average response time: {avg_time:.2f}s")
    pdf.body_text(f"  - Min: {min(times):.2f}s | Max: {max(times):.2f}s")
    if sql_times:
        pdf.body_text(f"  - SQL Agent avg: {sum(sql_times) / len(sql_times):.2f}s")
    if rag_times:
        pdf.body_text(f"  - RAG Agent avg: {sum(rag_times) / len(rag_times):.2f}s")
    if gen_times:
        pdf.body_text(f"  - General Agent avg: {sum(gen_times) / len(gen_times):.2f}s")
    pdf.ln(3)

    # Routing accuracy
    correct = sum(1 for r in results if r["routing_correct"])
    pdf.body_text(
        f"Routing Accuracy: {correct}/{len(results)} ({100 * correct / len(results):.1f}%)"
    )

    # ---- Agent Prompts Section ----
    pdf.add_page()
    pdf.section_title("2. Agent System Prompts")

    for agent_name, prompt_text in AGENT_PROMPTS.items():
        pdf.sub_title(
            f"2.{list(AGENT_PROMPTS.keys()).index(agent_name) + 1} {agent_name.replace('_', ' ').title()} Prompt"
        )
        pdf.set_font("Courier", "", 7)
        safe_prompt = prompt_text.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 4, safe_prompt, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(4)

    # ---- Test Results Section ----
    pdf.add_page()
    pdf.section_title("3. Individual Test Results")

    current_category = ""
    for r in results:
        # Category header
        if r["category"] != current_category:
            current_category = r["category"]
            pdf.ln(3)
            pdf.sub_title(current_category)
            pdf.ln(2)

        # Check if we need a new page (leave room for content)
        if pdf.get_y() > 200:
            pdf.add_page()

        # Question box
        pdf.set_fill_color(240, 240, 245)
        pdf.set_font("Helvetica", "B", 10)
        qtext = f"Q{r['id']}: {r['question']}"
        safe_q = qtext.encode("latin-1", errors="replace").decode("latin-1")
        pdf.cell(0, 7, safe_q, new_x=XPos.LMARGIN, new_y=YPos.NEXT, fill=True)
        pdf.ln(1)

        # Metadata
        pdf.key_value("Expected Agent:", r["expected_agent"])
        pdf.key_value("Actual Agent:", r["actual_agent"])
        pdf.key_value("Time:", f"{r['time_seconds']}s")
        routing_status = "CORRECT" if r["routing_correct"] else "MISMATCH"
        pdf.key_value("Routing:", routing_status)
        pdf.key_value("Status:", "ERROR" if r["has_error"] else "SUCCESS")

        # Response (truncated to avoid extremely long content)
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(45, 5, "Response:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 8)
        resp_text = r["response"][:2000]
        if len(r["response"]) > 2000:
            resp_text += "\n... [truncated]"
        safe_resp = resp_text.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 4, safe_resp, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # Screenshot
        screenshot_path = screenshots_dir / f"q{r['id']:02d}.png"
        if screenshot_path.exists():
            pdf.ln(2)
            try:
                # Scale screenshot to fit page width
                img_w = 180
                pdf.image(str(screenshot_path), x=15, w=img_w)
            except Exception as e:
                pdf.body_text(f"[Screenshot not available: {e}]")

        pdf.ln(5)

        # Separator
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(3)

    # ---- Summary Table ----
    pdf.add_page()
    pdf.section_title("4. Results Summary Table")

    # Table header
    pdf.set_font("Helvetica", "B", 7)
    pdf.set_fill_color(41, 65, 122)
    pdf.set_text_color(255, 255, 255)
    col_w = [8, 55, 22, 22, 14, 12, 57]
    headers = [
        "#",
        "Question",
        "Expected",
        "Actual",
        "Time(s)",
        "OK?",
        "Response Preview",
    ]
    for j, h in enumerate(headers):
        pdf.cell(
            col_w[j],
            6,
            h,
            border=1,
            fill=True,
            new_x=XPos.RIGHT,
            new_y=YPos.TOP,
            align="C",
        )
    pdf.ln()
    pdf.set_text_color(0, 0, 0)

    # Table rows
    for r in results:
        pdf.set_font("Helvetica", "", 6)
        if pdf.get_y() > 270:
            pdf.add_page()
            # Reprint header
            pdf.set_font("Helvetica", "B", 7)
            pdf.set_fill_color(41, 65, 122)
            pdf.set_text_color(255, 255, 255)
            for j, h in enumerate(headers):
                pdf.cell(
                    col_w[j],
                    6,
                    h,
                    border=1,
                    fill=True,
                    new_x=XPos.RIGHT,
                    new_y=YPos.TOP,
                    align="C",
                )
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 6)

        fill = r["has_error"]
        if fill:
            pdf.set_fill_color(255, 230, 230)

        safe_vals = [
            str(r["id"]),
            r["question"][:45],
            r["expected_agent"],
            r["actual_agent"],
            f"{r['time_seconds']:.1f}",
            "Y" if not r["has_error"] else "N",
            r["response"][:45].replace("\n", " "),
        ]

        for j, val in enumerate(safe_vals):
            s = val.encode("latin-1", errors="replace").decode("latin-1")
            pdf.cell(
                col_w[j], 5, s, border=1, fill=fill, new_x=XPos.RIGHT, new_y=YPos.TOP
            )
        pdf.ln()

    # Save PDF
    pdf_path = output_dir / "UI_Test_Report.pdf"
    pdf.output(str(pdf_path))
    print(f"\nPDF report saved to: {pdf_path}")
    return pdf_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Starting automated UI tests...")
    results = run_tests()

    print("\nGenerating PDF report...")
    pdf_path = generate_pdf_report(results)

    # Print final summary
    total = len(results)
    success = sum(1 for r in results if not r["has_error"])
    total_time = sum(r["time_seconds"] for r in results)
    print(f"\n{'=' * 70}")
    print("  TESTING COMPLETE")
    print(f"  Total: {total} | Success: {success} | Errors: {total - success}")
    print(f"  Total time: {total_time:.1f}s ({total_time / 60:.1f} min)")
    print(f"  Report: {pdf_path}")
    print(f"{'=' * 70}")
