"""ChromaDB vector store with semantic chunking, hybrid search, and cross-encoder reranking."""

import logging
import os

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.config.settings import get_chroma_settings, get_embedding_model

logger = logging.getLogger(__name__)


def _semantic_split_documents(
    documents, fallback_chunk_size=512, fallback_chunk_overlap=50
):
    """Split documents using semantic chunking with per-document fallback.

    Uses SemanticChunker from langchain_experimental when available.
    Falls back to RecursiveCharacterTextSplitter for short docs, errors,
    or when the package is not installed.
    """
    fallback_splitter = RecursiveCharacterTextSplitter(
        chunk_size=fallback_chunk_size,
        chunk_overlap=fallback_chunk_overlap,
    )

    try:
        from langchain_experimental.text_splitter import SemanticChunker
    except ImportError:
        logger.warning(
            "langchain-experimental not installed, falling back to RecursiveCharacterTextSplitter"
        )
        return fallback_splitter.split_documents(documents)

    embeddings = get_embedding_model()
    semantic_chunker = SemanticChunker(
        embeddings,
        breakpoint_threshold_type="percentile",
        breakpoint_threshold_amount=90,
    )

    all_chunks = []
    for doc in documents:
        if len(doc.page_content) < 200:
            all_chunks.extend(fallback_splitter.split_documents([doc]))
            continue
        try:
            chunks = semantic_chunker.split_documents([doc])
            all_chunks.extend(chunks)
        except Exception:
            logger.debug(
                "Semantic chunking failed for doc (source=%s), using fallback",
                doc.metadata.get("source", "unknown"),
            )
            all_chunks.extend(fallback_splitter.split_documents([doc]))

    return all_chunks


def _load_documents_from_chroma(vector_store):
    """Load all stored chunks from ChromaDB as Document objects for BM25 indexing."""
    collection_data = vector_store._collection.get(include=["documents", "metadatas"])
    documents = []
    for text, metadata in zip(
        collection_data["documents"], collection_data["metadatas"], strict=True
    ):
        documents.append(Document(page_content=text, metadata=metadata or {}))
    return documents


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
    """Get a hybrid retriever with BM25 + dense search and cross-encoder reranking.

    Pipeline: BM25(k=20) + Dense(k=20) -> EnsembleRetriever(0.4/0.6) -> CrossEncoderReranker(top_n=5)
    Falls back gracefully to plain dense retriever if any component fails.
    """
    search_kwargs = search_kwargs or {"k": 5}
    vector_store = get_vector_store()

    # --- Dense retriever (always available) ---
    dense_retriever = vector_store.as_retriever(search_kwargs={"k": 20})

    # --- Try to build hybrid + reranked pipeline ---
    try:
        from langchain_classic.retrievers import EnsembleRetriever
        from langchain_community.retrievers import BM25Retriever

        stored_docs = _load_documents_from_chroma(vector_store)
        if len(stored_docs) < 1:
            raise ValueError("No documents in ChromaDB, cannot build BM25 index")

        bm25_retriever = BM25Retriever.from_documents(stored_docs, k=20)
        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, dense_retriever],
            weights=[0.4, 0.6],
        )
        logger.info("Hybrid retriever (BM25 + dense) initialized")
    except Exception:
        logger.warning(
            "BM25/ensemble setup failed, using dense-only retriever", exc_info=True
        )
        ensemble_retriever = None

    base_retriever = ensemble_retriever or dense_retriever

    # --- Try to add cross-encoder reranking ---
    try:
        from langchain_classic.retrievers import ContextualCompressionRetriever
        from langchain_classic.retrievers.document_compressors import (
            CrossEncoderReranker,
        )
        from langchain_community.cross_encoders import HuggingFaceCrossEncoder

        top_n = search_kwargs.get("k", 5)
        cross_encoder = HuggingFaceCrossEncoder(
            model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
        )
        reranker = CrossEncoderReranker(model=cross_encoder, top_n=top_n)

        retriever = ContextualCompressionRetriever(
            base_compressor=reranker,
            base_retriever=base_retriever,
        )
        logger.info("Cross-encoder reranker initialized (top_n=%d)", top_n)
        return retriever
    except Exception:
        logger.warning(
            "Cross-encoder reranker setup failed, using base retriever", exc_info=True
        )
        # If no ensemble either, restore original k
        if ensemble_retriever is None:
            return vector_store.as_retriever(search_kwargs=search_kwargs)
        return base_retriever


def add_documents(documents, chunk_size=512, chunk_overlap=50):
    """Split and add documents to the vector store.

    Uses semantic chunking when available, with RecursiveCharacterTextSplitter as fallback.

    Args:
        documents: List of LangChain Document objects
        chunk_size: Fallback chunk size for RecursiveCharacterTextSplitter
        chunk_overlap: Fallback overlap for RecursiveCharacterTextSplitter
    """
    chunks = _semantic_split_documents(documents, chunk_size, chunk_overlap)

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
