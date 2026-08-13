#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate a UTF-8 audit report HTML from bundle/report audit commands."""

from __future__ import annotations

import argparse
import html
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_command(args: list[str]) -> tuple[int, str]:
    proc = subprocess.run(
        args,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.returncode, proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate financial-analysis audit_report.html")
    parser.add_argument("bundle", type=Path, help="Path to 公司名-analysis_bundle.json")
    parser.add_argument("report", type=Path, help="Path to 公司名-财务分析.html")
    parser.add_argument("-o", "--output", type=Path, help="Output audit report HTML path")
    args = parser.parse_args()

    skill_root = Path(__file__).resolve().parent.parent
    audit_bundle = skill_root / "scripts" / "audit_bundle.py"
    audit_report = skill_root / "scripts" / "audit_report.py"
    output = args.output or args.report.with_name(args.report.name.replace("-财务分析.html", "-audit_report.html"))

    bundle_code, bundle_text = run_command([sys.executable, str(audit_bundle), str(args.bundle)])
    report_code, report_text = run_command([sys.executable, str(audit_report), str(args.report)])
    status = "PASS" if bundle_code == 0 and report_code == 0 else "FAIL"
    status_cls = "pass" if status == "PASS" else "fail"

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(args.report.stem)} 审计报告</title>
<style>
body{{margin:0;background:#F1EFEA;color:#302D29;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",Arial,sans-serif;line-height:1.65}}
main{{width:min(1080px,100%);margin:0 auto;background:#FFFDF9;min-height:100vh;padding:42px 56px 72px;box-sizing:border-box}}
h1{{font-size:30px;margin:0 0 8px}}.deck{{color:#716A62;margin-bottom:24px}}.summary{{background:#F4EBDD;border:1px solid #DCCEBB;border-left:4px solid #5F6F52;border-radius:6px;padding:16px 18px;margin:18px 0 28px}}
h2{{font-size:17px;margin:30px 0 10px}}pre{{white-space:pre-wrap;background:#F7F3EC;border:1px solid #E4DED5;border-radius:6px;padding:14px;font-size:12px;overflow:auto}}.status{{font-weight:700}}.pass{{color:#2F7D67}}.fail{{color:#B0413E}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:14px}}th,td{{border:1px solid #E1D8CC;padding:8px 10px;text-align:right}}th{{background:#5F6F52;color:#fff}}@media print{{main{{padding:0}}section{{break-inside:avoid}}}}
</style>
</head>
<body>
<main>
<h1>{html.escape(args.report.stem)} 审计报告</h1>
<div class="deck">生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}；状态：<strong class="{status_cls}">{status}</strong></div>
<div class="summary"><strong>审计范围：</strong>analysis_bundle 结构与证据门禁、HTML 报告版式/图表/口径门禁。报告使用 UTF-8 写入，避免中文显示成问号或乱码。</div>
<table><thead><tr><th>文件</th><th>结果</th></tr></thead><tbody>
<tr><td>{html.escape(args.bundle.name)}</td><td class="{'pass' if bundle_code == 0 else 'fail'}">{'PASS' if bundle_code == 0 else 'FAIL'}</td></tr>
<tr><td>{html.escape(args.report.name)}</td><td class="{'pass' if report_code == 0 else 'fail'}">{'PASS' if report_code == 0 else 'FAIL'}</td></tr>
</tbody></table>
<section><h2>{html.escape(' '.join([sys.executable, str(audit_bundle), str(args.bundle)]))}</h2><p class="status {'pass' if bundle_code == 0 else 'fail'}">Exit code: {bundle_code}</p><pre>{html.escape(bundle_text)}</pre></section>
<section><h2>{html.escape(' '.join([sys.executable, str(audit_report), str(args.report)]))}</h2><p class="status {'pass' if report_code == 0 else 'fail'}">Exit code: {report_code}</p><pre>{html.escape(report_text)}</pre></section>
</main>
</body>
</html>
"""
    output.write_text(doc, encoding="utf-8")
    print(f"audit report generated: {output}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
