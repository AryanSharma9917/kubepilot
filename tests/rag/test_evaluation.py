from pathlib import Path

from rag.evaluation import (
    EvaluationCase,
    evaluate_retriever,
    evaluate_retriever_detailed,
    load_evaluation_cases,
    render_markdown_report,
)
from rag.models import Document
from rag.retrieval import KeywordRetriever


def test_load_evaluation_cases_from_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    path.write_text(
        '{"query": "image pull failing", "expected_sources": ["deployment.md"]}\n',
        encoding="utf-8",
    )

    cases = load_evaluation_cases(path)

    assert cases == [
        EvaluationCase(
            query="image pull failing",
            expected_sources=("deployment.md",),
        )
    ]


def test_evaluate_retriever_reports_recall_at_k() -> None:
    retriever = KeywordRetriever(
        [
            Document(
                source="deployment.md",
                title="Deployment rollout failures",
                content="ImagePullBackOff during deployment rollout.",
            )
        ]
    )

    result = evaluate_retriever(
        retriever,
        [
            EvaluationCase(
                query="deployment image pull",
                expected_sources=("deployment.md",),
            )
        ],
    )

    assert result.total == 1
    assert result.passed == 1
    assert result.failed == 0
    assert result.recall_at_k == 1.0


def test_render_markdown_report_includes_case_results() -> None:
    retriever = KeywordRetriever(
        [
            Document(
                source="rolling-restart.md",
                title="Rolling Restart",
                content="Restart deployment pods safely.",
            )
        ]
    )
    report = evaluate_retriever_detailed(
        retriever,
        [
            EvaluationCase(
                query="rolling restart",
                expected_sources=("rolling-restart.md",),
            )
        ],
        limit=1,
    )

    markdown = render_markdown_report(report, limit=1)

    assert "# KubePilot Retrieval Evaluation" in markdown
    assert "Recall@1: 1.000" in markdown
    assert "rolling-restart.md" in markdown
    assert "| rolling restart |" in markdown
