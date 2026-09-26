"""Final check on the files as installed in the user's folders."""

import sys
from pathlib import Path

import fitz
import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ASEK_DIR = Path(r"D:\研究生\资料\论文\2014_Karasek_机器人蜂鸟")
PARK_DIR = Path(r"D:\研究生\资料\论文\2025_Park_Phan_扑翼机器人")
REF = Path(r"D:\研究生\200g参考文献")

CHECK = [
    (
        "Asek 中文修正版(单语)",
        next((ASEK_DIR / "01_原文").glob("*.pdf")),
        ASEK_DIR / "02_译文" / "机器人蜂鸟_悬停扑翼微型飞行器控制机构设计_中文修正版.pdf",
        [89, 147, 178, 179],
    ),
    (
        "Asek 中英左右对照版",
        next((ASEK_DIR / "01_原文").glob("*.pdf")),
        ASEK_DIR / "02_译文" / "机器人蜂鸟_悬停扑翼微型飞行器控制机构设计_中英左右对照版.pdf",
        [89, 147, 178, 179],
    ),
    (
        "Zhu_2026 单语",
        REF / "Zhu_2026_Eng._Res._Express_8_055514.pdf",
        REF / "翻译" / "mono_Zhu_2026_Eng._Res._Express_8_055514.zh-CN.mono.pdf",
        [18, 23],
    ),
    (
        "Zhu_2026 对照",
        REF / "Zhu_2026_Eng._Res._Express_8_055514.pdf",
        REF / "翻译" / "dual_Zhu_2026_Eng._Res._Express_8_055514.zh-CN.dual.pdf",
        [18, 23],
    ),
    (
        "Park/Phan 对照",
        next((PARK_DIR / "01_原文").glob("*.pdf")),
        next((PARK_DIR / "02_译文").glob("*.dual.pdf")),
        [96],
    ),
]


def gray(page, clip=None, zoom=1.0):
    px = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csGRAY, clip=clip)
    return np.frombuffer(px.samples, dtype=np.uint8).reshape(px.height, px.stride)[:, : px.width]


print(f"{'file':<26}{'pages':<8}{'rot pages':<14}{'page':<7}{'src ink':<10}{'out ink':<10}{'mad':<9}verdict")
allok = True
for label, srcp, outp, pages in CHECK:
    s = fitz.open(srcp)
    d = fitz.open(outp)
    is_dual = "对照" in label or "dual" in outp.name
    ok_all = True
    for pno in pages:
        i = pno - 1
        sp = s[i]
        dp = d[i]
        if is_dual:
            half = dp.rect.width / 2
            L = gray(dp, fitz.Rect(0, 0, half, dp.rect.height))
            R = gray(dp, fitz.Rect(half, 0, dp.rect.width, dp.rect.height))
            src_ink = 1 - (gray(sp) > 250).mean()
            ink = min(1 - (L > 250).mean(), 1 - (R > 250).mean())
            md = float(np.abs(gray(sp, zoom=1.0).astype(np.int16) - L.astype(np.int16)).mean()) if L.shape == gray(sp).shape else None
        else:
            m = gray(d[i])
            src_ink = 1 - (gray(sp) > 250).mean()
            ink = 1 - (m > 250).mean()
            g = gray(sp)
            md = float(np.abs(g.astype(np.int16) - m.astype(np.int16)).mean()) if g.shape == m.shape else None
        good = ink > src_ink * 0.5
        ok_all = ok_all and good
        print(
            f"{label:<26}{d.page_count:<8}{str([p for p in pages]):<14}{pno:<7}"
            f"{src_ink:<10.4f}{ink:<10.4f}{(md if md is not None else -1):<9.3f}"
            f"{'ok' if good else 'LOST CONTENT'}"
        )
    allok = allok and ok_all
    s.close()
    d.close()

print()
print("ALL OK" if allok else "PROBLEMS REMAIN")
