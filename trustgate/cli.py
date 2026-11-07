"""Command-line interface."""

from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

from . import __version__
from .models import RULES, Severity
from .report import to_json, to_sarif, to_text
from .scanner import scan, scan_home

EXIT_OK, EXIT_FINDINGS, EXIT_USAGE = 0, 1, 2


def _severity(value: str) -> Severity:
    try:
        return Severity.parse(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="trustgate",
        description="Find everything a repository will execute when you open, install or build it.",
    )
    parser.add_argument("--version", action="version", version=f"trustgate {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="command")

    s = sub.add_parser("scan", help="scan a directory (default: current directory)")
    s.add_argument("path", nargs="?", default=".", help="directory to scan")
    s.add_argument("--home", action="store_true",
                   help="scan your user-level editor, agent and npm config instead of a repository")
    s.add_argument("--deps", action="store_true", help="also descend into node_modules")
    s.add_argument("-f", "--format", choices=("text", "json", "sarif"), default="text")
    s.add_argument("-o", "--output", help="write the report to a file instead of stdout")
    s.add_argument("--min-severity", type=_severity, default=Severity.INFO, metavar="LEVEL",
                   help="hide findings below LEVEL (default: info)")
    s.add_argument("--fail-on", type=_severity, default=Severity.HIGH, metavar="LEVEL",
                   help="exit 1 if any finding is at or above LEVEL (default: high)")
    s.add_argument("--ignore", action="append", default=[], metavar="RULE",
                   help="skip a rule id, e.g. --ignore TG600 (repeatable)")
    s.add_argument("--no-color", action="store_true", help="disable ANSI colours")

    sub.add_parser("rules", help="list every rule")
    return parser


def _rules() -> str:
    out = []
    for rule in RULES.values():
        out.append(f"{rule.id}  {rule.severity.label:8}  {rule.name}\n      {rule.summary}")
    return "\n".join(out) + "\n"


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "rules":
        sys.stdout.write(_rules())
        return EXIT_OK
    if args.command != "scan":
        parser.print_help()
        return EXIT_USAGE

    unknown = [r for r in args.ignore if r.upper() not in RULES]
    if unknown:
        parser.error(f"unknown rule id(s): {', '.join(unknown)}")
    try:
        if args.home:
            result = scan_home(ignore=args.ignore)
        else:
            result = scan(args.path, include_deps=args.deps, ignore=args.ignore)
    except NotADirectoryError as exc:
        print(f"trustgate: {exc}", file=sys.stderr)
        return EXIT_USAGE

    result.findings = result.at_least(args.min_severity)
    if args.format == "json":
        report = to_json(result)
    elif args.format == "sarif":
        report = to_sarif(result)
    else:
        color = (not args.no_color and not args.output and sys.stdout.isatty()
                 and "NO_COLOR" not in os.environ)
        report = to_text(result, color=color)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(report)
    else:
        sys.stdout.write(report)
    return EXIT_FINDINGS if result.at_least(args.fail_on) else EXIT_OK
