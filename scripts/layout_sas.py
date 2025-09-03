#!/usr/bin/env python3
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional
import unicodedata


@dataclass
class Field:
    name: str
    start: int  # 0-based start index
    width: int
    kind: str  # 'char' or 'num'
    label: Optional[str] = None  # comment text if present
    slug: Optional[str] = None   # normalized label (lowercase, ascii, underscores)


POS_RE = re.compile(r"^@\s*(\d+)")


def _slugify(text: str) -> str:
    # Normalize accents, drop non-alnum, collapse spaces to underscores
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^A-Za-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text.lower()


def _parse_layout_line(line: str) -> Optional[Field]:
    # Remove trailing comments
    label = None
    if "/*" in line:
        before, after = line.split("/*", 1)
        line = before
        if "*/" in after:
            label = after.split("*/", 1)[0].strip()
        else:
            label = after.strip()
    line = line.strip()
    if not line or not line.startswith("@"):
        return None
    # @<pos>
    m = POS_RE.match(line)
    if not m:
        return None
    pos_str = m.group(1)
    rest = line[m.end() :].strip()
    if not rest:
        return None
    parts = rest.split()
    if len(parts) < 2:
        return None
    name = parts[0]
    # The format/informat token may include $, letters and a width like 8. or 10.2 or $CHAR4.
    # Read tokens until we find a dot (.) indicating the end of the informat.
    fmt_tokens: List[str] = []
    i = 1
    while i < len(parts):
        tok = parts[i]
        fmt_tokens.append(tok)
        if "." in tok:
            break
        i += 1
    fmt = "".join(fmt_tokens)
    # Determine width: last integer before dot
    mwidth = re.search(r"(\d+)(?=\.)", fmt)
    if not mwidth:
        return None
    width = int(mwidth.group(1))
    # Char if contains '$' or 'char' in fmt (case-insensitive)
    kind = "char" if ("$" in fmt or "char" in fmt.lower()) else "num"

    start = int(pos_str) - 1
    slug = _slugify(label) if label else None
    return Field(name=name, start=start, width=width, kind=kind, label=label, slug=slug)


def parse_layout(path: Path) -> List[Field]:
    fields: List[Field] = []
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        f = _parse_layout_line(raw)
        if f:
            fields.append(f)
    fields.sort(key=lambda f: f.start)
    return fields


def fields_index(fields: List[Field]) -> dict:
    return {f.name: f for f in fields}


def slice_line(line: str, field: Field) -> str:
    return line[field.start : field.start + field.width]


def extract_line(line: str, selected: List[Field]) -> List[str]:
    out: List[str] = []
    for f in selected:
        val = slice_line(line, f).rstrip("\n\r")
        # normalize spaces
        out.append(val.strip())
    return out
