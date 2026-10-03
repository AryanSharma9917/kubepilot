import subprocess
from pathlib import Path


def test_helm_profiles_render_cleanly() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["bash", "scripts/helm-profile-smoke.sh"],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
