#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 pdf2zh_next 图形界面里"设置项的英文标签"替换成中文。

背景：
    界面里每个设置项的标签是 gui.py 里的 `label=field.description`，
    也就是直接取 pdf2zh_next/config/model.py 与 translate_engine_model.py 里
    pydantic 字段的 description 文本。上游只翻译了界面框架（gui_translation.yaml），
    这 149 处 description（135 条唯一文案）全是英文 —— 这就是"有些设置是英文"的原因。

本脚本做的事：
    把这两个文件里的 description="..." 按下面的对照表替换成中文，
    原文件备份为 *.orig-en.bak（只在第一次备份，不会被覆盖）。

用法：
    双击同目录的 应用中文标签.cmd   或   python apply-cn-labels.py
    升级 pdf2zh-next 之后重跑一次即可（升级会覆盖掉这两个文件）。

恢复英文：
    把 <site-packages>/pdf2zh_next/config/model.py.orig-en.bak 覆盖回 model.py，
    translate_engine_model.py 同理。
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

CN = {
    # ---------- 通用 / 命令行 ----------
    "Enable debug mode": "开启调试模式",
    "Enable GUI mode": "启动图形界面",
    "Only download and verify required assets then exit": "只下载并校验所需资源后退出",
    "Generate offline assets package in the specified directory": "在指定目录生成离线资源包",
    "Restore offline assets package from the specified file": "从指定文件恢复离线资源包",
    "Show version then exit": "显示版本号后退出",
    "Enable sharing mode": "开启分享模式（生成公网链接，不建议使用）",
    "Path to the authentication file": "登录凭据文件路径（内容格式：用户名,密码）",
    "Path to the welcome page html file": "欢迎页 HTML 文件路径",
    "Enabled services": "启用哪些翻译服务（逗号分隔，留空=全部）",
    "Disable GUI sensitive input": "隐藏界面上的敏感输入框（如 API Key）",
    "Disable automatic saving of configuration": "关闭配置自动保存",
    "WebUI port": "网页界面端口",
    "UI language": "界面语言",
    "Path to the configuration file": "配置文件路径",
    "Progress report interval in seconds": "进度上报间隔（秒）",

    # ---------- 翻译基本参数 ----------
    "Input PDF files to process": "要处理的 PDF 文件",
    "Pages to translate (e.g. '1,2,1-,-3,3-5')": "要翻译哪些页，例如 1-5（省 token 用；输出仍是完整 PDF）",
    "Source language code": "原文语言（en=英语）",
    "Target language code": "目标语言（zh=简体中文）",
    "Output directory for translated files": "译文输出目录",
    "QPS limit for translation service": "翻译并发上限 QPS（设太高会被服务商限流）",
    "Ignore translation cache": "忽略翻译缓存（强制重新翻译，会重复扣费）",
    "Glossary file list.": "术语表文件列表（CSV；可提升专业词一致性）",
    "save automatically extracted glossary": "保存自动提取出来的术语表",
    "Disable auto extract glossary": "关闭自动术语提取（省 token）",
    "Minimum text length to translate": "短于这个长度的文本不翻译",
    "Maximum number of workers for translation pool. If not set, will use qps as the number of workers":
        "翻译线程池最大线程数；留空则用 QPS 的值",
    "QPS limit for term extraction translation service. If not set, will follow qps.":
        "术语提取服务的 QPS 上限；留空则跟随主 QPS",
    "Maximum number of workers for term extraction translation pool. If not set or 0, will follow pool_max_workers.":
        "术语提取线程池最大线程数；留空或 0 则跟随主线程数",
    "RPC service host address for document layout analysis": "版面分析 RPC 服务地址（一般不用填）",

    # ---------- PDF 输出选项 ----------
    "Do not output bilingual PDF files": "不输出双语 PDF（不勾=生成左右对照的 dual 文件）",
    "Do not output monolingual PDF files": "不输出单语 PDF（不勾=生成纯中文的 mono 文件）",
    "Put translated pages first in dual PDF mode": "双语对照里把译文放前面（左右顺序对调）",
    "Use alternating pages mode for dual PDF": "双语用「交替页」模式（不勾=左右并排对照）",
    "Only include translated pages in the output PDF. Effective only when --pages is used.":
        "输出 PDF 只保留翻过的页（仅在指定了页范围时生效）",
    "Watermark output mode for PDF files (watermarked, no_watermark, or both)":
        "水印模式：watermarked 带水印 / no_watermark 无水印 / both 两种都出",
    "Maximum pages per part for split translation": "分段翻译时每段最大页数（0=不分段）",
    "Translate table text (experimental)": "翻译表格里的文字（实验性）",
    "Skip scanned detection": "跳过扫描件检测（扫描件已 OCR 过时用）",
    "Force translated text to be black and add white background": "译文强制黑字白底（OCR 兼容模式）",
    "Enable automatic OCR workaround. If a document is detected as heavily scanned, this will attempt to enable OCR processing and skip further scan detection. See documentation for details. (default: False)":
        "自动开启 OCR 兼容模式：检测到大量扫描页时自动启用并跳过后续扫描检测（默认关闭）",
    "Enhance all compatibility enhancement options": "开启全部兼容性增强选项",
    "Enable all compatibility enhancement options": "开启全部兼容性增强选项",
    "Disable rich text translation": "关闭富文本翻译（排版异常时可试）",
    "Force split short lines into different paragraphs": "强制把短行拆成不同段落",
    "Split threshold factor for short lines": "短行拆分阈值系数",
    "Skip PDF cleaning step": "跳过 PDF 清理步骤",
    "Font pattern to identify formula text": "识别公式文字的字体特征",
    "Character pattern to identify formula text": "识别公式文字的字符特征",
    "Override primary font family for translated text. Choices: 'serif' for serif fonts, 'sans-serif' for sans-serif fonts, 'script' for script/italic fonts. If not specified, uses automatic font selection based on original text properties.":
        "覆盖译文字体族：serif 衬线 / sans-serif 无衬线 / script 手写体；留空=按原文自动匹配",
    "Handle alternating line numbers and text paragraphs in documents with line numbers":
        "处理带行号文档中的交替行号与段落",
    "Remove non-formula lines within paragraph areas": "移除段落区域内的非公式行",
    "IoU threshold for identifying non-formula lines": "判定「非公式行」的 IoU 阈值",
    "Skip formula offset calculation during processing": "跳过公式偏移量计算",
    "Protection threshold for figures and tables (lines within figures/tables will not be processed)":
        "图表保护阈值（图表内部的线条不参与处理）",

    # ---------- 翻译引擎选择 ----------
    "Translation engine settings": "翻译引擎设置",
    "Term extraction translation engine settings": "术语提取所用翻译引擎的设置",
    "Whether the translator supports LLM": "该翻译器是否支持大模型（内部字段）",

    # ---------- OpenAI ----------
    "OpenAI model to use": "OpenAI 使用的模型名",
    "Base URL for OpenAI API": "OpenAI API 地址",
    "API key for OpenAI service": "OpenAI 的 API Key",
    "Temperature for OpenAI service": "OpenAI 的 temperature（越高越随机）",
    "Send temprature to OpenAI service": "向 OpenAI 发送 temperature 参数",
    "Enable JSON mode for OpenAI service": "OpenAI 启用 JSON 模式（有段落漏译时可试）",
    "Send reasoning effort to OpenAI service": "向 OpenAI 发送思考强度参数",
    "Reasoning effort for OpenAI service (minimal/low/medium/high)":
        "OpenAI 的思考强度（minimal/low/medium/high）",
    "Timeout (seconds) for OpenAI service": "OpenAI 超时时间（秒）",

    # ---------- OpenAI 兼容 ----------
    "OpenAI Compatible model to use": "OpenAI 兼容接口使用的模型名",
    "Base URL for OpenAI Compatible service": "OpenAI 兼容接口地址（填到 /v1 为止）",
    "API key for OpenAI Compatible service": "OpenAI 兼容接口的 API Key",
    "Temperature for OpenAI Compatible service": "OpenAI 兼容接口的 temperature",
    "Send temperature to OpenAI Compatible service": "向 OpenAI 兼容接口发送 temperature 参数",
    "Enable JSON mode for OpenAI Compatible service": "OpenAI 兼容接口启用 JSON 模式",
    "Send reasoning effort to OpenAI Compatible service": "向 OpenAI 兼容接口发送思考强度参数",
    "Reasoning effort for OpenAI Compatible service (minimal/low/medium/high)":
        "OpenAI 兼容接口的思考强度（minimal/low/medium/high）",
    "Timeout (seconds) for OpenAI Compatible service": "OpenAI 兼容接口超时时间（秒）",

    # ---------- DeepSeek ----------
    "DeepSeek model to use": "DeepSeek 使用的模型名（推荐 deepseek-v4-flash）",
    "API key for DeepSeek service": "DeepSeek 的 API Key",
    "Enable JSON mode for DeepSeek service": "DeepSeek 启用 JSON 模式（有段落漏译时可试）",
    "Thinking mode for DeepSeek v4 models (enabled/disabled)": "DeepSeek v4 思考模式（enabled/disabled）",
    "Reasoning effort for DeepSeek thinking mode (high/max)": "DeepSeek 思考强度（high / max）",

    # ---------- SiliconFlow ----------
    "SiliconFlow model to use": "硅基流动使用的模型名",
    "Base URL for SiliconFlow API": "硅基流动 API 地址（https://api.siliconflow.cn/v1）",
    "API key for SiliconFlow service": "硅基流动的 API Key",
    "Enable JSON mode for SiliconFlow service": "硅基流动启用 JSON 模式",
    "Enable JSON mode for SiliconFlow Free service": "免费版硅基流动启用 JSON 模式",
    "Enable thinking for SiliconFlow service": "硅基流动启用思考模式",
    "Send enable thinking param to SiliconFlow service": "向硅基流动发送 enable_thinking 参数",

    # ---------- 其它服务 ----------
    "Aliyun DashScope model to use": "阿里云百炼使用的模型名",
    "Base URL for Aliyun DashScope API": "阿里云百炼 API 地址",
    "API key for Aliyun DashScope service": "阿里云百炼的 API Key",
    "Temperature for Aliyun DashScope service": "阿里云百炼的 temperature",
    "Send temperature to Aliyun DashScope service": "向阿里云百炼发送 temperature 参数",
    "Enable JSON mode for Aliyun DashScope service": "阿里云百炼启用 JSON 模式",
    "Timeout (seconds) for Aliyun DashScope service": "阿里云百炼超时时间（秒）",

    "AzureOpenAI model to use": "Azure OpenAI 使用的模型名",
    "Base URL for AzureOpenAI API": "Azure OpenAI API 地址",
    "API key for AzureOpenAI service": "Azure OpenAI 的 API Key",
    "API version for AzureOpenAI service": "Azure OpenAI 的 API 版本（如 2024-02-01）",

    "Azure API Key": "Azure 翻译服务的 API Key",
    "Azure endpoint": "Azure 翻译服务端点",

    "ModelScope model to use": "魔搭（ModelScope）使用的模型名",
    "API key for ModelScope service": "魔搭的 API Key",
    "Enable JSON mode for ModelScope service": "魔搭启用 JSON 模式",

    "Zhipu model to use": "智谱使用的模型名",
    "API key for Zhipu service": "智谱的 API Key",
    "Enable JSON mode for Zhipu service": "智谱启用 JSON 模式",

    "Gemini model to use": "Gemini 使用的模型名",
    "API key for Gemini service": "Gemini 的 API Key",
    "Enable JSON mode for Gemini service": "Gemini 启用 JSON 模式",

    "Grok model to use": "Grok 使用的模型名",
    "API key for Grok service": "Grok 的 API Key",
    "Enable JSON mode for Grok service": "Grok 启用 JSON 模式",

    "Groq model to use": "Groq 使用的模型名",
    "API key for Groq service": "Groq 的 API Key",
    "Enable JSON mode for Groq service": "Groq 启用 JSON 模式",

    "QwenMt model to use": "QwenMt 使用的模型名",
    "Base URL for QwenMt API": "QwenMt API 地址",
    "API key for QwenMt service": "QwenMt 的 API Key",
    "the target domain to guide translation style for QwenMt service":
        "QwenMt 的目标领域（用于引导翻译风格）",

    "Ollama model to use": "Ollama 使用的模型名",
    "Ollama host": "Ollama 服务地址",
    "The max number of token to predict.": "最大生成 token 数",

    "Xinference model to use": "Xinference 使用的模型名",
    "Xinference host": "Xinference 服务地址",

    "DeepL auth key": "DeepL 的认证 Key",

    "Tencent Mechine Translation secret ID": "腾讯机器翻译 SecretId",
    "Tencent Mechine Translation secret Key": "腾讯机器翻译 SecretKey",

    "AnythingLLM API Key": "AnythingLLM 的 API Key",
    "AnythingLLM url": "AnythingLLM 服务地址",

    "Dify API Key": "Dify 的 API Key",
    "Dify url": "Dify 服务地址",

    "Claude Code model to use": "Claude Code 使用的模型名",
    "Path to Claude Code CLI": "Claude Code 命令行程序路径",
    "Command timeout in seconds": "命令超时时间（秒）",
}

TARGETS = [
    ("pdf2zh_next", "config", "model.py"),
    ("pdf2zh_next", "config", "translate_engine_model.py"),
]

# gui_translation.yaml 里缺失的界面文案（实测：界面上真正没中文的就是这几条）
EXTRA_UI = {
    "File(s)": "文件",
    "Uploaded files (this session)": "本次会话上传的文件",
    "Select File to Preview/Download": "选择要预览/下载的文件",
    "Download All (ZIP)": "打包下载全部（ZIP）",
    "Download All Dual (ZIP)": "打包下载全部双语版（ZIP）",
    "Download All Mono (ZIP)": "打包下载全部单语版（ZIP）",
    "Download All Glossaries (ZIP)": "打包下载全部术语表（ZIP）",
    "CLI command to execute. May include arguments and will be split like a shell command (e.g., 'your-translator-command --flag value').":
        "要执行的命令行（可带参数，按 shell 规则拆分），例如：your-translator-command --flag value",
    "Optional postprocess command to run on CLI output (reads from stdin). Example: 'jq -r .result.translation'":
        "可选的输出后处理命令（从 stdin 读取），例如：jq -r .result.translation",
}


def patch_translation_yaml(sp: Path) -> None:
    """给 gui_translation.yaml 补上缺失的界面文案（幂等）。"""
    try:
        import yaml
    except ImportError:
        print("!! 没装 pyyaml，跳过界面文案补丁")
        return
    path = sp / "pdf2zh_next" / "gui_translation.yaml"
    if not path.exists():
        print(f"!! 找不到 {path}，跳过")
        return
    backup = path.with_suffix(path.suffix + ".orig-en.bak")
    if not backup.exists():
        shutil.copy2(path, backup)
        print(f"   备份 -> {backup.name}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    zh = data.setdefault("zh", {})
    en = data.setdefault("en", {})
    added = 0
    for src, cn in EXTRA_UI.items():
        if zh.get(src) != cn:
            zh[src] = cn
            added += 1
        if src not in en:
            en[src] = src
    if added:
        path.write_text(
            yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print(f"   界面文案补丁：新增/更新 {added} 条")
    else:
        print("   界面文案补丁：已是最新，无需改动")
    # 复查
    check = yaml.safe_load(path.read_text(encoding="utf-8"))["zh"]
    missing = [s for s in EXTRA_UI if check.get(s) != EXTRA_UI[s]]
    print(f"   复查：仍缺 {len(missing)} 条" + (f" -> {missing}" if missing else " ✓"))


def find_site_packages() -> Path:
    here = Path(__file__).resolve().parent
    for candidate in (here / ".venv" / "Lib" / "site-packages",
                      here / ".venv" / "lib" / "site-packages"):
        if candidate.is_dir():
            return candidate
    print("!! 找不到 .venv/Lib/site-packages，请把本脚本放在 pdf2zh 项目目录下运行")
    sys.exit(1)


def main() -> int:
    sp = find_site_packages()
    print(f"site-packages: {sp}")
    total_hit = 0
    total_desc = 0
    unknown: set[str] = set()
    used: set[str] = set()

    for parts in TARGETS:
        path = sp.joinpath(*parts)
        if not path.exists():
            print(f"!! 跳过（不存在）: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        backup = path.with_suffix(path.suffix + ".orig-en.bak")
        if not backup.exists():
            shutil.copy2(path, backup)
            print(f"   备份 -> {backup.name}")
        else:
            print(f"   备份已存在，保持不变: {backup.name}")

        for m in re.finditer(r'description="([^"]*)"', text):
            total_desc += 1
            s = m.group(1)
            # 已经有中文的（本次或之前跑过）不算问题
            if s not in CN and not any("\u4e00" <= c <= "\u9fff" for c in s):
                unknown.add(s)

        def repl(m: re.Match[str]) -> str:
            nonlocal total_hit
            en = m.group(1)
            zh = CN.get(en)
            if zh is None:
                return m.group(0)
            total_hit += 1
            used.add(en)
            return 'description="' + zh + '"'

        new_text = re.sub(r'description="([^"]*)"', repl, text)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            print(f"   已替换: {path.name}")
        else:
            print(f"   无需改动（可能已经是中文）: {path.name}")

    print()
    print(f"共扫描 description {total_desc} 处，成功替换 {total_hit} 处")
    if unknown:
        print(f"!! 有 {len(unknown)} 条英文描述不在对照表里（会继续显示英文）：")
        for s in sorted(unknown):
            print(f"     - {s}")
    unused = sorted(set(CN) - used - unknown)
    if unused and total_hit > 0:
        # 只在"这一轮真的改过东西"时才提示，避免二次运行时刷屏
        print(f"!! 对照表里有 {len(unused)} 条本轮没用上（上游可能已改文案）：")
        for s in unused[:15]:
            print(f"     - {s}")

    print()
    print("=== 界面框架文案（gui_translation.yaml）===")
    patch_translation_yaml(sp)

    print()
    print("完成。重启图形界面即可看到中文标签。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
