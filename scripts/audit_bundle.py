#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迪慢慢财报分析 Skill v3.1 —— analysis_bundle.json 质量门禁

用法:
    python scripts/audit_bundle.py <公司名-analysis_bundle.json>

本脚本检查分析包的数据契约、关键指标口径、claim 证据链、核心问题闭环、
情景/行动字段和质量评分上限。它不替代财务判断，但会拦截来源不可追溯、
假设写成事实、关键链条缺失等结构性失败。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


REQUIRED_TOP_LEVEL = [
    "run",
    "disclosures",
    "metrics",
    "calculations",
    "claims",
    "issues",
    "scenarios",
    "actions",
    "quality",
]

OPTIONAL_TOP_LEVEL = [
    "management_statements",
]

RUN_FIELDS = [
    "company_name",
    "disclosure_regime",
    "accounting_basis",
    "report_cutoff_date",
    "main_analysis_period",
    "skill_version",
    "generated_at",
]

DISCLOSURE_FIELDS = [
    "source_id",
    "file_or_url",
    "disclosure_type",
    "publication_date",
    "reporting_period",
    "location",
    "currency",
    "unit",
    "extraction_method",
]

MANAGEMENT_STATEMENT_FIELDS = [
    "statement_id",
    "source_id",
    "speaker_or_document",
    "statement_date",
    "topic",
    "original_statement",
    "normalized_statement",
    "statement_type",
    "verification_metric_ids",
    "verification_calculation_ids",
    "verification_result",
    "report_usage",
]

METRIC_FIELDS = [
    "metric_id",
    "display_name",
    "original_name",
    "classification",
    "formula",
    "scope",
    "period",
    "currency",
    "unit",
    "source_chain",
    "definition_fingerprint",
    "cross_period_comparability",
    "peer_comparability",
    "reconciliation_status",
]

CALCULATION_FIELDS = [
    "calculation_id",
    "input_metric_ids",
    "formula",
    "period_alignment_rule",
    "scope_compatibility_rule",
    "output_metric_id",
    "tolerance",
    "reconciliation_result",
    "residual_difference",
]

CLAIM_FIELDS = [
    "claim_id",
    "text",
    "level",
    "evidence_ids",
    "dependent_metric_ids",
    "dependent_calculation_ids",
    "allowed_wording_strength",
    "appears_in",
]

ISSUE_FIELDS = [
    "issue_id",
    "management_question",
    "selected_module",
    "decision_chain",
    "evidence_sufficiency",
    "data_gaps",
    "boundary",
    "leading_indicators",
    "falsifier",
    "priority_action_ids",
]

DECISION_CHAIN_FIELDS = [
    "judgment",
    "key_evidence",
    "management_statement",
    "statement_verification",
    "financial_transmission_mechanism",
    "attribution",
    "operating_or_risk_boundary",
    "priority_action",
    "leading_indicator_and_falsifier",
    "data_gap",
]

SCENARIO_FIELDS = [
    "scenario_id",
    "management_question",
    "driver",
    "driver_to_result_rationale",
    "input_basis",
    "output_type",
    "action_implication",
    "limitations",
]

ACTION_FIELDS = [
    "action_id",
    "related_issue_id",
    "proposed_action",
    "expected_financial_mechanism",
    "owner_type",
    "leading_indicator",
    "warning_threshold_logic",
    "calibration_data_needed",
    "risk_of_false_positive_or_negative",
]

QUALITY_FIELDS = [
    "credibility_score",
    "insight_score",
    "decision_value_score",
    "expression_visual_score",
    "blocking_failures",
    "warnings",
    "audit_status",
    "delivery_decision",
]

VALID_CLAIM_LEVELS = {
    "disclosed_fact",
    "calculation",
    "supported_inference",
    "hypothesis_requires_validation",
}

VALID_METRIC_CLASSES = {"statutory", "non_gaap", "custom_kpi", "calculated"}
VALID_METRIC_SCOPES = {"consolidated", "attributable", "segment", "adjusted", "custom"}
VALID_STATEMENT_TYPES = {
    "fact_explanation",
    "strategy_intent",
    "market_view",
    "risk_view",
    "target_or_guidance",
}
VALID_VERIFICATION_RESULTS = {
    "supported",
    "partly_supported",
    "not_supported",
    "not_yet_verifiable",
    "contradicted",
}
VALID_STATEMENT_USAGE = {
    "core_judgment",
    "supporting_context",
    "data_gap",
    "appendix_only",
}


def is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    return False


def add_missing(prefix: str, obj: dict[str, Any], fields: list[str], failures: list[str]) -> None:
    for field in fields:
        if field not in obj or is_blank(obj[field]):
            failures.append(f"{prefix} 缺少必填字段: {field}")


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def collect_ids(items: list[dict[str, Any]], key: str) -> set[str]:
    return {str(item.get(key)) for item in items if not is_blank(item.get(key))}


def audit_bundle(bundle: dict[str, Any]) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []

    for field in REQUIRED_TOP_LEVEL:
        if field not in bundle:
            failures.append(f"顶层缺少: {field}")
    if failures:
        return failures, warnings

    if not isinstance(bundle["run"], dict):
        failures.append("run 必须是对象")
    else:
        add_missing("run", bundle["run"], RUN_FIELDS, failures)

    disclosures = as_list(bundle["disclosures"])
    management_statements = as_list(bundle.get("management_statements"))
    metrics = as_list(bundle["metrics"])
    calculations = as_list(bundle["calculations"])
    claims = as_list(bundle["claims"])
    issues = as_list(bundle["issues"])
    scenarios = as_list(bundle["scenarios"])
    actions = as_list(bundle["actions"])

    if not disclosures:
        failures.append("disclosures 为空：核心结论无法追溯来源")
    if not metrics:
        failures.append("metrics 为空：无法审计指标口径")
    if not claims:
        failures.append("claims 为空：无法审计判断证据链")
    if not issues:
        failures.append("issues 为空：报告缺少核心经营问题")
    if not actions:
        failures.append("actions 为空：报告缺少管理动作")

    source_ids = collect_ids(disclosures, "source_id")
    metric_ids = collect_ids(metrics, "metric_id")
    calculation_ids = collect_ids(calculations, "calculation_id")
    action_ids = collect_ids(actions, "action_id")

    for idx, disclosure in enumerate(disclosures, 1):
        if not isinstance(disclosure, dict):
            failures.append(f"disclosures[{idx}] 必须是对象")
            continue
        add_missing(f"disclosures[{idx}]", disclosure, DISCLOSURE_FIELDS, failures)

    if "management_statements" not in bundle:
        warnings.append("缺少 management_statements：若存在业绩说明会/IR/路演表述，应纳入经营者表述验证")
    for idx, statement in enumerate(management_statements, 1):
        if not isinstance(statement, dict):
            failures.append(f"management_statements[{idx}] 必须是对象")
            continue
        label = f"management_statements[{idx}] {statement.get('statement_id', '')}".strip()
        add_missing(label, statement, MANAGEMENT_STATEMENT_FIELDS, failures)
        source_id = statement.get("source_id")
        if source_id and str(source_id) not in source_ids:
            failures.append(f"{label} 引用不存在 source_id: {source_id}")
        statement_type = statement.get("statement_type")
        if statement_type and statement_type not in VALID_STATEMENT_TYPES:
            failures.append(f"{label} statement_type 非法: {statement_type}")
        verification_result = statement.get("verification_result")
        if verification_result and verification_result not in VALID_VERIFICATION_RESULTS:
            failures.append(f"{label} verification_result 非法: {verification_result}")
        report_usage = statement.get("report_usage")
        if report_usage and report_usage not in VALID_STATEMENT_USAGE:
            failures.append(f"{label} report_usage 非法: {report_usage}")
        metric_refs = as_list(statement.get("verification_metric_ids"))
        calculation_refs = as_list(statement.get("verification_calculation_ids"))
        if report_usage == "core_judgment" and not (metric_refs or calculation_refs):
            failures.append(f"{label} 用于核心判断但没有验证指标或计算")
        if verification_result in {"supported", "partly_supported", "not_supported", "contradicted"} and not (metric_refs or calculation_refs):
            failures.append(f"{label} 给出验证结论但没有验证指标或计算")
        for metric_id in metric_refs:
            if str(metric_id) not in metric_ids:
                failures.append(f"{label} 引用不存在 verification metric: {metric_id}")
        for calculation_id in calculation_refs:
            if str(calculation_id) not in calculation_ids:
                failures.append(f"{label} 引用不存在 verification calculation: {calculation_id}")

    for idx, metric in enumerate(metrics, 1):
        if not isinstance(metric, dict):
            failures.append(f"metrics[{idx}] 必须是对象")
            continue
        label = f"metrics[{idx}] {metric.get('metric_id', '')}".strip()
        add_missing(label, metric, METRIC_FIELDS, failures)
        classification = metric.get("classification")
        if classification and classification not in VALID_METRIC_CLASSES:
            failures.append(f"{label} classification 非法: {classification}")
        scope = metric.get("scope")
        if scope and scope not in VALID_METRIC_SCOPES:
            failures.append(f"{label} scope 非法: {scope}")
        source_chain = as_list(metric.get("source_chain"))
        if not source_chain:
            failures.append(f"{label} source_chain 为空")
        for source_id in source_chain:
            if str(source_id) not in source_ids:
                failures.append(f"{label} source_chain 引用不存在来源: {source_id}")
        if metric.get("display_name") == "净利率" and scope == "custom":
            warnings.append(f"{label} 使用泛称净利率且 scope=custom，正文必须解释归母/合并口径")
        if metric.get("classification") == "custom_kpi":
            for field in ["definition_fingerprint", "source_chain", "formula"]:
                if is_blank(metric.get(field)):
                    failures.append(f"{label} custom KPI 缺少 {field}")

    for idx, calculation in enumerate(calculations, 1):
        if not isinstance(calculation, dict):
            failures.append(f"calculations[{idx}] 必须是对象")
            continue
        label = f"calculations[{idx}] {calculation.get('calculation_id', '')}".strip()
        add_missing(label, calculation, CALCULATION_FIELDS, failures)
        for metric_id in as_list(calculation.get("input_metric_ids")):
            if str(metric_id) not in metric_ids:
                failures.append(f"{label} 引用不存在 input metric: {metric_id}")
        if calculation.get("reconciliation_result") not in {"pass", "warning", "not_applicable"}:
            failures.append(f"{label} reconciliation_result 未通过: {calculation.get('reconciliation_result')}")

    for idx, claim in enumerate(claims, 1):
        if not isinstance(claim, dict):
            failures.append(f"claims[{idx}] 必须是对象")
            continue
        label = f"claims[{idx}] {claim.get('claim_id', '')}".strip()
        add_missing(label, claim, CLAIM_FIELDS, failures)
        level = claim.get("level")
        if level and level not in VALID_CLAIM_LEVELS:
            failures.append(f"{label} level 非法: {level}")
        appears_in = as_list(claim.get("appears_in"))
        evidence_ids = as_list(claim.get("evidence_ids"))
        dependent_metric_ids = as_list(claim.get("dependent_metric_ids"))
        dependent_calculation_ids = as_list(claim.get("dependent_calculation_ids"))
        has_support = bool(evidence_ids or dependent_metric_ids or dependent_calculation_ids)
        if "judgment_panel" in appears_in and not has_support:
            failures.append(f"{label} 出现在判断面板但无证据/指标/计算支撑")
        if "judgment_panel" in appears_in and level == "hypothesis_requires_validation":
            failures.append(f"{label} 假设不能作为无保留判断面板结论")
        for source_id in evidence_ids:
            if str(source_id) not in source_ids:
                failures.append(f"{label} 引用不存在 evidence source: {source_id}")
        for metric_id in dependent_metric_ids:
            if str(metric_id) not in metric_ids:
                failures.append(f"{label} 引用不存在 metric: {metric_id}")
        for calculation_id in dependent_calculation_ids:
            if str(calculation_id) not in calculation_ids:
                failures.append(f"{label} 引用不存在 calculation: {calculation_id}")
        text = str(claim.get("text", ""))
        if level == "hypothesis_requires_validation" and any(word in text for word in ["已经", "必然", "证明"]):
            failures.append(f"{label} 假设文本使用事实化措辞")

    for idx, issue in enumerate(issues, 1):
        if not isinstance(issue, dict):
            failures.append(f"issues[{idx}] 必须是对象")
            continue
        label = f"issues[{idx}] {issue.get('issue_id', '')}".strip()
        add_missing(label, issue, ISSUE_FIELDS, failures)
        chain = issue.get("decision_chain")
        if not isinstance(chain, dict):
            failures.append(f"{label} decision_chain 必须是对象")
        else:
            add_missing(f"{label}.decision_chain", chain, DECISION_CHAIN_FIELDS, failures)
        for action_id in as_list(issue.get("priority_action_ids")):
            if str(action_id) not in action_ids:
                failures.append(f"{label} 引用不存在 action: {action_id}")

    for idx, scenario in enumerate(scenarios, 1):
        if not isinstance(scenario, dict):
            failures.append(f"scenarios[{idx}] 必须是对象")
            continue
        label = f"scenarios[{idx}] {scenario.get('scenario_id', '')}".strip()
        add_missing(label, scenario, SCENARIO_FIELDS, failures)
        if scenario.get("output_type") not in {
            "sensitivity",
            "boundary_test",
            "combined_stress_test",
            "reverse_stress_test",
            "directional_risk_tree",
        }:
            failures.append(f"{label} output_type 非法: {scenario.get('output_type')}")

    issue_ids = collect_ids(issues, "issue_id")
    for idx, action in enumerate(actions, 1):
        if not isinstance(action, dict):
            failures.append(f"actions[{idx}] 必须是对象")
            continue
        label = f"actions[{idx}] {action.get('action_id', '')}".strip()
        add_missing(label, action, ACTION_FIELDS, failures)
        if str(action.get("related_issue_id")) not in issue_ids:
            failures.append(f"{label} related_issue_id 不存在: {action.get('related_issue_id')}")

    quality = bundle.get("quality")
    if not isinstance(quality, dict):
        failures.append("quality 必须是对象")
    else:
        add_missing("quality", quality, QUALITY_FIELDS, failures)
        if failures and quality.get("delivery_decision") == "deliver":
            failures.append("存在阻断失败时 delivery_decision 不能为 deliver")
        if failures and quality.get("audit_status") == "pass":
            failures.append("存在阻断失败时 audit_status 不能为 pass")
        for field in [
            "credibility_score",
            "insight_score",
            "decision_value_score",
            "expression_visual_score",
        ]:
            value = quality.get(field)
            if isinstance(value, (int, float)) and not (0 <= value <= 10):
                failures.append(f"quality.{field} 必须在 0-10 之间")

    if len(issues) > 4:
        warnings.append("核心问题超过 4 个，可能回到章节堆砌")
    if len(issues) < 2:
        warnings.append("核心问题少于 2 个，需确认是否因披露限制而降级")

    return failures, warnings


def main() -> int:
    if len(sys.argv) != 2:
        print("用法: python scripts/audit_bundle.py <公司名-analysis_bundle.json>")
        return 2

    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"文件不存在: {path}")
        return 2

    try:
        bundle = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        print(f"JSON 解析失败: {exc}")
        return 2

    failures, warnings = audit_bundle(bundle)

    print("=" * 72)
    print("迪慢慢财报分析 v3.1 · analysis_bundle 质量门禁")
    print(f"文件: {path.name}")
    print("=" * 72)
    if failures:
        for item in failures:
            print(f"[FAIL] {item}")
    else:
        print("[PASS] blocking failures: 0")
    for item in warnings:
        print(f"[WARN] {item}")
    print("-" * 72)
    if failures:
        print(f"结果: FAIL —— {len(failures)} 项阻断失败，不能作为正常报告交付。")
        return 1
    print("结果: PASS —— analysis_bundle 通过结构与证据门禁。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
