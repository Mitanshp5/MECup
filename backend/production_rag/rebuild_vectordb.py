"""
Rebuild Vector Database with proper chunking for better retrieval
"""

import os
import shutil
from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
VECTORDB_DIR = SCRIPT_DIR / "vectordb"
EMBEDDING_MODEL = "BAAI/bge-base-en-v1.5"

def rebuild_database():
    print("="*60)
    print("REBUILDING VECTOR DATABASE")
    print("="*60)
    
    # Remove existing vector database
    if VECTORDB_DIR.exists():
        print(f"\n🗑️  Removing existing vector database...")
        shutil.rmtree(VECTORDB_DIR)
    
    # Load embeddings
    print(f"\n📦 Loading embedding model: {EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Load documents
    print(f"\n📄 Loading documents from: {DATA_DIR}")
    documents = []
    
    for file_path in DATA_DIR.glob("*.txt"):
        print(f"   Loading: {file_path.name}")
        loader = TextLoader(str(file_path), encoding='utf-8')
        documents.extend(loader.load())
    
    for file_path in DATA_DIR.glob("*.md"):
        print(f"   Loading: {file_path.name}")
        loader = TextLoader(str(file_path), encoding='utf-8')
        documents.extend(loader.load())
    
    print(f"\n   Total documents loaded: {len(documents)}")
    
    # Split documents into smaller chunks for better retrieval
    print(f"\n✂️  Splitting documents into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
        separators=["\n======", "\n\n", "\n", ". ", " "]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"   Total chunks created: {len(chunks)}")
    
    # Show sample chunks
    print(f"\n📋 Sample chunks:")
    for i, chunk in enumerate(chunks[:3]):
        preview = chunk.page_content[:100].replace('\n', ' ')
        print(f"   {i+1}. {preview}...")
    
    # Create vector database
    print(f"\n🔧 Creating vector database...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(VECTORDB_DIR)
    )
    
    print(f"\n✅ Vector database created at: {VECTORDB_DIR}")
    print(f"   Total vectors: {vectorstore._collection.count()}")
    
    # Test retrieval
    print(f"\n🧪 Testing retrieval...")
    test_queries = [
        "oversaturated images too bright",
        "light intensity",
        "camera not capturing"
    ]
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        docs = retriever.invoke(query)
        for doc in docs:
            preview = doc.page_content[:80].replace('\n', ' ')
            print(f"      → {preview}...")
    
    print("\n" + "="*60)
    print("REBUILD COMPLETE")
    print("="*60)

if __name__ == "__main__":
    rebuild_database()
