# CLAUDE.md — Project context for Claude Code

## What this project is
EPAM Quality Architect assessment: agent-assisted test generation and automation for the
**InvenTree Parts module**. Full brief in `agents/system-instructions.md` — read it first;
it defines the domain rules, quality bar, and output conventions for everything you generate.

## Application under test
- InvenTree (Python/Django + DRF), running locally via Docker:
  `git clone https://github.com/inventree/InvenTree && cd InvenTree && docker compose up -d`
- Web UI: http://localhost (platform UI at `/web`) — confirm port from compose output.
- API root: `${INVENTREE_URL}/api/` — token auth via `GET /api/user/token/` (basic auth).

## Environment variables (never hard-code)
| Var | Meaning | Default |
|---|---|---|
| `INVENTREE_URL` | Base URL of the running instance | `http://localhost:8000` |
| `INVENTREE_USER` | Admin username | `admin` |
| `INVENTREE_PASSWORD` | Admin password | `inventree` |

## Repo layout (fixed — do not restructure)
```
agents/           prompts.md, system-instructions.md, this file
test-cases/       ui-manual-tests.md, api-manual-tests.md
automation/api/   pytest + requests project (requirements.txt, conftest.py, tests/, utils/)
automation/ui/    Playwright Python project (requirements.txt, conftest.py, pages/, tests/)
video/            recording guide + final recording
```

## Commands
```bash
# API suite
cd automation/api && pip install -r requirements.txt && pytest -v

# UI suite
cd automation/ui && pip install -r requirements.txt && playwright install chromium && pytest -v

# Single test
pytest tests/test_part_crud.py::test_create_part_minimal -v
```

## Working rules for this repo
- Tests must be independent, re-runnable, and clean up what they create.
- Unique test data: suffix names with a short uuid/timestamp.
- Assertions: status code + schema + business rule (API); user-visible outcome (UI).
- Anything you cannot verify without the live instance → mark `# VERIFY-LIVE:` and move on.
- After any correction from the operator, append one line to README.md → "Agent corrections log".
- Do not touch files outside this submission tree.
