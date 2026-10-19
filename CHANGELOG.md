# Changelog

All notable changes to ODF. Format based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Fixed
- Re-indexing an edited file no longer leaves its old text in search results; existing
  indexes are repaired automatically on the next indexing run.
- Indexing errors now show an error dialog instead of failing silently.
- Linux builds store data in `~/.local/share/ODF` instead of a relative folder.
- Unreadable or empty files are now recorded in `odf.log` with the reason.

### Changed
- ChromaDB telemetry is explicitly disabled (it already sent nothing in the shipped version).
- Code moved into an installable `src/odf` package; run from source with `pip install -e .` then `python -m odf`.
- Dependencies pinned to exact versions; minimum Python is now 3.11.
- `odf.log` uses named loggers and no longer fills with HTTP request lines on first launch.

### Added
- Automated test suite and CI on Windows and Linux; release builds are smoke-tested before publishing.
- `ruff` linting and formatting, `CONTRIBUTING.md`, this changelog.

## [1.2] - 2026-05-20

Last release before this changelog was started.
