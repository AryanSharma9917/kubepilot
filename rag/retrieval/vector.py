"""Vector retrieval with optional FAISS acceleration."""

from pathlib import Path

from rag.chunking import chunk_markdown
from rag.embeddings import EmbeddingModel, HashingEmbeddingModel
from rag.loaders import load_markdown_documents
from rag.models import Document, RetrievedDocument


class VectorRetriever:
    """Retrieve documents by embedding similarity."""

    def __init__(
        self,
        documents: list[Document],
        embedding_model: EmbeddingModel | None = None,
        *,
        prefer_faiss: bool = True,
        vectors: list[list[float]] | None = None,
    ) -> None:
        self._documents = documents
        self._embedding_model = embedding_model or HashingEmbeddingModel()
        self._vectors = vectors or [
            self._embedding_model.embed(_document_text(document))
            for document in documents
        ]
        self._faiss_index = None
        self._numpy = None
        if prefer_faiss:
            self._build_faiss_index()

    def search(self, query: str, *, limit: int = 3) -> list[RetrievedDocument]:
        """Return the most relevant documents for a query."""

        query_vector = self._embedding_model.embed(query)
        if not any(query_vector):
            return []
        if self._faiss_index is not None and self._numpy is not None:
            return self._search_faiss(query_vector, limit=limit)
        return self._search_memory(query_vector, limit=limit)

    @property
    def backend(self) -> str:
        """Return the active vector search backend."""

        return "faiss" if self._faiss_index is not None else "memory"

    def _build_faiss_index(self) -> None:
        if not self._vectors:
            return
        try:
            import faiss
            import numpy
        except ImportError:
            return

        matrix = numpy.array(self._vectors, dtype="float32")
        index = faiss.IndexFlatIP(len(self._vectors[0]))
        index.add(matrix)
        self._faiss_index = index
        self._numpy = numpy

    def _search_faiss(self, query_vector: list[float], *, limit: int) -> list[RetrievedDocument]:
        query = self._numpy.array([query_vector], dtype="float32")
        scores, indexes = self._faiss_index.search(query, min(limit, len(self._documents)))
        matches: list[RetrievedDocument] = []
        for score, index in zip(scores[0], indexes[0], strict=True):
            if index >= 0 and score > 0:
                matches.append(
                    RetrievedDocument(document=self._documents[index], score=float(score))
                )
        return matches

    def _search_memory(self, query_vector: list[float], *, limit: int) -> list[RetrievedDocument]:
        matches = [
            RetrievedDocument(document=document, score=_dot(query_vector, vector))
            for document, vector in zip(self._documents, self._vectors, strict=True)
        ]
        return sorted(
            [match for match in matches if match.score > 0],
            key=lambda match: (-match.score, match.document.title, match.document.source),
        )[:limit]


def create_vector_retriever(runbooks_dir: Path | None = None) -> VectorRetriever:
    """Create a vector retriever over the local runbook directory."""

    directory = runbooks_dir or Path("docs/runbooks")
    documents = chunk_markdown(load_markdown_documents(directory))
    return VectorRetriever(documents)


def _document_text(document: Document) -> str:
    return f"{document.title}\n{document.content}"


def _dot(left: list[float], right: list[float]) -> float:
    return sum(
        left_value * right_value
        for left_value, right_value in zip(left, right, strict=True)
    )
