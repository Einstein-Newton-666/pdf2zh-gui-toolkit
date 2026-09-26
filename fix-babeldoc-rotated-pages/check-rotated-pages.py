#!/usr/bin/env python
"""Detect the BabelDOC "rotated page shifted by one page width" defect.

For every page whose landscape orientation comes from /Rotate 90 or /Rotate 270,
scan the content stream for the tell-tale wrapper

    1 0 0 1 <e> <f> cm     with  e == 0  and  f == -page_width

which means the translator shifted the entire page content by one page width.
Visually that makes wide landscape tables come out cut in half.

Usage:
    python check-rotated-pages.py <translated.pdf> [more.pdf ...]
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import fitz

CM_RE = re.compile(
    r"(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) cm"
)


def check(path: Path) -> int:
    doc = fitz.open(path)
    problems = 0
    print(f"== {path.name}  pages={doc.page_count}")
    rotated = [i for i, p in enumerate(doc) if p.rotation in (90, 270)]
    if not rotated:
        print("   no /Rotate 90|270 pages - this defect cannot apply")
    for i in rotated:
        page = doc[i]
        width = page.mediabox.width
        data = b""
        for x in page.get_contents():
            data += doc.xref_stream(x)
        cms = Counter(CM_RE.findall(data.decode("latin-1")))
        bad = sum(
            n
            for (a, b, c, d, e, f), n in cms.items()
            if a == "1" and b == "0" and c == "0" and d == "1"
            and abs(float(e)) < 0.5
            and abs(float(f) + width) < 0.5
        )
        if bad:
            problems += 1
            print(
                f"   p{i + 1:<5} /Rotate {page.rotation}  BROKEN: {bad} elements wrapped in "
                f"'1 0 0 1 0 -{width:.3f} cm' (shifted off page)"
            )
        else:
            print(f"   p{i + 1:<5} /Rotate {page.rotation}  ok")
    doc.close()
    return problems


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    total = 0
    for arg in sys.argv[1:]:
        total += check(Path(arg))
    print()
    print("RESULT:", "no shifted rotated pages found" if total == 0 else f"{total} broken page(s)")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main())
