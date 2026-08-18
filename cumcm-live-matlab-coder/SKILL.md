---
name: cumcm-live-matlab-coder
description: 面向中国大学生数学建模竞赛 A、B、C 题正在进行时，把已冻结模型合同快速实现为可批处理、可复现、可验证、可降级、可交接的 MATLAB 代码与结果。用户要求赛时用 MATLAB 完成 baseline、优化、预测、评价、仿真、结果表或论文图，并需要固定 seed、工具箱与许可证检查、MEX 兼容性门禁、结果冻结和失败回退时使用；内置通用实现配方，不用于赛前 MATLAB 教学。
---

# CUMCM 赛时 MATLAB 编码

## 开始条件

- 先读取问题合同和冻结的模型合同。缺少合同版本、`freeze_id`、输出字段或验收指标时停止编码并回传。
- 同时读取亮点账本中的 `CONTRIB-CANDIDATE`；账本缺失不阻断 baseline，但不得在编码阶段自行发明论文亮点。
- 确认本届规则允许当前 AI 使用方式；否则输出 `BLOCKED_RULES`。
- 原始题面和附件只读，代码与结果写入独立比赛工作目录。
- 使用 Skill 内置的原创实现配方，从模型合同重新编写本题代码；不读取或执行作者的私有工具箱和案例库。
- 只把团队本次编写且经过检查的最小源码目录加入 MATLAB path；外来 MEX、DLL、宏和安装器一律不加载。

复制 [assets/run-manifest.md](assets/run-manifest.md) 到本次运行目录并持续更新。

## 输入合同

编码前确认：

- `contract_version`、`model_contract_version`、`freeze_id`、小问 ID
- 输入路径、字段、单位、精度、Sheet 和只读状态
- baseline、主模型、公式、约束、参数、指标、验证切分和固定 seed
- `contribution_ledger_version`、待验证的 `CONTRIB-*`、证伪条件和预期 `RID/FIG/TAB` 产物
- 指定 MATLAB 版本、允许的工具箱、时间/内存预算和停止条件
- 输出 `.mat`、CSV/XLSX、图和日志的名称、字段、顺序与精度
- 回退路线、最晚切换时间和论文需要的证据

若工具箱许可、关键数据或输出合同不明确，输出 `BLOCKED_CODE_INPUT`，不得猜测。

## 环境预检

每次运行都重新记录：

- `version`、`computer`、`mexext`、`ver`
- 模型所需工具箱的 `license('test', feature)` 结果
- 关键函数的 `which -all`，排除同名函数和路径遮蔽
- 源文件编码、函数名与文件名是否一致
- 输入文件存在性、schema、单位和最小样本读取

优先使用 `matlab` 命令；若不在 `PATH`，再检测本机应用路径。发现平台不匹配的 MEX/DLL 时不得尝试加载。

## 赛时实现流程

1. 记录输入清单和 SHA-256，不在原始目录写输出。
2. 建立最小路径；不要对未知第三方目录使用递归 `addpath(genpath(...))`。
3. 先实现 baseline 并在缩小实例上验证数据流、目标、约束和输出。
4. 实现主模型；与 baseline 共用数据切分、指标和后处理。
5. 用固定 seed 执行规定的多次运行、敏感性和边界测试。
6. 独立重算优化目标/约束或预测指标，不依赖模型对象自报结果。
7. 为每条准备升级为 `PROVEN` 的亮点生成一个专门运行产物：baseline 对照表、差异图、消融结果或独立验证结果，并分配 `RID-*`、`FIG-*` 或 `TAB-*`。
8. 用 `-batch` 在新 MATLAB 进程中重跑，保存日志并检查所有结果文件。
9. 通过门禁后把运行清单标为 `FROZEN`，先交给 `cumcm-live-result-verifier`；复核报告未 `PASS` 前不得交给论文角色写确定性结论。

## 代码合同

- 把主流程写成接收配置结构的函数；数据、参数、输出目录和 seed 不得硬编码为个人路径。
- 入口执行 `rng(seed, "twister")`，并在运行清单记录 seed。
- 避免 `clear all`、全局 `cd` 和依赖 base workspace 的隐式变量。
- 使用相对工作路径或 `fullfile`；关闭文件句柄并显式保存结果。
- 批处理时禁用交互式弹窗；用 `exportgraphics` 或 `saveas` 保存图。
- 保存清洗后数据、参数、指标、预测/决策、图源数据、日志和异常报告。
- 函数文件名必须与首个函数名一致；自定义函数放入本次最小源码目录。
- 捕获异常时写入完整报告并返回失败状态，不得继续生成假成功结果。

短入口示例：

```matlab
function run_case(cfg)
    rng(cfg.seed, "twister");
    [base, candidate] = solve_models(cfg);
    export_results(cfg, base, candidate);
end
```

## Baseline 与工具箱降级

| 任务 | 首选内置路线 | 依赖不可用时 |
|---|---|---|
| 线性/整数规划 | `linprog`、`intlinprog` | 保留可行 baseline；不得加载未知旧求解器 |
| 二次/非线性规划 | `quadprog`、`fmincon` | 简化模型；罚函数回退必须独立核验原约束 |
| 回归/分类 | 基础回归、`fitclinear`、`fitcsvm`、`fitcensemble` | 自定义 MEX/LIBSVM 不可用时退回内置简单模型 |
| 时间序列 | 朴素/季节朴素、指数平滑、可用时 `arima` | 不因旧神经网络案例失败而阻断 baseline |
| 评价/排序 | 矩阵实现标准化、等权 baseline、TOPSIS/PCA | 工具箱缺失时保留可审计的基础矩阵路线 |
| 随机优化/仿真 | 固定 seed 的内置随机数与显式停止条件 | 超时则减小搜索并报告最优性限制 |

自定义工具箱只有在许可证、源码、平台、版本、路径和最小测试都通过后才能加入。当前机器是否安装某应用不等于拥有全部工具箱许可证。

## 验证门禁

- 输入哈希、字段、单位、样本量和输出格式与合同一致。
- baseline 与主模型使用同一评价口径，不挑选单次最好随机结果。
- 优化结果独立核算目标和每个约束；超容差即失败。
- 时间序列无未来泄漏，分类/回归无目标泄漏。
- 随机算法按合同固定 seed 并汇总多 seed；记录 MATLAB 版本和工具箱。
- 图和表的数据可回溯到冻结结果；论文数字不可从命令窗口手抄。
- 每条拟升级为 `CONTRIB-PROVEN` 的亮点都有专门、可复现的 `RID/FIG/TAB` 产物；只有文字主张或普通结果旁证时不得升级。
- 新进程 `-batch` 重跑成功，日志无未处理 warning/error，输出哈希已记录。

## 故障处理与冻结

- 平台 MEX、工具箱或许可证不可用：立即采用模型合同中的内置回退，保留诊断证据。
- 主模型超时或不优于 baseline：到切换时间冻结 baseline，不继续无限调参。
- 结果随 seed 剧烈变化：增加重复并报告分布；仍不稳则退回低方差路线。
- 编码乱码或空 `.m` 文件：不得修猜；改写 clean-room 实现或阻断该增强路线。
- 输出不符提交合同：修复后完整重跑，不手工修改最终表格。
- 冻结后禁止覆盖旧运行。任何代码、数据、参数或工具箱变化都创建新 `run_id`，并把相关论文内容标为 `STALE`。

交接至少包含运行清单、`.m` 源码、配置、`ver`/许可记录、输入清单、日志、baseline/主模型指标、结果表、图、`CONTRIB-*` 专门证明产物、失败与降级说明、批处理复现命令和输出哈希。下一接收者是 `cumcm-live-result-verifier`；论文角色只能使用同时具有 `FROZEN` 运行和同版本 `VER-* PASS` 报告的结果。无专门证据的亮点必须保持 `CANDIDATE` 或降级为 `DROPPED`。

## 论文图生成门

先读 [references/matlab-figure-recipes.md](references/matlab-figure-recipes.md)，并可复制 [assets/cumcm_plot_style.m](assets/cumcm_plot_style.m) 到本次最小源码目录。每张图先声明唯一结论，再按机理、结果、验证或敏感性选择图型。

- 开始出图前从样式资产的 `SET-A` 至 `SET-D` 中显式选择一组，调用 `cumcm_plot_style(..., palette_set)`，并在运行清单记录 `palette_set`；不得退回 MATLAB 默认 `ColorOrder`。
- 同一对象跨图保持颜色、线型和标记一致。
- 全文只使用已选组，不得逐图换组；颜色不能作为唯一编码，比较组同时使用线型、标记、填充纹理或直接标签。
- 拟合图必须保留观测点；预测图区分训练/验证/测试；随机结果显示区间或分布。
- 优化与仿真图标出基准、约束、推荐解、收敛容差或稳定区间。
- 禁止 3D 饼图、彩虹色带、无说明双轴、截断柱轴和不可读的密集子图。
- 保存图源 table/MAT、绘图函数、配置、`FIG-*` 和导出命令。
- 优先使用 `exportgraphics` 输出矢量 PDF 和 300 dpi 以上 PNG；不使用交互式编辑器手工改图。
- 从最终论文 PDF 检查中文字体、字号、图例、单位、灰度和裁切。
- 在运行清单记录同一个 `palette_set`；连续场若必须例外，记录原因、替代色带和灰度/色觉 QA 证据。

## 资源路由

- 使用 [assets/run-manifest.md](assets/run-manifest.md) 记录环境、运行、冻结与交接。
- 需要函数结构、数据类型、工具箱预检、求解器复核、矩阵陷阱和降级配方时读取 [references/matlab-contest-recipes.md](references/matlab-contest-recipes.md)。
- 需要论文图型选择、统一风格、导出和视觉 QA 时读取 [references/matlab-figure-recipes.md](references/matlab-figure-recipes.md)。
