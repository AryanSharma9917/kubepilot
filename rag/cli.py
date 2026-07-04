"""Command-line utilities for KubePilot retrieval indexes."""

import argparse
from pathlib import Path

from rag.indexing import build_runbook_index, write_runbook_index


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
    args = parser.parse_args()

    index = build_runbook_index(runbooks_dir=args.runbooks_dir)
    write_runbook_index(index, args.output)
    print(f"Indexed {len(index.documents)} chunks into {args.output}")


if __name__ == "__main__":
    main()
