# Python 国赛 A/B/C 论文图配方

本文件规定如何从冻结结果生成信息丰富、统一、可复现的论文图。不得为了视觉效果更改数据、隐藏失败结果或生成模型合同外的结论。

## 1. 图型路由

| 任务 | 首选 |
|---|---|
| 几何/机理 | Matplotlib patches、矢量线段、箭头和直接标注 |
| 时间趋势 | `plot` + marker；多组时使用小多图 |
| 原始值与拟合 | `scatter` + model line + confidence band |
| 分布比较 | box/violin/ECDF + 原始点 |
| 分类 | confusion matrix、ROC/PR、threshold curve |
| 预测 | actual-vs-predicted、residual、rolling error |
| 空间场 | `contourf`/`pcolormesh` + boundary + colorbar |
| 优化 | feasible region、objective history、Pareto front |
| 敏感性 | parameter-response、tornado、scenario heatmap |
| 路径/网络 | 坐标路径、network layout、edge weight |
| 排程 | broken-bar/Gantt |

复杂图型只有在它直接回答题面时使用。雷达图、桑基图和 3D 曲面不是默认选项。

## 2. 使用统一样式

复制 `assets/cumcm_plot_style.py` 到项目源码并调用：

```python
from cumcm_plot_style import (
    PALETTE_SETS,
    apply_cumcm_style,
    export_figure,
    get_palette_set,
    label_panels,
    style_axes,
)

palette_set = cfg["palette_set"]  # 必须预先显式选择 SET-A/B/C/D
palette_spec = get_palette_set(palette_set)
colors = palette_spec["colors"]
palette = palette_spec["palette"]
sequential_cmap = palette_spec["sequential"]
diverging_cmap = palette_spec["diverging"]
font = apply_cumcm_style(palette_set)
fig, ax = plt.subplots(figsize=(7.1, 4.2), constrained_layout=True)
style_axes(ax)
```

不提供默认配色。团队须从 `PALETTE_SETS` 的 `SET-A` 至 `SET-D` 中选定一组，把选择记录为 `palette_set`，并让全文所有图保持该组及对象映射一致；不得逐图换组。四组均按统一的 CIELAB L* 单调阶梯与逐组色相旋转设计，相邻系列实测 ΔL* 不低于 12，同一彩色角色跨组色相距不低于 60°；具体色值和色相性格见写作 Skill 的图表手册。不得改用 Matplotlib 默认高饱和循环色，颜色之外仍必须使用线型、标记、纹理或直接标签作为冗余编码。

记录实际选中的中文字体。若最终 PDF 出现方框或替换字体，修复字体后重跑，不用图片编辑器补字。

## 3. 原始点、拟合线与区间

```python
ax.scatter(x, y, s=22, color=colors["primary"],
           alpha=0.75, label="观测")
ax.plot(x_grid, y_hat, color=colors["contrast"],
        linewidth=1.6, label="模型")
ax.fill_between(x_grid, lo, hi, color=colors["contrast"],
                alpha=0.18, linewidth=0, label="95% 区间")
```

不要只画平滑线。异常点若被排除，仍用不同标记显示并在正文说明规则。

## 4. 多组趋势

组数不超过约 4 时可共轴；更多组改用小多图、突出重点组并把其他组置灰，或只在附录展示全量图。颜色之外同时使用线型或标记。

```python
for i, (name, values) in enumerate(series.items()):
    ax.plot(t, values, label=name, color=palette[i],
            linestyle=line_styles[i % len(line_styles)])
```

时间轴过密时减少刻度，不旋转成无法阅读的文字墙。

## 5. 分布与组间差异

- 样本量小：原始点 + 中位数/区间；
- 样本量中等：箱线或小提琴 + 抖动点；
- 多组完整分布：ECDF 或分面直方图；
- 类别均值比较：排序点图或带误差棒的柱图。

柱图默认从零开始。需要放大非零差异时优先使用点图/区间图；若使用轴断裂必须明确标识。

## 6. 空间、几何与机理图

- 使用相同尺度和坐标比例，必要时 `ax.set_aspect("equal")`。
- 用 `patches`、`annotate` 和箭头直接标尺寸、角度、方向和边界。
- 连续场使用所选组派生的 `sequential_cmap`。
- 有正负中心时使用 `TwoSlopeNorm(vcenter=0)` 和所选组派生的 `diverging_cmap`。
- 色条必须有变量名、单位、范围。
- 路径、可行域和障碍物使用不同线型/填充，不只依赖颜色。

禁止 `jet` 和无单位色条。

## 7. 优化、收敛与敏感性

```python
ax.semilogy(iteration, error, color=colors["primary"])
ax.axhline(tol, color=colors["accent"], linestyle="--",
           linewidth=1.0, label=f"容差={tol:g}")
```

收敛图显示全部迭代或说明截取范围；标出达到容差的迭代点。优化方案图同时表达目标和可行性。敏感性图标出基准参数、稳定区间和推荐值，不只标最大点。

## 8. 预测与分类

- 真实—预测图区分训练、验证和测试区间；
- 预测区间与点预测同时展示；
- 残差图包含零线；
- 混淆矩阵显示计数，并按需要附行/列比例；
- 类别不平衡时优先 PR 曲线和类别指标；
- ROC/PR 图标出实际采用阈值，不能只画曲线。

## 9. 多子图

```python
fig, axes = plt.subplots(2, 2, figsize=(7.1, 6.0),
                         sharex="col", constrained_layout=True)
label_panels(axes)
```

共享图例，避免每个子图重复。比较型子图共享轴范围；不同范围必须在题注说明。最终插入论文后任一标签小于约 8 pt 时，拆图或移至附录。

## 10. 导出与血缘

```python
paths = export_figure(
    fig,
    output_dir / "fig_q2_sensitivity",
    formats=("pdf", "png"),
    dpi=320,
)
```

同时保存：

- `fig_q2_sensitivity.csv`：图源数据；
- `fig_q2_sensitivity.json`：`figure_id`、标题、单位、调色板、轴范围；
- 生成脚本、配置和命令；
- PDF/PNG 的 SHA-256。

PNG 只用于栅格内容或兼容路线；线图、流程图和示意图优先使用矢量 PDF/SVG。

## 11. 视觉 QA

从最终论文 PDF 检查：

- 中文与数学符号字体正确；
- 单栏/双栏实际尺寸下文字可读；
- 颜色、线型、标记在灰度下可区分；
- 图表登记使用同一个 `palette_set`，没有逐图换组或混入默认高饱和色；
- 图例不挡数据，轴标签与色条有单位；
- 没有多余边框、软件界面或个人路径；
- 没有截断柱轴、彩虹色带、3D 饼图；
- 图中数字与机器可读结果一致；
- 每张图都被正文引用并给出定量结论。
