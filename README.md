# pdf2zh GUI Toolkit（Windows 双击即用）

把 [PDFMathTranslate-next](https://github.com/PDFMathTranslate/PDFMathTranslate-next)（`pdf2zh_next` + [BabelDOC](https://github.com/funstory-ai/BabelDOC)）包装成 **Windows 上双击就能用的图形界面**，并配批量脚本、界面汉化和几个踩坑补丁。

> 这不是官方项目，只是个人用的封装层：**引擎本身原样安装到 `.venv`，本仓库不含上游代码**。

---

## 它能解决什么

上游 `pdf2zh_next` 自带的 Gradio 界面本身没问题，但在 Windows 上有几个坑：

| 坑 | 本项目的处理 |
|---|---|
| 要记一堆命令行参数 | `图形界面.cmd` 双击即用，自动开浏览器 |
| 界面里 149 条设置说明全是英文 | `apply-cn-labels.py` 汉化（含 9 条界面文案） |
| 界面在高分屏上太大 | `图形界面-紧凑.cmd`：Edge 应用窗口 + 缩放 0.8 |
| 浏览器打开是白屏 / 报 `proxy software` 错 | 启动器设 `NO_PROXY=127.0.0.1,localhost,::1`（httpx 不读 Windows 的绕过代理名单） |
| 控制台偶发 `UnicodeEncodeError` 让退出码变 1 | 强制 `PYTHONUTF8=1`，并在退出码非 0 时按"产物是否生成"判定 |
| 服务默认监听 `0.0.0.0`（同一局域网可见） | 可选 `加固-仅本机访问.cmd` 加防火墙入站拦截（回环不受影响） |
| 出问题不知道看哪儿 | `launcher.log`（启动器步骤）+ `engine.log`（引擎完整输出） |
| 批量翻译要一个个点 | `translate-pdf.ps1`：整目录批量、失败统计、耗时统计 |

---

## 快速开始

前置：Windows 10/11、[uv](https://docs.astral.sh/uv/)、能访问 PyPI。

```powershell
# 1) 建目录（建议放非系统盘，模型缓存约 1.7 GB）
mkdir D:\pdf2zh; cd D:\pdf2zh

# 2) 建 Python 3.12 环境并装引擎
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv venv --python 3.12 .venv
uv pip install --python ".\.venv\Scripts\python.exe" pdf2zh-next

# 3) 把本仓库的文件放到同一目录，然后双击
#    图形界面.cmd
```

首次启动会下载 BabelDOC 的字体与版面模型（约 355 MB，缓存在 `%USERPROFILE%\.cache\babeldoc`）；
启动器默认走 `HF_ENDPOINT=https://hf-mirror.com` 镜像。

### 批量翻译

```powershell
.\translate-pdf.ps1 -Path "D:\papers"                                  # 免费服务试水
.\translate-pdf.ps1 -Path "D:\papers" -Service deepseek -ApiKey "sk-..." # DeepSeek，质量最好
.\translate-pdf.ps1 -Path ".\a.pdf" -Pages "1-3" -NoDual                # 只翻前 3 页、不出双语版
```

也可以直接把 PDF 或文件夹**拖到 `翻译PDF.cmd` 上**。

---

## 文件说明

| 文件 | 作用 |
|---|---|
| `图形界面.cmd` | 主入口：免登录，用默认浏览器打开界面 |
| `图形界面-紧凑.cmd` | 免登录 + Edge 应用窗口 + 界面缩小 20%（高分屏推荐） |
| `图形界面-窗口模式.cmd` | 免登录 + Edge 应用窗口（原尺寸） |
| `图形界面-带密码.cmd` | 需要用户名密码（不可信网络用），密码在 `gui-auth.txt` |
| `gui-launcher.ps1` | 启动器：端口试探、缩放、登录、代理绕过、日志 |
| `translate-pdf.ps1` / `翻译PDF.cmd` | 批量翻译（支持拖拽） |
| `apply-cn-labels.py` / `应用中文标签.cmd` | 界面汉化补丁（**升级引擎后要重跑**） |
| `加固-仅本机访问.cmd` | 加防火墙规则，禁止局域网访问界面端口（需管理员） |
| `界面设置中文对照.md` | 界面每一项设置的中文含义、推荐值、排错对应 |
| `README-install.md` | 安装与使用详解 |
| `安装记录.md` | 实战记录：每个坑的定位过程与修复（含上游代码位置） |

---

## 关于汉化

上游只翻译了界面框架（`gui_translation.yaml` 覆盖 100%），但**设置项的标签直接取自源码里的英文 `description`**：

```python
# pdf2zh_next/gui.py
label=field.description        # ← 149 处英文描述就是这么显示出来的
```

`apply-cn-labels.py` 把 `pdf2zh_next/config/{model,translate_engine_model}.py` 里的 149 条描述替换成中文，
并给 `gui_translation.yaml` 补上缺失的 9 条界面文案。原文件首次运行会备份为 `*.orig-en.bak`。

```powershell
.\.venv\Scripts\python.exe apply-cn-labels.py   # 或双击 应用中文标签.cmd
```

> ⚠️ `uv pip install --upgrade pdf2zh-next` 会覆盖 `.venv` 里的这两个文件，**升级后重跑一次即可**。

---

## 常见问题

- **界面白屏 / 提示 `Error launching GUI ... proxy software`** → 代理软件（Clash 等）干扰本机自检；启动器已设 `NO_PROXY`，若仍失败看 `engine.log`
- **段落漏译** → 打开对应服务的「启用 JSON 模式」；降低并发；检查额度
- **`Scanned PDF detected`** → 扫描件需先 OCR（OCRmyPDF / ABBYY / Acrobat），再勾「跳过扫描检测」
- **只想要左右对照版** → 「禁用双语输出」不勾、「禁用单语输出」勾上；双语文件默认就是**左右并排**
- 更多见 [`界面设置中文对照.md`](./界面设置中文对照.md)

---

## 许可与致谢

- 本仓库的脚本与文档：MIT（见 `LICENSE`）
- 引擎 [PDFMathTranslate-next](https://github.com/PDFMathTranslate/PDFMathTranslate-next) 与 [BabelDOC](https://github.com/funstory-ai/BabelDOC)：AGPL-3.0，**本项目不重新分发其代码**，只在自己机器上安装并打运行时补丁
- 汉化思路参考 [zotero-pdf2zh](https://github.com/guaguastandup/zotero-pdf2zh)（Zotero 插件版，本项目与其无隶属关系）
