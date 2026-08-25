# CUMCM Idea Combined Output Contract

Create exactly one UTF-8 Markdown document named `CUMCM_IDEA.md` unless the user requests another safe filename.

## Required heading order

1. `# <题目名称>｜CUMCM Idea` 
2. `## 0. 文档状态与输入范围`
3. `## 1. 整题概览`
4. `## 2. 逐句题意翻译与覆盖台账`
5. `## 3. 核心术语与统一口径`
6. `## 4. 各问输入—任务—输出表`
7. `## 5. 题意层跨问题联动链`
8. `## 6. 最容易漏读、误解或需要确认的内容`
9. `## 7. Phase-1 完整性核验`
10. `## 8. 整题建模主线`
11. `## 9. 全文共享变量、约束与评价口径`
12. `## 10. 分问题候选建模思路`
13. `## 11. 推荐的全文技术路线`
14. `## 12. 多模型对比、验证与风险设计`
15. `## 13. 论文、代码、图表与结果文件落地清单`
16. `## 14. 完整性、断链与阻断项检查`
17. `## 15. 给 cumcm-t2 的交接说明`

## Section contracts

### 0. 文档状态与输入范围

Include:

- `HANDOFF_STATUS`;
- contest/year/problem ID when known;
- actual problem-title anchor;
- source files and their versions or modification dates when available;
- attachments inspected, attachments described but unavailable, and unreadable/OCR-uncertain material;
- generation date;
- explicit statement: `本文件是候选思路文档，不是冻结模型合同，也不包含真实求解结果。`

### 2. 逐句题意翻译与覆盖台账

Use:

| 编号 | 题干原句 | 通俗而精确的翻译 | 明示条件/数据 | 隐含建模信号 | 与前后内容的联动 | 漏读后果 | 后文必须出现的证据 | 来源页码/位置 |
|---|---|---|---|---|---|---|---|---|

Keep every substantive source unit exactly once. Preserve exact source sentences without ellipses. Escape literal pipes as `\|` and replace internal newlines with `<br>`.

### 3 and 9: terminology versus modeling convention

Section 3 records prompt-defined or ambiguous terms and the adopted reading. Section 9 defines the proposed modeling notation and shared conventions. Do not present a modeling choice as if it came from the prompt.

### 4. 各问输入—任务—输出表

Use:

| 问题 | 直接输入 | 需要解决的任务 | 必须满足的约束 | 最终输出 | 依赖前问内容 | 将被后问复用的内容 | 验收证据 |
|---|---|---|---|---|---|---|---|

### 5. 题意层跨问题联动链

Use one primary fenced Mermaid block beginning with `flowchart TD` or `flowchart LR`.

- Represent every numbered question with a distinct node.
- Label every edge with the actual transferred definition, data, parameter, result, constraint, or validation evidence.
- Use parallel branches and return links when the prompt requires them.
- End at the actual whole-problem deliverable.
- Keep this graph semantic: do not insert an unselected model as though the prompt required it.

### 7. Phase-1 完整性核验

Report source-unit count, ledger-row count, question count, represented questions, attachment coverage, missing input, unresolved ambiguity, OCR uncertainty, excluded boilerplate, deliverables covered, and Mermaid completeness.

### 10. 分问题候选建模思路

For every numbered question, keep this order:

1. `问题概述` — task, known conditions, exact output, mathematical essence;
2. `总体求解思路` — input-to-output logic and cross-question interfaces;
3. `可用模型及选型比较`;
4. `创新与改进方向`.

Candidate table:

| 候选模型/思路 | 模型本质与核心变量 | 可执行步骤 | 数据与假设 | 优点 | 局限/失败风险 | 验证方法 | 前后问接口 | 适用条件 |
|---|---|---|---|---|---|---|---|---|

After it, state:

- `建议主方法`;
- `建议 usable baseline`;
- `条件备用（至多一个）` and its trigger;
- selection rationale;
- fair comparison design.

These are candidates, not frozen decisions.

Innovation table:

| 创新或改进 | 基础方案 | 具体改动 | 预期可检验改进 | 新增工作量 | 对照指标 | 风险与备用 | 影响问题 |
|---|---|---|---|---|---|---|---|

### 11. 推荐的全文技术路线

Give one coherent end-to-end route from data inspection through formulation, solution, validation, sensitivity/uncertainty analysis, and required deliverables. A second Mermaid technical-route graph is allowed here. Clearly label all model components as proposed.

### 12. 多模型对比、验证与风险设计

Match important proposed claims to independent evidence. Include applicable checks such as baseline comparison, held-out/entity/time validation, forward reconstruction, conservation/invariance, constraint recomputation, residual/calibration, convergence, repeated seeds, sensitivity, uncertainty propagation, and high-fidelity audit.

### 13. 落地清单

Separate mandatory from optional items. List expected formulas, algorithms, datasets, result tables, figures, metrics, units, precision, result files, and appendix code. Do not list invented numerical values.

### 14. 完整性、断链与阻断项检查

Check every question, subquestion, constraint, attachment, deliverable, dependency, proposed model input, and validation route. Identify incompatible definitions, circular dependence, leakage, unavailable data, unsupported assumptions, or outputs that cannot feed later questions.

### 15. 给 cumcm-t2 的交接说明

Include this meaning explicitly:

1. `CUMCM_IDEA.md` is a self-contained interpretation and candidate-plan handoff, not a frozen artifact.
2. The original problem, attachments, and official rules override this file.
3. Rebuild and freeze `PROBLEM_CONTRACT.md` before model freezing.
4. Run data/assumption/output-degeneracy/perturbation/scale risk probes before selecting the main method.
5. Freeze `MODELING_REPORT.md` before coding.
6. Obtain all paper numbers from executed and verified code, never from hypothetical examples in this file.

## Final validation

Before delivery confirm:

- exactly one Markdown output exists;
- no placeholder remains;
- all required headings appear once and in order;
- every source unit and numbered question is covered;
- every Mermaid block used is syntactically plausible and uses unique ASCII node IDs;
- tables have consistent columns after escaped pipes are accounted for;
- no candidate method is mislabeled as prompt fact or frozen decision;
- no fabricated result, score, accuracy, coefficient, or optimum appears;
- the handoff status matches the actual missing-input and ambiguity state.
