from pathlib import Path

from rag.loaders import load_markdown_documents


def test_load_markdown_documents_extracts_titles(tmp_path: Path) -> None:
    runbook = tmp_path / "rolling-restart.md"
    runbook.write_text("# Rolling restart\n\nRestart safely.", encoding="utf-8")

    documents = load_markdown_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0].title == "Rolling restart"
    assert documents[0].metadata["filename"] == "rolling-restart.md"
