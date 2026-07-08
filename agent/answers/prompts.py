"""Prompt construction for grounded runbook answers."""

from agent.state.chat import Citation
from rag import RetrievedDocument


def build_grounded_answer_prompt(
    *,
    message: str,
    matches: list[RetrievedDocument],
) -> str:
    """Build a grounded RAG prompt from retrieved runbook chunks."""

    context = "\n".join(
        f"[{index}] {match.document.title}: {_snippet(match.document.content)}"
        for index, match in enumerate(matches, start=1)
    )
    return (
        "You are KubePilot, a Kubernetes operations assistant.\n"
        "Answer only from the supplied runbook context. "
        "If context is missing, say no matching runbook was found.\n\n"
        f"QUESTION:\n{message}\n\n"
        f"CONTEXT:\n{context}\n\n"
        "RESPONSE REQUIREMENTS:\n"
        "- Be concise.\n"
        "- Cite source numbers when making runbook-backed claims.\n"
        "- Prefer concrete operational next steps."
    )


def citations_from_matches(matches: list[RetrievedDocument]) -> tuple[Citation, ...]:
    """Create citations from retrieved documents."""

    citations: list[Citation] = []
    seen: set[tuple[str, str]] = set()
    for match in matches:
        key = (match.document.title, match.document.source)
        if key in seen:
            continue
        seen.add(key)
        citations.append(
            Citation(
                title=match.document.title,
                source=match.document.source,
                snippet=_snippet(match.document.content),
            )
        )
    return tuple(citations)


def _snippet(content: str, *, max_length: int = 220) -> str:
    compact = " ".join(content.split())
    if len(compact) <= max_length:
        return compact
    return f"{compact[: max_length - 3].rstrip()}..."
