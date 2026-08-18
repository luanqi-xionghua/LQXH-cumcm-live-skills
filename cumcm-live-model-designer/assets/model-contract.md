# CUMCM 赛时模型合同

> 复制后填写。未知项写 `unknown`；未经上游确认不得删除字段、补造数据或改变题面硬约束。

## 0. 冻结状态

| 字段 | 值 |
|---|---|
| contract_version |  |
| model_contract_version | 1 |
| status | DRAFT / FROZEN / STALE / BLOCKED |
| contest_year |  |
| problem_id |  |
| question_id |  |
| freeze_id |  |
| generated_at |  |
| remaining_time |  |
| switch_deadline |  |

## 1. 上游问题合同

| 字段 | 值 |
|---|---|
| problem_contract_path |  |
| rules_evidence |  |
| ai_use_status | ALLOWED / PROHIBITED / UNKNOWN |
| statement_paths |  |
| attachment_manifest |  |
| required_output_contract |  |

若 `ai_use_status` 不是 `ALLOWED`，将状态设为 `BLOCKED`。

## 2. 小问边界

- 目标：
- 输入：
- 输出：
- 时间/空间粒度：
- 题面硬约束：
- 验收条件：
- 上游依赖：
- 下游消费者：
- 不得改变项：

## 3. 符号与数据映射

| 符号 | 含义 | 单位 | 取值域 | 数据字段/来源 | 输入/参数/决策变量/输出 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 4. 假设

| ID | 假设 | 依据 | 影响范围 | 检验/敏感性方法 | 状态 |
|---|---|---|---|---|---|
| A1 |  |  |  |  | 待验证 |

## 5. Baseline

- 名称：
- 使用理由：
- 数学表达：
- 输入与预处理：
- 参数：
- 求解/训练步骤：
- 固定 seed：
- 评价指标：
- 通过阈值：
- 预期运行时间：
- 输出：
- 已知限制：

## 6. 主模型

- 名称：
- 相对 baseline 的新增价值：
- 数学表达：
- 目标函数：
- 约束与容差：
- 参数及来源：
- 数据切分：
- 求解/训练步骤：
- 固定 seed 与重复次数：
- 停止条件：
- 时间/内存预算：
- 输出：
- 失败判据：

## 7. 候选比较

| 路线 | 数据要求 | 指标 | 稳定性 | 可解释性 | 依赖风险 | 预计耗时 | 决策 |
|---|---|---|---|---|---|---|---|
| Baseline |  |  |  |  |  |  | 保留 |
| Candidate 1 |  |  |  |  |  |  |  |
| Candidate 2 |  |  |  |  |  |  |  |

## 8. 亮点候选 `contribution_candidates[]`

- 差异化机会判断：`【填写，或明确写“无差异化机会”】`
- 亮点账本路径：

| contrib_id | claim | baseline_expectation | delta_type | falsification_test | 预期 evidence_ids | cost_risk | status | placement | fallback |
|---|---|---|---|---|---|---|---|---|---|
| `CONTRIB-Q?-###` |  |  | 建模创新 / 机理洞察 / 更强验证 / 反直觉结论 / 更优结果 / 更好泛化 |  |  |  | CANDIDATE / PROVEN / DROPPED |  |  |

每个小问至少填写一行；没有可靠机会时写明 `无差异化机会` 并设为 `DROPPED`。此处的 `PROVEN` 只可在模型冻结、必需验证门通过、专门运行证据生成且同版本 `VER-*` 重复复核报告为 `PASS` 后填写。

## 9. 验证设计

| Gate | 检查 | 方法 | 通过标准 | 失败动作 | 证据文件 |
|---|---|---|---|---|---|
| V0 | 数据 schema、单位、缺失、异常 |  |  |  |  |
| V1 | Baseline 可运行 |  |  |  |  |
| V2 | 主指标与切分无泄漏 |  |  |  |  |
| V3 | 约束/边界/守恒 |  |  |  |  |
| V4 | 多 seed 或敏感性 |  |  |  |  |
| V5 | 新进程可复现 |  |  |  |  |

## 10. 实验矩阵

| run_label | model | data_split | parameter_set | seed | repeats | expected_output | stop_condition |
|---|---|---|---|---:|---:|---|---|
| baseline |  |  |  |  |  |  |  |
| candidate |  |  |  |  |  |  |  |
| contribution-proof |  |  |  |  |  | `RID/FIG/TAB for CONTRIB-*` |  |

## 11. 故障降级

| 触发器 | 检测证据 | 回退路线 | 影响 | 最晚切换时间 | 论文披露 |
|---|---|---|---|---|---|
| 依赖不可用 |  |  |  |  |  |
| 超时 |  |  |  |  |  |
| 不优于 baseline |  |  |  |  |  |
| 数值/随机不稳定 |  |  |  |  |  |
| 数据不足 |  |  |  |  |  |

## 12. 冻结结果合同

| 产物 | 文件名/路径 | 字段/内容 | 单位 | 精度 | 生成者 | 验收方法 |
|---|---|---|---|---|---|---|
| 指标 |  |  |  |  |  |  |
| 结果表 |  |  |  |  |  |  |
| 图 |  |  |  |  |  |  |
| 日志 |  |  |  |  |  |  |
| 亮点证明产物 |  | `CONTRIB-* -> RID/FIG/TAB` |  |  |  |  |

## 13. 角色交接

### 给编码角色

- 必须实现：
- 可选增强：
- 不得改动：
- 回传运行清单：
- 回传 `CONTRIB-*` 专门证明产物：
- 截止时间：

### 给论文角色

- 可写结论：
- 可写 `CONTRIB-PROVEN`：
- 必须引用的冻结证据：
- 必须披露的假设与限制：
- 暂不可写内容：

任何输入、代码、参数、约束、seed 或数据切分变化都将本合同与亮点账本置为 `STALE`，必须重新验证并生成新的 `freeze_id`。
