"""
Page-Indexed Vector Database Builder
Chunks PDFs by page with metadata (page number, source, section) for fast retrieval.
"""

import os
import re
import shutil
from pathlib import Path
from typing import List

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_core.documents import Document

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
VECTORDB_DIR = SCRIPT_DIR / "vectordb"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

# Chunking config - smaller chunks = faster embedding search + more precise hits
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def detect_section_header(text: str) -> str:
    """Extract section/heading from chunk text if present."""
    lines = text.strip().split('\n')
    for line in lines[:3]:
        line = line.strip()
        # Match common header patterns: numbered sections, all-caps, markdown-style
        if re.match(r'^(\d+[\.\)]\s|#{1,3}\s|[A-Z][A-Z\s]{5,}$)', line):
            return line[:120]
    return ""


def enrich_metadata(docs: List[Document], source_name: str) -> List[Document]:
    """Add page index, source name, and section headers to each document's metadata."""
    enriched = []
    for doc in docs:
        page = doc.metadata.get("page", 0)
        section = detect_section_header(doc.page_content)
        doc.metadata.update({
            "source_file": source_name,
            "page_number": page + 1,  # 1-indexed for display
            "section": section,
            "char_count": len(doc.page_content),
        })
        enriched.append(doc)
    return enriched


def load_documents() -> List[Document]:
    """Load all documents from data directory with page-level metadata."""
    all_docs = []

    for file_path in sorted(DATA_DIR.glob("*.pdf")):
        print(f"   [PDF] {file_path.name}")
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()
        pages = enrich_metadata(pages, file_path.name)
        all_docs.extend(pages)
        print(f"         -> {len(pages)} pages loaded")

    for file_path in sorted(DATA_DIR.glob("*.txt")):
        print(f"   [TXT] {file_path.name}")
        loader = TextLoader(str(file_path), encoding='utf-8')
        docs = loader.load()
        docs = enrich_metadata(docs, file_path.name)
        all_docs.extend(docs)

    for file_path in sorted(DATA_DIR.glob("*.md")):
        print(f"   [MD]  {file_path.name}")
        loader = TextLoader(str(file_path), encoding='utf-8')
        docs = loader.load()
        docs = enrich_metadata(docs, file_path.name)
        all_docs.extend(docs)

    return all_docs


def chunk_documents(docs: List[Document]) -> List[Document]:
    """Split documents into small chunks, preserving page metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " "],
        keep_separator=True,
    )

    chunks = []
    for doc in docs:
        splits = splitter.split_documents([doc])
        # Each split inherits parent metadata (page_number, source_file, etc.)
        for i, split in enumerate(splits):
            split.metadata["chunk_index"] = i
            # Re-detect section for sub-chunks
            section = detect_section_header(split.page_content)
            if section:
                split.metadata["section"] = section
            chunks.append(split)

    return chunks


def rebuild_database():
    print("=" * 60)
    print("PAGE-INDEXED VECTOR DATABASE BUILDER")
    print("=" * 60)

    # Clear existing DB
    if VECTORDB_DIR.exists():
        print("\n[*] Removing existing vector database...")
        shutil.rmtree(VECTORDB_DIR)

    # Embeddings
    print(f"\n[*] Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
    )

    # Load
    print(f"\n[*] Loading documents from: {DATA_DIR}")
    docs = load_documents()
    print(f"\n    Total pages/docs loaded: {len(docs)}")

    # Chunk
    print(f"\n[*] Chunking (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})...")
    chunks = chunk_documents(docs)
    print(f"    Total chunks: {len(chunks)}")

    # Preview
    print(f"\n[*] Sample chunks:")
    for i, c in enumerate(chunks[:3]):
        meta = c.metadata
        preview = c.page_content[:90].replace('\n', ' ')
        print(f"    {i+1}. [p{meta['page_number']}|{meta['source_file']}] {preview}...")

    # Build vector store
    print(f"\n[*] Building vector database...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTORDB_DIR),
    )

    count = vectorstore._collection.count()
    print(f"\n[OK] Vector database created: {count} vectors")

    # Test
    print(f"\n[*] Testing retrieval...")
    test_queries = [
        "error code 1A68H",
        "camera not capturing images",
        "light intensity too bright",
    ]

    for query in test_queries:
        print(f"\n    Query: '{query}'")
        results = vectorstore.similarity_search_with_relevance_scores(query, k=2)
        for doc, score in results:
            meta = doc.metadata
            preview = doc.page_content[:70].replace('\n', ' ')
            print(f"      [{score:.3f}] p{meta['page_number']} | {meta['source_file']} | {preview}...")

    print("\n" + "=" * 60)
    print("REBUILD COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    rebuild_database()
