# Contributing to ODF

Thanks for helping! This page is for developers; see the [README](README.md) for what ODF does.

## Setup

Requires **Python 3.11 or 3.12** (the pinned numpy 1.26 has no wheels for 3.13+).

```bash
git clone https://github.com/7pk5/ODF.git
cd ODF
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt -e .
```

## Everyday commands

| Task | Command |
|---|---|
| Run the app | `python -m odf` (or `odf`) |
| Run tests | `python -m pytest` |
| Lint | `ruff check .` (auto-fix: `ruff check --fix .`) |
| Format | `ruff format .` |
| Build the Windows EXE | `python build_exe.py` → `dist/ODF/ODF.exe` |

CI runs lint, format check and tests on **Windows and Linux** for every push and pull request.

## Where things live

| Folder | Responsibility |
|---|---|
| `src/odf/extract/` | File → clean text, one module per format |
| `src/odf/index/` | Scanning, fingerprinting, chunking, `VectorStore`, `IndexService` |
| `src/odf/search/` | `SearchService`: retrieval + ranking |
| `src/odf/engine.py` | Wires model, index and services together |
| `src/odf/ui/` | CustomTkinter window — UI only, calls the services |
| `src/odf/desktop/` | OS integration (opening files; later hotkey/tray) |
| `tests/` | One test file per module; offline, uses a fake embedder |

Adding a file format: add `src/odf/extract/<format>.py` with `extract(path) -> str`, then register it in `src/odf/extract/__init__.py`.

## Rules of thumb

- **Tests first** for bug fixes: write a test that fails, then fix. Known open bugs are marked
  `@pytest.mark.xfail(strict=True, reason="B<n>: ...")` — when you fix one, remove its marker.
- **No UI logic in services, no service logic in the UI.**
- **Log, don't print**: `log = logging.getLogger(__name__)`. Use `log.exception(...)` for real failures.
- **Dependencies are pinned** in `requirements*.txt` (direct deps) and fully locked, with hashes,
  in `requirements-windows.lock` / `requirements-linux.lock` (everything CI and release builds
  install). After changing a `requirements*.txt`, regenerate both locks with the command at the
  top of each lock file. Bump deliberately — chromadb upgrades can change the on-disk index
  format and break existing users.
- Keep pull requests focused, and add a line to `CHANGELOG.md` under *Unreleased*.
