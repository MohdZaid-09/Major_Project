"""
Run this once (and again any time you edit/add files in knowledge_base/) to
(re)build the local vector index used for retrieval.

Usage:
    .venv\\Scripts\\python.exe scripts\\ingest_knowledge_base.py
"""
import os
import re

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
CHROMA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_store")

# Free, local, multilingual embedding model - no API key needed.
# Handles cross-lingual retrieval reasonably (e.g. a Hindi query can still
# retrieve relevant English reference chunks), though English-to-English
# matching will be the most accurate.
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def chunk_markdown_file(filepath: str) -> list[dict]:
    """
    Splits a markdown file into chunks by ## headers.
    Each chunk becomes one retrievable unit, tagged with which
    condition (H1) and which system of medicine (H2) it covers.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()

    condition_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    condition = condition_match.group(1).strip() if condition_match else os.path.basename(filepath)

    source_match = re.search(r"^Source:\s*(https://\S+)", text, re.MULTILINE)
    reviewed_match = re.search(r"^Reviewed-on:\s*(\S+)", text, re.MULTILINE)
    sections = re.split(r"^##\s+(.+)$", text, flags=re.MULTILINE)
    # sections[0] is anything before the first ##; skip it (just the H1 title)
    chunks = []
    for i in range(1, len(sections), 2):
        system_name = sections[i].strip()
        content = sections[i + 1].strip()
        section_source = re.search(r"^Source:\s*(https://\S+)", content, re.MULTILINE) or source_match
        chunks.append({
            "condition": condition,
            "system": system_name,
            "content": content,
            "source_url": section_source.group(1) if section_source else "",
            "reviewed_on": reviewed_match.group(1) if reviewed_match else "",

        })
    return chunks


def build_index():
    import chromadb
    from chromadb.utils import embedding_functions
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL_NAME
    )

    # Start fresh each time this script runs, so edits/removals in
    # knowledge_base/ are reflected correctly (no stale entries).
    try:
        client.delete_collection("swasthai_kb")
    except Exception:
        pass

    collection = client.create_collection(
        name="swasthai_kb",
        embedding_function=embedding_fn,
    )

    documents, metadatas, ids = [], [], []
    doc_id = 0

    for filename in sorted(os.listdir(KB_DIR)):
        if not filename.endswith(".md"):
            continue
        filepath = os.path.join(KB_DIR, filename)
        chunks = chunk_markdown_file(filepath)
        for chunk in chunks:
            documents.append(f"{chunk['condition']} - {chunk['system']}: {chunk['content']}")
            metadatas.append({
                "condition": chunk["condition"],
                "system": chunk["system"],
                "source_file": filename,
                "source_url": chunk["source_url"],
                "reviewed_on": chunk["reviewed_on"],
            })
            ids.append(f"chunk_{doc_id}")
            doc_id += 1

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    print(f"Indexed {len(documents)} chunks from {KB_DIR} into {CHROMA_DIR}")


if __name__ == "__main__":
    build_index()
