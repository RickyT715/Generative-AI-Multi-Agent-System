"""One-command setup: generate data -> seed SQLite -> generate PDFs -> index into ChromaDB."""

import os
import sys

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    print("Setting up Generative AI Multi-Agent Customer Support System\n")

    # Step 1: Generate synthetic data and seed SQLite
    print("[1/3] Generating synthetic data and seeding SQLite database...")
    from data.seed.seed_database import seed_database

    seed_database()
    print()

    # Step 2: Generate sample policy PDFs
    print("[2/3] Generating sample company policy PDFs...")
    from data.seed.generate_pdfs import generate_all_pdfs

    generate_all_pdfs()
    print()

    # Step 3: Index PDFs into ChromaDB
    print("[3/3] Indexing PDF documents into ChromaDB...")
    from data.seed.index_documents import index_all_documents

    num_chunks = index_all_documents()
    print()

    print("=" * 50)
    print("Setup complete!")
    print(f"  - SQLite database: data/customer_support.db")
    print(f"  - Policy PDFs: data/documents/")
    print(f"  - ChromaDB index: {num_chunks} chunks indexed")
    print("=" * 50)


if __name__ == "__main__":
    main()
