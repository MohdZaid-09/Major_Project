"""
Retrieval service: given a user's symptom message, finds the most relevant
reference chunks from the local knowledge base and formats them as context
to feed into the LLM prompt.
"""
import os
import logging
from threading import Lock

CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "chroma_store")
CHROMA_DIR = os.path.normpath(CHROMA_DIR)
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_client = None
_collection = None
_collection_lock = Lock()
logger = logging.getLogger(__name__)


def _get_collection():
    global _client, _collection
    with _collection_lock:
        if _collection is None:
            import chromadb
            from chromadb.utils import embedding_functions
            _client = chromadb.PersistentClient(path=CHROMA_DIR)
            embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBEDDING_MODEL_NAME
            )
            _collection = _client.get_collection(name="swasthai_kb", embedding_function=embedding_fn)
        return _collection


def warmup_retrieval():
    """Pay model initialization/first embedding cost before accepting requests."""
    retrieve_context_with_sources("general health guidance")


def _retrieve_chunks(query: str, top_k: int = 4) -> tuple[list[str], list[dict]]:
    collection = _get_collection()
    count = collection.count()
    if not count or top_k < 1:
        return [], []
    results = collection.query(query_texts=[query], n_results=min(top_k, count))
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    chunks = []
    sources = []
    for doc, meta in zip(documents, metadatas):
        metadata = meta or {}
        chunks.append(
            f"[{metadata.get('condition', 'Unknown')} — {metadata.get('system', 'Unknown')}]\n{doc}"
        )
        sources.append({
            "condition": metadata.get("condition", "Unknown"),
            "system": metadata.get("system", "Unknown"),
            "source_file": metadata.get("source_file", "Unknown"),
            "source_url": metadata.get("source_url", ""),
            "reviewed_on": metadata.get("reviewed_on", ""),
        })
    return chunks, sources


def retrieve_context_with_sources(query: str, top_k: int = 4) -> dict:
    """Return grounded context and safe source labels for the current query."""
    try:
        chunks, sources = _retrieve_chunks(query, top_k)
    except Exception:
        logger.warning("Knowledge retrieval unavailable; using general-knowledge fallback", exc_info=True)
        return {"context": "", "sources": []}

    return {"context": "\n\n".join(chunks), "sources": sources}


def retrieve_context(query: str, top_k: int = 4) -> str:
    """
    Returns a formatted string of the most relevant reference chunks, or an
    empty string if the knowledge base hasn't been built yet or nothing
    relevant is found. Empty string is safe - the LLM just falls back to
    its own general knowledge with no reference material provided.
    """
    return retrieve_context_with_sources(query, top_k)["context"]
