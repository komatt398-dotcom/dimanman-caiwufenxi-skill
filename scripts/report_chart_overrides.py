#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared v2.4 chart primitives for the bundled financial-report examples."""

from math import sqrt


def install_report_chart_overrides(ns):
    """Replace duplicated chart helpers in a generator module with corrected versions."""
    c_gray = "#89918F"
    c_red = "#B34A42"
    c_green = "#2F7463"
    c_secondary = "#65738A"
    c_grid = "#E2DED7"
    c_bg = "#FFFDF9"
    if "C_MAIN" in ns:
        c_main = "#8D3D4A"
    elif "C_PURPLE" in ns:
        c_main = "#6D5A8D"
    elif "C_NAVY" in ns:
        c_main = "#2E6270"
    else:
        c_main = "#496B78"
    raw_dp_rect = ns["dp_rect"]
    raw_dp_circle = ns["dp_circle"]

    def resolve_color(name, original, value=None, index=0):
        """Use a restrained semantic palette across all company generators."""
        label = str(name)
        if any(token in label for token in ("投资", "筹资", "费用率效应", "拖累", "亏损", "负")):
            return c_red
        if any(token in label for token in ("经营现金流", "改善", "增长", "半导体", "现金牛")):
            return c_green
        if any(token in label for token in ("现金及等价物", "货币资金", "终值", "合计", "其他", "基准")):
            return c_gray
        if index == 0 or any(token in label for token in ("收入", "主营", "茅台酒", "硅片")):
            return c_main
        if original == ns.get("C_RED"):
            return c_red
        if original in (ns.get("C_GREEN"), ns.get("C_OLIVE")):
            return c_green
        if original in (ns.get("C_GOLD"), ns.get("C_ORANGE")):
            return c_secondary
        return c_gray if index > 2 else c_main

    def dp_rect(x, y, w, h, fill, title, rx=2, opacity=0.85):
        return raw_dp_rect(x, y, w, h, resolve_color(title, fill), title, rx=rx, opacity=opacity)

    def dp_circle(cx, cy, r, fill, title, stroke="white", sw=1.5):
        return raw_dp_circle(cx, cy, r, resolve_color(title, fill), title, stroke=stroke, sw=sw)

    def bottom_legend_and_unit(parts, width, margin_bottom, unit, series):
        unit_y = 330
        if unit:
            parts.append(
                f'<text class="chart-unit" x="66" y="42" font-size="10" fill="#6B7280">单位：{unit}</text>'
            )
        display_series = [s for s in series if not (len(series) == 1 and s[0] == "数值")]
        if not display_series:
            return
        legend_item_w = min(150, 620 / max(len(display_series), 1))
        start_x = width / 2 - legend_item_w * len(display_series) / 2
        legend_y = 382
        for index, item in enumerate(display_series):
            name = item[0]
            original = item[1] if len(item) > 1 else c_main
            color = resolve_color(name, original, index=index)
            lx = start_x + index * legend_item_w
            parts.append(f'<line x1="{lx}" y1="{legend_y-3}" x2="{lx+16}" y2="{legend_y-3}" stroke="{color}" stroke-width="3"/>')
            parts.append(f'<text x="{lx+22}" y="{legend_y}" font-size="10" fill="#374151">{name}</text>')

    def svg_wrapper(width, height, content, title="", takeaway=""):
        aria = (title + "。" + takeaway).replace('"', "&quot;")
        # Metadata remains machine-readable; visible title and conclusion are rendered in HTML.
        title_tag = (
            f'<text class="chart-title" x="-9999" y="-9999" visibility="hidden">{title}</text>'
            if title else ""
        )
        takeaway_tag = (
            f'<text class="chart-takeaway" x="-9999" y="-9999" visibility="hidden">{takeaway}</text>'
            if takeaway else ""
        )
        crop_top = 36
        visible_height = height - crop_top
        return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {crop_top} {width} {visible_height}" width="{width}" height="{visible_height}" class="diagnostic-chart" role="img" aria-label="{aria}">
  <rect width="100%" height="100%" fill="{c_bg}"/>
  {title_tag}
  {takeaway_tag}
  {content}
</svg>'''

    def make_horizontal_bar_chart(title, labels, values, colors=None, unit="占比", takeaway="", width=720, height=320):
        margin = {"top": 46, "right": 72, "bottom": 24, "left": 92}
        chart_w = width - margin["left"] - margin["right"]
        chart_h = height - margin["top"] - margin["bottom"]
        y_max = max(values) * 1.08 or 1
        n = len(labels)
        slot = chart_h / n
        bar_h = min(30, slot * 0.48)
        palette = [ns.get("C_MAIN", ns.get("C_NAVY", "#334E68")), c_green, c_red, c_gray]
        parts = []
        for i, (label, val) in enumerate(zip(labels, values)):
            y = margin["top"] + i * slot + (slot - bar_h) / 2
            bw = val / y_max * chart_w
            color = resolve_color(label, colors[i] if colors else palette[i % len(palette)], val, i)
            suffix = "%" if unit in ("%", "占比") else f" {unit}" if unit else ""
            parts.append(dp_rect(margin["left"], y, bw, bar_h, color, f"{label}：{val:.2f}{suffix}", rx=3, opacity=0.9))
            parts.append(f'<text x="{margin["left"]-12}" y="{y+bar_h/2+4}" text-anchor="end" font-size="12" fill="#374151">{label}</text>')
            parts.append(f'<text x="{margin["left"]+bw+8}" y="{y+bar_h/2+4}" font-size="12" font-weight="600" fill="#374151">{val:.2f}{suffix}</text>')
        return svg_wrapper(width, height, "\n  ".join(parts), title, takeaway)

    def make_line_series_chart(title, xlabels, series, unit="", takeaway="", width=720, height=400):
        margin = {"top": 52, "right": 62, "bottom": 78, "left": 66}
        chart_w = width - margin["left"] - margin["right"]
        chart_h = height - margin["top"] - margin["bottom"]
        all_vals = [v for _, _, vals in series for v in vals if v is not None]
        raw_min, raw_max = min(all_vals), max(all_vals)
        span = raw_max - raw_min or max(abs(raw_max), 1)
        y_min = raw_min - span * 0.12
        y_max = raw_max + span * 0.14

        def x(i):
            return margin["left"] + i * chart_w / max(len(xlabels) - 1, 1)

        def y(v):
            return margin["top"] + chart_h - (v - y_min) / (y_max - y_min) * chart_h

        parts = []
        for k in range(5):
            val = y_min + (y_max - y_min) * k / 4
            yy = y(val)
            parts.append(f'<line x1="{margin["left"]}" y1="{yy}" x2="{width-margin["right"]}" y2="{yy}" stroke="{c_grid}" stroke-width="1"/>')
            parts.append(f'<text x="{margin["left"]-10}" y="{yy+4}" text-anchor="end" font-size="10" fill="#6B7280">{val:,.1f}</text>')
        if y_min < 0 < y_max:
            parts.append(f'<line x1="{margin["left"]}" y1="{y(0)}" x2="{width-margin["right"]}" y2="{y(0)}" stroke="#9CA3AF" stroke-width="1.4"/>')
        for i, label in enumerate(xlabels):
            parts.append(f'<text x="{x(i)}" y="{height-margin["bottom"]+20}" text-anchor="middle" font-size="11" fill="#4B5563">{label}</text>')
        for sidx, (name, color, vals) in enumerate(series):
            color = resolve_color(name, color, index=sidx)
            points = [(i, v) for i, v in enumerate(vals) if v is not None]
            pts = " ".join(f"{x(i)},{y(v)}" for i, v in points)
            parts.append(f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="2.4" stroke-linejoin="round" stroke-linecap="round"/>')
            for i, v in points:
                parts.append(dp_circle(x(i), y(v), 3.2, color, f"{name} {xlabels[i]}：{v:,.2f} {unit}"))
            i, v = points[-1]
            label_y = y(v) - 7 if sidx % 2 == 0 else y(v) + 15
            parts.append(f'<text x="{x(i)+8}" y="{label_y}" font-size="10" font-weight="600" fill="{color}">{v:,.2f}</text>')
        if unit:
            parts.append(f'<text class="chart-unit" x="{margin["left"]}" y="{margin["top"]-10}" font-size="10" fill="#6B7280">单位：{unit}</text>')
        legend_w = min(150, chart_w / max(len(series), 1))
        start_x = width / 2 - legend_w * len(series) / 2
        legend_y = height - 18
        for i, (name, color, _) in enumerate(series):
            color = resolve_color(name, color, index=i)
            lx = start_x + i * legend_w
            parts.append(f'<line x1="{lx}" y1="{legend_y-3}" x2="{lx+16}" y2="{legend_y-3}" stroke="{color}" stroke-width="3"/>')
            parts.append(f'<text x="{lx+22}" y="{legend_y}" font-size="10" fill="#374151">{name}</text>')
        return svg_wrapper(width, height, "\n  ".join(parts), title, takeaway)

    def make_growth_margin_matrix(title, bubbles, x_mid=0.0, y_mid=0.0, takeaway="", width=720, height=440):
        margin = {"top": 52, "right": 42, "bottom": 62, "left": 72}
        chart_w = width - margin["left"] - margin["right"]
        chart_h = height - margin["top"] - margin["bottom"]
        xs = [b[1] for b in bubbles] + [x_mid]
        ys = [b[2] for b in bubbles] + [y_mid]
        x_span = max(xs) - min(xs) or 10
        y_span = max(ys) - min(ys) or 10
        x_min, x_max = min(xs) - max(2, x_span * 0.18), max(xs) + max(2, x_span * 0.18)
        y_min, y_max = min(ys) - max(3, y_span * 0.18), max(ys) + max(3, y_span * 0.18)

        def X(v):
            return margin["left"] + (v - x_min) / (x_max - x_min) * chart_w

        def Y(v):
            return margin["top"] + chart_h - (v - y_min) / (y_max - y_min) * chart_h

        parts = [
            f'<rect x="{X(x_min)}" y="{Y(y_max)}" width="{max(0, X(x_mid)-X(x_min))}" height="{max(0, Y(y_mid)-Y(y_max))}" fill="#EEF6EC"/>',
            f'<rect x="{X(x_mid)}" y="{Y(y_mid)}" width="{max(0, X(x_max)-X(x_mid))}" height="{max(0, Y(y_min)-Y(y_mid))}" fill="#FAF0ED"/>',
            f'<line x1="{X(x_mid)}" y1="{Y(y_min)}" x2="{X(x_mid)}" y2="{Y(y_max)}" stroke="#9CA3AF" stroke-width="1" stroke-dasharray="4,4"/>',
            f'<line x1="{X(x_min)}" y1="{Y(y_mid)}" x2="{X(x_max)}" y2="{Y(y_mid)}" stroke="#9CA3AF" stroke-width="1" stroke-dasharray="4,4"/>',
            f'<text x="{margin["left"]+chart_w/2}" y="{height-18}" text-anchor="middle" font-size="11" fill="#4B5563">收入 CAGR（%） →</text>',
            f'<text x="{margin["left"]-18}" y="{margin["top"]+chart_h/2}" text-anchor="middle" font-size="11" fill="#4B5563" transform="rotate(-90 {margin["left"]-18} {margin["top"]+chart_h/2})">2025 毛利率（%） →</text>',
        ]
        max_rev = max(b[3] for b in bubbles) or 1
        for bidx, (name, cagr, gm, rev, color) in enumerate(bubbles):
            color = resolve_color(name, color, index=bidx)
            cx, cy = X(cagr), Y(gm)
            radius = 10 + sqrt(max(rev, 0) / max_rev) * 16
            parts.append(f'<circle class="data-point" cx="{cx}" cy="{cy}" r="{radius:.1f}" fill="{color}" opacity="0.52" stroke="{color}" stroke-width="1.2"><title>{name}：CAGR {cagr:.1f}%，毛利率 {gm:.2f}%，收入 {rev:,.2f} 亿元</title></circle>')
            parts.append(f'<text x="{cx}" y="{cy+4}" text-anchor="middle" font-size="9.5" fill="#1F2937" font-weight="600">{name}</text>')
        return svg_wrapper(width, height, "\n  ".join(parts), title, takeaway)

    def make_waterfall(title, steps, unit="pp", takeaway="", width=720, height=400):
        margin = {"top": 50, "right": 34, "bottom": 68, "left": 62}
        chart_w = width - margin["left"] - margin["right"]
        chart_h = height - margin["top"] - margin["bottom"]
        running = 0.0
        levels = []
        for label, val, color, is_abs in steps:
            if is_abs:
                levels.append((label, 0.0, val, val, c_gray, True))
                running = val
            else:
                start = running
                running += val
                levels.append((label, start, running, val, color, False))
        all_vals = [0.0] + [v for _, s, e, _, _, _ in levels for v in (s, e)]
        v_min, v_max = min(all_vals), max(all_vals)
        pad = (v_max - v_min or 1) * 0.13
        v_min, v_max = v_min - pad, v_max + pad

        def Y(v):
            return margin["top"] + chart_h - (v - v_min) / (v_max - v_min) * chart_h

        n = len(levels)
        gap = chart_w / n
        bw = gap * 0.56
        parts = []
        for k in range(5):
            val = v_min + (v_max - v_min) * k / 4
            yy = Y(val)
            parts.append(f'<line x1="{margin["left"]}" y1="{yy}" x2="{width-margin["right"]}" y2="{yy}" stroke="{c_grid}" stroke-width="1"/>')
            parts.append(f'<text x="{margin["left"]-9}" y="{yy+4}" text-anchor="end" font-size="10" fill="#6B7280">{val:.1f}</text>')
        if v_min < 0 < v_max:
            parts.append(f'<line x1="{margin["left"]}" y1="{Y(0)}" x2="{width-margin["right"]}" y2="{Y(0)}" stroke="#9CA3AF" stroke-width="1.4"/>')
        for i, (label, start, end, delta, color, absolute) in enumerate(levels):
            color = c_gray if absolute else resolve_color(label, color, delta, i)
            x = margin["left"] + i * gap + (gap - bw) / 2
            y_top = min(Y(start), Y(end))
            h = max(abs(Y(start) - Y(end)), 1.5)
            value_text = f"{end:.2f}" if absolute else f"{delta:+.2f}"
            tooltip = f"{label}：{value_text}{unit}"
            parts.append(dp_rect(x, y_top, bw, h, color, tooltip, rx=2, opacity=0.9))
            endpoint_y = Y(end)
            text_y = endpoint_y - 8 if end >= start else endpoint_y + 15
            parts.append(f'<text x="{x+bw/2}" y="{text_y}" text-anchor="middle" font-size="10" font-weight="600" fill="#374151">{value_text}</text>')
            parts.append(f'<text x="{x+bw/2}" y="{height-margin["bottom"]+20}" text-anchor="middle" font-size="10" fill="#374151">{label}</text>')
            if i < n - 1:
                next_x = margin["left"] + (i + 1) * gap + (gap - bw) / 2
                parts.append(f'<line class="bridge-connector" x1="{x+bw}" y1="{endpoint_y}" x2="{next_x}" y2="{endpoint_y}" stroke="#8B949E" stroke-width="1.2" stroke-dasharray="4,3"/>')
        parts.append(f'<text class="chart-unit" x="{margin["left"]}" y="{margin["top"]-10}" font-size="10" fill="#6B7280">单位：{unit}</text>')
        return svg_wrapper(width, height, "\n  ".join(parts), title, takeaway)

    def make_cashflow_bridge(title, flows, unit="亿元", takeaway="", width=720, height=400):
        terminal_label, terminal_value, terminal_color = flows[-1]
        increments = list(flows[:-1])
        residual = terminal_value - sum(v for _, v, _ in increments)
        tolerance = max(abs(terminal_value), 1) * 0.001
        if abs(residual) > tolerance:
            increments.append(("汇率及其他", residual, c_gray))
        steps = [(label, val, color, False) for label, val, color in increments]
        steps.append((terminal_label, terminal_value, terminal_color, True))
        return make_waterfall(title, steps, unit, takeaway, width, height)

    def make_debt_pressure(title, bars, annotations=None, unit="亿元", takeaway="", width=720, height=420):
        margin = {"top": 52, "right": 44, "bottom": 68, "left": 68}
        chart_w = width - margin["left"] - margin["right"]
        chart_h = height - margin["top"] - margin["bottom"]
        v_max = max(v for _, v, _ in bars) * 1.14 or 1

        def Y(v):
            return margin["top"] + chart_h - v / v_max * chart_h

        n = len(bars)
        gap = chart_w / n
        bw = gap * 0.46
        parts = []
        for k in range(5):
            val = v_max * k / 4
            yy = Y(val)
            parts.append(f'<line x1="{margin["left"]}" y1="{yy}" x2="{width-margin["right"]}" y2="{yy}" stroke="{c_grid}" stroke-width="1"/>')
            parts.append(f'<text x="{margin["left"]-9}" y="{yy+4}" text-anchor="end" font-size="10" fill="#6B7280">{val:,.0f}</text>')
        for i, (label, value, color) in enumerate(bars):
            color = resolve_color(label, color, value, i)
            x = margin["left"] + i * gap + (gap - bw) / 2
            h = max(Y(0) - Y(value), 1.5)
            parts.append(dp_rect(x, Y(value), bw, h, color, f"{label}：{value:,.2f} {unit}", rx=2, opacity=0.9))
            parts.append(f'<text x="{x+bw/2}" y="{Y(value)-9}" text-anchor="middle" font-size="11" font-weight="600" fill="#374151">{value:,.1f}</text>')
            parts.append(f'<text x="{x+bw/2}" y="{height-margin["bottom"]+20}" text-anchor="middle" font-size="11" fill="#374151">{label}</text>')
        parts.append(f'<text class="chart-unit" x="{margin["left"]}" y="{margin["top"]-10}" font-size="10" fill="#6B7280">单位：{unit}</text>')
        return svg_wrapper(width, height, "\n  ".join(parts), title, takeaway)

    ns.update({
        "dp_rect": dp_rect,
        "dp_circle": dp_circle,
        "bottom_legend_and_unit": bottom_legend_and_unit,
        "svg_wrapper": svg_wrapper,
        "make_horizontal_bar_chart": make_horizontal_bar_chart,
        "make_line_series_chart": make_line_series_chart,
        "make_growth_margin_matrix": make_growth_margin_matrix,
        "make_waterfall": make_waterfall,
        "make_cashflow_bridge": make_cashflow_bridge,
        "make_debt_pressure": make_debt_pressure,
    })
