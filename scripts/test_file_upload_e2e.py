"""Playwright-based E2E test for file upload and processing.

Uploads test files through the Streamlit UI, then verifies data
is queryable through the chat interface.

Usage:
    # Start the Streamlit app first:
    streamlit run app.py

    # Then run this test:
    python scripts/test_file_upload_e2e.py
"""

import os
import sys
from datetime import datetime

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")
TEST_FILES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "test_uploads",
)
RESULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "test_results",
    "e2e_upload",
)

# Files to upload in order
TEST_FILES = [
    "test_customers.csv",
    "test_tickets.csv",
    "quantum_backup_guide.pdf",
    "starshield_faq.txt",
]

# Verification questions and expected content
VERIFICATION_QUERIES = [
    {
        "question": "Is there a customer named Ziggy Stardust? What is their subscription tier?",
        "expect_contains": "enterprise",
        "agent": "SQL",
    },
    {
        "question": "Are there any tickets about quantum sync errors?",
        "expect_contains": "quantum sync",
        "agent": "SQL",
    },
    {
        "question": "What are the system requirements for Quantum Backup Ultra?",
        "expect_contains": "16GB",
        "agent": "RAG",
    },
    {
        "question": "How much does StarShield Antivirus cost per month?",
        "expect_contains": "$7.99",
        "agent": "RAG",
    },
]


def ensure_test_files():
    """Generate test files if they don't exist."""
    missing = [
        f for f in TEST_FILES if not os.path.exists(os.path.join(TEST_FILES_DIR, f))
    ]
    if missing:
        print(f"Generating missing test files: {missing}")
        from data.seed.generate_test_files import generate_all_test_files

        generate_all_test_files()

    # Verify all exist
    for f in TEST_FILES:
        path = os.path.join(TEST_FILES_DIR, f)
        if not os.path.exists(path):
            print(f"ERROR: Test file not found: {path}")
            sys.exit(1)


def run_e2e_test():
    """Run the full E2E upload and verification test."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "ERROR: playwright not installed. Run: pip install playwright && playwright install"
        )
        sys.exit(1)

    os.makedirs(RESULTS_DIR, exist_ok=True)
    ensure_test_files()

    results = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 900})

        print(f"\nConnecting to Streamlit at {STREAMLIT_URL}...")
        page.goto(STREAMLIT_URL, wait_until="networkidle", timeout=30000)
        page.wait_for_timeout(3000)

        # --- Upload each file ---
        for filename in TEST_FILES:
            filepath = os.path.join(TEST_FILES_DIR, filename)
            print(f"\nUploading: {filename}")

            # Find the file uploader and set files
            file_input = page.locator(
                'section[data-testid="stSidebar"] input[type="file"]'
            )
            file_input.set_input_files(filepath)
            page.wait_for_timeout(1000)

            # Click "Process Uploaded Files" button
            process_btn = page.get_by_text("Process Uploaded Files")
            if process_btn.is_visible(timeout=5000):
                process_btn.click()
                # Wait for processing to complete
                page.wait_for_timeout(5000)

            # Screenshot after processing
            screenshot_path = os.path.join(
                RESULTS_DIR, f"{timestamp}_upload_{filename}.png"
            )
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"  Screenshot: {screenshot_path}")

            results.append(
                {
                    "step": f"upload_{filename}",
                    "status": "done",
                    "screenshot": screenshot_path,
                }
            )

            # Clear the uploader for next file by reloading
            if filename != TEST_FILES[-1]:
                page.reload(wait_until="networkidle", timeout=15000)
                page.wait_for_timeout(2000)

        # --- Verification queries ---
        print("\n--- Verification Queries ---")
        for i, query in enumerate(VERIFICATION_QUERIES):
            print(f"\nQuery {i + 1}: {query['question']}")

            # Reload to clear state
            page.reload(wait_until="networkidle", timeout=15000)
            page.wait_for_timeout(2000)

            # Type the question in the chat input
            chat_input = page.locator('textarea[data-testid="stChatInputTextArea"]')
            chat_input.fill(query["question"])
            page.keyboard.press("Enter")

            # Wait for response
            page.wait_for_timeout(15000)

            # Screenshot the response
            screenshot_path = os.path.join(
                RESULTS_DIR, f"{timestamp}_query_{i + 1}.png"
            )
            page.screenshot(path=screenshot_path, full_page=True)

            # Try to extract the response text
            chat_messages = page.locator('[data-testid="stChatMessage"]').all()
            response_text = ""
            if len(chat_messages) >= 2:
                response_text = chat_messages[-1].inner_text()

            expected = query["expect_contains"].lower()
            passed = expected in response_text.lower()

            status = "PASS" if passed else "FAIL"
            print(f"  Expected '{query['expect_contains']}' in response: {status}")
            print(f"  Response preview: {response_text[:200]}...")

            results.append(
                {
                    "step": f"query_{i + 1}",
                    "question": query["question"],
                    "expected": query["expect_contains"],
                    "agent": query["agent"],
                    "passed": passed,
                    "response_preview": response_text[:500],
                    "screenshot": screenshot_path,
                }
            )

        browser.close()

    # --- Generate report ---
    report_path = os.path.join(RESULTS_DIR, f"{timestamp}_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("File Upload E2E Test Report\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write("=" * 60 + "\n\n")

        upload_results = [r for r in results if r["step"].startswith("upload_")]
        query_results = [r for r in results if r["step"].startswith("query_")]

        f.write(f"Uploads: {len(upload_results)}/{len(TEST_FILES)} completed\n\n")

        passed = sum(1 for r in query_results if r.get("passed"))
        f.write(f"Queries: {passed}/{len(query_results)} passed\n\n")

        for r in query_results:
            status = "PASS" if r.get("passed") else "FAIL"
            f.write(f"[{status}] {r['question']}\n")
            f.write(f"  Expected: {r['expected']}\n")
            f.write(f"  Agent: {r['agent']}\n")
            f.write(f"  Response: {r.get('response_preview', 'N/A')[:200]}\n\n")

    print(f"\nReport saved to: {report_path}")
    print(f"Screenshots in: {RESULTS_DIR}")

    # Summary
    query_results = [r for r in results if r["step"].startswith("query_")]
    passed = sum(1 for r in query_results if r.get("passed"))
    total = len(query_results)
    print(f"\nResults: {passed}/{total} verification queries passed")

    return passed == total


if __name__ == "__main__":
    success = run_e2e_test()
    sys.exit(0 if success else 1)
