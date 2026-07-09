from pathlib import Path

from rag.indexing import (
    build_runbook_index,
    create_persisted_vector_retriever,
    read_runbook_index,
    write_native_faiss_index,
    write_runbook_index,
)


def test_build_write_and_read_runbook_index(tmp_path: Path) -> None:
    runbooks_dir = tmp_path / "runbooks"
    runbooks_dir.mkdir()
    (runbooks_dir / "rollout.md").write_text(
        "# Deployment rollout failures\n\nCheck image pull errors and pod events.",
        encoding="utf-8",
    )
    output_path = tmp_path / "index" / "runbooks.json"

    index = build_runbook_index(runbooks_dir=runbooks_dir)
    write_runbook_index(index, output_path)
    reloaded = read_runbook_index(output_path)

    assert output_path.exists()
    assert reloaded.version == index.version
    assert reloaded.documents[0].title == "Deployment rollout failures"
    assert reloaded.vectors


def test_persisted_vector_retriever_searches_index(tmp_path: Path) -> None:
    runbooks_dir = tmp_path / "runbooks"
    runbooks_dir.mkdir()
    (runbooks_dir / "restart.md").write_text(
        "# Pod restarts\n\nUse previous logs to inspect CrashLoopBackOff.",
        encoding="utf-8",
    )
    output_path = tmp_path / "runbooks.json"
    write_runbook_index(build_runbook_index(runbooks_dir=runbooks_dir), output_path)

    retriever = create_persisted_vector_retriever(output_path)

    matches = retriever.search("previous logs crashloop")

    assert matches
    assert matches[0].document.title == "Pod restarts"


def test_native_faiss_index_writer_reports_whether_sidecar_was_written(tmp_path: Path) -> None:
    index = build_runbook_index(runbooks_dir=_runbooks_dir(tmp_path))
    output_path = tmp_path / "runbooks.faiss"

    written = write_native_faiss_index(index, output_path)

    assert written is output_path.exists()


def _runbooks_dir(tmp_path: Path) -> Path:
    runbooks_dir = tmp_path / "runbooks"
    runbooks_dir.mkdir()
    (runbooks_dir / "rollout.md").write_text(
        "# Deployment rollout failures\n\nCheck image pull errors and pod events.",
        encoding="utf-8",
    )
    return runbooks_dir
