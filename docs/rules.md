# Rules

Every finding has a rule id, a default severity and a fix. Some findings are raised or lowered from the default when the context makes them more or less dangerous (noted below).

| ID | Name | Default | What it means | What to do |
|----|------|---------|---------------|------------|
| TG001 | `hidden-unicode` | high | Invisible or bidirectional Unicode characters in a file that tools or agents execute or obey. | Remove the characters. Legitimate config files almost never need them. |
| TG100 | `vscode-folder-open-task` | high | A VS Code task is configured to run automatically when the folder is opened. | Delete the task or remove runOptions.runOn unless you wrote it yourself. |
| TG101 | `vscode-workspace-executable` | medium | A workspace setting points an extension at an executable inside the repository. | Point the setting at a trusted, system-installed binary or remove it from the workspace settings. |
| TG102 | `vscode-terminal-env` | high | Workspace settings inject environment variables that load code into every terminal process. | Remove the variable from terminal.integrated.env.* in the workspace settings. |
| TG103 | `vscode-auto-tasks-setting` | medium | Workspace settings try to allow automatic tasks without asking. | Remove task.allowAutomaticTasks from the workspace settings. |
| TG200 | `agent-hook` | medium | An AI coding agent hook runs a shell command on agent events. | Review the command. Only keep hooks you added yourself. |
| TG201 | `agent-command-setting` | medium | An AI agent setting executes a shell command (status line, API key helper). | Review the command or move the setting to your user-level config. |
| TG202 | `agent-auto-approve` | high | Project settings weaken the agent's approval prompts. | Remove the setting from the project; grant broad permissions only in your own user config. |
| TG203 | `mcp-server-autostart` | low | A project-level MCP server will be launched as a local process by the agent. | Confirm the server package and arguments are expected and pinned. |
| TG204 | `agent-env-injection` | high | Agent settings inject environment variables that load code into child processes. | Remove the variable from the agent's env settings. |
| TG300 | `npm-lifecycle-script` | medium | package.json defines a script that npm runs automatically on install. | Install with --ignore-scripts and review the script before running it. |
| TG301 | `node-gyp-exec` | medium | binding.gyp triggers an implicit install build or runs shell command expansions. | Review every <!( ) expansion; install with --ignore-scripts until reviewed. |
| TG302 | `npmrc-risk` | medium | A project .npmrc changes how npm executes scripts, where it downloads from, or contains a token. | Remove the setting from the committed .npmrc; keep tokens in your user config or CI secrets. |
| TG400 | `python-pth-exec` | high | A .pth file contains import lines, which Python executes at interpreter start-up. | Delete the .pth file or reduce it to plain path entries. |
| TG401 | `setup-py-exec` | medium | setup.py runs commands or fetches code at build/install time. | Build in an isolated environment and review the setup.py code paths. |
| TG402 | `python-startup-hook` | medium | sitecustomize.py or usercustomize.py is shipped and runs whenever it lands on sys.path. | Remove the file unless the project explicitly documents why it needs it. |
| TG500 | `devcontainer-host-command` | high | devcontainer initializeCommand runs on your host machine, outside the container. | Review the command; it has full access to your machine. |
| TG501 | `devcontainer-lifecycle-command` | low | A dev container lifecycle command runs automatically inside the container. | Review the command, especially if secrets or your SSH agent are forwarded. |
| TG600 | `git-hook-script` | low | A git hook manager will run repository scripts on git operations. | Read the hook scripts before running the project's install or setup step. |
| TG601 | `direnv-envrc` | medium | An .envrc file runs shell code when you cd into the directory (once allowed). | Read the file before running 'direnv allow'. |
| TG700 | `workflow-secret-dump` | critical | A GitHub Actions workflow serialises the entire secrets context. | Delete the workflow and rotate every repository and organisation secret. |
| TG701 | `workflow-untrusted-exec` | high | A workflow interpolates attacker-controlled event text directly into a shell step. | Pass the value through an environment variable and never execute it. |

## Severity adjustments

- **TG001**: Unicode tag characters (hidden text) are `critical`, bidirectional controls `high`, zero-width characters `medium`.
- **TG101**: `typescript.tsdk` pointing into `node_modules` is `low`, since it is a common, prompted VS Code setup.
- **TG200**: hooks on events that fire without a prompt from you (`SessionStart`, `SessionEnd`, `Stop`, `Notification`, `PreCompact`, `Setup`) are `high`.
- **TG202**: `permissions.defaultMode: bypassPermissions` is `critical`.
- **TG300**: `preinstall`, `install` and `postinstall` are `medium`; `prepare`-family and `prepublish` scripts are `low`.
- **TG301**: a `binding.gyp` with no command expansions only triggers the implicit `node-gyp rebuild` and is `low`.
- **TG302**: literal auth tokens are `high`; a custom registry is `low`.

## Disabling a rule

```sh
trustgate scan . --ignore TG600 --ignore TG203
```

trustgate deliberately reads no ignore or config file from the scanned repository: a malicious change could otherwise silence the scanner. Put `--ignore` flags in your CI workflow, where the change is reviewed like any other.
