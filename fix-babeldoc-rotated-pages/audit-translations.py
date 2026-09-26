"""Audit every translated PDF under D:\\研究生 for layout defects.

Checks per document
-------------------
1. source page-rotation inventory (/Rotate 90|270 are the at-risk pages)
2. on those rotated pages, in the MONO output:
     - the spurious "1 0 0 1 0 -<page width> cm" wrapper (whole page shifted
       by one page width -> viewer clips it)
     - text-line count vs the source page
     - rendered pixel difference vs the source page
3. global mono checks: page count, pages that lost all their text,
   text blocks falling outside the page box
4. dual: are both halves of every rotated page non-empty?
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REF = Path(r"D:\研究生\200g参考文献")
TRANS = REF / "翻译"
ASEK_DIR = Path(r"D:\研究生\资料\论文\2014_Karasek_机器人蜂鸟")
PARK = Path(r"D:\研究生\资料\论文\2025_Park_Phan_扑翼机器人")

CM_RE = re.compile(
    r"(-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) cm"
)

DOCS = [
    {
        "label": "54814_BionicOpter",
        "src": REF / "54814_Broschuere_BionicOpter_en_130502_lo_L.pdf",
        "mono": TRANS / "mono_54814_Broschuere_BionicOpter_en_130502_lo_L.zh-CN.mono.pdf",
        "dual": TRANS / "dual_54814_Broschuere_BionicOpter_en_130502_lo_L.zh-CN.dual.pdf",
    },
    {
        "label": "aerospace2020235",
        "src": REF / "aerospace2020235.pdf",
        "mono": TRANS / "mono_aerospace2020235.zh-CN.mono.pdf",
        "dual": TRANS / "dual_aerospace2020235.zh-CN.dual.pdf",
    },
    {
        "label": "science.aeb6744_sm",
        "src": REF / "science.aeb6744_sm.pdf",
        "mono": TRANS / "mono_science.aeb6744_sm.zh-CN.mono.pdf",
        "dual": TRANS / "dual_science.aeb6744_sm.zh-CN.dual.pdf",
    },
    {
        "label": "science.aeb6744",
        "src": REF / "science.aeb6744.pdf",
        "mono": TRANS / "mono_science.aeb6744.zh-CN.mono.pdf",
        "dual": TRANS / "dual_science.aeb6744.zh-CN.dual.pdf",
    },
    {
        "label": "yang-et-al-2017-dove",
        "src": REF / "yang-et-al-2017-dove-a-biomimetic-flapping-wing-micro-air-vehicle.pdf",
        "mono": TRANS / "mono_yang-et-al-2017-dove-a-biomimetic-flapping-wing-micro-air-vehicle.zh-CN.mono.pdf",
        "dual": TRANS / "dual_yang-et-al-2017-dove-a-biomimetic-flapping-wing-micro-air-vehicle.zh-CN.dual.pdf",
    },
    {
        "label": "Zhu_2024_035541",
        "src": REF / "Zhu_2024_Eng._Res._Express_6_035541.pdf",
        "mono": TRANS / "mono_Zhu_2024_Eng._Res._Express_6_035541.zh-CN.mono.pdf",
        "dual": TRANS / "dual_Zhu_2024_Eng._Res._Express_6_035541.zh-CN.dual.pdf",
    },
    {
        "label": "Zhu_2026_055514",
        "src": REF / "Zhu_2026_Eng._Res._Express_8_055514.pdf",
        "mono": TRANS / "mono_Zhu_2026_Eng._Res._Express_8_055514.zh-CN.mono.pdf",
        "dual": TRANS / "dual_Zhu_2026_Eng._Res._Express_8_055514.zh-CN.dual.pdf",
    },
    {
        "label": "Asek_蜂鸟(209p)",
        "src": next((ASEK_DIR / "01_原文").glob("*.pdf")),
        "mono": TRANS.parent.parent
        / "pdf2zh"
        / "output"
        / "Asek - Robotic hummingbird Design of a control mechanism for a hovering ﬂapping wing micro air vehicle.zh.mono.pdf",
        "dual": None,
    },
    {
        "label": "Park_Phan(旧译文)",
        "src": next((PARK / "01_原文").glob("*.pdf")),
        "mono": None,
        "dual": next((PARK / "02_译文").glob("*.dual.pdf")),
    },
]


def gray(page, zoom=1.0):
    px = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    return np.frombuffer(px.samples, dtype=np.uint8).reshape(px.height, px.stride)[:, : px.width]


def nlines(page):
    try:
        return sum(
            1
            for b in page.get_text("dict")["blocks"]
            if b.get("type") == 0
            for _ in b["lines"]
        )
    except Exception:
        return -1


def shift_count(doc, page, width):
    """How many elements are wrapped in '1 0 0 1 0 -pagewidth cm'."""
    total = 0
    try:
        data = b""
        for x in page.get_contents():
            data += doc.xref_stream(x)
    except Exception:
        return 0
    for a, b, c, d, e, f in CM_RE.findall(data.decode("latin-1")):
        if (
            a == "1" and b == "0" and c == "0" and d == "1"
            and abs(float(e)) < 0.5
            and abs(float(f) + width) < 0.5
        ):
            total += 1
    return total


def text_frame(page):
    """The frame get_text() reports coordinates in.

    On a /Rotate 90|270 page PyMuPDF returns coordinates in the *unrotated*
    MediaBox frame, so comparing them against page.rect would report bogus
    overflow on exactly the pages we care about.
    """
    return page.mediabox if page.rotation in (90, 270) else page.rect


def outside_blocks(page, tol=3.0):
    n = 0
    frame = text_frame(page)
    try:
        for b in page.get_text("blocks"):
            x0, y0, x1, y1 = b[:4]
            if x0 < -tol or y0 < -tol or x1 > frame.width + tol or y1 > frame.height + tol:
                n += 1
    except Exception:
        pass
    return n


def ink_fraction(page, zoom=1.0):
    """Fraction of non-white pixels - used to detect a half that lost content."""
    px = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    a = np.frombuffer(px.samples, dtype=np.uint8)
    return float((a <= 250).mean())


def audit(doc: dict) -> dict:
    res = {
        "label": doc["label"],
        "rotated": [],
        "blank": [],
        "outside": 0,
        "pagecount": "",
        "notes": [],
    }
    src = fitz.open(doc["src"])
    mono = fitz.open(doc["mono"]) if doc.get("mono") and Path(doc["mono"]).exists() else None
    dual = fitz.open(doc["dual"]) if doc.get("dual") and Path(doc["dual"]).exists() else None

    res["src_pages"] = src.page_count
    rotated = [i for i, p in enumerate(src) if p.rotation in (90, 270)]
    res["rotated_src"] = [i + 1 for i in rotated]

    if mono is not None:
        res["mono_pages"] = mono.page_count
        if mono.page_count != src.page_count:
            res["notes"].append(
                f"page count mismatch: src {src.page_count} vs mono {mono.page_count}"
            )
        for i in range(min(src.page_count, mono.page_count)):
            sp, mp = src[i], mono[i]
            if nlines(sp) > 3 and nlines(mp) == 0:
                res["blank"].append(i + 1)
            res["outside"] += outside_blocks(mp)
        for i in rotated:
            if i >= mono.page_count:
                continue
            sp, mp = src[i], mono[i]
            width = sp.mediabox.width
            sc = shift_count(mono, mp, width)
            entry = {
                "page": i + 1,
                "shift": sc,
                "src_lines": nlines(sp),
                "mono_lines": nlines(mp),
            }
            try:
                entry["src_ink"] = round(ink_fraction(sp), 4)
                entry["mono_ink"] = round(ink_fraction(mp), 4)
            except Exception:
                entry["src_ink"] = entry["mono_ink"] = None
            try:
                a, b = gray(sp), gray(mp)
                entry["mad"] = round(float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean()), 3) if a.shape == b.shape else None
            except Exception:
                entry["mad"] = None
            res["rotated"].append(entry)
    if dual is not None:
        res["dual_pages"] = dual.page_count
        bad_halves = []
        for i in rotated:
            if i >= dual.page_count:
                continue
            pg = dual[i]
            half = pg.rect.width / 2
            try:
                src_ink = ink_fraction(src[i])
                L = pg.get_pixmap(
                    matrix=fitz.Matrix(1.0, 1.0), colorspace=fitz.csGRAY,
                    clip=fitz.Rect(0, 0, half, pg.rect.height),
                )
                R = pg.get_pixmap(
                    matrix=fitz.Matrix(1.0, 1.0), colorspace=fitz.csGRAY,
                    clip=fitz.Rect(half, 0, pg.rect.width, pg.rect.height),
                )
                # A broken half loses most of its ink compared with the source
                # page; a merely sparse page keeps a similar amount.
                L_ink = 1 - float((np.frombuffer(L.samples, dtype=np.uint8) > 250).mean())
                R_ink = 1 - float((np.frombuffer(R.samples, dtype=np.uint8) > 250).mean())
                if src_ink > 0.005 and (L_ink < src_ink * 0.4 or R_ink < src_ink * 0.4):
                    bad_halves.append(
                        (i + 1, round(src_ink, 4), round(L_ink, 4), round(R_ink, 4))
                    )
            except Exception:
                pass
        res["dual_bad_halves"] = bad_halves

    src.close()
    if mono:
        mono.close()
    if dual:
        dual.close()
    return res


def main() -> int:
    print("=" * 100)
    print("译文布局体检")
    print("=" * 100)
    broken = []
    for doc in DOCS:
        r = audit(doc)
        rot = r["rotated_src"]
        print()
        print(f"### {r['label']}")
        print(
            f"    原文 {r['src_pages']} 页"
            + (f"，单语 {r.get('mono_pages')} 页" if r.get("mono_pages") else "")
            + (f"，对照 {r.get('dual_pages')} 页" if r.get("dual_pages") else "")
            + f"；/Rotate 90|270 页面: {rot if rot else '无'}"
        )
        for e in r["rotated"]:
            if e["shift"] > 0:
                flag = "BROKEN (shifted off page)"
            elif (
                e.get("src_ink") and e.get("mono_ink")
                and e["mono_ink"] < e["src_ink"] * 0.5
            ):
                flag = "SUSPECT (lost content)"
            else:
                flag = "ok"
            print(
                f"      p{e['page']:<5} shift={e['shift']:<5} lines {e['src_lines']}->{e['mono_lines']:<5} "
                f"ink {e.get('src_ink')}->{e.get('mono_ink')} mad={e.get('mad')}  {flag}"
            )
            if flag != "ok":
                broken.append((r["label"], e["page"], flag, e["shift"]))
        if r.get("dual_bad_halves"):
            print(f"      dual 半页丢失内容 (page, src_ink, L_ink, R_ink): {r['dual_bad_halves']}")
            for entry in r["dual_bad_halves"]:
                broken.append((r["label"], entry[0], "DUAL-HALF-LOST", 0))
        if r["blank"]:
            print(f"      单语空白页（原文有字）: {r['blank'][:20]}")
        if r["outside"]:
            print(f"      超出页面边界的文本块: {r['outside']}")
        if r["notes"]:
            for n in r["notes"]:
                print(f"      注意: {n}")

    print()
    print("=" * 100)
    if broken:
        print(f"发现问题的页面 {len(broken)} 处：")
        for b in broken:
            print("   ", b)
    else:
        print("未发现旋转页错位/空白问题")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
