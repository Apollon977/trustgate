"""PHP / Composer: event scripts that run automatically on install, update, or dump-autoload."""

from __future__ import annotations

from . import Context, command_text

COMPOSER_EVENTS = (
    "pre-install-cmd",
    "post-install-cmd",
    "pre-update-cmd",
    "post-update-cmd",
    "pre-autoload-dump",
    "post-autoload-dump",
    "post-root-package-install",
    "post-create-project-cmd",
)


def _composer_json(ctx: Context, rel: str) -> None:
    data = ctx.json(rel)
    if not isinstance(data, dict):
        return
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return
    for name in COMPOSER_EVENTS:
        val = scripts.get(name)
        if val is None:
            continue
        cmd = command_text(val).strip()
        if cmd:
            ctx.add("TG304", rel, f"'{name}' script runs automatically: {cmd}",
                    needle=f'"{name}"', evidence=cmd)


def check(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: p.name == "composer.json"):
        _composer_json(ctx, rel)
