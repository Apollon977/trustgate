# trustgate

**See everything a repository will run before you open, install or build it.**

You clone a repo, open it in your editor, start your AI coding agent and run `npm install`.
Each of those steps can run code that came with the repo: a VS Code task set to run on
folder open, a Claude Code `SessionStart` hook, a `postinstall` script, a dev container
`initializeCommand` that runs on your host, a `.pth` file that Python runs at start-up.

In 2026 self-spreading npm worms began writing exactly these files into the repositories
they infected. The Keyv-linked worm of August 2026 left `.claude/settings.json` and
`.vscode/tasks.json` hooks that start the payload as soon as the project is opened, so the
infection outlives a clean `npm install`. These files have valid syntax and look like
routine configuration, which makes them easy to miss in review.

trustgate finds every one of those auto-run entry points, tells you what each one will run
and when, and fails CI when something new shows up.

- **Zero dependencies.** Python 3.9+ standard library only. Nothing to trust but this code.
- **Offline.** Reads files and nothing else: no network, no execution, no telemetry.
- **Built for review and CI.** Text, JSON and SARIF output, GitHub Action, pre-commit hook.

```text
$ trustgate scan .
trustgate 0.1.0  /src/demo  (4 auto-run files)

HIGH     TG200 agent-hook  .claude/settings.json:3
         SessionStart hook runs: node .claude/setup.js
         fix: Review the command. Only keep hooks you added yourself.

HIGH     TG202 agent-auto-approve  .claude/settings.json:7
         enableAllProjectMcpServers auto-approves every server in .mcp.json.
         fix: Remove the setting from the project; grant broad permissions only in your own user config.

HIGH     TG500 devcontainer-host-command  .devcontainer/devcontainer.json:1
         initializeCommand runs on your host before the container exists: ./prep.sh
         fix: Review the command; it has full access to your machine.

HIGH     TG100 vscode-folder-open-task  .vscode/tasks.json:5
         Task 'init' runs automatically when the folder is opened: node .vscode/init.js
         fix: Delete the task or remove runOptions.runOn unless you wrote it yourself.

MEDIUM   TG300 npm-lifecycle-script  package.json:1
         'postinstall' script runs on install: node scripts/fetch.js
         fix: Install with --ignore-scripts and review the script before running it.

Summary: 4 high, 1 medium
```

## Install

```sh
pipx install git+https://github.com/kirtanbhatt10/trustgate
# or run from a checkout with no install at all:
git clone https://github.com/kirtanbhatt10/trustgate && python -m trustgate scan /path/to/repo
```

## Usage

```sh
trustgate scan                       # scan the current directory
trustgate scan ~/src/some-repo       # scan a fresh clone *before* opening it
trustgate scan . --deps              # also look inside node_modules
trustgate scan --home                # audit your own editor / agent / npm config
trustgate scan . -f sarif -o trustgate.sarif
trustgate scan . -f json --min-severity medium
trustgate rules                      # list every rule
```

| Option | Default | Meaning |
|--------|---------|---------|
| `-f, --format` | `text` | `text`, `json` or `sarif` |
| `-o, --output` | stdout | write the report to a file |
| `--fail-on LEVEL` | `high` | exit 1 if any finding is at or above `LEVEL` |
| `--min-severity LEVEL` | `info` | hide findings below `LEVEL` |
| `--ignore RULE` | | skip a rule id (repeatable) |
| `--deps` | off | descend into `node_modules` |
| `--home` | off | scan user-level config in your home directory instead of a repo |
| `--no-color` | | plain output (also respects `NO_COLOR`) |

Exit codes: `0` nothing at or above `--fail-on`, `1` findings, `2` usage error.

### A safer clone habit

```sh
git clone https://github.com/someone/project && trustgate scan project && code project
```

Only open the folder (and only grant VS Code *Workspace Trust*) once you have read what
trustgate reported.

### After a suspected compromise

`trustgate scan --home` checks the user-level files a worm would use to survive a repo
cleanup: `~/.claude/settings.json`, `~/.claude.json`, `~/.cursor/hooks.json`,
`~/.gemini/settings.json`, `~/.npmrc` and VS Code user `settings.json` / `tasks.json` on
Linux, macOS and Windows. Anything listed there runs for *every* project you open.

## What it checks

| Area | Files | What is flagged |
|------|-------|-----------------|
| VS Code | `.vscode/tasks.json`, `.vscode/settings.json`, `*.code-workspace` | tasks with `runOn: folderOpen`; settings pointing at executables inside the repo; `terminal.integrated.env.*` setting `NODE_OPTIONS`, `LD_PRELOAD`, `BASH_ENV` and similar; `task.allowAutomaticTasks` |
| AI agents | `.claude/settings*.json`, `.mcp.json`, `.cursor/hooks.json`, `.cursor/mcp.json`, `.gemini/settings.json` | every hook command (unprompted events like `SessionStart` rated high); `statusLine` and `apiKeyHelper`-style commands; loader env vars; `enableAllProjectMcpServers`, `bypassPermissions`, `Bash(*)`; locally launched MCP servers |
| npm | `package.json`, `binding.gyp`, `.npmrc` | install-time lifecycle scripts; gyp `<!( )` command expansions and implicit `node-gyp rebuild`; `script-shell` / `node-options`; committed auth tokens; non-default registries |
| Python | `*.pth`, `sitecustomize.py`, `usercustomize.py`, `setup.py` | `.pth` import lines; start-up hooks; `setup.py` process, eval or network calls and overridden install commands (parsed with `ast`, never executed) |
| Dev Containers | `.devcontainer/**/devcontainer.json`, `.devcontainer.json` | `initializeCommand` (runs on the host) and in-container lifecycle commands |
| Git hooks & shell | `.husky/*`, `lefthook.yml`, `.pre-commit-config.yaml`, `.envrc` | hook scripts, local pre-commit entries, direnv files |
| GitHub Actions | `.github/workflows/*.yml` | `toJSON(secrets)` dumps; issue / PR / comment / discussion text interpolated into `run:` |
| Everything above | | invisible Unicode: tag characters (decoded for you), bidi controls, zero-width characters |

Full rule list with severities: [docs/rules.md](docs/rules.md).

trustgate reports *where* code will run and *what* is configured to run. It does not try
to decide whether a script is malicious; a reviewer makes that call with the evidence in
front of them. Expect findings in healthy projects too (a `prepare: husky` script is
normal). The value is that nothing runs without you knowing.

## CI

### GitHub Action

```yaml
name: trustgate
on: [pull_request]
permissions:
  contents: read
  security-events: write
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          persist-credentials: false
      - uses: kirtanbhatt10/trustgate@main
        with:
          fail-on: high
      - uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: trustgate.sarif
```

A pull request that adds a folder-open task, an agent hook or an install script now fails
the check and shows up in code scanning with the file and line.

### pre-commit

```yaml
repos:
  - repo: https://github.com/kirtanbhatt10/trustgate
    rev: main
    hooks:
      - id: trustgate
```

## Design notes

- **No repository-controlled config.** trustgate never reads an ignore file from the
  repo it scans; otherwise the attacker's commit could switch the scanner off. Use
  `--ignore` in your CI workflow instead.
- **Never executes anything.** JSON and JSONC are parsed by a small built-in reader,
  `setup.py` by Python's `ast`, YAML by line matching. Symlinks are not followed.
- **Bounded.** Files over 2 MB and binary files are skipped; `.git`, virtualenvs and
  `node_modules` are skipped unless you pass `--deps`.
- **Stable fingerprints.** SARIF results carry `partialFingerprints` so code scanning can
  track a finding across commits.

## Related tools

trustgate covers one question: *what runs automatically?* For neighbouring problems:

- [mcp-warden](https://github.com/kirtanbhatt10/mcp-warden): deep audit of MCP server configs
- [runnerguard](https://github.com/kirtanbhatt10/runnerguard): full GitHub Actions workflow linting
- [promptshield](https://github.com/kirtanbhatt10/promptshield): runtime prompt-injection guardrails for LLM apps

## Contributing

Bug reports, false positives and new auto-run locations are welcome. See
[CONTRIBUTING.md](CONTRIBUTING.md). Security issues: [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) © 2026 Kirtan Bhatt
