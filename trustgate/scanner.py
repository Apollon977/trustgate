"""Walks a directory, runs every check and returns sorted findings."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterable, List, Optional, Sequence

from .checks import Context, agents, devcontainer, hooks, node, python, vscode, workflows
from .models import Finding, Severity
from .unicode import find_hidden

CHECKS = (vscode, agents, node, python, devcontainer, hooks, workflows)

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", ".venv", "venv", "__pycache__", ".tox", ".nox",
             ".mypy_cache", ".pytest_cache", ".ruff_cache", ".gradle", ".terraform", ".next", ".cache"}

AUTORUN_NAMES = {
    "tasks.json", "settings.json", "settings.local.json", "hooks.json", "mcp.json", ".mcp.json",
    ".claude.json", "package.json", "binding.gyp", ".npmrc", "setup.py", "sitecustomize.py",
    "usercustomize.py", "devcontainer.json", ".devcontainer.json", ".pre-commit-config.yaml",
    ".pre-commit-config.yml", ".envrc", "lefthook.yml", "lefthook.yaml", ".lefthook.yml", ".lefthook.yaml",
}

# User-level files worth checking after a suspected compromise (relative to $HOME).
HOME_FILES = (
    ".claude/settings.json", ".claude/settings.local.json", ".claude.json",
    ".cursor/hooks.json", ".cursor/mcp.json", ".gemini/settings.json", ".npmrc",
    ".config/Code/User/settings.json", ".config/Code/User/tasks.json",
    ".config/Code - Insiders/User/settings.json", ".config/VSCodium/User/settings.json",
    "Library/Application Support/Code/User/settings.json",
    "Library/Application Support/Code/User/tasks.json",
    "AppData/Roaming/Code/User/settings.json", "AppData/Roaming/Code/User/tasks.json",
)


@dataclass
class ScanResult:
    root: str
    findings: List[Finding] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    files_scanned: int = 0

    def at_least(self, severity: Severity) -> List[Finding]:
        return [f for f in self.findings if f.severity >= severity]


# Generic names only count inside the directories whose tools actually load them.
GENERIC_NAMES = {"tasks.json", "settings.json", "settings.local.json", "hooks.json", "mcp.json"}
GENERIC_PARENTS = {".vscode", "User", *agents.AGENT_DIRS}


def _autorun_file(p: PurePosixPath) -> bool:
    if p.name in GENERIC_NAMES:
        return len(p.parts) >= 2 and p.parts[-2] in GENERIC_PARENTS
    if p.name in AUTORUN_NAMES or p.suffix in (".pth", ".code-workspace"):
        return True
    if ".husky" in p.parts or (len(p.parts) >= 3 and p.parts[-3:-1] == (".github", "workflows")):
        return True
    return False


def walk(root: Path, include_deps: bool = False) -> List[str]:
    skip = SKIP_DIRS - ({"node_modules"} if include_deps else set())
    found: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if d not in skip)
        rel_dir = Path(dirpath).relative_to(root)
        for name in sorted(filenames):
            rel = PurePosixPath(*(rel_dir.parts + (name,)))
            if _autorun_file(rel) and not (root / rel_dir / name).is_symlink():
                found.append(str(rel))
    return found


def _unicode(ctx: Context) -> None:
    for rel in ctx.files:
        text = ctx.text(rel)
        if not text:
            continue
        for run in find_hidden(text):
            sev = {"tags": Severity.CRITICAL, "bidi": Severity.HIGH, "zero-width": Severity.MEDIUM}[run.kind]
            ctx.add("TG001", rel, f"{run.count} hidden {run.kind} character(s) at column {run.column}: {run.detail}",
                    line=run.line, severity=sev, evidence=run.detail)


def scan(path: str, *, include_deps: bool = False, files: Optional[Sequence[str]] = None,
         ignore: Iterable[str] = ()) -> ScanResult:
    root = Path(path).resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {path}")
    rels = list(files) if files is not None else walk(root, include_deps)
    ctx = Context(root=root, files=rels)
    for module in CHECKS:
        module.check(ctx)
    _unicode(ctx)
    ignored = {i.upper() for i in ignore}
    findings = [f for f in ctx.findings if f.rule_id not in ignored]
    unique = {}
    for f in findings:
        unique.setdefault((f.rule_id, f.path, f.line, f.message), f)
    ordered = sorted(unique.values(), key=lambda f: (-int(f.severity), f.path, f.line, f.rule_id))
    return ScanResult(root=str(root), findings=ordered, errors=ctx.errors, files_scanned=len(rels))


def scan_home(home: Optional[str] = None, ignore: Iterable[str] = ()) -> ScanResult:
    base = Path(home or Path.home())
    present = [rel for rel in HOME_FILES if (base / rel).is_file()]
    if sys.platform == "win32" and os.environ.get("APPDATA"):
        appdata = Path(os.environ["APPDATA"])
        if appdata.is_relative_to(base):
            for name in ("settings.json", "tasks.json"):
                rel = (appdata.relative_to(base) / "Code" / "User" / name).as_posix()
                if (base / rel).is_file() and rel not in present:
                    present.append(rel)
    return scan(str(base), files=present, ignore=ignore)
