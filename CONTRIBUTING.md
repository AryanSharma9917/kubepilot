# Contributing

Thanks for helping improve KubePilot.

## Ways to contribute

- report bugs or confusing behavior
- suggest improvements to the architecture or docs
- improve runbooks and troubleshooting guidance
- add tests for bug fixes and new behavior
- help validate the local demo and production profile

## Local setup

```bash
git clone https://github.com/AryanSharma9917/kubepilot.git
cd kubepilot
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Validation

Before opening a PR, run the relevant checks:

```bash
pytest -q
ruff check .
```

If you are changing deployment behavior, also validate the affected Helm or local
cluster smoke flow.

## Pull request expectations

- keep the change focused and easy to review
- explain the bug, improvement, or missing capability
- include or update tests when behavior changes
- keep the changes aligned with the project roadmap and architecture

## Code of conduct

Please keep discussions respectful, constructive, and focused on improving the
project. Productive feedback is welcome, and hostile or dismissive comments are
not.
