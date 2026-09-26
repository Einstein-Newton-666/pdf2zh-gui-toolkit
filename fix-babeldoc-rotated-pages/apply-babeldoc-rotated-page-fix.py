#!/usr/bin/env python
"""Re-apply the "rotated page content shifted by one page width" fix to BabelDOC.

Why this exists
---------------
BabelDOC rotates the page CropBox into the page's display frame for pages with
/Rotate 90 or /Rotate 270.  That rotation must swap width and height while
keeping the origin in place, but the shipped code also moved the origin:

    # babeldoc/format/pdf/new_parser/prepared_page.py  (active parser in 0.6.2)
    if page.rotate in (90, 270):
        return float(y0), float(x1), float(y1), float(x0)      # <-- origin swapped

    # babeldoc/format/pdf/pdfinterp.py  (legacy parser, same bug)
    if page.rotate == 90 or page.rotate == 270:
        (x0, y0, x1, y1) = (y0, x1, y1, x0)                    # <-- origin swapped

For an A4 landscape page (portrait MediaBox 595.276 x 841.89 plus /Rotate 90)
the result is y0 == 595.276.  The backend then wraps every emitted element of
that page in

    1 0 0 1 -x0 -y0 cm   ->   1 0 0 1 0 -595.276 cm

which shifts the whole page content by exactly one page width.  The content
ends up outside the page box and the PDF viewer clips it, so wide landscape
tables come out cut in half / incomplete.

Run with the Python that has babeldoc installed (the project venv):

    .venv\\Scripts\\python.exe fix-babeldoc-rotated-pages\\apply-babeldoc-rotated-page-fix.py

Idempotent: running it twice is safe.  Re-run it after reinstalling/upgrading
babeldoc, because site-packages edits do not survive that.
"""

from __future__ import annotations

import sys
from pathlib import Path

# --- babeldoc/format/pdf/new_parser/prepared_page.py -------------------------

OLD_NEW_PARSER = """    if page.rotate in (90, 270):
        return float(y0), float(x1), float(y1), float(x0)
"""

NEW_NEW_PARSER = """    if page.rotate in (90, 270):
        # Rotate the crop box into the page's display frame: width and height
        # swap, the origin stays put.
        # The previous code was
        #     return float(y0), float(x1), float(y1), float(x0)
        # which moved the origin to (y0, x1).  On a landscape page (portrait
        # MediaBox + /Rotate 90) that gives y0 == page width (e.g. 595.276),
        # and both wrap_page_base_operation() and
        # PDFCreater.update_page_content_stream() then wrap every emitted
        # element of that page in "1 0 0 1 -x0 -y0 cm" == "1 0 0 1 0 -595.276
        # cm".  That shifts the whole page content by one page width, pushing
        # it outside the page box where the viewer clips it -- which is what
        # made wide landscape tables come out cut in half in the mono PDF.
        return (
            float(x0),
            float(y0),
            float(x0) + (float(y1) - float(y0)),
            float(y0) + (float(x1) - float(x0)),
        )
"""

MARKER_NEW_PARSER = "float(x0) + (float(y1) - float(y0))"

# --- babeldoc/format/pdf/pdfinterp.py (legacy parser) ------------------------

OLD_LEGACY = """        if page.rotate == 90 or page.rotate == 270:
            (x0, y0, x1, y1) = (y0, x1, y1, x0)
"""

NEW_LEGACY = """        if page.rotate == 90 or page.rotate == 270:
            # Rotate the crop box into the page's display frame: the width and
            # the height swap, but the origin must stay where it is.
            # The previous code was
            #     (x0, y0, x1, y1) = (y0, x1, y1, x0)
            # which moved the origin to (y0, x1).  For a landscape page
            # (A4 portrait MediaBox + /Rotate 90) that yields
            #     y == page width   (e.g. 595.276)
            # and the backend then wraps *every* re-emitted element of that
            # page in "1 0 0 1 -x -y cm" == "1 0 0 1 0 -595.276 cm", i.e. it
            # shifts the whole page content by one page width.  The shifted
            # content falls outside the page box and is clipped by the viewer,
            # which is what made wide landscape tables come out cut in half in
            # the monolingual (mono) PDF.
            x1, y1 = x0 + (y1 - y0), y0 + (x1 - x0)
"""

MARKER_LEGACY = "x1, y1 = x0 + (y1 - y0), y0 + (x1 - x0)"


def patch(path: Path, old: str, new: str, marker: str) -> str:
    if not path.exists():
        return f"SKIP  {path.name}: file not found"
    text = path.read_text(encoding="utf-8")
    if marker in text:
        return f"OK    {path.name}: already patched"
    if old not in text:
        return f"FAIL  {path.name}: expected code not found (babeldoc changed upstream?)"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return f"PATCH {path.name}: fixed"


def main() -> int:
    try:
        import babeldoc
    except ImportError:
        print("ERROR: babeldoc is not importable with this interpreter.")
        print("       Use the project venv, e.g. .venv\\Scripts\\python.exe")
        return 2

    root = Path(babeldoc.__file__).parent
    print(f"babeldoc root: {root}")
    results = [
        patch(
            root / "format" / "pdf" / "new_parser" / "prepared_page.py",
            OLD_NEW_PARSER,
            NEW_NEW_PARSER,
            MARKER_NEW_PARSER,
        ),
        patch(
            root / "format" / "pdf" / "pdfinterp.py",
            OLD_LEGACY,
            NEW_LEGACY,
            MARKER_LEGACY,
        ),
    ]
    for line in results:
        print(" ", line)
    failed = [r for r in results if r.startswith("FAIL")]
    print()
    if failed:
        print("Finished with failures - the patch was NOT fully applied.")
        return 1
    print("Done - rotated (/Rotate 90|270) pages will no longer be shifted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
