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


@dataclass(frozen=True)
class EvaluationCaseResult:
    """One retrieval evaluation case result."""

    query: str
    expected_sources: tuple[str, ...]
    returned_sources: tuple[str, ...]
    passed: bool


@dataclass(frozen=True)
class EvaluationReport:
    """Detailed retrieval evaluation report."""

    summary: EvaluationResult
    cases: tuple[EvaluationCaseResult, ...]


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


def evaluate_retriever_detailed(
    retriever: Searcher,
    cases: list[EvaluationCase],
    *,
    limit: int = 3,
) -> EvaluationReport:
    """Evaluate retrieval and keep per-case returned sources."""

    case_results: list[EvaluationCaseResult] = []
    for case in cases:
        matches = retriever.search(case.query, limit=limit)
        returned_sources = tuple(match.document.source for match in matches)
        returned_source_set = set(returned_sources)
        passed = all(source in returned_source_set for source in case.expected_sources)
        case_results.append(
            EvaluationCaseResult(
                query=case.query,
                expected_sources=case.expected_sources,
                returned_sources=returned_sources,
                passed=passed,
            )
        )

    passed_count = sum(1 for case_result in case_results if case_result.passed)
    total = len(case_results)
    summary = EvaluationResult(
        total=total,
        passed=passed_count,
        failed=total - passed_count,
        recall_at_k=passed_count / total if total else 0.0,
    )
    return EvaluationReport(summary=summary, cases=tuple(case_results))


def render_markdown_report(report: EvaluationReport, *, limit: int) -> str:
    """Render a retrieval evaluation report as markdown."""

    lines = [
        "# KubePilot Retrieval Evaluation",
        "",
        f"- Recall@{limit}: {report.summary.recall_at_k:.3f}",
        f"- Passed: {report.summary.passed}",
        f"- Failed: {report.summary.failed}",
        f"- Total: {report.summary.total}",
        "",
        "| Query | Expected Sources | Returned Sources | Result |",
        "| --- | --- | --- | --- |",
    ]
    for case_result in report.cases:
        expected = ", ".join(case_result.expected_sources) or "-"
        returned = ", ".join(case_result.returned_sources) or "-"
        result = "pass" if case_result.passed else "fail"
        lines.append(
            f"| {_escape_table_cell(case_result.query)} | "
            f"{_escape_table_cell(expected)} | "
            f"{_escape_table_cell(returned)} | "
            f"{result} |"
        )
    return "\n".join(lines) + "\n"


def _escape_table_cell(value: str) -> str:
    return value.replace("|", "\\|")
