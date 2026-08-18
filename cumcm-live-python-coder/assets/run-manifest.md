# CUMCM Python 赛时运行清单

> 每次运行复制一份，禁止覆盖已冻结运行。未知项写 `unknown`。

## 0. 状态

| 字段 | 值 |
|---|---|
| run_id |  |
| status | DRAFT / RUNNING / FROZEN / FAILED / BLOCKED |
| contest_year |  |
| problem_id |  |
| question_id |  |
| contract_version |  |
| model_contract_version |  |
| model_freeze_id |  |
| contribution_ledger_version |  |
| contribution_ledger_path |  |
| started_at |  |
| finished_at |  |
| operator |  |

## 1. 环境

| 字段 | 值 |
|---|---|
| operating_system |  |
| architecture |  |
| python_executable |  |
| python_version |  |
| virtual_environment |  |
| package_snapshot_path |  |
| available_solvers |  |
| working_directory |  |

### 关键依赖

| 包 | 请求版本 | 实际版本 | 用途 | 状态 |
|---|---|---|---|---|
|  |  |  |  | OK / MISSING / FALLBACK |

## 2. 输入冻结

| 相对路径/逻辑名 | 绝对来源路径 | 大小 | SHA-256 | schema/Sheet | 单位 | 只读 |
|---|---|---:|---|---|---|---|
|  |  |  |  |  |  | yes |

- 原始输入是否被修改：no / yes
- 数据清洗产物：
- 已确认的数据问题：

## 3. 运行配置

| 字段 | 值 |
|---|---|
| config_path |  |
| seed |  |
| additional_seeds |  |
| data_split |  |
| baseline_model |  |
| candidate_model |  |
| primary_metric |  |
| timeout_or_stop_condition |  |
| fallback_deadline |  |
| palette_set | `SET-A / SET-B / SET-C / SET-D；出图前显式选择` |

### 精确复现命令

```bash
# 填写从新 shell 可直接执行的命令
```

## 4. 冒烟与数据门禁

| 检查 | 结果 | 证据 |
|---|---|---|
| 文件存在、可读、哈希一致 | PASS / FAIL |  |
| 字段、类型、单位、行数 | PASS / FAIL |  |
| 缺失、重复、异常范围 | PASS / WARN / FAIL |  |
| 数据切分无泄漏 | PASS / FAIL |  |
| 最小样本运行 | PASS / FAIL |  |

## 5. Baseline 与主模型

| 路线 | 状态 | seed/repeats | 主要指标 | 运行时间 | 结果路径 |
|---|---|---|---|---|---|
| baseline |  |  |  |  |  |
| candidate |  |  |  |  |  |

## 6. 验证

| Gate | 通过标准 | 实际结果 | 状态 | 证据路径 |
|---|---|---|---|---|
| 指标口径一致 |  |  |  |  |
| 约束/边界独立核验 |  |  |  |  |
| 多 seed/敏感性 |  |  |  |  |
| NaN/Inf 与数值稳定性 |  |  |  |  |
| 新进程完整重跑 |  |  |  |  |
| 输出 schema、排序、精度 |  |  |  |  |

## 7. 亮点证明产物

亮点不能只靠文字主张。每条拟升级为 `PROVEN` 的 `CONTRIB-*` 必须拥有一个专门的冻结产物，并用与 baseline 相同的数据、切分、指标和约束口径比较。

| contrib_id | baseline_expectation | falsification_test | 专门 evidence_id | 产物路径 | 量化 proof | cost_risk | 状态 |
|---|---|---|---|---|---|---|---|
| `CONTRIB-Q?-###` |  |  | `RID/FIG/TAB-Q?-###` |  |  |  | CANDIDATE / PROVEN / DROPPED |

`evidence_id` 为空、证伪实验未运行、模型未冻结或必需验证门失败时，状态不得为 `PROVEN`。

## 8. 故障与降级

| 时间 | 故障/触发器 | 诊断证据 | 采取的回退 | 结果影响 | 论文披露 |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

## 9. 冻结产物

| 角色 | 路径 | SHA-256 | 来源代码/命令 | 状态 |
|---|---|---|---|---|
| 源码 |  |  |  |  |
| 配置 |  |  |  |  |
| 清洗数据 |  |  |  |  |
| 指标 |  |  |  |  |
| 结果表 |  |  |  |  |
| 图与图源数据 |  |  |  |  |
| 亮点证明产物 |  |  |  |  |
| 日志 |  |  |  |  |

### 图表登记

| `figure_id` | 小问 | 唯一结论 | 图型 | palette_set | 图源数据 | 生成代码/命令 | PDF/PNG | 最终尺寸/灰度 QA |
|---|---|---|---|---|---|---|---|---|
| `FIG-Q*-###` |  |  |  | `【与运行配置相同】` |  |  |  | PASS / FAIL |

## 10. 交接

- 下一接收者：`cumcm-live-result-verifier`
- 首次结果只读目录与哈希：
- 预声明复核容差：
- 可供论文引用的冻结数字：
- 可供论文使用的冻结图表：
- 可供论文使用的 `CONTRIB-PROVEN` 及专门证据：
- 保持 `CANDIDATE` 或已 `DROPPED` 的亮点：
- 失败路线与不得宣称的内容：
- 已知限制：
- 论文需要披露的降级：
- 下游接收者：
- 下游文件失效条件：

只有所有必需 Gate 通过且产物哈希完整时，才把状态改为 `FROZEN`。此状态只表示首次运行冻结；同版本 `VER-*` 报告 `PASS` 前不得直接进入论文。
