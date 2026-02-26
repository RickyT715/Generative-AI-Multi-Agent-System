"""Quick 9-question verification test: 3 SQL, 3 RAG, 3 General.

Targets previously problematic questions:
- Q10: RAG runaway loop (was 15 LLM calls)
- Q14: routing mismatch (expected rag_agent, got sql_agent)
- Q20: routing mismatch (expected general, got rag_agent)
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("HF_HOME", str(PROJECT_ROOT / ".hf_cache"))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

# Import after env setup — instrumented_test wraps stdout/stderr on import
from scripts.instrumented_test import LLMCallTracker, run_single_question  # noqa: E402

QUESTIONS = [
    # SQL (3)
    {
        "id": 1,
        "question": "Show me a list of all customers with enterprise subscription tier.",
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
        "id": 8,
        "question": "Show me all billing-related tickets from premium customers.",
        "expected_agent": "sql_agent",
        "category": "SQL - Cross-table",
    },
    # RAG (3) — Q10 was 15-call runaway, Q14 was misrouted to sql_agent
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
        "id": 14,
        "question": "What are the subscription tiers and their prices?",
        "expected_agent": "rag_agent",
        "category": "RAG - Terms of Service",
    },
    # General (3) — Q20 was misrouted to rag_agent
    {
        "id": 17,
        "question": "Hello! What can you help me with?",
        "expected_agent": "general",
        "category": "General - Greeting",
    },
    {
        "id": 20,
        "question": "Can you tell me about TechCorp's services?",
        "expected_agent": "general",
        "category": "General - About",
    },
    {
        "id": 22,
        "question": "Thank you for your help! Goodbye!",
        "expected_agent": "general",
        "category": "General - Courtesy",
    },
]


def main():
    print("=" * 70)
    print("  Quick Verification — 9 questions (3 SQL, 3 RAG, 3 General)")
    print("  Targeting: Q10 (runaway), Q14 (mismatch), Q20 (mismatch)")
    print("=" * 70)

    from src.graph import build_graph

    print("\nBuilding graph...")
    graph = build_graph()
    tracker = LLMCallTracker()

    results = []
    for i, q in enumerate(QUESTIONS):
        print(f"\n[{i + 1}/{len(QUESTIONS)}] Q{q['id']}: {q['question'][:65]}")
        metrics = run_single_question(graph, q["question"], tracker)

        match = "OK" if metrics["query_category"] == q["expected_agent"] else "MISMATCH"
        print(
            f"  Route: {metrics['query_category']} (expected: {q['expected_agent']}) [{match}]"
        )
        print(
            f"  LLM calls: {metrics['num_llm_calls']} | "
            f"Time: {metrics['total_time']:.1f}s | "
            f"Tokens: {metrics['total_tokens']}"
        )
        print(f"  Response: {metrics['response'][:120]}...")

        results.append({"question_data": q, "metrics": metrics})

    # Summary
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)

    total_calls = sum(r["metrics"]["num_llm_calls"] for r in results)
    total_tokens = sum(r["metrics"]["total_tokens"] for r in results)
    total_time = sum(r["metrics"]["total_time"] for r in results)
    mismatches = [
        r
        for r in results
        if r["metrics"]["query_category"] != r["question_data"]["expected_agent"]
    ]

    print(
        f"\n  Total: {total_calls} LLM calls | {total_tokens:,} tokens | {total_time:.1f}s"
    )
    print(f"  Average: {total_calls / len(results):.1f} calls/question")
    print(f"  Routing mismatches: {len(mismatches)}")
    for m in mismatches:
        q = m["question_data"]
        print(
            f"    Q{q['id']}: expected={q['expected_agent']}, got={m['metrics']['query_category']}"
        )

    print("\n  Per-question breakdown:")
    print(
        f"  {'ID':>3} | {'Expected':>12} | {'Actual':>12} | {'Calls':>5} | {'Time':>6} | {'Match':>5}"
    )
    print("  " + "-" * 60)
    for r in results:
        q = r["question_data"]
        m = r["metrics"]
        match = "OK" if m["query_category"] == q["expected_agent"] else "MISS"
        print(
            f"  {q['id']:>3} | {q['expected_agent']:>12} | {m['query_category']:>12} | "
            f"{m['num_llm_calls']:>5} | {m['total_time']:>5.1f}s | {match:>5}"
        )

    return len(mismatches) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
