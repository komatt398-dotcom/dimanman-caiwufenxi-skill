# v3.1 管理层财报诊断系统

本文件是 v3.1 的执行参考。`SKILL.md` 只保留入口流程；生成报告、判断口径、选择图表、做审计时读取本文件。

## 1. 核心原则

目标读者是管理层和业务负责人。报告不追求章节完整，追求少数关键问题的决策闭环。

核心原则：

> 先确定管理问题，再决定数据、口径、同行、情景和图表。

> 管理是语言活动；财务分析要验证经营者公开说过的话是否被经营结果支持。

默认不做估值、目标价、投资评级、市场情绪判断和股价预期差。除非用户明确要求，报告不写股东回报专章和杜邦分析。

定期报告、审计报告和公告是财务数字及会计口径的主来源；业绩说明会、投资者关系活动记录表和公开路演材料是管理层解释的补充来源。两类来源必须分工清楚，不能用路演覆盖财报数字。

## 2. 固定报告结构

每份 v3.1 报告使用“固定决策底座 + 动态诊断模块”：

1. 管理层判断面板
2. 一页经营概览
3. 两到四个核心经营问题
4. 管理建议或后续关注事项
5. 监控与预警表
6. 证据与指标附录

旧七段结构不得作为强制章节。七段里的收入、成本、现金、债务、研发、会计政策等内容只作为动态模块，在能回答管理问题时进入正文。

## 3. 管理层判断面板

第一屏必须给出：

- 三个核心判断。
- 两条经营或风险边界。
- 一个关键反证指标。

每条判断必须带来源 ID，如 `[S03]`，并在 `analysis_bundle.json` 的 `claims` 与附录证据链中可追溯。

禁止把假设写成事实。若证据不足，写“该判断只能作为待验证假设”，不能放进核心判断。

## 4. 核心问题闭环

每个被选中的核心问题必须完整覆盖：

```text
Judgment
-> Key evidence
-> Financial transmission mechanism
-> Industry, company, or accounting attribution
-> Operating or risk boundary
-> Priority action
-> Leading indicator and falsifier
-> Data gap
```

中文正文可写得自然，不必显式展示英文标签，但后台 bundle 的 `issues[].decision_chain` 必须包含这些键。

旧“五问”逻辑转为后台审计门：

- 事实：指标变动是什么。
- 解释：业务、行业、会计或一次性因素分别是什么。
- 质量：趋势性还是一次性，现金是否支持。
- 影响：对经营边界、资源配置或风险动作意味着什么。
- 反证：什么可观测指标会推翻判断。

前台不再要求每章都展示“五问自检”。

## 5. 动态诊断模块

按问题选择模块：

| 管理问题 | 可选模块 | 进入正文条件 |
|---|---|---|
| 经营者表述是否被财务结果支持 | 管理层公开表述与财务验证 | 有年报 MD&A、业绩说明会、IR 活动记录或公开路演表述，且可连接至少一个财务或经营指标 |
| 增长是否有质量 | 产品/区域/客户结构、价格-销量-成本 | 有分部、价格、销量、单价或可接受代理指标 |
| 利润改善是否可持续 | 毛利率、费用率、减值、非经常性损益、会计重分类 | 能区分经营因素、会计口径和一次性项目 |
| 利润是否转化为现金 | 利润到经营现金流桥、营运资本、回款 | 有现金流量表和营运资本拆解或可靠代理 |
| 投入是否形成产出 | R&D、人员效率、产能、capex | 有投入指标和至少一个产出或商业化代理 |
| 风险是否越过边界 | 债务、流动性、库存、减值、客户集中 | 有边界指标和可监控前导指标 |
| 是行业问题还是公司问题 | 同行校准 | 有 2-4 个可比同行和 3-5 个相关指标 |
| 管理动作是否会变 | 情景/压力/反向压力测试 | 驱动关系清楚，结果会改变动作 |

披露不足时优雅降级：

1. 使用公司原始披露指标。
2. 使用可靠代理并标注“代理证据”。
3. 无可靠代理则省略模块，并说明该问题不能闭合。

增长与销售路径模块至少尝试收集：产品/区域/渠道收入、直销/经销、客户集中度、销售费用、销售费用率、销售人员、销售人员占员工比例、总员工数、收入/销售人员、品牌活动或市场拓展描述。未披露项必须列为缺口，不能推测。

研发模块至少尝试覆盖主分析期内的研发投入、研发费用、研发投入率、研发人员、研发人员占比、专利结构、软件著作权、集成电路布图设计、技术难题或产品适配进展。若只披露 2024 年和 2025 年，不得只列 2025 年。

## 6. 分析包数据契约

每份报告必须先生成：

```text
公司名-analysis_bundle.json
公司名-财务分析.html
公司名-audit_report.html
```

HTML 是展示层，`analysis_bundle.json` 是事实、口径、计算、claim 和审计的源头。

顶层结构：

```json
{
  "run": {},
  "disclosures": [],
  "management_statements": [],
  "metrics": [],
  "calculations": [],
  "claims": [],
  "issues": [],
  "scenarios": [],
  "actions": [],
  "quality": {}
}
```

### 6.1 run

必填：

- `company_name`
- `disclosure_regime`
- `accounting_basis`
- `report_cutoff_date`
- `main_analysis_period`
- `skill_version`
- `generated_at`

若使用中期或季度数据，写入 `interim_update_period`，并在正文中分开说明。

#### 6.1.1 期间契约

- 默认主分析期为最近三年已披露年报。除非用户另有指定，不得只用最近一年替代三年主序列。
- 如果存在最近一期半年报或季报，把它作为“最近一期更新”单独列示；不要把未经审计的中期数据混入年度趋势图表。
- 具体指标的披露期间应尽量与主分析期一致。若公司只披露最近一年，表格中用 `—` 标出缺口，并写明“未单独披露”，不能把单年数据写成趋势判断。
- 表格年份字段写完整：`2023年`、`2024年`、`2025年`；中期字段写 `2026H1` 或 `2026年上半年`，全篇保持一致。

### 6.2 disclosures

每个来源必填：

- `source_id`
- `file_or_url`
- `disclosure_type`
- `publication_date`
- `reporting_period`
- `location`
- `currency`
- `unit`
- `extraction_method`

来源类型建议写入 `disclosure_type`，如 `annual_report`、`interim_report`、`quarterly_report`、`audit_report`、`announcement`、`earnings_briefing`、`investor_relations_record`、`public_roadshow`、`company_website_material`。

财务数字和会计口径只能由定期报告、审计报告或公告支撑。业绩说明会、IR 记录和路演可支撑“管理层公开表述”，但不能单独支撑财务事实。

### 6.2a management_statements

当报告使用管理层对市场、策略、渠道、产品、成本、现金、风险或资本配置的公开解释时，必须填写：

- `statement_id`
- `source_id`
- `speaker_or_document`
- `statement_date`
- `topic`
- `original_statement`
- `normalized_statement`
- `statement_type`: `fact_explanation`、`strategy_intent`、`market_view`、`risk_view` 或 `target_or_guidance`
- `verification_metric_ids`
- `verification_calculation_ids`
- `verification_result`: `supported`、`partly_supported`、`not_supported`、`not_yet_verifiable` 或 `contradicted`
- `report_usage`: `core_judgment`、`supporting_context`、`data_gap` 或 `appendix_only`

同一事项同时出现在财报和路演中时，财报中的解读为主，路演用于补充管理层语气、原因解释或后续动作。正文不得只摘录表态，必须给出财务验证结果或数据缺口。

### 6.3 metrics

每个进入核心结论的指标必填：

- `metric_id`
- `display_name`
- `original_name`
- `classification`: `statutory`、`non_gaap`、`custom_kpi` 或 `calculated`
- `formula`
- `scope`: `consolidated`、`attributable`、`segment`、`adjusted` 或 `custom`
- `period`
- `currency`
- `unit`
- `source_chain`
- `definition_fingerprint`
- `cross_period_comparability`
- `peer_comparability`
- `reconciliation_status`

当指标有分子分母时，写入 `numerator` 和 `denominator`。没有分子分母的原始披露值可写 `null`。

### 6.4 calculations

关键计算必填：

- `calculation_id`
- `input_metric_ids`
- `formula`
- `period_alignment_rule`
- `scope_compatibility_rule`
- `output_metric_id`
- `tolerance`
- `reconciliation_result`
- `residual_difference`

### 6.5 claims

每条关键 claim 必填：

- `claim_id`
- `text`
- `level`: `disclosed_fact`、`calculation`、`supported_inference` 或 `hypothesis_requires_validation`
- `evidence_ids`
- `dependent_metric_ids`
- `dependent_calculation_ids`
- `allowed_wording_strength`
- `appears_in`

管理层判断面板中的 claim 必须有 evidence、metric 或 calculation 支撑。

### 6.6 issues

每个核心问题必填：

- `issue_id`
- `management_question`
- `selected_module`
- `decision_chain`
- `evidence_sufficiency`
- `data_gaps`
- `boundary`
- `leading_indicators`
- `falsifier`
- `priority_action_ids`

`decision_chain` 必须包含：

```json
{
  "judgment": "",
  "key_evidence": [],
  "management_statement": "",
  "statement_verification": "",
  "financial_transmission_mechanism": "",
  "attribution": "",
  "operating_or_risk_boundary": "",
  "priority_action": "",
  "leading_indicator_and_falsifier": "",
  "data_gap": ""
}
```

若没有可用公开管理层表述，`management_statement` 写“未找到可审计的公开管理层表述”，`statement_verification` 写“本问题仅基于财务披露验证”。不得编造路演信息。

### 6.7 scenarios

只有触发情景分析时填写。必填：

- `scenario_id`
- `management_question`
- `driver`
- `driver_to_result_rationale`
- `input_basis`
- `output_type`
- `action_implication`
- `limitations`

关系弱时 `output_type` 使用 `directional_risk_tree`，禁止输出精确数字。

### 6.8 actions

每个行动必填：

- `action_id`
- `related_issue_id`
- `proposed_action`
- `expected_financial_mechanism`
- `owner_type`
- `leading_indicator`
- `warning_threshold_logic`
- `calibration_data_needed`
- `risk_of_false_positive_or_negative`

### 6.9 quality

必填：

- `credibility_score`
- `insight_score`
- `decision_value_score`
- `expression_visual_score`
- `blocking_failures`
- `warnings`
- `audit_status`
- `delivery_decision`

## 7. 指标口径纪律

每个关键指标必须保留原始披露名称和定义指纹。跨期或同行对比前先判断定义是否一致。

必须防止：

- 归母净利率和合并口径销售净利率混称为“净利率”。
- 税前和税后指标直接桥接。
- 季度数据混入年度 CAGR 或年度利润率序列。
- 利润到经营现金流桥与资金净变动桥混用。
- 自定义 KPI 未保留原始定义、覆盖范围、排除项、期间口径和币种。

自定义 KPI，如 ARR、NRR、RPO、bookings、billings，只有在明确连接收入、利润、现金或资本效率时才能进入核心判断。

## 8. Claim 语言规则

| Claim level | 允许写法 | 禁止写法 |
|---|---|---|
| `disclosed_fact` | 公司披露、报告显示 | 推导管理动机 |
| `calculation` | 按公式计算为、同比变化 | 直接解释因果 |
| `supported_inference` | 表明、指向、与某机制一致 | 写成确定事实 |
| `hypothesis_requires_validation` | 可能、假设、需要验证 | 放进无保留核心结论 |

任何 unsupported causality 都必须降级为假设或删除。

## 8.1 经营者表述语言规则

管理层公开表述不等于事实。正文必须区分：

- “公司披露”：定期报告、公告、审计报告中的财务事实或正式解释。
- “管理层公开表述”：业绩说明会、IR 活动记录、路演、公司公开交流材料中的解释或计划。
- “本报告判断”：基于财务数据、公开表述和缺口做出的支持性推断。

推荐句式：

```text
财报披露……；管理层在公开交流中进一步解释……；从已披露财务数据看，该表述目前得到……支持/仅得到部分支持/尚不能验证。
```

禁止句式：

- 管理层说了，所以事实就是如此。
- 公开交流提到某策略，因此该策略已经兑现。
- 未披露同店、订单、库龄或客户细节时，用模型推测补全。

## 9. 同行分析规则

同行分析只回答：

> 这是行业共性问题，还是公司自身问题？

要求：

- 2-4 个真正可比同行。
- 3-5 个与核心问题相关的指标。
- A/B/C 可比性评级。
- C 级可比不写领先、落后、排名或优劣判断。

同行分析的价值是归因，不是排名。

## 10. 情景与压力测试规则

只有满足以下条件才做：

- 有明确驱动因素。
- 驱动到结果的关系可解释。
- 结果会改变管理动作。
- 输入来自历史、行业数据、公司指引或显式假设。

优先使用：

- 敏感性分析。
- 边界测试。
- 组合压力测试。
- 反向压力测试。

阈值不能编造。可以写阈值逻辑和需要哪些内部数据校准。

## 11. 图表选择规则

取消固定六图和最低图表数量。

先问：

> 这张图是否缩短了读者理解管理问题的路径？

推荐图表：

- 价格-销量-结构或 driver bridge。
- 增长-毛利或 profit-pool matrix。
- 利润桥。
- 利润到经营现金流桥。
- 资金流动桥，必须明确区别于利润到现金。
- 同行标准化趋势或 small multiples。
- 敏感性矩阵或边界曲线。
- 债务期限和现金覆盖。
- 管理目标与实际对照。
- 管理层表述与财务验证矩阵。
- 风险树。

图表标题、takeaway、单位放在图正文上方。正文与图表宽度保持一致。单图通常不超过四种颜色。无决策价值的图不画。

## 12. 阻断项和评分上限

阻断交付：

- 关键指标定义冲突。
- 核心结论缺可追溯来源。
- 关键公式或勾稽失败。
- 假设写成事实。
- 判断面板结论无证据。
- 跨期定义漂移未披露。
- 使用报告 cutoff 之后的信息。
- 图表类型误导财务机制。

评分权重：

- 可信度 35%。
- 洞察 25%。
- 决策价值 25%。
- 表达与视觉 15%。

评分上限：

- 关键指标定义冲突：最高 6.0。
- 关键来源不可追溯：最高 6.5。
- 假设写成事实：最高 6.5。
- 桥或计算无法勾稽：最高 7.0。
- 分析没有边界或动作：最高 7.5。
- 章节完整但没有核心矛盾：最高 7.5。

## 13. 交付流程

必须按顺序执行：

```text
1. 收集披露并确定 cutoff
2. 检索公开管理层表述来源；找到则构建 management_statements，未找到则记录缺口
3. 构建 analysis_bundle.json
4. 运行 scripts/audit_bundle.py
5. 修复 bundle 的 blocking failures
6. 基于 bundle 写 HTML 报告
7. 运行 scripts/audit_report.py
8. 修复 HTML 和视觉 FAIL
9. 交付 analysis_bundle.json、财务分析.html、audit_report.html
```

如果 bundle 审计失败，不得把 HTML 当作正常报告交付。
