# -*- coding: utf-8 -*-
"""
通用 Markdown → HTML 财报报告转换器（自包含版）
==================================================
用法（在 skill 根目录或任意位置运行均可，脚本自行定位 examples/）：
    python scripts/md_to_html.py                      # 转换 examples/ 下所有 .md
    python scripts/md_to_html.py 海尔智家2020-2025财务分析.md   # 按文件名（在 examples/ 下找）
    python scripts/md_to_html.py /任意/路径/报告.md             # 绝对路径

行为：
- 自动给 markdown 生成的裸 <table> 加 class="fin-table"（手写 HTML 表格若已带 class 不受影响）
- 表格全部右对齐；数值表必须使用独立「单位」列；年份表头写完整「2025年」
- 内联 SVG：把 md 中 <img src="charts/xxx.svg"> 替换为实际 SVG 内容（在 md 同目录下查找）
- 主题色按报告名自动推断：含「海尔」→ 紫 #5B5FC7；含「TCL/中环」→ 深蓝 #1F3A5F；其他 → 默认紫
- 输出 HTML 与源 md 同目录
"""
import re
import sys
from pathlib import Path
from html.parser import HTMLParser
import markdown

SKILL_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = SKILL_ROOT / "examples"


def pick_accent(md_path):
    """按公司推断低饱和主题色，保持报告、表格和图表的同一视觉语义。"""
    name = Path(md_path).name
    if "TCL" in name or "中环" in name:
        return "#2E6270"   # TCL 中环：青灰蓝
    if "海尔" in name:
        return "#6D5A8D"   # 海尔智家：低饱和紫灰
    if "茅台" in name:
        return "#8D3D4A"   # 贵州茅台：酒红
    return "#6D5A8D"


def extract_title(html_body, fallback):
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html_body, re.DOTALL)
    if m:
        return re.sub(r"<[^>]+>", "", m.group(1)).strip()
    return fallback


# ---------- 表格列类型自动识别 ----------
TEXT_KEYWORDS = ["区域", "地区", "产品", "指标", "机构", "项目", "来源", "问题",
                 "判断", "验证", "核心", "摘要", "备注", "说明", "名称", "事项", "用途",
                 "文件", "命题", "证据"]
NUMERIC_KEYWORDS = ["亿元", "万元", "人", "占比", "增速", "同比", "净额", "费用", "比率",
                    "毛利率", "净利率", "营收", "收入", "利润", "现金流", "数额", "数值", "%"]
UNIT_KEYWORDS = ["单位", "口径"]
STATUS_KEYWORDS = ["期间", "年度", "年份", "主要来源", "验证结果", "状态"]


def classify_header(text):
    """用户硬约束：表格全部右对齐。列分类只保留兼容旧 HTML 的 class。"""
    return "num"


class TableClassifier(HTMLParser):
    """解析 fin-table，给每列加上 col-num 类。"""
    def __init__(self):
        super().__init__()
        self.in_target_table = False
        self.col_types = []
        self.col_idx = 0
        self.in_header = False
        self.output = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "table" and attrs_dict.get("class", "").startswith("fin-table"):
            self.in_target_table = True
            self.col_types = []
            self.col_idx = 0
            self.output.append(self._tag_str(tag, attrs))
            return
        if not self.in_target_table:
            self.output.append(self._tag_str(tag, attrs))
            return
        if tag in ("thead", "tbody", "tr"):
            if tag == "tr":
                self.col_idx = 0
            if tag == "thead":
                self.in_header = True
            self.output.append(self._tag_str(tag, attrs))
            return
        if tag in ("th", "td"):
            cls = attrs_dict.get("class", "")
            if self.in_header and tag == "th":
                self._pending_tag = (tag, attrs)
                self._pending_text = ""
                self.skip_depth = 1
            else:
                col_type = self.col_types[self.col_idx] if self.col_idx < len(self.col_types) else "num"
                attrs_dict["class"] = (cls + " col-" + col_type).strip()
                self.output.append(self._tag_str(tag, list(attrs_dict.items())))
                self.col_idx += 1
            return
        self.output.append(self._tag_str(tag, attrs))

    def handle_endtag(self, tag):
        if not self.in_target_table:
            self.output.append(f"</{tag}>")
            return
        if tag == "table":
            self.in_target_table = False
            self.output.append(f"</{tag}>")
            return
        if tag == "thead":
            self.in_header = False
            self.output.append(f"</{tag}>")
            return
        if tag in ("th", "td") and hasattr(self, "_pending_tag") and self._pending_tag[0] == tag:
            text_type = classify_header(self._pending_text)
            if text_type is None:
                text_type = "num"
            self.col_types.append(text_type)
            tag_name, attrs = self._pending_tag
            attrs_dict = dict(attrs)
            cls = attrs_dict.get("class", "")
            attrs_dict["class"] = (cls + " col-" + text_type).strip()
            self.output.append(self._tag_str(tag_name, list(attrs_dict.items())))
            self.output.append(self._pending_text)
            self.output.append(f"</{tag_name}>")
            self.col_idx += 1
            del self._pending_tag
            del self._pending_text
            self.skip_depth = 0
            return
        self.output.append(f"</{tag}>")

    def handle_data(self, data):
        if not self.in_target_table:
            self.output.append(data)
            return
        if hasattr(self, "_pending_tag"):
            self._pending_text += data
        else:
            self.output.append(data)

    def handle_entityref(self, name):
        self.handle_data(f"&{name};")

    def handle_charref(self, name):
        self.handle_data(f"&#{name};")

    def _tag_str(self, tag, attrs):
        if not attrs:
            return f"<{tag}>"
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs)
        return f"<{tag} {attr_str}>"


def classify_tables(html):
    pattern = re.compile(r'<table class="fin-table">.*?</table>', re.DOTALL)

    def repl(match):
        parser = TableClassifier()
        parser.feed(match.group(0))
        return "".join(parser.output)

    return pattern.sub(repl, html)


def reject_unit_rows(html):
    """Fail fast on legacy unit rows; professional numeric tables need a unit column."""
    for table_index, table in enumerate(re.findall(r'<table[^>]*class="fin-table"[^>]*>.*?</table>', html, re.DOTALL), 1):
        for row in re.findall(r"<tr[^>]*>.*?</tr>", table, re.DOTALL):
            first_td = re.search(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)
            first_text = re.sub(r"<[^>]+>", "", first_td.group(1)).strip() if first_td else ""
            if first_text == "单位":
                raise ValueError(
                    f"表{table_index} 使用了旧式单位行。请改为独立「单位」列，"
                    "例如：指标 | 单位 | 2023 | 2024 | 2025。"
                )
    return html


def format_five_questions(html):
    """Render each five-question check as a separate, readable block."""
    pattern = re.compile(r"<p>(?P<body>(?:(?!</p>).)*五问自检(?:(?!</p>).)*)</p>", re.DOTALL)

    def replace(match):
        body = match.group("body").replace("【五问自检】", "")
        markers = list(re.finditer(r'<strong>(事实|解释|质量|影响|反证)</strong>：?', body))
        if len(markers) < 5:
            return match.group(0)
        blocks = []
        for index, marker in enumerate(markers[:5]):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(body)
            label = marker.group(1)
            detail = re.sub(r"^[:：]\s*", "", body[marker.end():end].strip())
            blocks.append(
                f'<div class="five-question five-question-{index + 1}">'
                f'<span class="five-label">{label}</span><span class="five-detail">{detail}</span></div>'
            )
        return '<section class="five-questions" aria-label="五问自检">' + "".join(blocks) + "</section>"

    return pattern.sub(replace, html)


def _analysis_list(items, lead=""):
    """Render dense clauses as scan-friendly rows."""
    lead_html = f'<div class="analysis-lead">{lead}</div>' if lead.strip() else ""
    cleaned = [
        re.sub(r"^[；;，,\s]+|[；;，,\s]+$", "", item.strip())
        for item in items
    ]
    cleaned = [item for item in cleaned if item]
    rows = []
    for index, item in enumerate(cleaned, 1):
        marker = "—" if len(cleaned) == 1 else f"{index:02d}"
        rows.append(
            f'<div class="analysis-item"><span class="analysis-index">{marker}</span>'
            f'<span class="analysis-text">{item}</span></div>'
        )
    single = " analysis-list-single" if len(cleaned) == 1 else ""
    return f'<div class="analysis-list{single}">{lead_html}{"".join(rows)}</div>' if rows else ""


def format_numbered_lists(html):
    """Replace reset-to-1 markdown lists with stable numbered rows."""
    html = re.sub(
        r"(?:\s*<ol>\s*<li>.*?</li>\s*</ol>){2,}",
        lambda match: _analysis_list(re.findall(r"<ol>\s*<li>(.*?)</li>\s*</ol>", match.group(0), re.DOTALL)),
        html,
        flags=re.DOTALL,
    )
    return re.sub(
        r"<ol>\s*<li>(.*?)</li>\s*</ol>",
        lambda match: _analysis_list([match.group(1)]),
        html,
        flags=re.DOTALL,
    )


def format_inline_clauses(html):
    """Split circled or Chinese-ordinal clauses under facts, impacts and analysis."""
    marker = re.compile(r"(?:第一|第二|第三|第四|第五)\s*[、，,:：]|[①②③④⑤]")
    paragraph = re.compile(r"<p(?P<attrs>[^>]*)>(?P<body>.*?)</p>", re.DOTALL)

    def replace(match):
        attrs = match.group("attrs")
        body = match.group("body")
        markers = list(marker.finditer(body))
        if len(markers) < 2:
            return match.group(0)
        lead = body[:markers[0].start()].strip()
        chunks = []
        for index, current in enumerate(markers):
            end = markers[index + 1].start() if index + 1 < len(markers) else len(body)
            chunks.append(body[current.end():end])
        if "panel-" in attrs:
            rows = []
            for index, chunk in enumerate(chunks, 1):
                chunk = re.sub(r"^[；;，,\s]+|[；;，,\s]+$", "", chunk.strip())
                if chunk:
                    rows.append(
                        f'<span class="panel-list-item"><span class="panel-list-index">{index:02d}</span>'
                        f'<span>{chunk}</span></span>'
                    )
            lead_html = f'<span class="panel-list-lead">{lead}</span>' if lead else ""
            return f'<p{attrs}>{lead_html}<span class="panel-list">{"".join(rows)}</span></p>'
        return _analysis_list(chunks, lead)

    return paragraph.sub(replace, html)


def _panel_class(text):
    """Map the fixed judgment-panel labels to stable layout hooks."""
    labels = [
        ("核心判断", "panel-core"),
        ("公司状态", "panel-state"),
        ("主要矛盾", "panel-conflict"),
        ("盈利质量", "panel-profit"),
        ("现金 / 债务边界", "panel-cash"),
        ("最大不确定性", "panel-uncertainty"),
        ("接下来 12 个月必盯指标", "panel-watch"),
        ("反证指标", "panel-falsifier"),
    ]
    for label, cls in labels:
        if label in text:
            return cls
    return "panel-item"


def structure_report(html):
    """Turn the markdown stream into a report shell with a compact first screen."""
    html = re.sub(
        r"<p>\s*(<div class=\"chart-container\">.*?</div>)\s*</p>",
        r'<figure class="chart-figure">\1</figure>',
        html,
        flags=re.DOTALL,
    )
    h1_match = re.search(r"<h1[^>]*>.*?</h1>", html, flags=re.DOTALL)
    panel_match = re.search(
        r"<h3[^>]*>[^<]*判断面板.*?</h3>(.*?)(?=<hr\s*/?>)",
        html,
        flags=re.DOTALL,
    )
    if not h1_match or not panel_match:
        return f'<main class="report-shell"><article class="report-content">{html}</article></main>'

    title_html = h1_match.group(0)
    panel_content = panel_match.group(1)
    panel_paragraphs = []
    for paragraph in re.findall(r"<p[^>]*>.*?</p>", panel_content, flags=re.DOTALL):
        text = re.sub(r"<[^>]+>", "", paragraph)
        panel_paragraphs.append(
            re.sub(r"<p([^>]*)>", f'<p class="{_panel_class(text)}"\\1>', paragraph, count=1)
        )
    panel = (
        '<section class="judgment-panel" aria-label="判断面板">'
        '<div class="panel-heading"><span>判断面板</span><strong>先看结论，再看证据</strong></div>'
        '<div class="panel-grid">'
        + "".join(panel_paragraphs)
        + "</div></section>"
    )

    source_match = re.search(r"<blockquote>.*?</blockquote>", html, flags=re.DOTALL)
    source = ""
    if source_match:
        source = (
            '<details class="method-note"><summary>数据口径与来源</summary>'
            + source_match.group(0)
            + "</details>"
        )

    remainder = html.replace(title_html, "", 1)
    remainder = remainder.replace(panel_match.group(0), "", 1)
    if source_match:
        remainder = remainder.replace(source_match.group(0), "", 1)
    remainder = re.sub(r"^\s*<hr\s*/?>", "", remainder, count=1)
    remainder = re.sub(r"^\s*<hr\s*/?>", "", remainder, count=1)

    header = (
        '<header class="report-header">'
        '<div class="report-kicker">上市公司 · 财务诊断</div>'
        + title_html
        + '<div class="report-deck">以经营机制、现金质量与可证伪边界组织证据</div>'
        + "</header>"
    )
    return (
        '<main class="report-shell">'
        + header
        + panel
        + source
        + '<article class="report-content">'
        + remainder
        + "</article></main>"
    )


def md_to_html(md_path):
    md_path = Path(md_path)
    accent = pick_accent(md_path)
    md_text = md_path.read_text(encoding="utf-8")

    html_body = markdown.markdown(md_text, extensions=["tables"], output_format="html")
    html_body = re.sub(r"<style>.*?</style>", "", html_body, flags=re.DOTALL).strip()
    # 自动给 markdown 生成的裸表格加 fin-table class（手写带 class 的不受影响）
    html_body = html_body.replace("<table>", '<table class="fin-table">')

    def inline_svg(match):
        src = match.group(1)
        svg_path = md_path.parent / src
        if svg_path.exists():
            svg_content = svg_path.read_text(encoding="utf-8")
            svg_content = re.sub(r"<\?xml.*?\?>", "", svg_content).strip()
            title_match = re.search(r'<text class="chart-title"[^>]*>(.*?)</text>', svg_content, re.DOTALL)
            takeaway_match = re.search(r'<text class="chart-takeaway"[^>]*>(.*?)</text>', svg_content, re.DOTALL)
            unit_matches = re.findall(r'<text[^>]*(?:class="chart-unit"|>单位：).*?</text>', svg_content, re.DOTALL)
            unit_text = ""
            if unit_matches:
                unit_text = re.sub(r"<[^>]+>", "", unit_matches[0]).strip()
                svg_content = re.sub(r'<text[^>]*(?:class="chart-unit"|>单位：).*?</text>', "", svg_content, flags=re.DOTALL)
            chart_title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip() if title_match else ""
            chart_takeaway = re.sub(r"<[^>]+>", "", takeaway_match.group(1)).strip() if takeaway_match else ""
            if unit_text:
                unit_value = re.sub(r"^单位[:：]\s*", "", unit_text)
                chart_title = re.sub(
                    rf"[（(]\s*{re.escape(unit_value)}\s*[)）]\s*$",
                    "",
                    chart_title,
                )
            heading = (
                '<div class="chart-heading">'
                + (f'<h4>{chart_title}</h4>' if chart_title else "")
                + (f'<p>{chart_takeaway}</p>' if chart_takeaway else "")
                + (f'<span class="chart-unit">{unit_text}</span>' if unit_text else "")
                + '</div>'
            ) if chart_title or chart_takeaway else ""
            return f'<div class="chart-container">{heading}{svg_content}</div>'
        return match.group(0)

    html_body = re.sub(r'<img[^>]+src="([^"]+\.svg)"[^>]*/?>', inline_svg, html_body)
    html_body = format_five_questions(html_body)
    html_body = format_numbered_lists(html_body)
    html_body = classify_tables(html_body)
    html_body = reject_unit_rows(html_body)
    html_body = structure_report(html_body)
    html_body = format_inline_clauses(html_body)

    title = extract_title(html_body, md_path.stem)

    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
:root {{
  --ink: #302D29;
  --text: #49443E;
  --muted: #716A62;
  --line: #E4DED5;
  --paper: #FFFDF9;
  --canvas: #F1EFEA;
  --soft: #F7F3EC;
  --risk: #B33A32;
  --accent: {accent};
}}
* {{ box-sizing: border-box; }}
html {{ background: var(--canvas); }}
body {{
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.68;
  color: var(--text);
  background: var(--canvas);
}}
.report-shell {{
  width: min(1180px, 100%);
  min-height: 100vh;
  margin: 0 auto;
  background: var(--paper);
}}
.report-header {{ padding: 42px 64px 26px; border-bottom: 1px solid var(--line); }}
.report-kicker {{ color: var(--accent); font-size: 12px; font-weight: 700; letter-spacing: 0; text-transform: uppercase; }}
h1, h2, h3, h4 {{ text-align: left !important; text-indent: 0 !important; margin-left: 0 !important; }}
h1 {{ max-width: 900px; margin: 8px 0 0; color: var(--ink); font-size: 34px; line-height: 1.2; font-weight: 750; }}
.report-deck {{ margin-top: 10px; color: var(--muted); font-size: 14px; }}
.judgment-panel {{ margin: 0; padding: 26px 64px 30px; color: var(--text); background: #F4EBDD; border-bottom: 1px solid #DCCEBB; }}
.panel-heading {{ display: flex; align-items: baseline; gap: 14px; margin-bottom: 14px; color: var(--muted); font-size: 12px; }}
.panel-heading span {{ color: var(--accent); font-weight: 750; }}
.panel-heading strong {{ color: var(--ink); font-size: 19px; font-weight: 680; }}
.panel-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }}
.panel-grid p {{ margin: 0; padding: 14px 16px; border: 1px solid #E4D8C8; border-radius: 6px; color: var(--text); background: rgba(255,253,249,.86); font-size: 13px; line-height: 1.62; }}
.panel-grid p strong {{ color: var(--ink); }}
.panel-grid .panel-core, .panel-grid .panel-falsifier {{ grid-column: 1 / -1; }}
.panel-grid .panel-core {{ padding: 17px 18px; border-left: 4px solid var(--accent); color: var(--ink); font-size: 17px; line-height: 1.62; }}
.panel-grid .panel-core strong {{ display: block; margin-bottom: 5px; color: var(--ink); }}
.panel-grid .panel-falsifier {{ border-left: 4px solid var(--risk); }}
.panel-list-lead {{ display: block; margin-bottom: 6px; }}
.panel-list {{ display: grid; gap: 7px; }}
.panel-list-item {{ display: grid; grid-template-columns: 24px minmax(0, 1fr); gap: 8px; }}
.panel-list-index {{ color: var(--accent); font-size: 10px; font-weight: 800; line-height: 1.8; }}
.method-note {{ margin: 0; padding: 14px 64px; border-bottom: 1px solid var(--line); background: var(--soft); color: var(--muted); font-size: 12px; }}
.method-note summary {{ cursor: pointer; color: var(--text); font-weight: 650; }}
.method-note blockquote {{ margin: 12px 0 0; padding: 0 0 0 14px; border-left: 2px solid var(--line); background: transparent; }}
.report-content {{ padding: 24px 64px 80px; }}
.report-content > p, .report-content > ul, .report-content > ol, .report-content > blockquote, .report-content > h3, .five-questions {{ width: 100%; max-width: 1040px; }}
.report-content > p {{ margin: 14px 0; }}
.report-content strong {{ color: #2E2925; font-weight: 760; }}
.report-content u {{ text-decoration-color: var(--accent); text-decoration-thickness: 2px; text-underline-offset: 3px; }}
.report-content .key-risk, .report-content strong.key-risk {{ color: var(--risk); }}
.report-content > h2 {{ position: relative; max-width: 1040px; margin: 62px 0 22px; padding: 0 0 0 16px; color: var(--ink); font-size: 24px; line-height: 1.3; }}
.report-content > h2::before {{ content: ""; position: absolute; left: 0; top: 3px; width: 4px; height: 1.1em; border-radius: 2px; background: var(--accent); }}
.report-content > h2:first-child {{ margin-top: 8px; }}
.report-content > h3 {{ margin: 30px 0 10px; color: var(--ink); font-size: 17px; }}
.report-content > hr {{ display: none; }}
.five-questions {{ margin: 24px 0 34px; padding: 4px 0 4px 18px; border-left: 3px solid var(--accent); }}
.five-question {{ display: grid; grid-template-columns: 54px minmax(0, 1fr); gap: 14px; padding: 14px 0; border-bottom: 1px solid #F0EBE3; }}
.five-question:last-child {{ border-bottom: 0; }}
.five-label {{ align-self: start; color: var(--accent); font-size: 13px; font-weight: 780; line-height: 1.8; }}
.five-question-5 .five-label {{ color: var(--risk); }}
.five-detail {{ color: var(--text); font-size: 15px; line-height: 1.82; }}
.five-question-3 .five-detail, .five-question-4 .five-detail, .five-question-5 .five-detail {{ font-weight: 560; }}
.five-question-5 .five-detail {{ text-decoration: underline; text-decoration-color: rgba(179,58,50,.45); text-underline-offset: 3px; }}
.chart-figure {{ max-width: 1040px; margin: 42px 0 28px; padding: 4px 0 10px; break-inside: avoid; }}
.chart-container {{ width: 100%; margin: 0; text-align: center; overflow-x: auto; }}
.chart-heading {{ width: 100%; margin: 0 0 16px; padding: 0 4px; text-align: left; }}
.chart-heading h4 {{ margin: 0; color: var(--ink); font-size: 18px; line-height: 1.35; font-weight: 720; }}
.chart-heading p {{ margin: 6px 0 0; color: var(--muted); font-size: 13px; line-height: 1.55; }}
.chart-heading .chart-unit {{ display: block; margin-top: 8px; color: var(--accent); font-size: 12px; font-weight: 650; }}
.chart-container svg {{ display: block; width: 100%; height: auto; margin: 0 auto; font-family: inherit; }}
.chart-container svg > rect:first-child {{ fill: var(--paper); }}
.chart-figure svg .chart-title, .chart-figure svg .chart-takeaway {{ visibility: hidden; }}
.chart-figure svg .chart-unit {{ visibility: hidden; }}
.analysis-list {{ width: 100%; max-width: 1040px; margin: 18px 0 24px; padding: 4px 0 4px 16px; border-left: 2px solid var(--line); }}
.analysis-lead {{ margin: 0 0 6px; color: var(--muted); font-size: 13px; font-weight: 650; }}
.analysis-item {{ display: grid; grid-template-columns: 30px minmax(0, 1fr); gap: 10px; padding: 9px 0; border-bottom: 1px solid #F2EEE8; }}
.analysis-item:last-child {{ border-bottom: 0; }}
.analysis-index {{ color: var(--accent); font-size: 11px; font-weight: 780; line-height: 1.8; }}
.analysis-text {{ color: var(--text); font-size: 14px; line-height: 1.75; }}
.analysis-text strong {{ color: var(--ink); }}
p.fin-table.note, p.data-source {{ max-width: 1040px; margin: 0 0 24px; padding: 7px 0; border-bottom: 1px solid var(--line); color: var(--muted); font-size: 12px; line-height: 1.45; }}
.fin-table {{ width: 100%; border-collapse: collapse; margin: 20px 0 6px; font-size: 12.5px; break-inside: avoid; }}
.fin-table th {{ background-color: {accent}; color: #FFFFFF; padding: 10px 12px; font-weight: 650; border: 1px solid #D1D5DB; white-space: nowrap; }}
.fin-table td {{ padding: 8px 12px; border: 1px solid #E1E5EA; color: var(--text); background-color: #FFFFFF; vertical-align: middle; }}
.fin-table tr:nth-child(even) td {{ background-color: #FAFBFC; }}
.fin-table th, .fin-table td {{ text-align: right; }}
blockquote {{ margin: 16px 0; padding: 8px 16px; border-left: 3px solid var(--line); color: var(--muted); background: var(--soft); font-size: 13px; }}
@media (max-width: 760px) {{
  .report-header, .judgment-panel, .method-note, .report-content {{ padding-left: 18px; padding-right: 18px; }}
  .report-header {{ padding-top: 28px; }}
  h1 {{ font-size: 27px; }}
  .panel-heading {{ display: block; }}
  .panel-heading strong {{ display: block; margin-top: 4px; }}
  .panel-grid {{ grid-template-columns: 1fr; }}
  .panel-grid .panel-core, .panel-grid .panel-falsifier {{ grid-column: auto; }}
  .panel-grid .panel-core {{ font-size: 16px; }}
  .report-content {{ padding-top: 14px; }}
  .report-content > h2 {{ margin-top: 46px; font-size: 21px; }}
  .five-question {{ grid-template-columns: 44px minmax(0, 1fr); gap: 10px; }}
  .five-detail {{ font-size: 14px; line-height: 1.8; }}
  .fin-table {{ display: block; overflow-x: auto; white-space: nowrap; }}
  .chart-figure {{ margin-left: -2px; margin-right: -2px; }}
  .chart-container svg {{ width: 640px; max-width: none; min-height: 0; }}
}}
@media print {{
  @page {{ size: A4; margin: 14mm 12mm; }}
  html, body {{ background: #FFFFFF; }}
  .report-shell {{ width: 100%; }}
  .report-header {{ padding: 0 0 14px; }}
  .judgment-panel {{ padding: 16px 18px; break-inside: avoid; }}
  .method-note {{ padding: 8px 0; }}
  .report-content {{ padding: 12px 0 30px; }}
  .fin-table th, .fin-table td {{ font-size: 10.5px; }}
  .chart-container svg {{ min-height: 0; }}
  h2, h3 {{ break-after: avoid; }}
  .fin-table, .chart-figure {{ break-inside: avoid; }}
}}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""
    html_path = md_path.with_suffix(".html")
    html_path.write_text(full_html, encoding="utf-8")
    print(f"HTML report generated: {html_path}")


def main():
    args = sys.argv[1:]
    if args:
        targets = [Path(a) if Path(a).is_absolute() else EXAMPLES_DIR / a for a in args]
    else:
        targets = sorted(EXAMPLES_DIR.glob("*.md"))
    if not targets:
        print(f"No .md files found in {EXAMPLES_DIR}")
        sys.exit(1)
    for t in targets:
        if not t.exists():
            print(f"[SKIP] not found: {t}")
            continue
        md_to_html(t)


if __name__ == "__main__":
    main()
