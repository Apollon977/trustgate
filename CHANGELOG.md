# Changelog

All notable changes are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-08

### Added

- `trustgate scan` for repositories and `trustgate scan --home` for user-level config.
- VS Code: folder-open tasks, repository-controlled executables, loader environment
  variables in terminal settings, `task.allowAutomaticTasks`.
- AI agents (Claude Code, Cursor, Gemini CLI): hooks, command settings, environment
  injection, auto-approval settings and local MCP servers.
- npm: install lifecycle scripts, `binding.gyp` command expansions, risky `.npmrc` keys.
- Python: `.pth` import lines, `sitecustomize.py` / `usercustomize.py`, `setup.py`
  side effects via `ast`.
- Dev Containers: `initializeCommand` on the host and in-container lifecycle commands.
- husky, lefthook, local pre-commit hooks and direnv `.envrc`.
- GitHub Actions: `toJSON(secrets)` and untrusted event text in `run:` steps.
- Hidden Unicode detection with decoding of tag-character text.
- Text, JSON and SARIF 2.1.0 output; GitHub Action; pre-commit hook.
