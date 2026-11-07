"""GitHub Actions: two high-signal patterns seen in repository-hijacking campaigns.

For complete workflow linting (pinning, permissions, pwn requests) use a
dedicated workflow linter; trustgate only flags the patterns below.
"""

from __future__ import annotations

import re

from . import Context

SECRETS_DUMP = re.compile(r"toJSON\(\s*secrets\s*\)", re.I)
UNTRUSTED = re.compile(
    r"\$\{\{\s*github\.(event\.(issue\.(title|body)|pull_request\.(title|body|head\.ref|head\.label)"
    r"|comment\.body|review\.body|review_comment\.body|discussion\.(title|body)|head_commit\.(message|author\.name)"
    r"|pages\.[^}]*\.page_name|commits\.[^}]*\.message)|head_ref)\s*\}\}")
RUN_KEY = re.compile(r"^(\s*)(?:-\s+)?run:\s*(.*)$")


def check(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: len(p.parts) >= 3 and p.parts[-3:-1] == (".github", "workflows")
                            and p.suffix in (".yml", ".yaml")):
        text = ctx.text(rel)
        if text is None:
            continue
        run_indent = None
        for lineno, line in enumerate(text.splitlines(), 1):
            if SECRETS_DUMP.search(line):
                ctx.add("TG700", rel, "Workflow serialises every secret with toJSON(secrets).",
                        line=lineno, evidence=line.strip())
            m = RUN_KEY.match(line)
            if m:
                run_indent = len(m.group(1))
                in_run = True
            elif run_indent is not None and line.strip():
                in_run = (len(line) - len(line.lstrip())) > run_indent
                if not in_run:
                    run_indent = None
            else:
                in_run = run_indent is not None
            if in_run:
                hit = UNTRUSTED.search(line)
                if hit:
                    ctx.add("TG701", rel, f"Shell step interpolates attacker-controlled {hit.group(0)}.",
                            line=lineno, evidence=line.strip())
