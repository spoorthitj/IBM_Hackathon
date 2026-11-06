"""
Memory — Vector Store (ChromaDB Long-Term Memory)
Stores agent outputs, historical facts, and domain knowledge for retrieval.
"""
import os

_collection = None
_client     = None
DB_PATH     = os.path.join(os.path.dirname(__file__), "..", ".chromadb_store")


def _get_collection():
    global _collection, _client
    if _collection is not None:
        return _collection
    try:
        import chromadb
        _client     = chromadb.PersistentClient(path=DB_PATH)
        _collection = _client.get_or_create_collection(
            name="cyclone_memory",
            metadata={"hnsw:space": "cosine"},
        )
        return _collection
    except Exception as e:
        print(f"[vector_store] ChromaDB unavailable: {e}")
        return None


def store_document(doc_id: str, text: str, metadata: dict | None = None):
    """Store a document in the vector store."""
    col = _get_collection()
    if col is None:
        return
    try:
        col.upsert(
            ids=[doc_id],
            documents=[text[:3000]],
            metadatas=[metadata or {}],
        )
    except Exception as e:
        print(f"[vector_store] store error: {e}")


def query(query_text: str, n_results: int = 3) -> list[dict]:
    """Retrieve relevant documents for a query."""
    col = _get_collection()
    if col is None:
        return []
    try:
        results = col.query(query_texts=[query_text[:500]], n_results=n_results)
        docs  = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        return [{"text": d, "meta": m} for d, m in zip(docs, metas)]
    except Exception:
        return []


def query_as_context(query_text: str, n: int = 2) -> str:
    """Return retrieved documents as a formatted context string."""
    docs = query(query_text, n)
    if not docs:
        return ""
    return "\n---\n".join(f"[Memory] {d['text'][:400]}" for d in docs)


def store_agent_output(agent_name: str, run_id: str, report: str):
    store_document(
        doc_id=f"{agent_name}_{run_id}",
        text=report,
        metadata={"agent": agent_name, "run": run_id, "type": "agent_output"},
    )


def collection_count() -> int:
    col = _get_collection()
    try:
        return col.count() if col else 0
    except Exception:
        return 0
