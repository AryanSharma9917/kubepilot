"""Persisted runbook index support."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rag.chunking import chunk_markdown
from rag.embeddings import EmbeddingModel, HashingEmbeddingModel
from rag.loaders import load_markdown_documents
from rag.models import Document
from rag.retrieval.vector import VectorRetriever

INDEX_VERSION = 1


@dataclass(frozen=True)
class PersistedIndex:
    """Serializable retrieval index for local runbooks."""

    version: int
    embedding_model: str
    documents: list[Document]
    vectors: list[list[float]]


def build_runbook_index(
    *,
    runbooks_dir: Path,
    embedding_model: EmbeddingModel | None = None,
) -> PersistedIndex:
    """Build a persisted index model from markdown runbooks."""

    model = embedding_model or HashingEmbeddingModel()
    documents = chunk_markdown(load_markdown_documents(runbooks_dir))
    vectors = [
        model.embed(f"{document.title}\n{document.content}")
        for document in documents
    ]
    return PersistedIndex(
        version=INDEX_VERSION,
        embedding_model=type(model).__name__,
        documents=documents,
        vectors=vectors,
    )


def write_runbook_index(index: PersistedIndex, path: Path) -> None:
    """Write a persisted index as JSON."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": index.version,
        "embedding_model": index.embedding_model,
        "documents": [asdict(document) for document in index.documents],
        "vectors": index.vectors,
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_runbook_index(path: Path) -> PersistedIndex:
    """Read a persisted runbook index from JSON."""

    payload = json.loads(path.read_text(encoding="utf-8"))
    _validate_payload(payload)
    return PersistedIndex(
        version=payload["version"],
        embedding_model=payload["embedding_model"],
        documents=[
            Document(
                source=document["source"],
                title=document["title"],
                content=document["content"],
                metadata=document.get("metadata", {}),
            )
            for document in payload["documents"]
        ],
        vectors=payload["vectors"],
    )


def create_persisted_vector_retriever(path: Path) -> VectorRetriever:
    """Create a vector retriever from a persisted index."""

    index = read_runbook_index(path)
    return VectorRetriever(
        index.documents,
        embedding_model=HashingEmbeddingModel(),
        prefer_faiss=True,
        vectors=index.vectors,
    )


def _validate_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise ValueError("Index payload must be a JSON object.")
    if payload.get("version") != INDEX_VERSION:
        raise ValueError(f"Unsupported index version: {payload.get('version')}")
    if not isinstance(payload.get("documents"), list):
        raise ValueError("Index payload must contain documents.")
    if not isinstance(payload.get("vectors"), list):
        raise ValueError("Index payload must contain vectors.")
