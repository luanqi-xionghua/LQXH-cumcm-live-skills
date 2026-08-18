---
name: cumcm-live-python-coder
description: 面向中国大学生数学建模竞赛 A、B、C 题正在进行时，把已冻结的模型合同快速实现为可复现、可验证、可降级、可交接的 Python 代码与结果。用户要求赛时用 Python 完成 baseline、主模型、数据处理、求解、指标、结果表或论文图，并需要固定 seed、环境记录、结果冻结和失败回退时使用；内置通用实现配方，不用于赛前 Python 教学。
---

# CUMCM 赛时 Python 编码

## 开始条件

- 先读取问题合同和冻结的模型合同。没有 `model_contract_version`、`freeze_id`、输出字段或验收指标时停止并请求模型角色补齐。
- 同时读取亮点账本中的 `CONTRIB-CANDIDATE`；账本缺失不阻断 baseline，但不得在编码阶段自行发明论文亮点。
- 确认本届规则允许当前 AI 使用方式；否则输出 `BLOCKED_RULES`。
- 原始题面与附件只读。所有代码、临时文件和结果写入独立比赛工作目录。
- 使用 Skill 内置的原创实现配方，从模型合同重新编写本题代码；不读取或执行作者的私有代码库。
- 先交付 baseline，再实现主模型。接近截止时优先保住已验证的可提交版本。

复制 [assets/run-manifest.md](assets/run-manifest.md) 到本次运行目录并从开始时持续填写。

## 输入合同

编码前确认：

- `contract_version`、`model_contract_version`、`freeze_id`、小问 ID
- 输入绝对路径、文件角色、字段、单位、精度和只读状态
- baseline、主模型、参数、约束、指标、数据切分和固定 seed
- `contribution_ledger_version`、待验证的 `CONTRIB-*`、证伪条件和预期 `RID/FIG/TAB` 产物
- 结果文件名、Sheet/字段、图表、排序和精度要求
- 时间/内存预算、停止条件、最晚回退时间和允许的降级路线

字段或单位存在会改变结果的歧义时输出 `BLOCKED_CODE_INPUT`，不得自行猜测。

## 赛时实现流程

1. 复制数据到工作区或以只读方式引用，记录路径、大小和 SHA-256。
2. 记录 Python 版本、平台、实际导入的包版本和可用求解器。
3. 检查数据 schema、空值、重复、范围、单位和目标泄漏；先跑最小样本冒烟测试。
4. 实现并冻结 baseline；保存指标、结果表和最小诊断图。
5. 实现主模型；与 baseline 使用相同数据切分和评价指标。
6. 执行模型合同规定的稳健性、敏感性、约束和多 seed 检查。
7. 为每条准备升级为 `PROVEN` 的亮点生成一个专门运行产物：baseline 对照表、差异图、消融结果或独立验证结果，并分配 `RID-*`、`FIG-*` 或 `TAB-*`。
8. 在全新进程中按记录命令重跑；核对输出字段、行数、精度和哈希。
9. 将运行清单状态改为 `FROZEN`，先交给 `cumcm-live-result-verifier`；复核报告未 `PASS` 前不得交给论文角色写确定性结论。

## 代码合同

- 使用命令行参数或配置文件接收输入、输出、seed 和关键参数；禁止硬编码个人绝对路径。
- 使用 `pathlib.Path` 管理路径；不得在原始输入目录写文件。
- 把读取、清洗、建模、评价和导出拆成可测试函数，并保留 `if __name__ == "__main__":` 入口。
- 固定所有随机源。优先使用 `numpy.random.default_rng(seed)`，并同步需要的库级 seed。
- 禁止交互式 `input()` 和赛时阻塞的 `plt.show()`；用 `savefig` 保存图并关闭画布。
- 保存清洗后数据、参数、指标、预测/决策结果、图源数据、日志和异常信息。
- 对排序、类别编码、时间索引和浮点输出做显式处理，避免依赖默认顺序。
- 捕获异常时保留 traceback；不得吞掉失败后继续生成看似正常的结果。

短入口示例：

```python
def main(config_path: str) -> None:
    cfg = load_config(config_path)
    rng = np.random.default_rng(cfg["seed"])
    run_baseline_and_candidate(cfg, rng)

if __name__ == "__main__":
    main(parse_args().config)
```

## Baseline 与依赖降级

| 任务 | 首选 baseline/内置路线 | 依赖不可用时 |
|---|---|---|
| 线性/整数优化 | SciPy `linprog` / `milp` 的 HiGHS | 先验证可行性；CVXPY 仅在目标 solver 已安装时使用 |
| 回归/分类 | scikit-learn 线性模型、树或随机森林 | 不因缺 XGBoost/LightGBM 阻断，退回 sklearn |
| 时间序列 | 朴素/季节朴素、指数平滑、现代 `ARIMA` | 禁止使用已移除的旧 `statsmodels.tsa.ARMA` |
| 评价/排序 | NumPy/Pandas 实现标准化、权重和 TOPSIS | 保留等权 baseline 和排序敏感性 |
| 图网络 | NetworkX 内置算法 | 用小图手算或第二实现交叉核验 |
| Monte Carlo | NumPy 向量化仿真 | 降低样本量时必须报告置信区间变宽 |
| 图像 | 先探测 Pillow/OpenCV 等依赖 | OpenCV 缺失时用已安装的简单方案或阻断该增强路线 |

禁止在模型合同未授权时临时安装大量依赖。必须安装时先记录版本、来源和对复现的影响。

## 验证门禁

交付前必须通过：

- 输入哈希、schema、单位和样本量与合同一致。
- baseline 与主模型使用同一评价口径；不得只选择最好的一次随机结果。
- 时间序列无未来泄漏，分类/回归无目标泄漏，分组数据无跨组泄漏。
- 优化结果独立重算目标与约束，违反容差即失败。
- 至少用合同规定的 seed 重跑；随机模型按规定汇总多 seed。
- 论文所需每个数字和图都能指向机器可读结果及生成代码。
- 每条拟升级为 `CONTRIB-PROVEN` 的亮点都有专门、可复现的 `RID/FIG/TAB` 产物；只有文字主张或普通结果旁证时不得升级。
- 新进程重跑命令成功，最终输出不依赖当前交互会话状态。

## 故障处理与冻结

- 主模型超时、报错或未超过 baseline：在最晚回退时间前切回 baseline，保留失败日志。
- solver、包或数据缺失：使用合同中的回退；没有授权回退时设为 `BLOCKED_DEPENDENCY`。
- 数值不稳定或结果含 NaN/Inf：缩放数据、检查单位和容差；修复前不得冻结。
- 输出格式不符：结果正确也不能交接，先按提交合同修复并重新校验。
- 冻结后禁止覆盖旧运行。创建新 `run_id`，把旧下游产物标为 `STALE`。

交接至少包含运行清单、源码、配置、环境版本、输入清单、日志、baseline/主模型指标、结果表、图、`CONTRIB-*` 专门证明产物、失败与降级说明、复现命令和输出哈希。下一接收者是 `cumcm-live-result-verifier`；论文角色只能使用同时具有 `FROZEN` 运行和同版本 `VER-* PASS` 报告的结果。无专门证据的亮点必须保持 `CANDIDATE` 或降级为 `DROPPED`。

## 论文图生成门

先读 [references/python-figure-recipes.md](references/python-figure-recipes.md)，并可复制 [assets/cumcm_plot_style.py](assets/cumcm_plot_style.py) 到本次源码目录。每张图先声明唯一结论，再选择图型；丰富性来自机理、结果、验证和敏感性等互补证据，不来自装饰。

- 开始出图前从样式资产的 `SET-A` 至 `SET-D` 中显式选择一组，调用 `apply_cumcm_style(palette_set)`，并在运行清单记录 `palette_set`；不得退回 Matplotlib 默认高饱和循环色。
- 同一对象跨图保持颜色、线型和标记一致。
- 全文只使用已选组，不得逐图换组；颜色不能作为唯一编码，比较组必须同时使用线型、标记、填充纹理或直接标签。
- 拟合图同时显示原始点；预测图分开训练/验证/测试；随机结果显示分布或区间。
- 优化图标出可行边界、baseline、推荐解或最优间隙；收敛图标出容差。
- 禁止 3D 饼图、彩虹色带、无说明双轴、截断柱轴和不可读的密集子图。
- 同时保存图源数据、绘图配置、生成脚本和 `FIG-*` 标识。
- 优先输出矢量 PDF/SVG 和 300 dpi 以上 PNG；禁止 `plt.show()` 阻塞批处理。
- 在最终论文尺寸检查中文字体、字号、图例、单位、灰度和裁切。
- 在运行清单图表登记中记录同一个 `palette_set`；若因连续场科学可读性必须例外，记录理由、替代色带和灰度/色觉 QA 证据。

## 资源路由

- 使用 [assets/run-manifest.md](assets/run-manifest.md) 记录运行、冻结和交接。
- 需要工程结构、数据断言、现代库路由、数值稳定性、测试与降级配方时读取 [references/python-contest-recipes.md](references/python-contest-recipes.md)。
- 需要论文图型选择、统一风格、导出和视觉 QA 时读取 [references/python-figure-recipes.md](references/python-figure-recipes.md)。
