"""npm / Node.js: install-time lifecycle scripts, node-gyp and .npmrc."""

from __future__ import annotations

import re

from ..models import Severity
from . import Context

# Scripts npm runs on a plain `npm install` in the project (or of the package).
INSTALL_SCRIPTS = {
    "preinstall": Severity.MEDIUM,
    "install": Severity.MEDIUM,
    "postinstall": Severity.MEDIUM,
    "prepublish": Severity.LOW,
    "preprepare": Severity.LOW,
    "prepare": Severity.LOW,
    "postprepare": Severity.LOW,
}

GYP_EXPANSION = re.compile(r"<!@?\(")
NPMRC_KEY = re.compile(r"^\s*([^=#;\s][^=]*?)\s*=\s*(.*?)\s*$")
DEFAULT_REGISTRY = re.compile(r"^https://registry\.(npmjs\.org|yarnpkg\.com)/?$")


def _package_json(ctx: Context, rel: str) -> None:
    data = ctx.json(rel)
    if not isinstance(data, dict):
        return
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return
    for name, sev in INSTALL_SCRIPTS.items():
        cmd = scripts.get(name)
        if isinstance(cmd, str) and cmd.strip():
            ctx.add("TG300", rel, f"'{name}' script runs on install: {cmd}",
                    needle=f'"{name}"', evidence=cmd, severity=sev)


def _binding_gyp(ctx: Context, rel: str) -> None:
    text = ctx.text(rel)
    if text is None:
        return
    for lineno, line in enumerate(text.splitlines(), 1):
        if GYP_EXPANSION.search(line):
            ctx.add("TG301", rel, f"gyp command expansion runs a shell command during the build: {line.strip()}",
                    line=lineno, evidence=line.strip())
    parent = rel.rsplit("/", 1)[0] + "/package.json" if "/" in rel else "package.json"
    pkg = ctx.json(parent) if parent in ctx.files else None
    scripts = pkg.get("scripts") if isinstance(pkg, dict) else None
    if not (isinstance(scripts, dict) and (scripts.get("install") or scripts.get("preinstall"))):
        ctx.add("TG301", rel, "binding.gyp makes npm run 'node-gyp rebuild' automatically on install.",
                severity=Severity.LOW, line=1)


def _npmrc(ctx: Context, rel: str) -> None:
    text = ctx.text(rel)
    if text is None:
        return
    for lineno, line in enumerate(text.splitlines(), 1):
        m = NPMRC_KEY.match(line)
        if not m:
            continue
        key, value = m.group(1).strip(), m.group(2)
        lower = key.lower()
        if lower in ("script-shell", "node-options", "onload-script", "init-module"):
            ctx.add("TG302", rel, f"{key} changes what npm executes: {value}", line=lineno, evidence=line.strip())
        elif lower.endswith("_authtoken") or lower.endswith("_password") or lower.endswith("_auth"):
            if value and not value.startswith("${"):
                ctx.add("TG302", rel, f"{key} contains a literal credential committed to the repository.",
                        line=lineno, severity=Severity.HIGH, evidence=key)
        elif (lower == "registry" or lower.endswith(":registry")) and value and not DEFAULT_REGISTRY.match(value):
            ctx.add("TG302", rel, f"{key} sends package downloads to {value}", line=lineno,
                    severity=Severity.LOW, evidence=value)


def check(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: p.name == "package.json"):
        _package_json(ctx, rel)
    for rel in ctx.matching(lambda p: p.name == "binding.gyp"):
        _binding_gyp(ctx, rel)
    for rel in ctx.matching(lambda p: p.name == ".npmrc"):
        _npmrc(ctx, rel)
