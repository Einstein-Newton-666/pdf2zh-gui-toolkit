## 使用方法

下载下面的 `pdf2zh-gui-toolkit-*.zip`，解压到你的 pdf2zh 项目目录（和 `.venv` 同级），然后：

1. 首次使用先按 [README-install.md](README-install.md) 建好环境：
   ```powershell
   uv venv --python 3.12 .venv
   uv pip install --python ".\.venv\Scripts\python.exe" pdf2zh-next
   ```
2. 双击 **`图形界面.cmd`** 启动图形界面（免登录，自动开浏览器）
3. 觉得界面太大就用 **`图形界面-紧凑.cmd`**（缩放 0.8 的应用窗口）
4. 界面若显示英文，双击 **`应用中文标签.cmd`** 打一次汉化补丁

批量翻译：把 PDF 或文件夹拖到 **`翻译PDF.cmd`** 上，或用命令行
`.\translate-pdf.ps1 -Path "D:\papers" -Service deepseek -ApiKey "sk-..."`。

## 本次包含

- 图形界面启动器与 4 个入口（默认 / 紧凑 / 窗口模式 / 带密码）
- 批量翻译脚本 + 拖拽入口
- 界面汉化补丁（149 条设置说明 + 9 条界面文案，带原文件备份、可重复执行）
- 仅本机访问的防火墙加固脚本
- 4 份文档：README / 安装详解 / 界面设置中文对照 / 实战安装记录

## 注意

- 包里**不含**翻译引擎，需要按上面第 1 步安装（上游 PDFMathTranslate-next / BabelDOC，AGPL-3.0）
- 首次启动会下载字体与版面模型（约 355 MB，缓存在 `%USERPROFILE%\.cache\babeldoc`）
- 升级引擎后请重新运行 `应用中文标签.cmd`（升级会覆盖汉化补丁）
