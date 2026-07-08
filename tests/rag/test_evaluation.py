from pathlib import Path

from rag.evaluation import EvaluationCase, evaluate_retriever, load_evaluation_cases
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
