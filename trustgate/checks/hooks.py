"""Git hook managers (husky, lefthook, pre-commit) and direnv."""

from __future__ import annotations

import re

from . import Context

PRE_COMMIT_ENTRY = re.compile(r"^\s*(?:-\s*)?entry:\s*(.+?)\s*$")
LEFTHOOK_RUN = re.compile(r"^\s*run:\s*(.+?)\s*$")
LEFTHOOK_FILES = {"lefthook.yml", "lefthook.yaml", ".lefthook.yml", ".lefthook.yaml",
                  "lefthook-local.yml", "lefthook-local.yaml"}


def _husky(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: len(p.parts) >= 2 and p.parts[-2] == ".husky"
                            and not p.name.startswith(".")):
        text = ctx.text(rel) or ""
        body = [ln.strip() for ln in text.splitlines()
                if ln.strip() and not ln.lstrip().startswith("#") and "husky.sh" not in ln]
        summary = "; ".join(body)[:200] or "(empty)"
        ctx.add("TG600", rel, f"husky runs this on '{rel.rsplit('/', 1)[-1]}': {summary}", evidence=summary,
                line=1)


def _pre_commit(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: p.name in (".pre-commit-config.yaml", ".pre-commit-config.yml")):
        text = ctx.text(rel) or ""
        if not re.search(r"^\s*-?\s*repo:\s*local\s*$", text, re.M):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            m = PRE_COMMIT_ENTRY.match(line)
            if m:
                ctx.add("TG600", rel, f"pre-commit local hook runs: {m.group(1)}", line=lineno,
                        evidence=m.group(1))


def _lefthook(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: p.name in LEFTHOOK_FILES):
        text = ctx.text(rel) or ""
        for lineno, line in enumerate(text.splitlines(), 1):
            m = LEFTHOOK_RUN.match(line)
            if m:
                ctx.add("TG600", rel, f"lefthook runs: {m.group(1)}", line=lineno, evidence=m.group(1))


def _direnv(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: p.name in (".envrc", ".env.rc")):
        text = ctx.text(rel) or ""
        lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
        ctx.add("TG601", rel, f".envrc contains {len(lines)} line(s) of shell that run on cd after 'direnv allow'.",
                line=1, evidence="; ".join(ln.strip() for ln in lines[:3]))


EXRC_FILES = {".nvim.lua", ".nvimrc", ".exrc", ".vimrc"}


def _exrc(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: len(p.parts) == 1 and p.name in EXRC_FILES):
        text = ctx.text(rel) or ""
        lines = [ln for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith(("#", '"', "--"))]
        evidence = "; ".join(ln.strip() for ln in lines[:3])
        ctx.add("TG602", rel, f"{rel} runs automatically when Neovim or Vim opens this directory with 'exrc' enabled.",
                line=1, evidence=evidence)


def check(ctx: Context) -> None:
    _husky(ctx)
    _pre_commit(ctx)
    _lefthook(ctx)
    _direnv(ctx)
    _exrc(ctx)
