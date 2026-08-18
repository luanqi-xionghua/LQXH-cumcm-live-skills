# CUMCM-Review 报告

- 审查时间: `{datetime}`
- 审查对象: `{pdf_path}`（SHA-256 `{sha}`，{pages} 页）
- 审查基线: {baseline}（上一版 PDF/frozen SHA，可选；有则做差异审查）
- 审查模式: {mode}（只读）
- 规则依据: {rules}（未提供 → 合规维度标“未核验”）

## 结论摘要

- 总体评分: {score}/10
- P0: {p0} 项 | P1: {p1} 项 | P2: {p2} 项 | 未核验: {na}

### Top 5 问题

1. [P1] {title} — {location}：{one-line}
2. ...

## 问题清单

### P0（提交级阻塞）

- [P0] **{title}** — {location}
  - 证据：{evidence}
  - 置信度：{confidence}
  - 修复建议：{fix}
    - 受影响上游：{upstream: contract/model_freeze/run_id}
    - 建议重跑：{command}

### P1（应修复）

...

### P2（建议改进）

...

## 9 维度结论

| 维度 | 结论 | 说明 |
|---|---|---|
| 数字可回溯 | PASS/WARN/FAIL/未核验 | ... |
| 跨节一致性 | ... | ... |
| 合规性 | ... | ... |
| 排版质量 | ... | ... |
| 反AI五查 | ... | ... |
| 图表完整性 | ... | ... |
| 文献与对照 | ... | ... |
| 可复现性 | ... | ... |
| 方法学健全性 | ... | 共线性/删失不可识别性/阈值泄漏/小样本/伪精确（维度9） |

## 总体评估

### 优点
- ...

### 风险与残余问题
- ...

## 机器预检附件

- `checks/cumcm-review-precheck.json`


