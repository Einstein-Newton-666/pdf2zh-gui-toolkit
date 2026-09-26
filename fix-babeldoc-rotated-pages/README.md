# 横向（/Rotate 90）页面表格被截断 —— 根因与修复

## 一、现象

Karasek 蜂鸟论文（Asek，209 页）里有 4 个**横向页面**：

| 页码 | 说明 |
|---|---|
| 89、147、178、179 | 正文大表格 / 横向插图页 |

- **双语对照版**：表格正常，只有一份完整的（左半页是原文翻页图，完整）。
- **单语版（中文修正版）**：同一张表格被“截半”，只剩一部分，表格不全。

## 二、这 4 页为什么特殊

它们不是“MediaBox 就是横向”的页面，而是 **竖版 MediaBox + `/Rotate 90`**：

```
MediaBox = [0 0 595.276 841.89]   (A4 竖)
/Rotate  = 90                     -> 显示时才是 841.89 x 595.276 横版
```

页内文字在内容流里是**旋转 90° 存的**，靠 `/Rotate 90` 转回水平。

实测该页源文件的文本矩阵：

| 文件 | `Tm` 矩阵统计 |
|---|---|
| 原文 p147 | `(0 1 -1 0)` × 10 —— 全部旋转 90° |
| 单语输出 p147（修复前） | `1 0 0 1 0 -595.276 cm` 出现 **578 次** + `(0 1 -1 0)` |

## 三、根因（已定位到具体代码）

BabelDOC 在解析 `/Rotate 90|270` 页面时，要把 CropBox 旋转到“显示坐标系”：
**宽高互换、原点不动**。但实际代码把原点也换了：

```python
# babeldoc/format/pdf/new_parser/prepared_page.py  (0.6.2 实际走的路径)
def legacy_page_cropbox(page):
    x0, y0, x1, y1 = page.cropbox
    if page.rotate in (90, 270):
        return float(y0), float(x1), float(y1), float(x0)   # ← 原点被改成 (y0, x1)
```

对这张页面，`cropbox = (0, 0, 595.276, 841.89)`，于是返回 `(0, 595.276, 841.89, 0)`
—— **y0 变成了页面宽度 595.276**。

后端随后用这个值给该页**每一个**绘制元素套一层变换：

```python
# babeldoc/format/pdf/document_il/backend/pdf_creater.py
ctm_for_ops = (1, 0, 0, 1, -page_crop_box.x, -page_crop_box.y)
             = (1, 0, 0, 1, 0, -595.276)      # ← 整页内容沿 y 平移一个页宽
```

`babeldoc/format/pdf/new_parser/base_operations.py:wrap_page_base_operation()` 用同样的公式
（旧的 `format/pdf/pdfinterp.py` 里有一份完全相同的错误，只是 0.6.2 默认不再走那条路）。

**结果**：整个页面内容被平移 595.276pt（正好一个页宽），几乎全部跑出页面盒子外，
阅读器按页面裁剪 → 只剩一角 → 表格看起来“被截半 / 不全”。

**为什么双语版看着正常**：`create_side_by_side_dual_pdf()` 会把原文页干净地直接贴到左半页
（`show_pdf_page` + `rotate=-rotate_angle`），左半页不受这个平移影响，所以表格完整；
右半页（译文页）和单语版一样是坏的，用户看到的就是“只有一份好的”。

## 四、证据

最小复现：用本地桩翻译器（`--clitranslator`，不联网）翻译 8 页样本的第 7 页（= 论文 p147）。

| 指标 | 修复前 | 修复后 |
|---|---|---|
| 内容流里的 `1 0 0 1 0 -595.276 cm` | 578 次 | 0 次 |
| 单语页 vs 原文页 像素差 (MAD) | 13.741 | **0.208** |
| 单语页可提取文本行数 | **15** | **91**（原文也是 91） |
| 中文文本 | 8 字（图注） | 8 字（图注） |

修复前后的渲染对比图（`before-*.png` / `after-*.png`）**只保留在本机**，
没有跟进这个公开仓库——它们是论文页面的截图，含 Figure 与表格内容。
本机路径：`D:\研究生\pdf2zh\fix-babeldoc-rotated-pages\`。
上面的表格已经把所有可量化的判据列全，不看图也能独立验证。

## 四之二、真实论文（Asek 209 页）复跑验证

修复后只重跑这 4 个横向页（`-Pages "89,147,178,179"`），输出在
`tmp\dbg\asek_landscape\`：

```
 page   rot   src lines  mono lines  mad       cn chars  verdict
 89     90    192        192         0.347     15        OK
 147    90    91         91          0.200     6         OK
 178    90    73         59          0.291     4         OK(见下)
 179    90    76         64          0.417     14        OK(见下)
```

`check-rotated-pages.py` 对 4 页全部报 ok（不再有 `1 0 0 1 0 -595.276 cm`）。

178/179 的“行数”少一些只是因为页眉被翻成了更短的中文（`7 Control mechanism` → `7 控制机构`），
`mad` 都在 0.3 左右（几乎与原文逐像素一致），渲染检查确认插图、曲线、标注、图注全部完整。

## 五、修复

改两处（同一 bug 的两份拷贝），保留原点、只交换宽高：

```python
# format/pdf/new_parser/prepared_page.py
if page.rotate in (90, 270):
    return (float(x0), float(y0),
            float(x0) + (float(y1) - float(y0)),
            float(y0) + (float(x1) - float(x0)))

# format/pdf/pdfinterp.py  (legacy 路径)
if page.rotate == 90 or page.rotate == 270:
    x1, y1 = x0 + (y1 - y0), y0 + (x1 - x0)
```

`/Rotate 0` 和 `/Rotate 180` 的返回值完全不变，**竖版页面不受影响**（已用单元检查确认）。

已经在 `.venv\Lib\site-packages\babeldoc` 里改好，并留了 `.orig-bak` 备份。

### 重装/升级后需要重新打补丁

```powershell
.\.venv\Scripts\python.exe .\fix-babeldoc-rotated-pages\apply-babeldoc-rotated-page-fix.py
```

脚本幂等，可重复运行。

### 检查任意译文是否还有这个毛病

```powershell
.\.venv\Scripts\python.exe .\fix-babeldoc-rotated-pages\check-rotated-pages.py <译文.pdf>
```

### 全库体检

```powershell
.\.venv\Scripts\python.exe .\fix-babeldoc-rotated-pages\audit-translations.py    # 全部译文
.\.venv\Scripts\python.exe .\fix-babeldoc-rotated-pages\final-check-installed.py # 已修复的文件
```

## 五、本机全部译文的体检与修复结果

见 [译文体检与修复报告.md](译文体检与修复报告.md)。结论：

- 6 篇论文没有 `/Rotate` 页面，不受影响
- **Zhu_2026_055514**（PDF p18、p23 = 打印 17、22）：已整篇重翻修复
- **Asek 蜂鸟**（PDF p89、147、178、179）：已整篇重翻修复
- **Park / Phan**（p96）：已精准重建对照版左半页
- 旧文件都备份在各自目录的 `_backup_before_rotfix\`

## 六、注意

1. **已经存在的 `中文修正版.pdf` 不会自动变好**。它是 2026-09-04 用旧版引擎生成的，
   坏法不同（是把 90° 旋转丢了，`Tm` 有 428 个 `1 0 0 1`），需要**重新翻译**才能得到
   正确的单语版。
2. 修好之后，之前手工做的 `机器人蜂鸟_中英左右对照版_表格修正版.pdf`（往右半页贴图 + 重画
   中文表格）就不需要了，重新跑一遍即可得到原生正确的结果。
3. 这 4 页的表格正文在 BabelDOC 里属于“旋转段落”，会被**跳过翻译**
   （`il_translator.py`：`if paragraph.vertical: return None, None`）。
   所以修复后这 4 页是**表格完整、方向正确，但表格内容仍是英文，只有图注/表注是中文**。
   若要让表格正文也翻成中文，需要另外处理（改 `typesetting.py` 里写死的 `vertical=False`
   并放开旋转段落的翻译），风险更大，需要单独评估。
