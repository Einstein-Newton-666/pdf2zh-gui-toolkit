"""Verify the 4 landscape pages of the re-translated Asek thesis."""

import sys
from pathlib import Path

import fitz
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ASEK_DIR = Path(r"D:\研究生\资料\论文\2014_Karasek_机器人蜂鸟\01_原文")
SRC = next(ASEK_DIR.glob("*.pdf"))
OUTDIR = Path(r"D:\研究生\pdf2zh\tmp\dbg\asek_landscape")

MONO = next(OUTDIR.glob("*.mono.pdf"), None)
DUAL = next(OUTDIR.glob("*.dual.pdf"), None)
LAND = [89, 147, 178, 179]


def g(page, zoom=1.0):
    px = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY)
    return np.frombuffer(px.samples, dtype=np.uint8).reshape(px.height, px.stride)[:, : px.width]


def nl(page):
    return sum(
        1
        for b in page.get_text("dict")["blocks"]
        if b.get("type") == 0
        for _ in b["lines"]
    )


def cn(page):
    t = page.get_text()
    return sum(1 for c in t if "\u4e00" <= c <= "\u9fff")


print("source :", SRC.name)
print("mono   :", MONO.name if MONO else "MISSING")
print("dual   :", DUAL.name if DUAL else "MISSING")
print()

s = fitz.open(SRC)
m = fitz.open(MONO) if MONO else None
d = fitz.open(DUAL) if DUAL else None

print(f"{'page':<7}{'rot':<6}{'src lines':<11}{'mono lines':<12}{'mad':<10}{'cn chars':<10}verdict")
for p in LAND:
    i = p - 1
    a = s[i]
    row = [f"{p:<7}", f"{a.rotation:<6}", f"{nl(a):<11}"]
    if m is None:
        row.append("n/a")
        print("".join(row))
        continue
    b = m[i]
    md = float(np.abs(g(a).astype(np.int16) - g(b).astype(np.int16)).mean())
    ok = "OK" if md < 3.0 and nl(b) >= nl(a) * 0.9 else "SUSPECT"
    print(
        f"{p:<7}{a.rotation:<6}{nl(a):<11}{nl(b):<12}{md:<10.3f}{cn(b):<10}{ok}"
    )

if d is not None:
    print()
    for p in LAND:
        pg = d[p - 1]
        print(f"dual p{p}: rect={pg.rect.width:.1f}x{pg.rect.height:.1f} rot={pg.rotation}")

s.close()
if m:
    m.close()
if d:
    d.close()
