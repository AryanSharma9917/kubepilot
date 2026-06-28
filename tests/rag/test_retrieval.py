from rag.models import Document
from rag.retrieval import KeywordRetriever


def test_keyword_retriever_returns_relevant_document() -> None:
    retriever = KeywordRetriever(
        [
            Document(
                source="deployment.md",
                title="Deployment rollout failures",
                content="Pods are in ImagePullBackOff after a rollout.",
            ),
            Document(
                source="restart.md",
                title="Pod restarts",
                content="Check previous logs for CrashLoopBackOff.",
            ),
        ],
    )

    matches = retriever.search("deployment image pull failing")

    assert matches
    assert matches[0].document.title == "Deployment rollout failures"


def test_keyword_retriever_returns_empty_list_for_blank_query() -> None:
    retriever = KeywordRetriever(
        [Document(source="restart.md", title="Pod restarts", content="Check previous logs.")]
    )

    assert retriever.search("   ") == []
