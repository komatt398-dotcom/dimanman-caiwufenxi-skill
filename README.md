[README.md](https://github.com/user-attachments/files/31011124/README.md)
# 迪慢慢财报分析 Skill

面向上市公司年报、半年报和季度报告的财务分析 Skill。它不是把财报复述一遍，而是把财务数据、管理层公开表述、指标口径和图表审计放进同一条验证链，帮助读者判断经营问题、风险边界和后续动作。

## 适合什么场景

- A 股、港股、美股上市公司多年财报分析
- 管理层经营诊断、业务复盘、经营分析会材料
- 年报/半年报/季报中的收入、利润、现金流、研发、人员、债务和存货分析
- 需要来源追溯、指标口径校验、图表质量门禁和审计报告的研究报告

## 核心思路
<img width="2136" height="1140" alt="image" src="https://github.com/user-attachments/assets/75665a8a-2f8e-47bc-98e0-e0e04260a661" />
报告默认以最近三年年报为主序列；若有最近一期半年报或季报，则作为单独更新模块，不混入年度趋势。

每个核心判断都要求完成：

```text
judgment -> evidence -> management_statement -> verification -> mechanism
-> attribution -> boundary -> action -> indicator -> falsifier
```

这意味着报告不仅回答“数字变了多少”，还要回答：

- 管理层过去怎么解释市场、产品、渠道和风险？
  <img width="2122" height="898" alt="image" src="https://github.com/user-attachments/assets/7d4ac099-64d4-4127-a4d8-5573a40485a0" />
- 财务数据是否支持这些说法？
  <img width="2048" height="700" alt="image" src="https://github.com/user-attachments/assets/288278ae-aa9f-44f7-b75f-601922c4fb85" />
- 利润是否真正转成现金？
  <img width="1970" height="950" alt="image" src="https://github.com/user-attachments/assets/7f767e69-3d89-4223-8c57-a4896a8b7cc2" />
- 增长来自客户、产品、渠道还是价格/周期？
- 哪个指标会推翻当前判断？

## 固定交付物

每次分析建议输出三件套：

```text
公司名-analysis_bundle.json
公司名-财务分析.html
公司名-audit_report.html
```

- `analysis_bundle.json`：事实、来源、口径、计算、claim、issue 和管理层表述验证链
- `财务分析.html`：面向读者的管理诊断报告
- `audit_report.html`：bundle 和 HTML 的质量门禁结果

## 质量门禁

内置脚本会检查：

- 来源与指标口径是否可追溯
- 关键 claim 是否有证据链
- 数值表是否有独立单位列
- 表格是否全部右对齐
- 年份表头是否写成完整字段，如 `2025年`
- 图表标题、结论、单位、来源是否齐全
- SVG 数据点是否有 `<title>` tooltip
- 图表标签是否碰撞、画布是否有异常空白
- 客户销售指标和供应商采购指标是否被错误混图
- 是否出现 AI 式口号、粗糙话术或未闭合的“待补充”

## 使用方式

在支持 Codex Skill 的环境中，把本目录放到 skills 目录下，然后在对话中输入：

```text
/dimanman-caiwufenxi
```

建议先准备公司定期报告、公告、业绩说明会或投资者关系活动记录。财务数字以定期报告和公告为准，路演和说明会仅作为管理层解释来源。

## 目录结构

```text
dimanman-caiwufenxi/
  SKILL.md
  meta.json
  references/
  scripts/
  examples/
```

## 示例

`examples/` 中包含一份示例分析包和 HTML 报告，可用于观察输出结构、图表样式和审计要求。

## 边界

- 不提供投资评级、目标价或股价预测
- 不把假设写成事实
- 不用路演内容覆盖财务数字
- 不把“章节齐全”当作分析质量
- 不自动修改自身文件，除非用户明确要求更新 skill
