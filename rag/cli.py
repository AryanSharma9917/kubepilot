"""Command-line utilities for KubePilot retrieval indexes."""

import argparse
from pathlib import Path

from rag.evaluation import evaluate_retriever, load_evaluation_cases
from rag.indexing import build_runbook_index, write_native_faiss_index, write_runbook_index
from rag.retrieval.keyword import create_default_retriever


def main() -> None:
    """Run the KubePilot indexing command."""

    parser = argparse.ArgumentParser(description="Build KubePilot runbook indexes.")
    parser.add_argument(
        "--runbooks-dir",
        type=Path,
        default=Path("docs/runbooks"),
        help="Directory containing markdown runbooks.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".kubepilot/index/runbooks.json"),
        help="Path for the persisted index JSON.",
    )
    parser.add_argument(
        "--faiss-output",
        type=Path,
        default=None,
        help="Optional path for a native FAISS sidecar index.",
    )
    args = parser.parse_args()

    index = build_runbook_index(runbooks_dir=args.runbooks_dir)
    write_runbook_index(index, args.output)
    print(f"Indexed {len(index.documents)} chunks into {args.output}")
    if args.faiss_output is not None:
        if write_native_faiss_index(index, args.faiss_output):
            print(f"Wrote FAISS sidecar index to {args.faiss_output}")
        else:
            print("Skipped FAISS sidecar index because faiss/numpy are not installed")


def evaluate() -> None:
    """Run retrieval evaluation from JSONL cases."""

    parser = argparse.ArgumentParser(description="Evaluate KubePilot runbook retrieval.")
    parser.add_argument(
        "--cases",
        type=Path,
        default=Path("tests/fixtures/retrieval-evaluation.jsonl"),
        help="JSONL file with query and expected_sources fields.",
    )
    parser.add_argument(
        "--runbooks-dir",
        type=Path,
        default=Path("docs/runbooks"),
        help="Directory containing markdown runbooks.",
    )
    parser.add_argument("--limit", type=int, default=3, help="Top-k retrieval limit.")
    args = parser.parse_args()

    cases = load_evaluation_cases(args.cases)
    result = evaluate_retriever(
        create_default_retriever(args.runbooks_dir),
        cases,
        limit=args.limit,
    )
    print(
        f"retrieval_recall_at_{args.limit}={result.recall_at_k:.3f} "
        f"passed={result.passed} failed={result.failed} total={result.total}"
    )


if __name__ == "__main__":
    main()
