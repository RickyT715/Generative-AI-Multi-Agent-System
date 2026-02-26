"""Index PDF documents into ChromaDB vector store."""

import glob
import os


def index_all_documents(docs_dir="data/documents", chunk_size=512, chunk_overlap=50):
    """Load all PDFs from docs_dir and index into ChromaDB."""
    from src.db.vector_store import add_pdf_files

    pdf_files = sorted(glob.glob(os.path.join(docs_dir, "*.pdf")))

    if not pdf_files:
        print(f"  No PDF files found in {docs_dir}/")
        return 0

    num_chunks = add_pdf_files(pdf_files, chunk_size, chunk_overlap)
    print(f"  Indexed {len(pdf_files)} PDFs ({num_chunks} chunks) into ChromaDB")
    return num_chunks


if __name__ == "__main__":
    index_all_documents()
