"""Markdown document loader."""

from pathlib import Path

from rag.models import Document


def load_markdown_documents(directory: Path) -> list[Document]:
    """Load markdown files from a directory in stable filename order."""

    documents: list[Document] = []

    for path in sorted(directory.glob("*.md")):
        content = path.read_text(encoding="utf-8").strip()
        title = _extract_title(content) or path.stem.replace("-", " ").title()
        documents.append(
            Document(
                source=str(path),
                title=title,
                content=content,
                metadata={"filename": path.name},
            ),
        )

    return documents


def _extract_title(content: str) -> str | None:
    for line in content.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return None
