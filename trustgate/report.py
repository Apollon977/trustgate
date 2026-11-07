"""Output formats: human-readable text, JSON and SARIF 2.1.0."""

from __future__ import annotations

import json
from collections import Counter

from . import __version__
from .models import RULES, Severity
from .scanner import ScanResult

COLORS = {
    Severity.CRITICAL: "\033[1;35m", Severity.HIGH: "\033[1;31m", Severity.MEDIUM: "\033[33m",
    Severity.LOW: "\033[36m", Severity.INFO: "\033[37m",
}
RESET, DIM, BOLD = "\033[0m", "\033[2m", "\033[1m"

SARIF_LEVEL = {Severity.CRITICAL: "error", Severity.HIGH: "error", Severity.MEDIUM: "warning",
               Severity.LOW: "note", Severity.INFO: "note"}
SECURITY_SEVERITY = {Severity.CRITICAL: "9.5", Severity.HIGH: "8.0", Severity.MEDIUM: "5.5",
                     Severity.LOW: "3.0", Severity.INFO: "1.0"}


def to_text(result: ScanResult, color: bool = False) -> str:
    def paint(code: str, s: str) -> str:
        return f"{code}{s}{RESET}" if color else s

    lines = [paint(BOLD, f"trustgate {__version__}") + f"  {result.root}  ({result.files_scanned} auto-run files)", ""]
    if not result.findings:
        lines.append("No auto-run entry points found.")
    for f in result.findings:
        tag = paint(COLORS[f.severity], f"{f.severity.label.upper():8}")
        lines.append(f"{tag} {f.rule_id} {f.rule.name}  {f.path}:{f.line}")
        lines.append(f"         {f.message}")
        lines.append(paint(DIM, f"         fix: {f.rule.remediation}"))
        lines.append("")
    for err in result.errors:
        lines.append(paint(DIM, f"warning: {err}"))
    counts = Counter(f.severity for f in result.findings)
    summary = ", ".join(f"{counts[s]} {s.label}" for s in sorted(counts, reverse=True)) or "0 findings"
    lines.append(f"Summary: {summary}")
    return "\n".join(lines) + "\n"


def to_json(result: ScanResult) -> str:
    counts = Counter(f.severity.label for f in result.findings)
    doc = {
        "tool": "trustgate",
        "version": __version__,
        "root": result.root,
        "files_scanned": result.files_scanned,
        "summary": {s.label: counts.get(s.label, 0) for s in sorted(Severity, reverse=True)},
        "findings": [f.to_dict() for f in result.findings],
        "errors": result.errors,
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def to_sarif(result: ScanResult) -> str:
    rule_ids = sorted({f.rule_id for f in result.findings})
    rules = [{
        "id": rid,
        "name": RULES[rid].name,
        "shortDescription": {"text": RULES[rid].summary},
        "help": {"text": RULES[rid].remediation},
        "defaultConfiguration": {"level": SARIF_LEVEL[RULES[rid].severity]},
        "properties": {"security-severity": SECURITY_SEVERITY[RULES[rid].severity],
                       "tags": ["security", "supply-chain"]},
    } for rid in rule_ids]
    results = [{
        "ruleId": f.rule_id,
        "ruleIndex": rule_ids.index(f.rule_id),
        "level": SARIF_LEVEL[f.severity],
        "message": {"text": f.message},
        "locations": [{"physicalLocation": {
            "artifactLocation": {"uri": f.path, "uriBaseId": "%SRCROOT%"},
            "region": {"startLine": f.line},
        }}],
        "partialFingerprints": {"trustgate/v1": f.fingerprint},
        "properties": {"severity": f.severity.label, "security-severity": SECURITY_SEVERITY[f.severity]},
    } for f in result.findings]
    doc = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {"name": "trustgate", "version": __version__,
                                "informationUri": "https://github.com/kirtanbhatt10/trustgate",
                                "rules": rules}},
            "results": results,
        }],
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
