"""ChromaDB vector store for document retrieval."""

import os

from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import get_chroma_settings, get_embedding_model


def get_vector_store():
    """Get or create ChromaDB vector store instance."""
    settings = get_chroma_settings()
    embeddings = get_embedding_model()

    return Chroma(
        collection_name=settings["collection_name"],
        embedding_function=embeddings,
        persist_directory=settings["persist_directory"],
    )


def get_retriever(search_kwargs=None):
    """Get a retriever from the vector store."""
    search_kwargs = search_kwargs or {"k": 5}
    vector_store = get_vector_store()
    return vector_store.as_retriever(search_kwargs=search_kwargs)


def add_documents(documents, chunk_size=512, chunk_overlap=50):
    """Split and add documents to the vector store.

    Args:
        documents: List of LangChain Document objects
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    chunks = text_splitter.split_documents(documents)

    vector_store = get_vector_store()
    vector_store.add_documents(chunks)

    return len(chunks)


def add_pdf_files(file_paths, chunk_size=512, chunk_overlap=50):
    """Process PDF files and add to vector store.

    Args:
        file_paths: List of paths to PDF files
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks

    Returns:
        Number of chunks indexed
    """
    from langchain_community.document_loaders import PyMuPDFLoader

    all_docs = []
    for path in file_paths:
        if not os.path.exists(path):
            print(f"  Warning: {path} not found, skipping")
            continue
        loader = PyMuPDFLoader(path)
        docs = loader.load()
        all_docs.extend(docs)

    if not all_docs:
        print("  No documents to index")
        return 0

    return add_documents(all_docs, chunk_size, chunk_overlap)


def add_text_files(file_paths, chunk_size=512, chunk_overlap=50):
    """Process plain text files and add to vector store.

    Args:
        file_paths: List of paths to .txt files
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks

    Returns:
        Number of chunks indexed
    """
    from langchain_community.document_loaders import TextLoader

    all_docs = []
    for path in file_paths:
        if not os.path.exists(path):
            print(f"  Warning: {path} not found, skipping")
            continue
        loader = TextLoader(path, encoding="utf-8")
        docs = loader.load()
        all_docs.extend(docs)

    if not all_docs:
        print("  No documents to index")
        return 0

    return add_documents(all_docs, chunk_size, chunk_overlap)


def get_document_count():
    """Return the number of documents in the ChromaDB collection."""
    try:
        vector_store = get_vector_store()
        collection = vector_store._collection
        return collection.count()
    except Exception:
        return 0
