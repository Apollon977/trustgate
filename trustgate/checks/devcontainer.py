"""Dev Containers: lifecycle commands, including initializeCommand which runs on the host."""

from __future__ import annotations

from pathlib import PurePosixPath

from . import Context, command_text

CONTAINER_COMMANDS = ("onCreateCommand", "updateContentCommand", "postCreateCommand",
                      "postStartCommand", "postAttachCommand")


def _is_devcontainer(p: PurePosixPath) -> bool:
    if p.name == ".devcontainer.json":
        return True
    return p.name == "devcontainer.json" and ".devcontainer" in p.parts


def check(ctx: Context) -> None:
    for rel in ctx.matching(_is_devcontainer):
        data = ctx.json(rel)
        if not isinstance(data, dict):
            continue
        cmd = data.get("initializeCommand")
        if cmd:
            text = command_text(cmd)
            ctx.add("TG500", rel, f"initializeCommand runs on your host before the container exists: {text}",
                    needle="initializeCommand", evidence=text)
        for key in CONTAINER_COMMANDS:
            if data.get(key):
                text = command_text(data[key])
                ctx.add("TG501", rel, f"{key} runs automatically: {text}", needle=key, evidence=text)
