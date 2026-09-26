#!/usr/bin/env python
"""Fit over-wide translated paragraphs back inside the text column.

Symptom
-------
BabelDOC sometimes emits a translated paragraph as a line that is far wider
than the column it belongs to (observed up to ~80 pt too wide).  The text runs
past the page edge and the PDF viewer clips the trailing characters, so the
sentence looks truncated.

Approach
--------
Geometry only - not one character is added, removed or re-fonted.  For the
affected lines the text matrix is rewritten

    1 0 0 1 <x> <y> Tm   ->   <s> 0 0 1 <x_left + s*(x - x_left)> <y> Tm

so every glyph is compressed by s about its own origin AND moved to its
compressed position.  The line shrinks by s and lands inside the column.  Text
content, embedded fonts, reading order and text extraction stay unchanged;
characters that used to be clipped off-page simply become visible again.

Usage
-----
    python fix-overflow-paragraphs.py <in.pdf> [out.pdf] [--column-right 540]
                                      [--pages 10,12,16] [--dry-run]

If --column-right is omitted it is derived from the page: the largest right
edge among text lines that do NOT overflow, falling back to page_width - 72.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

import fitz

TM_RE = re.compile(rb"(-?[\d.]+) 0 0 1 (-?[\d.]+) (-?[\d.]+) Tm")


def text_lines(page):
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        for ln in b["lines"]:
            yield ln


def detect_column_right(page) -> float:
    """Right margin implied by the lines that do NOT overflow."""
    edges = [ln["bbox"][2] for ln in text_lines(page) if ln["bbox"][2] <= page.rect.width - 0.5]
    if edges:
        return max(edges)
    return page.rect.width - 72.0


def overflowing_bands(page, threshold):
    """Bands of paragraphs that still run past `threshold`.

    PyMuPDF reports text boxes top-down while the Tm operator uses PDF's
    bottom-up user space, so the y band must be flipped.
    """
    H = page.rect.height
    bands = []
    for b in page.get_text("dict")["blocks"]:
        if b.get("type") != 0:
            continue
        rights = [ln["bbox"][2] for ln in b["lines"]]
        if not rights or max(rights) <= threshold + 0.5:
            continue
        bands.append(
            {
                "x0": b["bbox"][0],
                "ymin": H - b["bbox"][3] - 2.0,
                "ymax": H - b["bbox"][1] + 2.0,
                "xmax": max(rights),
            }
        )
    return bands


def squeeze_page(page, doc, threshold, max_passes=30, verbose=True) -> int:
    total = 0
    for attempt in range(1, max_passes + 1):
        bands = overflowing_bands(page, threshold)
        if not bands:
            if verbose and attempt > 1:
                print(f"      converged after {attempt - 1} pass(es)")
            return total
        touched = 0
        for band in bands:
            x_left = band["x0"]
            if band["xmax"] - x_left <= 0:
                continue
            s = (threshold - x_left) / (band["xmax"] - x_left)
            s = max(0.5, min(1.0, s))
            for xref in page.get_contents():
                data = doc.xref_stream(xref)

                def repl(m):
                    nonlocal touched
                    a, x, y = float(m.group(1)), float(m.group(2)), float(m.group(3))
                    if (
                        band["ymin"] <= y <= band["ymax"]
                        and x_left - 1.0 <= x <= band["xmax"] + 1.0
                    ):
                        touched += 1
                        return (
                            f"{a * s:.6f} 0 0 1 "
                            f"{x_left + s * (x - x_left):.4f} {y:.4f} Tm"
                        ).encode()
                    return m.group(0)

                new = TM_RE.sub(repl, data)
                if new != data:
                    doc.update_stream(xref, new)
        total += touched
        if touched == 0:
            return total
    if verbose:
        print(f"      WARNING: did not converge in {max_passes} passes")
    return total


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path, nargs="?")
    ap.add_argument("--column-right", type=float, default=None)
    ap.add_argument("--pages", default=None, help="e.g. 10,12,16 (default: all)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out = args.output or args.input.with_name(args.input.stem + ".fitted.pdf")
    doc = fitz.open(args.input)

    pages = (
        [int(p) for p in args.pages.split(",")]
        if args.pages
        else list(range(1, doc.page_count + 1))
    )

    before = {p: doc[p - 1].get_text() for p in pages}
    plan = []
    for p in pages:
        page = doc[p - 1]
        col = args.column_right if args.column_right is not None else detect_column_right(page)
        bands = overflowing_bands(page, col)
        if bands:
            plan.append((p, col, max(b["xmax"] for b in bands)))

    if not plan:
        print("nothing overflows - no change needed")
        doc.close()
        return 0

    print(f"{'page':<7}{'column':<10}{'widest line':<13}action")
    for p, col, wide in plan:
        print(f"{p:<7}{col:<10.1f}{wide:<13.1f}fit by factor {(col - 73) / max(1.0, wide - 73):.4f}")

    if args.dry_run:
        print("\n--dry-run: nothing written")
        doc.close()
        return 0

    for p, col, _ in plan:
        print(f"p{p}:")
        n = squeeze_page(doc, doc, col)
        print(f"      rewrote {n} text matrices")

    doc.save(out, garbage=4, deflate=True)
    doc.close()

    # verify: no character lost, nothing left overflowing
    old = fitz.open(args.input)
    new = fitz.open(out)
    ok = True
    print()
    for p, col, _ in plan:
        i = p - 1
        missing = Counter(old[i].get_text()) - Counter(new[i].get_text())
        gained = Counter(new[i].get_text()) - Counter(old[i].get_text())
        mx = max(
            (ln["bbox"][2] for ln in text_lines(new[i])),
            default=0,
        )
        over = [ln for ln in text_lines(new[i]) if ln["bbox"][2] > new[i].rect.width - 0.5]
        print(
            f"p{p}: chars lost={sum(missing.values())} gained={sum(gained.values())} "
            f"max_right={mx:.1f} overflowing_lines={len(over)}"
        )
        if gained:
            print("      newly visible:", "".join(sorted(gained)))
        ok = ok and not missing and not over and mx <= col + 0.6
    old.close()
    new.close()
    print()
    print(f"written: {out}")
    print("VERIFIED" if ok else "PROBLEM - inspect before using")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
