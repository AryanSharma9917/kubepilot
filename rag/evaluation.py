"""Retrieval evaluation helpers."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from rag.models import RetrievedDocument


class Searcher(Protocol):
    """Minimal search interface used by retrieval evaluation."""

    def search(self, query: str, *, limit: int = 3) -> list[RetrievedDocument]:
        """Return matching documents."""


@dataclass(frozen=True)
class EvaluationCase:
    """One retrieval evaluation example."""

    query: str
    expected_sources: tuple[str, ...]


@dataclass(frozen=True)
class EvaluationResult:
    """Aggregate retrieval evaluation result."""

    total: int
    passed: int
    failed: int
    recall_at_k: float


def load_evaluation_cases(path: Path) -> list[EvaluationCase]:
    """Load retrieval evaluation cases from JSONL."""

    cases: list[EvaluationCase] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        expected_sources = payload.get("expected_sources")
        if not isinstance(payload.get("query"), str) or not isinstance(expected_sources, list):
            raise ValueError(f"Invalid evaluation case on line {line_number}")
        cases.append(
            EvaluationCase(
                query=payload["query"],
                expected_sources=tuple(str(source) for source in expected_sources),
            )
        )
    return cases


def evaluate_retriever(
    retriever: Searcher,
    cases: list[EvaluationCase],
    *,
    limit: int = 3,
) -> EvaluationResult:
    """Evaluate whether expected sources appear in top-k retrieval results."""

    passed = 0
    for case in cases:
        matches = retriever.search(case.query, limit=limit)
        returned_sources = {match.document.source for match in matches}
        if all(source in returned_sources for source in case.expected_sources):
            passed += 1

    total = len(cases)
    failed = total - passed
    recall_at_k = passed / total if total else 0.0
    return EvaluationResult(
        total=total,
        passed=passed,
        failed=failed,
        recall_at_k=recall_at_k,
    )
