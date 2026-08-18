# CUMCM 赛时亮点账本

> 复制后填写。本账本只记录“已经被证据证明或正在等待验证的差异”，不记录为了显得复杂而增加的模型名。亮点是被证明的差异，不是被主张的复杂度。

## 0. 账本状态

| 字段 | 值 |
|---|---|
| contribution_ledger_version | 1 |
| status | DRAFT / FROZEN / STALE / BLOCKED / PASS |
| contest_year |  |
| problem_id |  |
| model_contract_version |  |
| model_freeze_ids |  |
| generated_at |  |
| updated_at |  |
| owner |  |

只有账本状态为 `FROZEN`，且记录状态为 `PROVEN` 的亮点，才能进入论文。模型、数据、代码、参数或证据变化后，将本账本及引用它的论文内容标记为 `STALE`。

## 1. 亮点记录

为每条候选复制一行；每个小问至少完成一次差异化判断。若确实没有可靠机会，在 `claim` 填 `无差异化机会` 并将状态设为 `DROPPED`，不得留空跳过。

| 字段 | 内容与约束 |
|---|---|
| `contrib_id` | 稳定标识，例如 `CONTRIB-Q2-001` |
| `claim` | 一句可证伪的差异化陈述；禁止“模型效果好”“方法更先进”等空话 |
| `baseline_expectation` | 评委或透明标准解法对本问的默认预期；写清比较参照和口径 |
| `delta_type` | 只取：`建模创新` / `机理洞察` / `更强验证` / `反直觉结论` / `更优结果` / `更好泛化` |
| `falsification_test` | 哪个具体运行结果会推翻 `claim`；写不出即保持 `DRAFT` |
| `evidence_ids` | 绑定 `RID-*` / `FIG-*` / `TAB-*` / `MODEL-*`；无证据 ID 自动降级为 `DROPPED` |
| `verification_ids` | 绑定同版本 `VER-* PASS`；缺失、失效或未完成独立复核时不得 `PROVEN` |
| `proof` | 已运行结果给出的量化差异、发现或稳定区间，不得写计划和设想 |
| `cost_risk` | 额外计算/数据代价、适用边界、失效条件和过拟合风险 |
| `status` | `CANDIDATE` / `PROVEN` / `DROPPED` |
| `placement` | 摘要/引言/正文/模型评价的具体节、段、图或表位置 |
| `fallback` | 亮点被证伪、超时或证据失效时采用的可提交退路 |

### `CONTRIB-Q?-###`

| 字段 | 值 |
|---|---|
| contrib_id | `CONTRIB-Q?-###` |
| claim |  |
| baseline_expectation |  |
| delta_type |  |
| falsification_test |  |
| evidence_ids |  |
| verification_ids |  |
| proof |  |
| cost_risk |  |
| status | CANDIDATE / PROVEN / DROPPED |
| placement |  |
| fallback |  |

## 2. 状态转换

```text
CANDIDATE
  ├─ 模型合同已 FROZEN
  ├─ 对应模型通过全部必需验证门
  ├─ 有专门的 RID/FIG/TAB 运行产物
  ├─ 同版本 VER-* 报告 PASS
  ├─ proof 与产物一致
  └─ cost_risk、placement、fallback 已填写
        -> PROVEN

CANDIDATE
  ├─ 无 evidence_ids
  ├─ 验证失败或未运行
  ├─ 只增加复杂度而无可证伪差异
  └─ 截止前无法完成
        -> DROPPED
```

不得从 `CANDIDATE` 直接写入摘要。`PROVEN` 记录绑定的模型必须属于当前 `model_freeze_ids`；旧冻结版本上的亮点不能沿用。

## 3. 防吹嘘硬门

1. **无证据即删**：`evidence_ids` 为空，记录立即改为 `DROPPED`，从正文和摘要删除。
2. **可证伪性门**：`claim` 必须能被 `falsification_test` 中的一个具体结果推翻；否则不是亮点。
3. **代价强制申报**：`cost_risk` 与 `fallback` 任一为空，记录保持 `DRAFT`，不得升级。
4. **同口径比较**：声称优于 baseline 时必须使用相同数据、切分、指标、约束和统计口径。
5. **不得挑结果**：不得只选最好 seed、最好折、最好情景或最好参数证明亮点。

## 4. 论文呈现检查

| contrib_id | 摘要位置 | 正文位置 | 证明图/表/结果 | 边界是否披露 | 状态 |
|---|---|---|---|---|---|
| `CONTRIB-Q?-###` |  |  |  |  |  |

进入摘要的记录必须是 `PROVEN`，并在第一屏给出量化 `proof`。进入正文的洞察必须同时引用 `contrib_id` 与其 `evidence_ids`。模型评价中的优点、推广和改进方向分别来自 `PROVEN`、`delta_type=更好泛化` 的 `PROVEN`、以及仍有价值的 `DROPPED` 记录。

## 5. 冻结签核

- [ ] 每个小问都登记了候选，或明确写明 `无差异化机会`。
- [ ] 所有 `PROVEN` 记录绑定当前冻结模型和专门运行产物。
- [ ] 所有 `PROVEN` 记录绑定同版本 `VER-* PASS`，且量化 proof 已独立复核。
- [ ] 所有 `claim` 均可由明确结果证伪。
- [ ] 所有 `proof` 均为实际运行结果且可复现。
- [ ] 所有 `cost_risk`、`placement` 和 `fallback` 已填写。
- [ ] 无证据、证伪或超时的候选均已 `DROPPED`。
- [ ] 论文位置与账本一致，未在正文额外发明亮点。
