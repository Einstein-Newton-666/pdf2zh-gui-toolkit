# PDF 翻译环境（pdf2zh_next + BabelDOC）安装说明

> 示例路径说明：文中 D:\研究生\pdf2zh 指本项目在你机器上的实际安装目录，按自己的位置替换即可；%USERPROFILE% 是你的用户目录。


> 位置：`D:\研究生\pdf2zh\`　安装日期：2026-09-10
> 用途：把英文 PDF 论文翻成**保留公式与排版**的中文/双语版，**完全不需要 Zotero**。

---

## 1. 装了什么

| 组件 | 版本/位置 | 说明 |
|---|---|---|
| Python 解释器 | 3.12.13（uv 自带，`~\AppData\Roaming\uv\python\`） | 系统里的 Python 3.8.4 太老，没有使用 |
| 虚拟环境 | `.venv\`（846 MB） | 全部依赖都装在这个文件夹里，删掉即卸载 |
| 翻译引擎 | `pdf2zh_next` **2.9.0** | 上游 [PDFMathTranslate-next](https://github.com/PDFMathTranslate/PDFMathTranslate-next) |
| 排版引擎 | `babeldoc` 0.6.x | 负责公式保留、双语对照排版 |
| uv 包缓存 | `.uv-cache\`（887 MB） | **可以安全删除**，只影响以后重装的速度 |
| **图形界面** | `图形界面.cmd` | **双击即用**（桌面快捷方式 `PDF翻译`），中文界面 |
| 图形界面·紧凑 | `图形界面-紧凑.cmd` | 界面缩小 20% 的应用窗口（高分屏用） |
| 图形界面·窗口模式 | `图形界面-窗口模式.cmd` | Edge 应用窗口，无地址栏，像桌面软件 |
| 图形界面·带密码 | `图形界面-带密码.cmd` | 需要输密码（校园网等不可信网络用） |
| 启动器逻辑 | `gui-launcher.ps1` | 上面几个 .cmd 都只是它的入口；负责端口避让、缩放、登录凭据 |
| **界面汉化补丁** | `apply-cn-labels.py` + `应用中文标签.cmd` | 把 149 条英文设置说明换成中文（**升级引擎后要重跑**） |
| **设置速查表** | `界面设置中文对照.md` | 界面每项设置的中文说明与推荐值 |
| 登录凭据 | `gui-auth.txt` | 内容 `用户名,密码`，首次启动自动生成随机密码（可自行改） |
| 批量脚本 | `translate-pdf.ps1` | 批量翻译 + 失败统计 + 耗时统计 |
| 拖拽入口 | `翻译PDF.cmd` | 把 PDF/文件夹拖上去即可（命令行批量的图形化外壳） |
| 命令行帮助快照 | `cli-help.txt` | `pdf2zh_next --help` 的完整输出 |

> ⚠ **改这些文件时注意编码**（2026-09-10 踩过的坑）：
> - 两个 `.ps1` 必须存成 **UTF-8 带 BOM**，否则 Windows PowerShell 5.1 会按 GBK 解码 → 中文乱码 + 语法错误，点了没反应
> - 四个 `.cmd` 必须保持 **纯 ASCII**（中文全部由 .ps1 输出），因为 cmd.exe 按控制台代码页读 .cmd，写中文会乱码导致找不到脚本

模型/字体资源缓存（引擎自动下载，**不在**本文件夹）：`%USERPROFILE%\.cache\babeldoc\`

---

## 2. 四种用法

### 用法零：图形界面（推荐，不用记任何命令）

双击桌面的 **`PDF翻译`** 图标，或双击 `D:\研究生\pdf2zh\图形界面.cmd`：

1. 弹出一个黑色窗口，里面写着**地址**（默认 `http://127.0.0.1:7860`）
2. 浏览器自动打开界面（首次 10~30 秒）
3. 界面里：拖入 PDF → 选翻译服务（免费选 `SiliconFlowFree`；要质量好就选 `DeepSeek` 并把 Key 填一次）→ 选页范围/术语表 → 点翻译 → 下载译文

要点：

- **默认免登录**（本机单人使用，不弹密码框）；翻译设置（含 API Key）存到 `%USERPROFILE%\.config\pdf2zh\`，**填一次就记住**
- **那个黑窗口不要关**：关掉就等于停服务，翻译中途关会中断
- 入口一览：
  | 入口 | 用途 |
  |---|---|
  | 桌面 `PDF翻译` 图标 | **推荐**：免登录 + 紧凑应用窗口（界面缩小 20%，无地址栏） |
  | `图形界面.cmd` | 免登录，用默认浏览器打开（想要普通标签页时用） |
  | `图形界面-紧凑.cmd` | 免登录 + Edge 应用窗口 + 界面缩小 20%（高分屏觉得界面太大时用） |
  | `图形界面-窗口模式.cmd` | 免登录 + Edge 应用窗口（原始大小） |
  | `图形界面-带密码.cmd` | **需要输密码**（密码印在黑窗口里，也存在 `gui-auth.txt`）——在校园网等不可信网络时用它 |
  | `加固-仅本机访问.cmd` | 一键加防火墙规则，禁止局域网访问本机 GUI 端口（**需要管理员**，右键"以管理员身份运行"） |
- **觉得界面太大**：在界面里按 `Ctrl` + `-`（减号）两三次，浏览器会记住这个缩放；或者直接用桌面的 `PDF翻译` 图标（已内置缩小 20% 的紧凑模式）

### 界面里怎么选输出格式（双语对照 / 左右并排）

在界面的 **「## PDF 输出选项」** 区域（汉化后的标签）：

| 选项（界面上的中文标签） | 说明 |
|---|---|
| **禁用双语输出** | **别勾**。不勾 → 生成 `*.zh.dual.pdf`（左右对照） |
| **禁用单语输出** | **别勾**。不勾 → 生成 `*.zh.mono.pdf`（纯中文） |
| **使用交替页面进行双页 PDF 阅读** | **别勾**（默认）。不勾 = **左右并排**（左原文 / 右译文）；勾上 = 原文页、译文页交替排列 |
| **在双语模式下优先显示翻译后的页面** | 勾上则左右顺序反过来（右原文 / 左译文） |
| **水印模式** | 无水印 / 带水印 |
| **仅在输出 PDF 中包含已翻译的页面。** | 只保留翻过的那几页 |

翻完在页面下方点 **「下载翻译（双语）」** = 左右对照版，**「下载翻译（单语版）」** = 纯中文版。

### 界面还是英文怎么办

上游只翻译了界面框架，**设置项的说明文字来自引擎源码里的英文描述（149 条）**，所以原本大量设置是英文。
项目里提供了汉化补丁：

```powershell
# 双击 应用中文标签.cmd 即可；或命令行：
.\.venv\Scripts\python.exe apply-cn-labels.py
```

- 已把 **149 条设置说明 + 9 条界面文案**换成中文（原文件备份为 `*.orig-en.bak`）
- **升级引擎后要重跑一次**（`uv pip install --upgrade pdf2zh-next` 会覆盖掉补丁）
- 每一项设置的中文含义与推荐值，见 **`界面设置中文对照.md`**

> ⚠️ 界面上**没有**"左左右右 / 上下对照"的开关，这是上游的有意设计：`babeldoc/translation_config.py` 里
> `use_side_by_side_dual = True  # Deprecated: 拼版式双语 PDF（并排显示原文和译文）…已停用` ——
> **左右并排就是双语文件唯一且默认的形态**，所以不需要选。
> 实测：双语文件第 1 页左半是英文原文、右半是中文译文，页宽由 595pt 变成 1191pt。

- 端口默认 7860，被占用会自动往后找（7861、7862…），实际端口以黑窗口里打印的为准
- **出问题看这两个日志**（都在本目录）：
  - `launcher.log`：启动器每一步。空文件=脚本没被调用；只有 cmd 行没有 PowerShell 行=PowerShell 没起来
  - `engine.log`：引擎的完整输出（界面白屏/启动失败时，真正的报错在这里）
- 文件名里**不要加括号**（`(` `)`）：某些调用方式下 cmd 会把括号当命令分隔符，结果执行到别的文件
- 本机自检与代理：启动器已设置 `NO_PROXY=127.0.0.1,localhost,::1`，避免 Gradio 的本地自检请求被 Clash 等代理吞掉（httpx 不读 Windows 的"绕过代理"名单）

### 用法一：拖拽批量（多个文件，最省事）

把 **一个 PDF 文件** 或 **一个装满 PDF 的文件夹** 拖到 `翻译PDF.cmd` 上。
默认用免费服务 `siliconflowfree`（不需要 API Key，可能漏译少量内容）。

### 用法二：命令行（推荐）

```powershell
cd "D:\研究生\pdf2zh"

# 单篇，免费服务
.\translate-pdf.ps1 -Path "D:\论文\a.pdf"

# 整个文件夹批量
.\translate-pdf.ps1 -Path "D:\论文\待翻译"

# 用 DeepSeek（质量最好，作者推荐）
.\translate-pdf.ps1 -Path "D:\论文" -Service deepseek -ApiKey "sk-你的key"

# DeepSeek + 指定模型
.\translate-pdf.ps1 -Path "D:\论文" -Service deepseek -ApiKey "sk-xxx" -Model "deepseek-v4-flash"

# 先试翻前 2 页看效果（省 token，但输出仍是完整 PDF，未选中的页保持原文）
.\translate-pdf.ps1 -Path ".\a.pdf" -Pages "1-2"

# 只要中文单语版，不要双语对照版
.\translate-pdf.ps1 -Path ".\a.pdf" -NoDual

# 关掉自动术语提取（省 token）
.\translate-pdf.ps1 -Path ".\a.pdf" -Service deepseek -ApiKey "sk-xxx" -NoAutoGlossary
```

常用参数一览：`-Out`（输出目录，默认 `output\`）、`-Pages`、`-LangIn/-LangOut`、`-Qps`（并发）、`-NoDual`、`-NoMono`、`-NoAutoGlossary`、`-SkipScannedDetection`、`-EngineDebug`。

> Key 安全：`-ApiKey` 只作为子进程参数使用，脚本不写入任何文件。也可以先 `$env:PDF2ZH_API_KEY="sk-xxx"` 再用。

### 用法三：直接用引擎（最灵活）

```powershell
.\.venv\Scripts\pdf2zh_next.exe "论文.pdf" --lang-in en --lang-out zh --output .\output --deepseek --deepseek-api-key sk-xxx
.\.venv\Scripts\pdf2zh_next.exe --gui      # 打开图形界面
.\.venv\Scripts\pdf2zh_next.exe --warmup   # 预热：提前下载字体与版面模型
```

产物默认两份：`xxx.zh.pdf`（中文单语）和 `xxx.dual.pdf`（中英对照）。

---

## 3. 翻译服务怎么选

| 服务 | 参数值 | 说明 |
|---|---|---|
| siliconflowfree | `-Service siliconflowfree` | 免费免 Key，**可能漏译**，适合先试水 |
| **deepseek** | `-Service deepseek` | **推荐**；质量好、有缓存命中；作者建议 `deepseek-v4-flash` |
| siliconflow | `-Service siliconflow` | 需 Key，可填 `-BaseUrl https://api.siliconflow.cn/v1` |
| zhipu / openai | `-Service zhipu` / `openai` | 需 Key |
| bing / google | `-Service bing` / `google` | 免费但限流严重，务必 `-Qps 2` 以下 |

**成本量级**：一篇 10 页英文文献约 7～10 万 token（单页约 5k）。按 DeepSeek V4-Flash 的价格算，一篇大约一两毛钱人民币。同一篇重复翻译会走缓存，不会重复大量扣费。

---

## 4. 常见坑

1. **首次运行会下载字体和版面模型**，国内直连 HuggingFace 常卡住。脚本已默认设置 `HF_ENDPOINT=https://hf-mirror.com`；如果仍然失败，先单独跑一次 `--warmup`。
2. **扫描件必须先 OCR**：引擎不提供 OCR。直接翻扫描版会报 `Scanned PDF detected` 或出现断行/重影。先用 OCRmyPDF / ABBYY / Acrobat 处理，然后加 `-SkipScannedDetection`。
3. **个别段落没翻**：翻译失败时程序用原文顶上。可换服务、检查 API 额度；DeepSeek 可加 `--deepseek-enable-json-mode` 缓解（默认关闭）。
4. **本文件夹不要改名/移动**：`.venv` 里记录了绝对路径，改名会导致入口失效。真要移动，删掉 `.venv` 重装（见下）。
5. **`output\` 会被脚本自动排除**，批量时不会把译文再翻一遍。
6. **退出码 1 但文件其实翻好了**：上游 `rich` 进度条在 GBK 控制台遇到 `ﬂ` 之类生僻字符会抛 `UnicodeEncodeError`，把退出码带成 1。脚本已强制 UTF-8 并在退出码非 0 时检查产物，不会再误报失败。
7. **`-Pages` 只控制"翻哪些页"，输出永远是完整 PDF**（未选中的页保留原文）。另外注意：即便只翻 2 页也要 ~1 分钟——**时间主要花在整篇的版面解析上，翻页省的是 token 不是时间**（实测 209 页文档：翻 2 页 58 s）。
8. **图形界面默认监听 `0.0.0.0`（局域网可见）** —— 这是上游写死的，同网段的人能打开你的界面、也能用你填的 Key。所以默认入口带随机密码登录；确需免登录时请只在可信网络使用，或用管理员权限加一条防火墙规则拦入站：
   ```powershell
   New-NetFirewallRule -DisplayName "Block pdf2zh GUI inbound" -Direction Inbound -Protocol TCP -LocalPort 7860 -Action Block
   ```
9. 引擎是 **AGPL** 协议，个人/科研使用没问题。

---

## 5. 升级 / 卸载 / 重装

```powershell
# 升级引擎到最新版
cd "D:\研究生\pdf2zh"
$env:UV_CACHE_DIR = "$PWD\.uv-cache"
uv pip install --python ".\.venv\Scripts\python.exe" --upgrade pdf2zh-next

# 彻底卸载：直接删掉整个 pdf2zh 文件夹即可
# （另外可顺手删掉 %USERPROFILE%\.cache\babeldoc 释放模型缓存）
```

### 换位置（搬文件夹）怎么办

`.venv` 里记的是绝对路径，**直接剪切会让 `pdf2zh_next.exe` 失效**。正确做法是"只搬内容 + 原地重建环境"（`.uv-cache` 一起搬的话，重建时不用重新下载任何包）：

```powershell
$src = "旧路径\pdf2zh"; $dst = "新路径\pdf2zh"
New-Item -ItemType Directory -Force -Path $dst | Out-Null
Get-ChildItem $src -Force | Where-Object { $_.Name -ne '.venv' } | Move-Item -Destination $dst
Remove-Item "$src\.venv" -Recurse -Force
Remove-Item $src -Recurse -Force          # 旧目录已空，可删
$env:UV_CACHE_DIR = "$dst\.uv-cache"
uv venv --python 3.12 "$dst\.venv"
uv pip install --python "$dst\.venv\Scripts\python.exe" pdf2zh-next
```

> 2026-09-10 已按此法把整个环境从 `D:\研究生\资料\pdf2zh` 搬到 **`D:\研究生\pdf2zh`**，重建后实测翻译正常。

---

## 6. 可选：还想要"历史记录 + 批量队列"的网页？

内置图形界面已经能满足"上传→翻译→下载"，但它**没有历史记录列表**。要那个功能就装原项目 `zotero-pdf2zh` 里的 **Server**（Zotero 插件本身仍然不需要装）。
它会另建一套自己的虚拟环境（再占约 1 GB），装法：

```powershell
cd "D:\研究生\pdf2zh"
# 下载 server.zip（GitHub 或 Gitee）
#   https://github.com/guaguastandup/zotero-pdf2zh/releases/latest/download/server.zip
#   https://gitee.com/guaguastandup/zotero-pdf2zh/raw/v4.1.7/server.zip
# 解压出 server\server.py 后：
cd server
uv run --python 3.12 --with-requirements requirements.txt server.py
# 浏览器打开 http://127.0.0.1:8890
```

注意：Server 运行期间终端不能关；默认只监听 `127.0.0.1`，不要改成 `0.0.0.0`。

---

## 7. 本次安装的实测记录

见 `安装记录.md`（首次翻译的耗时、产物、图形界面实测、遇到的问题）。
