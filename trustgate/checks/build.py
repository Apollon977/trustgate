"""JVM and Rust build tools: Gradle wrapper and Cargo build scripts."""

from __future__ import annotations

import re

from ..models import Severity
from . import Context

DISTRIBUTION_URL = re.compile(r"^\s*distributionUrl\s*[=:]\s*(.+?)\s*$")
OFFICIAL = re.compile(r"^https\\?://services\.gradle\.org/distributions(?:-snapshots)?/")


def _wrapper(ctx: Context, rel: str) -> None:
    text = ctx.text(rel)
    if text is None:
        return
    has_checksum = "distributionSha256Sum" in text
    for lineno, line in enumerate(text.splitlines(), 1):
        m = DISTRIBUTION_URL.match(line)
        if not m:
            continue
        raw = m.group(1)
        if OFFICIAL.match(raw):
            continue
        url = raw.replace("\\:", ":")
        plain_http = url.lower().startswith("http:")
        sev = Severity.HIGH if plain_http and not has_checksum else None
        note = "" if has_checksum else " with no distributionSha256Sum"
        ctx.add("TG800", rel, f"Gradle wrapper downloads Gradle from {url}{note}.", line=lineno,
                severity=sev, evidence=url)


CARGO_BUILD = re.compile(r'^\s*build\s*=\s*["\'](.+?)["\']\s*$')


def _rust(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: p.name == "build.rs"):
        ctx.add("TG801", rel, "Cargo and rust-analyzer run build.rs when the project is built or opened.",
                line=1)

    for rel in ctx.matching(lambda p: p.name == "Cargo.toml"):
        text = ctx.text(rel)
        if not text:
            continue
        in_package = False
        for lineno, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("["):
                in_package = stripped == "[package]"
                continue
            if in_package:
                m = CARGO_BUILD.match(line)
                if m:
                    script = m.group(1)
                    if script != "build.rs":
                        ctx.add("TG801", rel,
                                f"Cargo.toml specifies a custom build script '{script}' that runs on build or open.",
                                line=lineno, evidence=script)


def check(ctx: Context) -> None:
    for rel in ctx.matching(lambda p: p.name == "gradle-wrapper.properties"):
        _wrapper(ctx, rel)
    _rust(ctx)
