"""Markdown chunking utilities."""

from collections.abc import Iterable

from rag.models import Document


def chunk_markdown(documents: Iterable[Document], *, max_chars: int = 1200) -> list[Document]:
    """Split markdown documents into small heading-aware chunks."""

    chunks: list[Document] = []

    for document in documents:
        sections = _split_sections(document.content)
        for index, section in enumerate(sections, start=1):
            for part_index, content in enumerate(_split_large_section(section, max_chars), start=1):
                chunks.append(
                    Document(
                        source=document.source,
                        title=document.title,
                        content=content,
                        metadata={
                            **document.metadata,
                            "chunk": str(index),
                            "part": str(part_index),
                        },
                    ),
                )

    return chunks


def _split_sections(content: str) -> list[str]:
    sections: list[str] = []
    current: list[str] = []

    for line in content.splitlines():
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)

    if current:
        sections.append("\n".join(current).strip())

    return [section for section in sections if section]


def _split_large_section(section: str, max_chars: int) -> list[str]:
    if len(section) <= max_chars:
        return [section]

    parts: list[str] = []
    current: list[str] = []
    current_length = 0

    for paragraph in section.split("\n\n"):
        paragraph_length = len(paragraph)
        if current and current_length + paragraph_length > max_chars:
            parts.append("\n\n".join(current).strip())
            current = [paragraph]
            current_length = paragraph_length
        else:
            current.append(paragraph)
            current_length += paragraph_length

    if current:
        parts.append("\n\n".join(current).strip())

    return parts
