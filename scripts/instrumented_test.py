"""Instrumented UI test runner with detailed token/timing/prompt tracking.

For each test question, captures:
- Router classification (prompt, tokens, time)
- Agent execution (all LLM calls with prompts, tokens, time)
- Full response text
- UI screenshot
- Total time and total tokens

Generates a comprehensive PDF report.

Usage:
    python scripts/instrumented_test.py [--dry-run] [--count N]
"""

import argparse
import io
import json
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", line_buffering=True)

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os  # noqa: E402

# Set HuggingFace cache to project dir (avoid Windows permission issues)
os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / ".hf_cache"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

from langchain_core.callbacks import BaseCallbackHandler  # noqa: E402

# ---------------------------------------------------------------------------
# 22 Test Questions (balanced: 8 SQL, 8 RAG, 6 General)
# ---------------------------------------------------------------------------

TEST_QUESTIONS = [
    # --- SQL Agent (8) ---
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
        "question": "How many open tickets are there currently?",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 4,
        "question": "What is the average satisfaction rating across all resolved tickets?",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 5,
        "question": "Which support agent has the most assigned tickets?",
        "expected_agent": "sql_agent",
        "category": "SQL - Tickets",
    },
    {
        "id": 6,
        "question": "List all products in the security category with their prices.",
        "expected_agent": "sql_agent",
        "category": "SQL - Products",
    },
    {
        "id": 7,
        "question": "Which customer has submitted the most support tickets?",
        "expected_agent": "sql_agent",
        "category": "SQL - Cross-table",
    },
    {
        "id": 8,
        "question": "Show me all billing-related tickets from premium customers.",
        "expected_agent": "sql_agent",
        "category": "SQL - Cross-table",
    },
    # --- RAG Agent (8) ---
    {
        "id": 9,
        "question": "What is the refund policy for monthly subscription plans?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 10,
        "question": "Which items are non-refundable according to the refund policy?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 11,
        "question": "How long does it take to process a refund?",
        "expected_agent": "rag_agent",
        "category": "RAG - Refund Policy",
    },
    {
        "id": 12,
        "question": "What encryption standards does TechCorp use to protect data?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    {
        "id": 13,
        "question": "What rights do users have under GDPR?",
        "expected_agent": "rag_agent",
        "category": "RAG - Privacy Policy",
    },
    {
        "id": 14,
        "question": "What are the subscription tiers and their prices?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    {
        "id": 15,
        "question": "What is TechCorp's uptime guarantee for paid plans?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    {
        "id": 16,
        "question": "What happens to my data when my account is terminated?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    # --- General Agent (6) ---
    {
        "id": 17,
        "question": "Hello! What can you help me with?",
        "expected_agent": "general",
        "category": "General - Greeting",
    },
    {
        "id": 18,
        "question": "What types of questions can I ask this system?",
        "expected_agent": "general",
        "category": "General - System Info",
    },
    {
        "id": 19,
        "question": "How does this customer support system work?",
        "expected_agent": "general",
        "category": "General - System Info",
    },
    {
        "id": 20,
        "question": "Can you tell me about TechCorp's services?",
        "expected_agent": "general",
        "category": "General - About",
    },
    {
        "id": 21,
        "question": "Is there a way to talk to a human agent?",
        "expected_agent": "general",
        "category": "General - Guidance",
    },
    {
        "id": 22,
        "question": "Thank you for your help! Goodbye!",
        "expected_agent": "general",
        "category": "General - Courtesy",
    },
]

# ---------------------------------------------------------------------------
# Agent Prompt Constants (for report)
# ---------------------------------------------------------------------------

SUPERVISOR_PROMPT = """You are a query classifier for a customer support system. Your job is to analyze the user's message and route it to the correct specialist agent.

You must classify each query into exactly one of these categories:

1. sql_agent: For queries about customer data, accounts, profiles, support tickets, products, billing history, subscription details, or any structured data lookups.

2. rag_agent: For queries about company policies, terms of service, privacy policy, refund policy, procedures, guidelines.

3. general: For greetings, general conversation, clarifications, or queries that don't fit the above categories."""

SQL_AGENT_PROMPT = """You are a customer support SQL agent with access to a SQLite database containing customer support data.

Database Tables:
- customers: customer profiles (name, email, phone, account_type, subscription_tier, join_date, address, account_status)
- products: product catalog (name, category, price, description)
- tickets: support tickets (subject, description, category, priority, status, channel, assigned_agent, created_at, resolved_at, resolution, satisfaction_rating)

Instructions:
1. Use sql_db_list_tables to see available tables.
2. Use sql_db_schema to understand table structure before writing queries.
3. Use sql_db_query_checker to validate your SQL before executing.
4. Use sql_db_query to execute the validated query.
5. Present results in a clear, readable format.
6. NEVER execute INSERT, UPDATE, DELETE, DROP, or any data-modifying statements.
7. If a query returns too many results, use LIMIT to keep output manageable.
8. When searching for names, use LIKE with wildcards for partial matching.
9. Always explain what data you found in a helpful, conversational manner."""

RAG_AGENT_PROMPT = """You are a company policy expert agent. You have access to a retrieval tool that searches through company policy documents (refund policy, privacy policy, terms of service).

Instructions:
1. Use the retrieve_policy_documents tool to search for relevant policy information.
2. Base your answers ONLY on the retrieved document content.
3. Quote or reference specific sections from the documents when possible.
4. If the retrieved documents don't contain relevant information, clearly state: "I don't have information about that in the company policy documents."
5. Be precise and helpful - customers rely on accurate policy information.
6. When citing information, mention which document it comes from (e.g., "According to the Refund Policy..." or "The Privacy Policy states...")."""

GENERAL_AGENT_PROMPT = """You are a friendly customer support assistant for TechCorp Inc. You handle general inquiries, greetings, and help guide users to the right resources.

What you can help with:
- Greet customers and provide a warm welcome
- Explain what the customer support system can do
- Guide users to ask the right questions
- Answer general questions about TechCorp's services
- Be professional, friendly, and concise

Important:
- If a question needs database lookups or policy info, let the user know
- Do not make up information about specific customers or policies"""


# ---------------------------------------------------------------------------
# LLM Call Tracker (Callback Handler)
# ---------------------------------------------------------------------------


class LLMCallTracker(BaseCallbackHandler):
    """Tracks all LLM calls with prompts, tokens, and timing."""

    def __init__(self):
        self.calls = []
        self._pending = {}

    def on_llm_start(self, serialized: dict, prompts: list[str], **kwargs: Any):
        run_id = kwargs.get("run_id", str(uuid.uuid4()))
        self._pending[str(run_id)] = {
            "start_time": time.time(),
            "prompts": prompts,
            "model": serialized.get("kwargs", {}).get("model", "unknown"),
        }

    def on_chat_model_start(self, serialized: dict, messages: list, **kwargs: Any):
        run_id = kwargs.get("run_id", str(uuid.uuid4()))
        # Flatten messages to readable format
        flat_msgs = []
        for msg_list in messages:
            for msg in msg_list:
                role = getattr(msg, "type", "unknown")
                content = getattr(msg, "content", str(msg))
                if isinstance(content, list):
                    # Tool use messages
                    content = str(content)
                flat_msgs.append({"role": role, "content": content[:2000]})

        model_name = serialized.get("kwargs", {}).get("model", "unknown")
        if model_name == "unknown":
            model_name = serialized.get("kwargs", {}).get("model_name", "unknown")

        self._pending[str(run_id)] = {
            "start_time": time.time(),
            "messages": flat_msgs,
            "model": model_name,
        }

    def on_llm_end(self, response, **kwargs: Any):
        run_id = str(kwargs.get("run_id", ""))
        end_time = time.time()

        pending = self._pending.pop(run_id, {})
        start_time = pending.get("start_time", end_time)

        # Extract token usage from response
        input_tokens = 0
        output_tokens = 0
        total_tokens = 0

        if response and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    msg = gen.message if hasattr(gen, "message") else None
                    if msg:
                        # Try usage_metadata (newer LangChain)
                        um = getattr(msg, "usage_metadata", None)
                        if um:
                            input_tokens += um.get("input_tokens", 0)
                            output_tokens += um.get("output_tokens", 0)
                            total_tokens += um.get("total_tokens", 0)
                        # Try response_metadata (Anthropic)
                        rm = getattr(msg, "response_metadata", {})
                        if rm and not total_tokens:
                            usage = rm.get("usage", {})
                            input_tokens += usage.get("input_tokens", 0)
                            output_tokens += usage.get("output_tokens", 0)

        if not total_tokens:
            total_tokens = input_tokens + output_tokens

        # Extract response text
        response_text = ""
        if response and response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, "text"):
                        response_text = gen.text[:1000]
                    elif hasattr(gen, "message"):
                        content = getattr(gen.message, "content", "")
                        if isinstance(content, str):
                            response_text = content[:1000]

        call_record = {
            "duration_seconds": round(end_time - start_time, 3),
            "model": pending.get("model", "unknown"),
            "messages": pending.get("messages", pending.get("prompts", [])),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "response_preview": response_text[:500],
        }
        self.calls.append(call_record)

    def on_llm_error(self, error, **kwargs: Any):
        run_id = str(kwargs.get("run_id", ""))
        pending = self._pending.pop(run_id, {})
        self.calls.append(
            {
                "duration_seconds": round(
                    time.time() - pending.get("start_time", time.time()), 3
                ),
                "model": pending.get("model", "unknown"),
                "messages": pending.get("messages", []),
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "response_preview": f"ERROR: {str(error)[:500]}",
                "error": True,
            }
        )

    def reset(self):
        self.calls = []
        self._pending = {}


# ---------------------------------------------------------------------------
# Run a single question through the graph with instrumentation
# ---------------------------------------------------------------------------


def run_single_question(graph, question_text, tracker, thread_id=None):
    """Run a single question through the graph and capture detailed metrics."""
    tracker.reset()
    thread_id = thread_id or str(uuid.uuid4())

    config = {
        "configurable": {"thread_id": thread_id},
        "callbacks": [tracker],
    }
    input_state = {
        "messages": [{"role": "user", "content": question_text}],
        "query_category": "",
        "customer_id": "",
    }

    start_time = time.time()
    result = graph.invoke(input_state, config=config)
    total_time = round(time.time() - start_time, 3)

    # Extract response
    agent_messages = result.get("messages", [])
    response_text = ""
    if agent_messages:
        last_msg = agent_messages[-1]
        if hasattr(last_msg, "content"):
            response_text = last_msg.content
        elif isinstance(last_msg, dict):
            response_text = last_msg.get("content", "")

    # Extract routing
    query_category = result.get("query_category", "unknown")

    # Classify LLM calls into stages
    all_calls = list(tracker.calls)
    router_calls = all_calls[:1] if all_calls else []  # First call is router
    agent_calls = all_calls[1:] if len(all_calls) > 1 else []

    # Calculate totals
    total_input_tokens = sum(c["input_tokens"] for c in all_calls)
    total_output_tokens = sum(c["output_tokens"] for c in all_calls)
    total_tokens = sum(c["total_tokens"] for c in all_calls)

    router_time = sum(c["duration_seconds"] for c in router_calls)
    agent_time = sum(c["duration_seconds"] for c in agent_calls)

    return {
        "response": response_text,
        "query_category": query_category,
        "total_time": total_time,
        "router_time": round(router_time, 3),
        "agent_time": round(agent_time, 3),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "num_llm_calls": len(all_calls),
        "router_calls": router_calls,
        "agent_calls": agent_calls,
        "all_calls": all_calls,
    }


# ---------------------------------------------------------------------------
# Take UI screenshot
# ---------------------------------------------------------------------------


def take_ui_screenshot(question_text, screenshot_path, app_url="http://localhost:8501"):
    """Open the Streamlit UI, submit a question, and take a screenshot."""
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 900})
            page.goto(app_url, wait_until="networkidle", timeout=30000)
            page.wait_for_selector("textarea", timeout=15000)
            time.sleep(2)

            # Type and submit
            textarea = page.locator("textarea").first
            textarea.click()
            textarea.fill(question_text)
            time.sleep(0.5)
            textarea.press("Enter")

            # Wait for response
            max_wait = 180
            waited = 0
            while waited < max_wait:
                time.sleep(3)
                waited += 3
                msgs = page.locator('[data-testid="stChatMessage"]').all()
                if len(msgs) >= 2:
                    spinners = page.locator('[data-testid="stSpinner"]').all()
                    if len(spinners) == 0:
                        break

            time.sleep(2)
            page.screenshot(path=str(screenshot_path), full_page=True)
            browser.close()
            return True
    except Exception as e:
        print(f"    Screenshot failed: {e}")
        return False


# ---------------------------------------------------------------------------
# PDF Report Generator
# ---------------------------------------------------------------------------


def generate_pdf_report(results, output_dir):
    """Generate comprehensive PDF report with all captured data."""
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    class Report(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 9)
            self.cell(
                0,
                7,
                "AI Customer Support - Instrumented Test Report",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
                align="C",
            )
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(2)

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

        def safe(self, text):
            return str(text).encode("latin-1", errors="replace").decode("latin-1")

        def section_title(self, title):
            self.set_font("Helvetica", "B", 13)
            self.set_fill_color(41, 65, 122)
            self.set_text_color(255, 255, 255)
            self.cell(
                0,
                9,
                f"  {self.safe(title)}",
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
                fill=True,
            )
            self.set_text_color(0, 0, 0)
            self.ln(3)

        def sub_title(self, title):
            self.set_font("Helvetica", "B", 10)
            self.set_text_color(41, 65, 122)
            self.cell(0, 6, self.safe(title), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            self.set_text_color(0, 0, 0)

        def kv(self, key, value):
            self.set_font("Helvetica", "B", 8)
            self.cell(40, 4, self.safe(key), new_x=XPos.RIGHT, new_y=YPos.TOP)
            self.set_font("Helvetica", "", 8)
            self.multi_cell(
                0, 4, self.safe(str(value)), new_x=XPos.LMARGIN, new_y=YPos.NEXT
            )

        def body(self, text, size=8):
            self.set_font("Helvetica", "", size)
            self.multi_cell(0, 4, self.safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        def code_block(self, text, max_lines=30):
            self.set_font("Courier", "", 6)
            self.set_fill_color(245, 245, 250)
            lines = text.split("\n")[:max_lines]
            for line in lines:
                self.cell(
                    0,
                    3,
                    self.safe(line[:150]),
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                    fill=True,
                )
            if len(text.split("\n")) > max_lines:
                self.cell(
                    0,
                    3,
                    f"... [{len(text.split(chr(10)))} total lines]",
                    new_x=XPos.LMARGIN,
                    new_y=YPos.NEXT,
                    fill=True,
                )

    pdf = Report()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)

    # ---- Title Page ----
    pdf.add_page()
    pdf.ln(25)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(
        0,
        12,
        "AI Customer Support Assistant",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(
        0,
        10,
        "Instrumented UI Test Report",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(
        0,
        7,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )
    pdf.cell(
        0,
        7,
        f"Total Questions Tested: {len(results)}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )

    total_time = sum(r["metrics"]["total_time"] for r in results)
    total_tokens = sum(r["metrics"]["total_tokens"] for r in results)
    total_calls = sum(r["metrics"]["num_llm_calls"] for r in results)
    pdf.cell(
        0,
        7,
        f"Total Time: {total_time:.1f}s | Total Tokens: {total_tokens:,} | LLM Calls: {total_calls}",
        new_x=XPos.LMARGIN,
        new_y=YPos.NEXT,
        align="C",
    )

    # ---- Executive Summary ----
    pdf.add_page()
    pdf.section_title("1. Executive Summary")

    sql_results = [r for r in results if r["metrics"]["query_category"] == "sql_agent"]
    rag_results = [r for r in results if r["metrics"]["query_category"] == "rag_agent"]
    gen_results = [r for r in results if r["metrics"]["query_category"] == "general"]

    pdf.body("Agent Routing:")
    pdf.body(f"  SQL Agent: {len(sql_results)} questions")
    pdf.body(f"  RAG Agent: {len(rag_results)} questions")
    pdf.body(f"  General Agent: {len(gen_results)} questions")
    pdf.ln(2)

    # Timing
    pdf.body("Timing (seconds):")
    for label, subset in [
        ("SQL Agent", sql_results),
        ("RAG Agent", rag_results),
        ("General Agent", gen_results),
    ]:
        if subset:
            times = [r["metrics"]["total_time"] for r in subset]
            avg_t = sum(times) / len(times)
            pdf.body(
                f"  {label}: avg={avg_t:.1f}s, min={min(times):.1f}s, max={max(times):.1f}s"
            )
    pdf.ln(2)

    # Token usage
    pdf.body("Token Usage:")
    for label, subset in [
        ("SQL Agent", sql_results),
        ("RAG Agent", rag_results),
        ("General Agent", gen_results),
    ]:
        if subset:
            inp = sum(r["metrics"]["total_input_tokens"] for r in subset)
            out = sum(r["metrics"]["total_output_tokens"] for r in subset)
            tot = sum(r["metrics"]["total_tokens"] for r in subset)
            pdf.body(f"  {label}: input={inp:,}, output={out:,}, total={tot:,}")
    pdf.body(f"  GRAND TOTAL: {total_tokens:,} tokens across {total_calls} LLM calls")

    # ---- Agent Prompts ----
    pdf.add_page()
    pdf.section_title("2. Agent System Prompts")

    for name, prompt in [
        ("Supervisor (Router)", SUPERVISOR_PROMPT),
        ("SQL Agent", SQL_AGENT_PROMPT),
        ("RAG Agent", RAG_AGENT_PROMPT),
        ("General Agent", GENERAL_AGENT_PROMPT),
    ]:
        pdf.sub_title(name)
        pdf.code_block(prompt, max_lines=20)
        pdf.ln(3)

    # ---- Individual Results ----
    pdf.add_page()
    pdf.section_title("3. Individual Test Results")

    for r in results:
        q = r["question_data"]
        m = r["metrics"]

        if pdf.get_y() > 180:
            pdf.add_page()

        # Question header
        pdf.set_fill_color(230, 235, 245)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(
            0,
            7,
            pdf.safe(f"Q{q['id']}: {q['question']}"),
            new_x=XPos.LMARGIN,
            new_y=YPos.NEXT,
            fill=True,
        )
        pdf.ln(1)

        # Metadata
        pdf.kv("Category:", q["category"])
        pdf.kv("Expected Agent:", q["expected_agent"])
        pdf.kv("Actual Agent:", m["query_category"])
        routing_ok = (
            "CORRECT" if m["query_category"] == q["expected_agent"] else "MISMATCH"
        )
        pdf.kv("Routing:", routing_ok)
        pdf.ln(1)

        # Timing breakdown
        pdf.sub_title("Timing Breakdown")
        pdf.kv("Total Time:", f"{m['total_time']}s")
        pdf.kv("Router Time:", f"{m['router_time']}s")
        pdf.kv("Agent Time:", f"{m['agent_time']}s")
        pdf.kv("LLM Calls:", str(m["num_llm_calls"]))
        pdf.ln(1)

        # Token breakdown
        pdf.sub_title("Token Usage")
        pdf.kv("Input Tokens:", f"{m['total_input_tokens']:,}")
        pdf.kv("Output Tokens:", f"{m['total_output_tokens']:,}")
        pdf.kv("Total Tokens:", f"{m['total_tokens']:,}")
        pdf.ln(1)

        # Per-call details
        pdf.sub_title("LLM Call Log")
        for ci, call in enumerate(m["all_calls"]):
            call_type = "Router" if ci == 0 else f"Agent Call #{ci}"
            pdf.set_font("Helvetica", "B", 7)
            pdf.cell(
                0,
                4,
                pdf.safe(
                    f"  [{call_type}] model={call['model']} | "
                    f"time={call['duration_seconds']}s | "
                    f"in={call['input_tokens']} out={call['output_tokens']} "
                    f"total={call['total_tokens']}"
                ),
                new_x=XPos.LMARGIN,
                new_y=YPos.NEXT,
            )

            # Show prompt summary for this call
            msgs = call.get("messages", [])
            if msgs and isinstance(msgs, list):
                for msg in msgs[:3]:
                    if isinstance(msg, dict):
                        role = msg.get("role", "?")
                        content = msg.get("content", "")[:200]
                        pdf.set_font("Courier", "", 5)
                        pdf.cell(
                            0,
                            3,
                            pdf.safe(f"    [{role}]: {content}"),
                            new_x=XPos.LMARGIN,
                            new_y=YPos.NEXT,
                        )

            if pdf.get_y() > 260:
                pdf.add_page()

        pdf.ln(1)

        # Response
        pdf.sub_title("Response")
        resp_preview = m.get("response", "")[:1500]
        pdf.body(resp_preview, size=7)
        pdf.ln(1)

        # Screenshot
        ss_path = r.get("screenshot_path")
        if ss_path and Path(ss_path).exists():
            pdf.sub_title("Screenshot")
            try:
                if pdf.get_y() > 120:
                    pdf.add_page()
                pdf.image(str(ss_path), x=15, w=180)
            except Exception:
                pdf.body("[Screenshot could not be embedded]")
        pdf.ln(3)

        # Separator
        pdf.set_draw_color(180, 180, 180)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    # ---- Summary Table ----
    pdf.add_page()
    pdf.section_title("4. Summary Table")

    col_w = [7, 42, 18, 18, 12, 14, 14, 14, 14, 14, 14, 9]
    headers = [
        "#",
        "Question",
        "Expected",
        "Actual",
        "Time",
        "Router",
        "Agent",
        "InTok",
        "OutTok",
        "Total",
        "Calls",
        "OK",
    ]
    pdf.set_font("Helvetica", "B", 6)
    pdf.set_fill_color(41, 65, 122)
    pdf.set_text_color(255, 255, 255)
    for j, h in enumerate(headers):
        pdf.cell(
            col_w[j],
            5,
            h,
            border=1,
            fill=True,
            new_x=XPos.RIGHT,
            new_y=YPos.TOP,
            align="C",
        )
    pdf.ln()
    pdf.set_text_color(0, 0, 0)

    for r in results:
        q = r["question_data"]
        m = r["metrics"]
        pdf.set_font("Helvetica", "", 5)

        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 6)
            pdf.set_fill_color(41, 65, 122)
            pdf.set_text_color(255, 255, 255)
            for j, h in enumerate(headers):
                pdf.cell(
                    col_w[j],
                    5,
                    h,
                    border=1,
                    fill=True,
                    new_x=XPos.RIGHT,
                    new_y=YPos.TOP,
                    align="C",
                )
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 5)

        ok = "Y" if m["query_category"] == q["expected_agent"] else "N"
        vals = [
            str(q["id"]),
            q["question"][:35],
            q["expected_agent"],
            m["query_category"],
            f"{m['total_time']:.1f}",
            f"{m['router_time']:.1f}",
            f"{m['agent_time']:.1f}",
            str(m["total_input_tokens"]),
            str(m["total_output_tokens"]),
            str(m["total_tokens"]),
            str(m["num_llm_calls"]),
            ok,
        ]
        for j, val in enumerate(vals):
            pdf.cell(
                col_w[j], 4, pdf.safe(val), border=1, new_x=XPos.RIGHT, new_y=YPos.TOP
            )
        pdf.ln()

    # Totals row
    pdf.set_font("Helvetica", "B", 5)
    pdf.cell(
        col_w[0] + col_w[1] + col_w[2] + col_w[3],
        4,
        "TOTALS",
        border=1,
        new_x=XPos.RIGHT,
        new_y=YPos.TOP,
        align="R",
    )
    total_vals = [
        f"{total_time:.1f}",
        f"{sum(r['metrics']['router_time'] for r in results):.1f}",
        f"{sum(r['metrics']['agent_time'] for r in results):.1f}",
        str(sum(r["metrics"]["total_input_tokens"] for r in results)),
        str(sum(r["metrics"]["total_output_tokens"] for r in results)),
        str(total_tokens),
        str(total_calls),
        "",
    ]
    for j, val in enumerate(total_vals):
        pdf.cell(
            col_w[j + 4],
            4,
            pdf.safe(val),
            border=1,
            new_x=XPos.RIGHT,
            new_y=YPos.TOP,
            align="C",
        )
    pdf.ln()

    pdf_path = output_dir / "Instrumented_Test_Report.pdf"
    pdf.output(str(pdf_path))
    return pdf_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Test 3 questions only")
    parser.add_argument(
        "--count", type=int, default=22, help="Number of questions to test"
    )
    parser.add_argument(
        "--no-screenshots", action="store_true", help="Skip UI screenshots"
    )
    args = parser.parse_args()

    output_dir = PROJECT_ROOT / "test_results"
    screenshots_dir = output_dir / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    questions = TEST_QUESTIONS[:3] if args.dry_run else TEST_QUESTIONS[: args.count]

    print(f"\n{'=' * 70}")
    print("  Instrumented UI Test Runner")
    print(f"  Questions: {len(questions)} | Screenshots: {not args.no_screenshots}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 70}\n")

    # Build the graph with callback tracker
    print("Building agent graph...")
    from src.config.settings import get_llm
    from src.graph import build_graph

    tracker = LLMCallTracker()
    llm = get_llm()

    # Build graph with plain LLM (callbacks passed at invoke time)
    graph = build_graph(llm=llm)
    print("Graph built successfully.\n")

    results = []
    for i, q in enumerate(questions):
        qid = q["id"]
        question = q["question"]

        print(f"[{i + 1}/{len(questions)}] Q{qid}: {question}")

        # Run through graph with instrumentation
        try:
            metrics = run_single_question(graph, question, tracker)
            print(f"  Router: {metrics['query_category']} ({metrics['router_time']}s)")
            print(
                f"  Agent: {metrics['agent_time']}s | LLM calls: {metrics['num_llm_calls']}"
            )
            print(
                f"  Tokens: in={metrics['total_input_tokens']}, out={metrics['total_output_tokens']}, total={metrics['total_tokens']}"
            )
            print(f"  Total: {metrics['total_time']}s")
            print(f"  Response: {metrics['response'][:100]}...")
        except Exception as e:
            print(f"  ERROR: {e}")
            metrics = {
                "response": f"Error: {e}",
                "query_category": "error",
                "total_time": 0,
                "router_time": 0,
                "agent_time": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "num_llm_calls": 0,
                "router_calls": [],
                "agent_calls": [],
                "all_calls": [],
            }

        # Take screenshot
        ss_path = ""
        if not args.no_screenshots:
            ss_path = str(screenshots_dir / f"q{qid:02d}.png")
            print("  Taking screenshot...")
            take_ui_screenshot(question, ss_path)

        results.append(
            {
                "question_data": q,
                "metrics": metrics,
                "screenshot_path": ss_path,
                "timestamp": datetime.now().isoformat(),
            }
        )

        print()

    # Save JSON
    json_path = output_dir / "instrumented_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        # Make JSON serializable
        serializable = []
        for r in results:
            sr = {
                "question_data": r["question_data"],
                "metrics": {
                    k: v
                    for k, v in r["metrics"].items()
                    if k not in ("router_calls", "agent_calls", "all_calls")
                },
                "screenshot_path": r["screenshot_path"],
                "timestamp": r["timestamp"],
                "llm_calls": [
                    {k: v for k, v in c.items() if k != "messages"}
                    for c in r["metrics"].get("all_calls", [])
                ],
            }
            serializable.append(sr)
        json.dump(serializable, f, indent=2, ensure_ascii=False)
    print(f"JSON saved: {json_path}")

    # Generate PDF
    print("Generating PDF report...")
    pdf_path = generate_pdf_report(results, output_dir)
    print(f"PDF saved: {pdf_path}")

    # Final summary
    total_time = sum(r["metrics"]["total_time"] for r in results)
    total_tokens = sum(r["metrics"]["total_tokens"] for r in results)
    total_calls = sum(r["metrics"]["num_llm_calls"] for r in results)
    errors = sum(1 for r in results if r["metrics"]["query_category"] == "error")

    print(f"\n{'=' * 70}")
    print("  COMPLETE")
    print(f"  Questions: {len(results)} | Errors: {errors}")
    print(f"  Time: {total_time:.1f}s ({total_time / 60:.1f}min)")
    print(f"  Tokens: {total_tokens:,} across {total_calls} LLM calls")
    print(f"  Report: {pdf_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
