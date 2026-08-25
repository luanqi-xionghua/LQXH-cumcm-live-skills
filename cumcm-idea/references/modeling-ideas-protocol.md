---
name: bzd-modeling-ideas
description: Generate a coherent, whole-paper mathematical modeling solution framework from a complete contest problem. Use after the user supplies a CUMCM or other modeling problem and asks for modeling ideas, an overall solution plan, question-by-question analysis, candidate-model comparison, model-selection reasons, innovations, validation, or cross-question linkage. For every question, explain the task and mathematical essence, compare multiple feasible models in tables, recommend a route with explicit reasons, and keep all questions connected through shared data, variables, parameters, constraints, and validation.
---

# BZD Modeling Ideas

> Imported into `cumcm-idea` as the Phase-2 protocol. It must consume the completed Phase-1 ledger and write into the single combined handoff document rather than creating a separate modeling report.

Produce solution ideas with a whole-problem perspective. Build one coherent paper-level modeling system instead of attaching unrelated model names to separate questions.

This Skill is distilled from the problem statements, scoring rules, reviewer points, review summaries, and complete review workflows of 16 Higher Education Press Cup CUMCM problems from 2020–2025. Use historical materials to learn transferable expectations: complete task coverage, appropriate model choice, cross-question continuity, credible computation, independent validation, and implementable innovation. Never copy a historical model or numerical conclusion into a new problem without current-problem support.

## Input

Require:

- the complete problem statement and every numbered/sub-question;
- attachment descriptions, data dictionaries, figures, notes, and required output files;
- actual attachment data when data inspection affects model choice.

Phase-1 台账由本控制器先行生成，必须作为唯一题意输入：使用其句账、隐藏条件、输入—任务—输出表与联动图，不得在 Phase-2 重新解读题干。

Do not invent missing data, coefficients, results, accuracy, or official preferred methods. Mark unavailable information and give conditional branches where it changes the route.

## Required references

Read completely before generating the report:

- [integrated-modeling-patterns.md](integrated-modeling-patterns.md)
- [strategy-output-standard.md](strategy-output-standard.md)
- [cumcm-idea-output-contract.md](cumcm-idea-output-contract.md)

## Core workflow

1. Reconstruct the full task graph before analyzing any single question.
2. Extract shared objects, data, indices, variables, parameters, units, coordinate/time systems, constraints, objectives, and evaluation metrics.
3. Identify each question's role: foundation, estimation, explanation, prediction, extension, optimization, decision, or validation.
4. Define interfaces between questions. State which earlier output becomes a later input, parameter, baseline, constraint, initial value, or validator.
5. Design a shared modeling backbone that can run through the whole paper. Preserve physical, statistical, temporal, spatial, recursive, and decision structures when present.
6. For each question, perform the required four-part analysis below and give genuinely distinct candidate models.
7. Compare candidate models on the same task and output. Explain selection from suitability, assumptions, data, interpretability, accuracy, implementation cost, validation, and downstream compatibility.
8. Recommend a paper-level model combination. Avoid selecting locally attractive models that create incompatible definitions or broken data flow across questions.
9. Add verifiable innovations and improvements. Every proposal must state the changed component, implementation, measurable comparison, risk, and fallback.
10. Audit every explicit requirement, sub-question, attachment, deliverable, constraint, and cross-question dependency.

## Required Phase-2 content

Write the following material into the Phase-2 sections of the single `CUMCM_IDEA.md` document. The combined output contract controls the final heading order; do not export a separate modeling-ideas report.

### 协议内容 → 合同章节映射

| 本协议内容 | 输出合同章节 | 说明 |
|---|---|---|
| 1. 整题建模主线 | 第 8 节 | 一一对应 |
| 2. 跨问题联动链 | 第 5 节（禁止复制）＋第 11 节（仅技术路线图） | 语义联动图已在第 5 节生成，Phase-2 不得重复输出 |
| 3. 全文统一建模口径 | 第 9 节（全文共享变量、约束与评价口径） | 与第 3 节题目术语表分离 |
| 4. 分问题求解思路 | 第 10 节（分问题候选建模思路） | 合同版以“候选”表述，未冻结 |
| 5. 推荐的全文技术路线 | 第 11 节 | 可含第二张技术路线 Mermaid 图 |
| 6. 多模型对比与验证设计 | 第 12 节 | 一一对应 |
| 7. 论文落地清单 | 第 13 节 | 一一对应 |
| 8. 完整性与断链检查 | 第 14 节 | 一一对应 |

### 1. 整题建模主线

Explain the research object, central contradiction, final goal, foundational model, and the progression among questions. State the recommended shared backbone and why it can run through the entire paper.

### 2. 跨问题联动链

语义联动图已在第 5 节生成，此处禁止复制；如需技术路线图，只放入第 11 节。

### 3. 全文统一建模口径

Use a compact table to define shared symbols, index sets, variables, parameters, units, coordinate/time conventions, preprocessing rules, constraints, objectives, and metrics. State which questions use each item.

### 4. 分问题求解思路

For every numbered question, write `问题分析` in this exact sequence.

#### 4.x.1 问题概述

Briefly state:

1. what must be solved;
2. what conditions and inherited results are known;
3. what exact result must be obtained;
4. which mathematical model family the problem essentially belongs to and why.

Separate problem-given conditions from newly introduced assumptions.

#### 4.x.2 总体求解思路

Describe the complete logic from raw data or known conditions to the requested result. Explain the main processing, formulation, solution, and validation steps and how they connect. Identify inputs inherited from earlier questions and outputs supplied to later questions.

#### 4.x.3 可用模型及选型比较

Give at least two genuinely different feasible models when possible; prefer three when meaningful mechanism, statistical, or computational alternatives exist.

| 可行模型/思路 | 模型本质与核心变量 | 完整实现步骤 | 所需数据与假设 | 优点 | 局限与失败风险 | 验证方法 | 与前后问题的接口 | 适用场景 |
|---|---|---|---|---|---|---|---|---|

After the table, provide:

- `推荐模型`：name the primary route;
- `选用理由`：explain task fit, data support, assumptions, required output, scoring concerns, and later-question compatibility;
- `备选模型`：state when another route should replace it;
- `多模型对比建议`：state how to compare models fairly using common data, constraints, metrics, uncertainty, and computational budget.

Do not list models that cannot produce the requested result. Do not treat a solver name as a model. Merge alternatives that differ only by superficial settings.

#### 4.x.4 创新与改进方向

| 创新或改进方向 | 基础方案 | 具体改动与实现步骤 | 预期改进 | 新增工作量 | 验证指标与对照实验 | 风险及备用方案 | 影响的问题 |
|---|---|---|---|---|---|---|---|

Innovations may include mechanism refinement, coupling, adaptive resolution, robust/uncertain formulation, dependence-aware statistics, hybrid solving, error propagation, independent validation, or operational decision improvement. `使用遗传算法`、`模型融合`、`增加可视化`、`考虑更多因素` alone are not innovations.

### 5. 推荐的全文技术路线

Select one coherent combination across all questions. Give the sequence from data reading and exploratory checks through formulation, solution, validation, sensitivity/uncertainty analysis, and required deliverables. Explain why this combination is globally coherent and why alternatives are retained only as comparisons or fallbacks.

### 6. 多模型对比与验证设计

Define fair comparison experiments for important alternatives. Match every important claim to an independent check such as forward reconstruction, conservation/invariance, residual/significance, held-out validation, calibration, sensitivity, uncertainty propagation, convergence, feasibility recomputation, baseline comparison, or high-fidelity audit.

### 7. 论文落地清单

List formulas, algorithms, data tables, result tables, figures, flowcharts, metrics, units, precision, files, and appendix code. Separate mandatory deliverables from optional enhancements.

### 8. 完整性与断链检查

Confirm coverage of every question, sub-question, constraint, attachment, output, and dependency. Identify missing data, unsupported assumptions, incompatible definitions, circular dependence, leakage, unvalidated conclusions, or outputs that cannot feed the next question.

## Quality rules

- Reward fit and completeness, not model prestige.
- Prefer one shared backbone plus justified extensions over unrelated per-question models.
- Preserve feasibility before optimization and verify final schemes in the original system.
- Compare candidate models on identical targets and compatible metrics.
- Reuse shared parameters consistently and propagate uncertainty when later decisions depend on estimates.
- Treat validation as part of each model, not a generic final paragraph.
- Make every table cell implementable; avoid vague steps such as `进行数据处理` or `使用优化算法`.
- State ambiguity and scenario branches rather than silently choosing an interpretation.
- Do not fabricate results or claim that a method is officially preferred.
