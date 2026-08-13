# 财报报告视觉系统 v3.1

这份参考文件只解决“读者如何扫描报告”和“图表如何帮助判断”，不替代数据口径或财务分析逻辑。

## 设计判断

将财报 HTML 视为一份管理诊断报告，而不是网页首页：

- 读者是管理层、业务负责人或投委会，首先要知道结论、边界、反证和行动。
- 视觉密度取 7/10，版式自由度取 4/10，动效取 2/10。
- 使用浅暖灰画布、米白正文和单一公司强调色。禁止深蓝整块判断面板、渐变、彩虹配色、卡片套卡片和装饰性背景。
- 中文正文使用系统中文字体栈；数字保持可扫描，字号不小于 12px，轴标签不小于 11px。

## 页面骨架

```text
报告头部：公司名 / 年份 / 一句话说明
判断面板：核心判断 + 状态 + 主要矛盾 + 盈利质量 + 现金债务边界 + 反证
口径与来源：折叠为方法说明，不抢首屏
正文、图表和表格：统一证据列（约 1040px）
动态模块：根据管理问题选取，不强制七段
```

首屏必须先出现判断面板。数据来源、公司概况和方法说明可以保留，但不得在视觉顺序上压过核心判断。判断面板使用米白两列模块，顶部只写“判断面板”，内容中的“核心判断”只出现一次，卡片半径不超过 6px。

五问自检在 v3.0 中是后台审计门，不再要求每个章节都显式排成五块。若需要在正文中展开，事实、解释、质量、影响、反证可以分行呈现，但不强制章节模板化。

章节层级主要依靠留白、字号和短小强调标记，不使用贯穿内容列的装饰性横线。图表不使用上下分隔线或外框，标题、结论、单位构成独立图题区，图表下方紧接来源；不要给每张图套厚重阴影卡片。表格可以横向滚动，但桌面端不应出现无意义的嵌套容器。

连续事实、影响、分析、红线、必盯指标必须分行陈列。两个及以上事项使用 01 / 02 / 03 连续编号；单个事项使用短横标记，不显示 1.。禁止因 Markdown 空行把同一组有序列表拆成多个从 1. 开始的列表。

## 图表语法

每张图只回答一个命题，并按以下顺序生成：

1. 标题写“指标 + 时间范围”，由 HTML 放在 SVG 绘图区上方，不写“图 1”或空泛标题。
2. takeaway 放在标题下方、绘图区上方，写完整判断，不复述标题。
3. 单位由 HTML 图题区显示在 takeaway 下方，不放在 SVG 裁剪边界内；零轴在负值图中明确可见。
4. 只给终点、异常点或关键年份显示文字；完整数值放进 SVG `<title>` 或 ECharts tooltip。
5. 图例只解释系列，单一系列不显示“数值”图例。
6. 颜色按语义分配：公司主色表示主线，绿色表示正向改善，砖红表示亏损/风险，灰色表示基准或不可比项。单图最多 4 种数据点颜色。
7. 横向条形已经有条末数值时，不再显示横轴、刻度和单位；费用率多年序列使用折线。
8. 净利率桥和现金流桥必须首尾衔接，终值从零轴绘制；现金净变动只作为终值出现一次。
9. 债务图不在绘图区放覆盖倍数、负债率等长段文字；这些判断进入 takeaway 或正文。

推荐图型：

| 命题 | 推荐图型 | 不要做 |
|---|---|---|
| 规模与利润是否同向 | 双系列折线或并列柱 | 两个无解释的独立大数字 |
| 谁是利润池、谁在拖累 | 增长-毛利散点矩阵 | 拥挤的分组柱 |
| 净利率为什么变 | 瀑布桥 | 只列出费用率的折线 |
| 利润如何变成现金 | 现金流桥 | 只放经营现金流折线 |
| 债务是否越过边界 | 债务压力图 | 仪表盘、评分环、进度条 |
| 管理层是否兑现承诺 | 判断-兑现时间线 | 只摘录管理层原话 |
| 管理层公开表述是否被数据支持 | 表述-验证矩阵或小型对照表 | 把路演内容做成语录墙 |

## 语言系统

报告应像财务负责人、经营分析经理或审计沟通材料中的自然表达，不像模型给概念命名。优先使用财报、审计报告、业绩说明会和公开场合常见语言。

避免模型式命名：

| 禁用或慎用 | 推荐表达 |
|---|---|
| 收缩式提质 | 关闭低效门店、放缓低回报扩张、提高单店经营质量 |
| 非内生扩张 | 并购扩张、外延扩张；能不用则不用 |
| 增长换挡期 | 收入增速放缓；从门店数量扩张转向存量门店经营 |
| 剪刀差扩大 | 收入、利润和现金流变化方向不一致 |
| 经营现金流下滑，是扰动还是趋势 | 经营现金流下降需区分结算时点影响和营运资本变化 |
| 经营现金流变动桥 | 净利润调节为经营活动现金流净额的分项分析 |
| 行业出清期 | 有行业证据才写；否则写行业竞争加剧、价格压力或删除 |
| 优先行动卡 | 管理建议、后续关注事项、监控清单 |
| 现金转换驾驶舱 | 现金流监控表、营运资本跟踪表 |

写作要求：

- 不给普通财务现象强行起名。若一个词不能自然出现在董事会材料、审计沟通或业绩说明会中，改写。
- 少用抽象判断，多写“哪个指标变化、与哪个表述是否一致、还缺哪个数据”。
- 标题避免口号化。用 `收入增速与零售毛利率`，不要用 `增长质量再验证` 这类泛化标题。
- “管理建议”不要写成咨询模板。用动作、责任口径、观察指标和触发条件表达。
- 管理层公开表述必须标注来源身份，不能写成事实本身。

## ECharts 使用边界

浏览器交互报告可以使用本 skill 同目录的 ECharts 本地构建文件或项目已有依赖。不要默认使用 CDN，确保离线打开和 Edge 打印仍能得到完整报告。静态 SVG 仍是默认交付格式，原因是它可审计、可打印、无运行时依赖。

使用 ECharts 时遵循：

- 优先 `dataset` + 明确的 `encode`，让指标、年份和单位保持可追溯。
- `grid.containLabel = true`，给标题、takeaway、坐标轴和底部图例留出稳定空间。
- 使用 `aria.enabled = true`；tooltip 负责完整读值，图内只标注关键点。
- 负值图显式设置 `yAxis.min`/`max` 或使用包含零轴的范围，禁止把负柱压成零。
- 使用 `markLine` 标出零轴或业务红线，使用 `markArea` 只标注有解释价值的区间。
- 关闭无意义动画；打印和 `prefers-reduced-motion` 下不依赖动画传达信息。

参考配置骨架：

```js
const option = {
  animation: false,
  aria: { enabled: true },
  color: [accent, positive, negative, neutral],
  grid: { left: 64, right: 24, top: 72, bottom: 78, containLabel: true },
  tooltip: { trigger: "axis", confine: true },
  xAxis: { type: "category", axisTick: { show: false } },
  yAxis: { type: "value", splitLine: { lineStyle: { color: "#E5E7EB" } } },
  series: [{ type: "line", showSymbol: false, emphasis: { focus: "series" } }]
};
```

## 交付前检查

- 首屏截图在 1440px 和 390px 宽度下都先看到判断面板。
- 图表标题、takeaway、单位、来源均可读；单位只出现一次且位于 SVG 上方，图例不与单位重叠。
- 章节与图表周围没有连续贯穿内容列的装饰性横线。
- 事实、影响、分析、红线和必盯指标按事项分行；没有连续重置的 1.。
- 单图颜色不超过 4 种；负值柱向零轴下方延伸。
- 图表和表格不会被分页拆成难以阅读的两半。
- HTML 离线打开、浏览器缩放、A4 打印均不依赖外部网络资源。
- 正文呼吸感来自段落、章节、图表 figure 外侧的 margin；图表绘图区本身必须紧凑，不得用 SVG 空白、CSS `min-height` 或过大的 ECharts `grid` 留白来制造版面感。


## 2026-08-12 Cambricon Regression Rules

These rules come from the Cambricon report revision and override generic chart aesthetics:

- Passing audit is not enough. If a chart has odd grammar, overlapping labels, confusing units, or non-mainstream visual form, treat the report as failed.
- If the chart heading says `unit: %`, numeric labels inside the plot must not repeat `%`. Default percentage precision is 1 decimal place; use 2 decimals only for exact reconciliation or direct disclosure reproduction.
- Do not force mixed units into one bar chart or one axis. Inventory amount, inventory/assets %, and supplier procurement % should become a table, small multiples, or separate visuals.
- Do not put explanatory sentences inside the SVG plotting area, such as axis-exemption notes. Put reading guidance in takeaway, body text, or source note.
- When readers need point-by-point comparison on a line chart, show compact labels at each point and offset labels to avoid covering points, lines, or bars.
- Avoid dual-axis and bar-line charts unless both scales are necessary and label placement is proven clean. If scales conflict, use small multiples or a chart plus table.
- Profit-to-operating-cash-flow analysis must prefer the cash-flow-statement reconciliation bridge: net profit -> non-cash items -> inventory/receivables/payables -> operating cash flow. A simple operating-cash-flow trend is not a substitute.
- Cash bridges must be visually connected from start to end, with the terminal value drawn from the zero axis. Keep an auditable terminal marker in SVG titles while using business-readable visible labels.
- Management market view is a high-value module. If disclosures contain industry view, product route, software ecosystem, or risk boundary, synthesize a judgment timeline instead of only restating financial metrics.
- If two adjacent list items are both facts supporting the same point, merge them into one `fact synthesis` item.
- Use a stable low-saturation palette. Risk red is reserved for risk, drag, and falsifier items; do not use it as ordinary emphasis.

- Final reports must not contain production-process language such as `previous version`, `this revision`, `changed to`, or `put back into a table`. Explain the analytical reason in the reader's language.
- For metrics with different units but one analytical theme, use small multiples, separated panels, or a table. Example: R&D amount and R&D/revenue rate can share one figure only if the SVG is split into separate scale bands.
- Axis ticks are allowed only when they help decode magnitude. If each point/bar already has a compact numeric label, keep axes sparse and remove redundant gridlines.

- Never title a chart `growth concentration` when it mixes revenue composition, customer concentration, and supplier concentration. Split into revenue structure, customer concentration, and supply-chain concentration.
- In revenue/channel sections, use positive analytical labels such as `revenue composition`, `customer concentration`, and `supply-chain concentration`. Do not use a negated title like `not growth concentration`; it keeps the ambiguous phrase in the reader's mind.
- Customer metrics and supplier metrics must not appear in one horizontal bar chart unless clearly grouped as separate panels with different headings. A supplier is not a customer.
- Use explicit time ranges in Chinese titles: write `2023年-2025年`, not `2023-2025`, when it could be mistaken for subtraction.
- Judgment paragraphs must distinguish source disclosure from report inference. Avoid vague wording like `this line is valuable`; write `from disclosed evidence, this report uses it as...` or remove the sentence.
- In the judgment panel, use statutory term names consistently. Prefer `存货` over colloquial `库存` when the cited metric is inventory from financial statements.
- All numeric tables must use an explicit `单位` or `unit/scope` column. Do not use standalone unit rows such as `unit-row`; they create empty-looking columns and reduce report professionalism.
- Timeline or judgment charts must label growth metrics with full口径, e.g. `2025收入同比+453.2%`, not `收入+453.2`. A plus sign without denominator/time basis is invalid.
- Final prose should read like a professional report, not narrator notes. Avoid phrases such as `这里必须`, `这一段的管理含义`, `积极的一面/谨慎的一面`, and `从管理层视角看`; use direct section leads and evidence-backed conclusions.
- R&D sections must distinguish disclosed R&D input from income-statement R&D expense. If R&D input excludes share-based payment or has zero capitalization, state the口径 before interpreting efficiency.
- R&D quality cannot be proven by patent count alone. Separate invention patents, utility models, design patents, software copyrights, IC layout designs, current technical problems, model/framework adaptation, and missing commercial conversion metrics.
- Sales-channel diagnosis should seek direct/dealer revenue, selling expense ratio, sales staff count/share, customer concentration, new vs long-term customers, customer service/brand/ecosystem disclosures, and disclose gaps before recommending expansion or contraction.

- Chart canvases must be compact. After excluding hidden accessibility text at x/y=-9999, visible marks and labels should normally end within 24px of the SVG bottom; if bottom whitespace is larger, reduce `viewBox` height and SVG `height` instead of leaving a large blank plotting area.
- Do not set a desktop CSS `min-height` on `.chart-container svg`. Compact charts should keep their intrinsic SVG ratio; only mobile/print overrides may remove minimum height constraints.
- Compactness applies to both directions: visible marks and labels should not begin after a large empty top band. Do not push the plot downward to avoid label collision; change the scale, viewBox, label offsets, or chart type.
- For waterfall/cash bridge charts, the x-axis labels, value labels, and bars must not overlap. If negative bars approach the axis labels, reduce chart height only after moving label baselines, shrinking bar width/gap, or using staggered labels.
- Table alignment is a hard contract: all table headers and body cells use right alignment. Do not mix left/center/right alignment inside one report unless the user explicitly asks for a different table system.
- Year headers in tables must be complete fields: write `2023年`, `2024年`, `2025年`, not `2023`, `2024`, `2025`. Use `2026H1` or `2026年上半年` consistently for interim periods.
- Table commentary headers should use `说明` or `解读`; do not use `读法`.
- Revenue/channel charts may include revenue composition, region, sales mode, and customer sales concentration. Supplier procurement concentration belongs to supply-chain analysis or a table row, not the same ungrouped revenue chart. A supplier is not a customer.
- Default analysis period is the latest three audited annual reports. If the latest interim report is available, use `two full fiscal years + latest interim update` only in a separate update module; do not let the interim period replace the three-year annual baseline.
- Specific metric tables should follow the default period whenever disclosed. If a metric is only disclosed for the latest year, show the missing years as `—` and say `未单独披露`, rather than presenting a single-year row as if it were a trend.
- Revenue/channel analysis should actively look for selling expense, selling expense ratio, sales staff count, sales staff share, total staff, revenue per sales staff, direct/dealer mode, customer concentration, and market development/brand activity disclosures. If not disclosed, list the gap instead of inferring it.
- R&D analysis should cover every disclosed year in the default period. If only 2024/2025 R&D input or expense is available, show those years and mark 2023 as `—` or omit only with a clear source-boundary note.
