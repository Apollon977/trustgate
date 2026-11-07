"""Detection of invisible and direction-changing Unicode characters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

ZERO_WIDTH = {
    0x200B: "ZERO WIDTH SPACE",
    0x200C: "ZERO WIDTH NON-JOINER",
    0x200D: "ZERO WIDTH JOINER",
    0x2060: "WORD JOINER",
    0x2061: "FUNCTION APPLICATION",
    0x2062: "INVISIBLE TIMES",
    0x2063: "INVISIBLE SEPARATOR",
    0x2064: "INVISIBLE PLUS",
    0x180E: "MONGOLIAN VOWEL SEPARATOR",
    0xFEFF: "ZERO WIDTH NO-BREAK SPACE",
}

BIDI = {
    0x200E: "LEFT-TO-RIGHT MARK",
    0x200F: "RIGHT-TO-LEFT MARK",
    0x202A: "LEFT-TO-RIGHT EMBEDDING",
    0x202B: "RIGHT-TO-LEFT EMBEDDING",
    0x202C: "POP DIRECTIONAL FORMATTING",
    0x202D: "LEFT-TO-RIGHT OVERRIDE",
    0x202E: "RIGHT-TO-LEFT OVERRIDE",
    0x2066: "LEFT-TO-RIGHT ISOLATE",
    0x2067: "RIGHT-TO-LEFT ISOLATE",
    0x2068: "FIRST STRONG ISOLATE",
    0x2069: "POP DIRECTIONAL ISOLATE",
}

TAG_START, TAG_END = 0xE0000, 0xE007F


@dataclass
class HiddenRun:
    line: int
    column: int
    kind: str  # "tags", "zero-width" or "bidi"
    count: int
    detail: str


def _classify(cp: int) -> str:
    if TAG_START <= cp <= TAG_END:
        return "tags"
    if cp in BIDI:
        return "bidi"
    if cp in ZERO_WIDTH:
        return "zero-width"
    return ""


def find_hidden(text: str) -> List[HiddenRun]:
    """Group consecutive hidden characters into runs and describe each run.

    Unicode tag characters (U+E0000-U+E007F) mirror ASCII and are rendered as
    nothing by editors and diff views, but language models read them. Runs of
    tag characters are decoded so the reviewer can see the smuggled text.
    A single byte-order mark at the very start of the file is ignored.
    """
    runs: List[HiddenRun] = []
    line, col = 1, 0
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "\n":
            line, col = line + 1, 0
            i += 1
            continue
        col += 1
        cp = ord(ch)
        kind = _classify(cp)
        if not kind or (i == 0 and cp == 0xFEFF):
            i += 1
            continue
        start_line, start_col = line, col
        j = i
        chars = []
        while j < n and _classify(ord(text[j])) == kind:
            chars.append(ord(text[j]))
            j += 1
        col += len(chars) - 1
        if kind == "tags":
            decoded = "".join(chr(c - TAG_START) for c in chars if 0x20 <= c - TAG_START < 0x7F)
            detail = f"decodes to: {decoded!r}" if decoded else "tag characters"
        else:
            table = BIDI if kind == "bidi" else ZERO_WIDTH
            names = sorted({table[c] for c in chars})
            detail = ", ".join(f"U+{c:04X}" for c in sorted(set(chars))) + " (" + "; ".join(names) + ")"
        runs.append(HiddenRun(start_line, start_col, kind, len(chars), detail))
        i = j
    return runs
