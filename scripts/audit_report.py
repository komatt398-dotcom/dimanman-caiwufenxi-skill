#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迪慢慢财报分析 Skill —— 报告质量门禁 (audit_report.py)

每份 HTML 出完后运行本脚本自检，修复所有 FAIL 后才能交付。
用法:
    python audit_report.py <报告.html>
    python audit_report.py  (无参数时扫描同目录/上级 docs 下的 *.html)

检查项 (v3.1.0 话术与图表质量版):
    1. 首屏判断面板: 第一个 h2 之前必须出现「核心判断」「主要矛盾」「反证/推翻」
    2. 单位列: 数值表必须使用「单位」列；禁止使用 unit-row 单位行。文字表(含 non-numeric 类
       或数字单元格占比 < 25%) 自动豁免，避免误杀管理层判断/风险清单等文字表
    3. 图表悬停: 仅校验带 class="data-point" 的真实数据点是否含 <title>；
       背景框/图例色块/辅助线(不带 data-point)不计入，杜绝误杀
    4. 禁无意义图例: 不得出现单一系列「数值」图例文字
    5. 图表诊断性: 每个 SVG 必须有 diagnostic-chart / chart-title / chart-takeaway
    6. 数据来源: 按每个 <table>/<svg> 结束后窗口内是否含来源标注逐元素检查
       (不再只数全文频次)，窗口 = 到下一个 block / <h2> / 1200 字符取最小
    7. 禁 [待补充]: 全文不得出现「待补充」
    8. 禁粗糙话术: 禁止口语化/情绪化/网感表达
    9. 表格对齐契约: 所有表格单元格右对齐；年份表头必须写完整「2025年」；禁止「读法」
    10. v3.0 起五问是 analysis_bundle 后台审计门；HTML 不强制显性五问。
    11. 首屏截图(可选): 提示用 Playwright 人工/自动核对
"""

import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BANNED_PHRASES = [
    "年报复述机",
    "废话",
    "真金",
    "堆出来",
    "糊弄",
    "我错了",
    "能跑通",
    "跑不通",
    "不大行",
    "亏损王",
    "卖一片亏一片",
    "杀疯了",
    "爆雷",
    "躺赢",
    "血亏",
    "崩了",
    "这里必须",
    "这一段的管理含义",
    "积极的一面",
    "谨慎的一面",
    "从管理层视角看",
    "接下来最该做的不是",
    "收缩式提质",
    "非内生扩张",
    "增长换挡期",
    "剪刀差扩大",
    "经营现金流下滑，是扰动还是趋势",
    "经营现金流变动桥",
    "行业出清期",
    "优先行动卡",
    "现金转换驾驶舱",
    "语录墙",
]

BANNED_CHART_LABELS = [
    "收入+",
    "收入 +",
    "净利+",
    "净利 +",
]


def _strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def _is_numeric_cell(text: str) -> bool:
    """判断单元格是否为数字单元格（含千分符/小数/负号/破折号/百分号）。"""
    t = text.strip()
    if not t:
        return False
    # 纯数字/小数/负号/破折号(—)/千分符/百分号，或单纯「—」缺失标记
    if re.match(r"^[\d,.\-\u2014\u2013]+%?$", t):
        return True
    return False


def _extract_elements(svg: str, tag: str, cls: str):
    """提取 svg 中所有带 cls 类的 tag 元素完整片段（含子元素如 <title>）。"""
    out = []
    for m in re.finditer(rf"<{tag}\b", svg):
        start = m.start()
        gt = svg.find(">", start)
        if gt == -1:
            continue
        open_tag = svg[start:gt + 1]
        # 精确匹配 class 值中的 data-point，避免 not-data-point 误匹配
        if not re.search(rf"(?<![-\w]){re.escape(cls)}(?![-\w])", open_tag):
            continue
        if svg[gt - 1] == "/":  # 自闭合，无子元素
            out.append(open_tag)
        else:
            em = re.search(rf"</{tag}>", svg[gt + 1:])
            if em:
                out.append(svg[start:gt + 1 + em.end()])
            else:
                out.append(open_tag)
    return out


def check_panel(content: str):
    """首屏判断面板。取 <body> 到第一个 <h2> 之前的内容。"""
    m = re.search(r"<body[^>]*>(.*?)<h2", content, re.S | re.I)
    head = m.group(1) if m else content[:4000]
    text = _strip_tags(head)
    missing = []
    if "核心判断" not in text:
        missing.append("核心判断")
    if "主要矛盾" not in text:
        missing.append("主要矛盾")
    if not ("反证" in text or "推翻" in text):
        missing.append("反证指标(什么情况会推翻本报告结论)")
    return missing


def check_unit_rows(content: str):
    tables = re.findall(r'<table[^>]*class="fin-table"[^>]*>.*?</table>', content, re.S)
    issues = []
    skipped = 0
    for i, t in enumerate(tables, 1):
        # 显式豁免：文字表
        if "non-numeric" in t:
            skipped += 1
            continue
        if "unit-row" in t:
            issues.append(f"表{i} 使用 unit-row 单位行；专业报告必须改为独立「单位」列")
            continue
        has_unit_col = bool(re.search(r"<th[^>]*>\s*单位\s*</th>", t))
        if has_unit_col:
            continue
        # 无单位列：按数字单元格占比判断是否为文字表
        cells = re.findall(r"<td[^>]*>(.*?)</td>", t, re.S)
        if not cells:
            continue
        numeric = sum(1 for c in cells if _is_numeric_cell(_strip_tags(c)))
        ratio = numeric / len(cells)
        if ratio < 0.25:
            skipped += 1  # 文字表，豁免
            continue
        issues.append(f"表{i} 数值表但缺单位列 (数字单元格占比 {ratio:.0%})")
    return issues, len(tables), skipped


def check_table_header_wording(content: str):
    issues = []
    for i, table in enumerate(re.findall(r'<table[^>]*class="fin-table"[^>]*>.*?</table>', content, re.S), 1):
        headers = [_strip_tags(h).strip() for h in re.findall(r"<th[^>]*>(.*?)</th>", table, re.S)]
        if "读法" in headers:
            issues.append(f"表{i}: 表头禁止使用「读法」，改为「说明」或「解读」")
        for h in headers:
            if re.fullmatch(r"20\d{2}", h):
                issues.append(f"表{i}: 年份表头「{h}」不完整，应写为「{h}年」")
    return issues


def check_titles(content: str):
    svgs = re.findall(r"<svg.*?</svg>", content, re.S)
    issues = []
    for i, svg in enumerate(svgs, 1):
        elements = []
        for tag in ("rect", "circle", "polygon", "polyline"):
            elements += _extract_elements(svg, tag, "data-point")
        n = len(elements)
        if n == 0:
            issues.append(
                f"svg{i}: 未发现带 class=\"data-point\" 的真实数据点 "
                f"(背景框/图例/辅助线不应计入；真实数据点须加 class=\"data-point\" 且含 <title>)"
            )
            continue
        missing = sum(1 for e in elements if "<title>" not in e)
        if missing:
            issues.append(f"svg{i}: {n} 个数据点中 {missing} 个缺少 <title> 悬停提示")
    return issues, len(svgs)


def check_legend_value(content: str):
    if re.search(r"<text[^>]*>\s*数值\s*</text>", content):
        return ["发现无意义「数值」图例文字 (单一系列图不应显示「数值」图例)"]
    return []


def check_chart_diagnostic(content: str):
    svgs = re.findall(r"<svg.*?</svg>", content, re.S)
    issues = []
    for i, svg in enumerate(svgs, 1):
        if "diagnostic-chart" not in svg:
            issues.append(f"svg{i}: 缺 class=\"diagnostic-chart\"")
        if "chart-title" not in svg:
            issues.append(f"svg{i}: 缺 chart-title")
        if "chart-takeaway" not in svg:
            issues.append(f"svg{i}: 缺 chart-takeaway（一句话图表结论）")
    return issues, len(svgs)


def check_layout(content: str):
    """Check the report-shell contract created by md_to_html.py."""
    issues = []
    required = {
        'report-shell': '报告外壳',
        'report-header': '报告头部',
        'judgment-panel': '判断面板',
        'chart-figure': '图表 figure',
    }
    for cls, label in required.items():
        if f'class="{cls}"' not in content:
            issues.append(f'缺少 {label} class="{cls}"')
    panel_pos = content.find('class="judgment-panel"')
    first_h2 = content.find('<h2')
    if panel_pos == -1 or (first_h2 != -1 and panel_pos > first_h2):
        issues.append('判断面板未排在正文章节之前')
    if '@media (max-width: 760px)' not in content:
        issues.append('缺少移动端断点')
    if '@media print' not in content or 'break-inside: avoid' not in content:
        issues.append('缺少打印分页保护')
    return issues


def check_chart_visual(content: str):
    """Catch common visual regressions without judging brand colors."""
    svgs = re.findall(r"<svg.*?</svg>", content, re.S | re.I)
    issues = []
    figure_count = content.count('class="chart-figure"')
    if svgs and figure_count < len(svgs):
        issues.append(f'图表 figure 数量不足：{figure_count} < {len(svgs)}')
    desktop_svg_css = re.search(r'\.chart-container\s+svg\s*\{(?P<body>[^}]*)\}', content, re.S)
    if desktop_svg_css and re.search(r'min-height\s*:', desktop_svg_css.group('body')):
        issues.append('桌面端 .chart-container svg 不得设置 min-height；应由 SVG viewBox/height 控制紧凑度')
    for i, svg in enumerate(svgs, 1):
        fills = set(re.findall(r'class="data-point"[^>]*\bfill="([#\w]+)"', svg))
        if len(fills) > 4:
            issues.append(f'svg{i}: 数据点颜色超过 4 种（{len(fills)} 种），可能形成彩虹图')
        size = re.search(r'width="(\d+)" height="(\d+)"', svg)
        if size:
            width, height = map(int, size.groups())
            complex_chart = bool(re.search(r"<polyline|bridge-connector|<circle", svg))
            min_height = 260 if complex_chart else 180
            if width < 560 or height < min_height:
                issues.append(f'svg{i}: 画布过小（{width}x{height}），移动端与打印易失真')
    return issues, len(svgs)


def check_reading_rhythm(content: str):
    """Enforce the layout decisions introduced after visual review."""
    issues = []
    five_sections = re.findall(r'<section class="five-questions".*?</section>', content, re.S)
    for i, section in enumerate(five_sections, 1):
        if section.count('class="five-question ') != 5:
            issues.append(f'五问#{i}: 未拆成 5 个独立段落')
    if 'class="chart-heading"' not in content:
        issues.append('图表标题未移到 SVG 上方的 chart-heading')
    if '.chart-figure svg .chart-title' not in content or 'visibility: hidden' not in content:
        issues.append('SVG 内部标题未隐藏，可能与外部标题重复')
    if 'background: #F4EBDD' not in content:
        issues.append('判断面板未使用米白色主题')
    if 'grid-template-columns: repeat(2' not in content:
        issues.append('判断面板未使用两列呼吸布局')
    if re.search(r'\.report-content > h2 \{[^}]*border-top:', content, re.S):
        issues.append('章节标题仍使用贯穿内容列的上分隔线')
    chart_css = re.search(r'\.chart-figure \{(?P<body>[^}]*)\}', content, re.S)
    if chart_css and ('border-top:' in chart_css.group('body') or 'border-bottom:' in chart_css.group('body')):
        issues.append('图表仍使用上下分隔线')
    if five_sections:
        five_css = re.search(r'\.five-detail \{(?P<body>[^}]*)\}', content, re.S)
        if not five_css or not re.search(r'font-size:\s*15px', five_css.group('body')):
            issues.append('五问正文桌面端字号必须为 15px')
    if '<span class="chart-unit">单位：' not in content:
        issues.append('图表单位未移到 HTML 图题区')
    for i, svg in enumerate(re.findall(r'<svg.*?</svg>', content, re.S), 1):
        visible = re.sub(r'<text class="chart-(?:title|takeaway)".*?</text>', '', svg, flags=re.S)
        if '单位：' in visible:
            issues.append(f'svg{i}: 单位仍在 SVG 绘图区，可能被裁切或重复')
    if '<ol>' in content:
        issues.append('报告仍含有序列表，可能出现重复 1.；应转为 analysis-list')
    return issues, len(five_sections)


def check_diagnostic_semantics(content: str):
    issues = []
    for figure in re.findall(r'<figure class="chart-figure">.*?</figure>', content, re.S):
        text = _strip_tags(figure)
        svg_m = re.search(r'<svg.*?</svg>', figure, re.S)
        if not svg_m:
            continue
        svg = svg_m.group(0)
        if '费用率结构' in text:
            if '<polyline' not in svg or re.search(r'class="data-point"[^>]*<rect', svg):
                issues.append('费用率结构图必须使用折线趋势，不得使用分组柱')
        if '净利率变化桥' in text or '现金流桥' in text:
            if 'class="bridge-connector"' not in svg:
                issues.append(f'{text[:18]}: 缺少桥接线')
        if '现金流桥' in text:
            terminal_labels = re.findall(r'<title>现金净变动：', svg)
            if len(terminal_labels) != 1:
                issues.append(f'现金流桥终值应只出现一次，当前 {len(terminal_labels)} 次')
        if '债务压力图' in text:
            visible_risk_text = re.findall(r'<text[^>]*(?:fill="#B0413E"|font-weight="600")[^>]*>[^<]{18,}</text>', svg)
            if visible_risk_text:
                issues.append('债务压力图内存在长段诊断文字，应移到正文或 takeaway')
        if ('客户' in text and '供应商' in text and '<rect' in svg
                and not re.search(r'客户[^<]{0,20}</text>.*供应商|供应商[^<]{0,20}</text>.*客户', svg, re.S)):
            issues.append('客户销售指标和供应商采购指标不得混在同一张未分组条形图中；供应商不是客户')
        if '收入路径和集中度' in text and '供应商' in text:
            issues.append('收入路径图不得混入供应商采购集中度，应拆为收入结构/客户集中度/供应链约束')
    return issues


def check_svg_compactness(content: str):
    issues = []
    for i, svg in enumerate(re.findall(r"<svg\b.*?</svg>", content, re.S | re.I), 1):
        vb = re.search(r'viewBox="[^"]*?\s+([\d.]+)\s+([\d.]+)"', svg)
        if not vb:
            continue
        height = float(vb.group(2))
        visible = re.sub(r'<text class="chart-(?:title|takeaway)".*?</text>', '', svg, flags=re.S)
        min_vals = []
        max_vals = []
        for tag in re.finditer(r'<(text|rect|circle|line|polyline|polygon)\b([^>]*)>', visible):
            name, attrs = tag.group(1), tag.group(2)
            if 'x="-9999"' in attrs or 'y="-9999"' in attrs:
                continue

            def f(attr):
                m = re.search(attr + r'="([\d.\-]+)"', attrs)
                return float(m.group(1)) if m else None

            if name == "text":
                y = f("y")
                if y is not None:
                    min_vals.append(y - 12)
                    max_vals.append(y + 14)
            elif name == "rect":
                y, h = f("y"), f("height")
                if y is not None:
                    min_vals.append(y)
                    max_vals.append(y + (h or 0))
            elif name == "circle":
                cy, rr = f("cy"), f("r")
                if cy is not None:
                    r = rr or 0
                    min_vals.append(cy - r)
                    max_vals.append(cy + r)
            elif name == "line":
                for attr in ("y1", "y2"):
                    y = f(attr)
                    if y is not None:
                        min_vals.append(y)
                        max_vals.append(y)
            elif name == "polyline":
                m = re.search(r'points="([^"]+)"', attrs)
                if m:
                    for pair in re.split(r"\s+", m.group(1).strip()):
                        if "," in pair:
                            try:
                                y = float(pair.split(",")[1])
                                min_vals.append(y)
                                max_vals.append(y)
                            except ValueError:
                                pass
        if min_vals and max_vals:
            top_gap = min(min_vals)
            bottom_gap = height - max(max_vals)
            if top_gap > 56:
                issues.append(f"svg{i}: 顶部空白 {top_gap:.0f}px，需收紧 viewBox/height 或调整绘图区")
            if bottom_gap > 36:
                issues.append(f"svg{i}: 底部空白 {bottom_gap:.0f}px，需收紧 viewBox/height")
    return issues


def _text_width_estimate(text: str, font_size: float) -> float:
    width = 0.0
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            width += font_size
        elif ch.isdigit() or ch in ".,-%/":
            width += font_size * 0.55
        else:
            width += font_size * 0.65
    return max(width, font_size)


def check_svg_text_collisions(content: str):
    issues = []
    for i, svg in enumerate(re.findall(r"<svg\b.*?</svg>", content, re.S | re.I), 1):
        labels = []
        for m in re.finditer(r"<text\b([^>]*)>(.*?)</text>", svg, re.S | re.I):
            attrs, raw_text = m.group(1), m.group(2)
            if 'x="-9999"' in attrs or 'y="-9999"' in attrs:
                continue
            text = _strip_tags(raw_text).strip()
            if not text:
                continue
            x_m = re.search(r'\bx="([\d.\-]+)"', attrs)
            y_m = re.search(r'\by="([\d.\-]+)"', attrs)
            if not x_m or not y_m:
                continue
            x = float(x_m.group(1))
            y = float(y_m.group(1))
            fs_m = re.search(r'font-size="([\d.]+)"', attrs)
            fs = float(fs_m.group(1)) if fs_m else 12.0
            anchor_m = re.search(r'text-anchor="([^"]+)"', attrs)
            anchor = anchor_m.group(1) if anchor_m else "start"
            w = _text_width_estimate(text, fs)
            if anchor == "middle":
                x1, x2 = x - w / 2, x + w / 2
            elif anchor == "end":
                x1, x2 = x - w, x
            else:
                x1, x2 = x, x + w
            y1, y2 = y - fs, y + fs * 0.35
            labels.append((text, x1, y1, x2, y2))
        for a_idx in range(len(labels)):
            a = labels[a_idx]
            for b in labels[a_idx + 1:]:
                overlap_x = min(a[3], b[3]) - max(a[1], b[1])
                overlap_y = min(a[4], b[4]) - max(a[2], b[2])
                if overlap_x > 2 and overlap_y > 2:
                    issues.append(f"svg{i}: 文本标签可能重叠: 「{a[0]}」/「{b[0]}」")
                    break
            if any(msg.startswith(f"svg{i}:") for msg in issues):
                break
    return issues


def check_source(content: str):
    """按每个 <table>/<svg> 结束后窗口内是否含来源标注逐元素检查。"""
    blocks = []
    for m in re.finditer(r"<table\b.*?</table>", content, re.S | re.I):
        blocks.append(("table", m.start(), m.end()))
    for m in re.finditer(r"<svg\b.*?</svg>", content, re.S | re.I):
        blocks.append(("svg", m.start(), m.end()))
    blocks.sort(key=lambda x: x[1])
    src_kw = re.compile(r"数据来源|资料来源|来源[:：]|注[:：]|口径[:：]")
    issues = []
    n = len(blocks)
    for idx, (kind, _start, end) in enumerate(blocks):
        candidates = [end + 1200]
        if idx + 1 < n:
            candidates.append(blocks[idx + 1][1])
        h2 = re.search(r"<h2", content[end:])
        if h2:
            candidates.append(end + h2.start())
        stop = min(candidates)
        window = content[end:stop]
        if not src_kw.search(window):
            issues.append(f"{kind}#{idx + 1} 其后 {stop - end} 字符内未见数据来源标注")
    return issues, n


def check_no_todo(content: str):
    if "待补充" in content:
        return ["出现「待补充」字样 (应以「—」标注缺失，不写待补充)"]
    return []


def check_banned_phrases(content: str):
    text = _strip_tags(content)
    hits = []
    for phrase in BANNED_PHRASES:
        if phrase in text:
            hits.append(phrase)
    for label in BANNED_CHART_LABELS:
        if label in text:
            hits.append(f"图表标签口径不完整: {label}")
    return hits


def check_alignment(content: str):
    """用户硬约束：表格全部右对齐，避免随机对齐。"""
    issues = []
    css_m = re.search(r"<style[^>]*>(.*?)</style>", content, re.S | re.I)
    css = css_m.group(1) if css_m else content
    if not re.search(r'\.fin-table\s+th\s*,\s*\.fin-table\s+td\s*\{[^}]*text-align:\s*right', css, re.S):
        issues.append("缺少所有表格单元格右对齐规则: .fin-table th,.fin-table td{text-align:right}")
    for selector in (r"\.fin-table[^{}]*(?:th|td)[^{}]*", r"\.statement-table[^{}]*(?:th|td)[^{}]*", r"\.non-numeric[^{}]*(?:th|td)[^{}]*"):
        for m in re.finditer(selector + r"\{(?P<body>[^}]*)\}", css, re.S):
            body = m.group("body")
            if re.search(r"text-align:\s*(left|center)", body):
                snippet = m.group(0)[:100].replace("\n", " ")
                issues.append(f"表格存在非右对齐覆盖规则: {snippet}")
    return issues


EXEMPT_H2 = ["判断", "面板", "核心判断", "目录", "摘要", "封面", "前言", "说明", "导读"]
FIVE_Q = ["事实", "解释", "质量", "影响", "反证"]


def check_five_q(content: str):
    """按 <h2> 章节切片，非豁免章节须含五问标记。"""
    parts = re.split(r"<h2[^>]*>", content)
    chapter_issues = []
    for idx, part in enumerate(parts[1:], 1):
        title_m = re.match(r"(.*?)(?:<|\n)", part, re.S)
        title = _strip_tags(title_m.group(1)).strip() if title_m else f"章节{idx}"
        if any(k in title for k in EXEMPT_H2):
            continue
        missing = [w for w in FIVE_Q if w not in part]
        if missing:
            chapter_issues.append(f"「{title[:24]}」缺五问标记: {', '.join(missing)}")
    return chapter_issues


def audit(html_path: str):
    with open(html_path, "r", encoding="utf-8") as f:
        content = f.read()

    results = []  # (name, passed, detail)

    # 1 首屏判断面板
    miss = check_panel(content)
    results.append(("首屏判断面板(核心判断/主要矛盾/反证)", not miss,
                    "OK" if not miss else f"缺失: {', '.join(miss)}"))

    # 2 单位列
    issues, n_tables, skipped = check_unit_rows(content)
    results.append(("数值表单位列", not issues,
                    f"共 {n_tables} 张表(豁免文字表 {skipped} 张), "
                    + ("OK" if not issues else "; ".join(issues))))

    # 2b 表头措辞
    issues = check_table_header_wording(content)
    results.append(("表头字段完整性(年份/说明)", not issues,
                    "OK" if not issues else "; ".join(issues)))

    # 3 图表悬停
    issues, n_svg = check_titles(content)
    results.append(("SVG 数据点(data-point) <title> 悬停", not issues,
                    f"共 {n_svg} 个 svg, " + ("OK" if not issues else "; ".join(issues))))

    # 4 无意义图例
    issues = check_legend_value(content)
    results.append(("禁无意义「数值」图例", not issues,
                    "OK" if not issues else "; ".join(issues)))

    # 5 图表诊断性
    issues, n_svg = check_chart_diagnostic(content)
    results.append(("图表诊断性(chart-title/chart-takeaway)", not issues,
                    f"共 {n_svg} 个 svg, " + ("OK" if not issues else "; ".join(issues))))

    # 6 报告布局
    issues = check_layout(content)
    results.append(("报告布局(report-shell/judgment-panel/chart-figure)", not issues,
                    "OK" if not issues else "; ".join(issues)))

    # 7 图表视觉回归
    issues, n_svg = check_chart_visual(content)
    results.append(("图表视觉(颜色数量/画布尺寸/figure)", not issues,
                    f"共 {n_svg} 个 svg, " + ("OK" if not issues else "; ".join(issues))))

    # 7b 图表紧凑度
    issues = check_svg_compactness(content)
    results.append(("图表紧凑度(底部空白)", not issues,
                    "OK" if not issues else "; ".join(issues)))

    # 8 数据来源
    issues, n_blocks = check_source(content)
    results.append(("每张表/图后数据来源标注", not issues,
                    f"共 {n_blocks} 个元素(table+svg), " + ("OK" if not issues else "; ".join(issues))))

    # 9 禁待补充
    issues = check_no_todo(content)
    results.append(("禁 [待补充]", not issues,
                    "OK" if not issues else "; ".join(issues)))

    # 10 禁粗糙话术
    hits = check_banned_phrases(content)
    results.append(("禁粗糙/口语化话术", not hits,
                    "OK" if not hits else "命中: " + ", ".join(hits)))

    # 11 表格左对齐
    issues = check_alignment(content)
    results.append(("表格对齐契约", not issues,
                    "OK" if not issues else "; ".join(issues)))

    # 12 五问句法
    five_sections = re.findall(r'<section class="five-questions".*?</section>', content, re.S)
    if five_sections:
        chapter_issues = check_five_q(content)
        results.append(("显性五问句法(事实/解释/质量/影响/反证)", not chapter_issues,
                        "OK" if not chapter_issues else f"{len(chapter_issues)} 个章节未达标: "
                        + " | ".join(chapter_issues)))
    else:
        results.append(("五问后台审计门(v3 analysis_bundle)", True,
                        "v3 HTML 不强制显性五问；须另跑 audit_bundle.py"))

    # 13 首屏截图 (可选)
    issues, n_five = check_reading_rhythm(content)
    results.append(("阅读节奏(五问/图题/米白判断面板)", not issues,
                    f"共 {n_five} 组五问, " + ("OK" if not issues else "; ".join(issues))))

    # 14 图表语义
    issues = check_diagnostic_semantics(content)
    results.append(("图表语义(折线/桥接/终值/图内注释)", not issues,
                    "OK" if not issues else "; ".join(issues)))

    # 15 SVG 文本碰撞
    issues = check_svg_text_collisions(content)
    results.append(("SVG 文本标签碰撞", not issues,
                    "OK" if not issues else "; ".join(issues)))

    # 16 首屏截图 (可选)
    results.append(("首屏截图人工核对(可选)", True,
                    "建议用 Playwright 生成首屏截图，确认直接进入判断而非公司概况"))

    # 输出
    print("=" * 64)
    print("迪慢慢财报分析 · 质量门禁  audit_report.py")
    print(f"文件: {os.path.basename(html_path)}")
    print("=" * 64)
    fails = 0
    for name, passed, detail in results:
        tag = "PASS" if passed else "FAIL"
        if not passed:
            fails += 1
        print(f"[{tag}] {name}")
        if detail and (not passed or name.startswith("首屏")):
            print(f"       -> {detail}")
    print("-" * 64)
    if fails == 0:
        print("结果: PASS —— 报告通过门禁，可交付。")
    else:
        print(f"结果: FAIL —— {fails} 项未通过，需返修后再交付。")
    print("=" * 64)
    return fails


def main():
    if len(sys.argv) > 1:
        targets = [sys.argv[1]]
    else:
        here = os.path.dirname(os.path.abspath(__file__))
        docs = os.path.join(here, "..", "..", "docs")
        candidates = []
        for base in [os.getcwd(), docs]:
            if os.path.isdir(base):
                for fn in os.listdir(base):
                    if fn.lower().endswith(".html"):
                        candidates.append(os.path.join(base, fn))
        targets = candidates

    if not targets:
        print("未找到待检查 HTML，请提供路径: python audit_report.py <报告.html>")
        sys.exit(2)

    total_fail = 0
    for t in targets:
        if not os.path.isfile(t):
            print(f"跳过(不存在): {t}")
            continue
        total_fail += audit(t)
    sys.exit(1 if total_fail > 0 else 0)


if __name__ == "__main__":
    main()
