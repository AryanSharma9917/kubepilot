"""Simple keyword-based retriever for local runbook search."""

import re
from collections import Counter
from pathlib import Path

from rag.chunking import chunk_markdown
from rag.loaders import load_markdown_documents
from rag.models import Document, RetrievedDocument

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


class KeywordRetriever:
    """Rank documents by token overlap with the query."""

    def __init__(self, documents: list[Document]) -> None:
        self._documents = documents

    def search(self, query: str, *, limit: int = 3) -> list[RetrievedDocument]:
        """Return the most relevant documents for a query."""

        query_terms = _token_counts(query)
        if not query_terms:
            return []

        matches: list[RetrievedDocument] = []
        for document in self._documents:
            score = _score_document(query_terms, document)
            if score > 0:
                matches.append(RetrievedDocument(document=document, score=score))

        return sorted(
            matches,
            key=lambda match: (-match.score, match.document.title, match.document.source),
        )[:limit]


def create_default_retriever(runbooks_dir: Path | None = None) -> KeywordRetriever:
    """Create a keyword retriever over the local runbook directory."""

    directory = runbooks_dir or Path("docs/runbooks")
    documents = chunk_markdown(load_markdown_documents(directory))
    return KeywordRetriever(documents)


def _score_document(query_terms: Counter[str], document: Document) -> int:
    document_text = f"{document.title}\n{document.content}"
    document_terms = _token_counts(document_text)
    return sum(
        query_count * document_terms.get(term, 0)
        for term, query_count in query_terms.items()
    )


def _token_counts(text: str) -> Counter[str]:
    return Counter(TOKEN_PATTERN.findall(text.lower()))
