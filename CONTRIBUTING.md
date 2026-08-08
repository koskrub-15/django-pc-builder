# Contributing

Thanks for taking a look! This is an open pet project — issues and pull requests are welcome.

## Development setup

```bash
uv sync
uv run pre-commit install
uv run python manage.py test apps --settings=core.test_settings
```

The test settings need no configuration. To run the real stack you also need
`.env` and `compose.override.yaml` — `just d-up` creates both from the committed
examples. See the [README](README.md) for the full run instructions.

## Workflow

- Direct commits to `main` are blocked. Work in a branch and open a pull request.

  ```bash
  git checkout -b feature/my-change
  git commit                 # pre-commit runs automatically
  git push origin feature/my-change
  ```

- Every push and PR runs CI: tests (Python 3.13 / 3.14) with a 90% coverage
  floor, lint & type-check (ruff, mypy, djlint, prettier), a dependency audit,
  and a Docker stack smoke test. All checks must pass.
- Keep pull requests focused and small where possible.

## Code style

- Formatting and linting are enforced by pre-commit (`ruff`, `ruff-format`,
  `djlint`, `prettier`). Run `just pre-commit-i-run-i-all` before pushing.
- Type hints are required on function signatures — `mypy` runs in CI.
- Comments explain non-obvious constraints only, not what the code already says.
- Add or update tests for any behaviour change. Tests live in
  `apps/<app>/tests/` and use Django's `TestCase`.

## Reporting bugs

Open an issue with steps to reproduce, the expected result, and what actually
happened. Include the output of `just d-compose-inspect` if it is a setup problem.
