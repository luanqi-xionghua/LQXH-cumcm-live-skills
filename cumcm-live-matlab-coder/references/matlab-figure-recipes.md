# MATLAB 国赛 A/B/C 论文图配方

本文件规定如何从冻结 MATLAB 结果生成信息丰富、统一、可复现的论文图。不得使用 Plot Tools 手工移动数据点或修改数值。

## 1. 图型路由

| 任务 | MATLAB 路线 |
|---|---|
| 几何/机理 | `plot`、`patch`、`quiver`、`annotation` |
| 时间趋势 | `plot`、`tiledlayout` |
| 原始值与拟合 | `scatter` + `plot` + 区间 `patch` |
| 分布比较 | `boxchart`、`histogram`、ECDF |
| 空间场 | `contourf`、`imagesc`、`surf` 的俯视表达 |
| 优化/收敛 | objective history、gap/violation curve |
| 敏感性 | parameter-response、heatmap、tornado |
| 路径/网络 | 坐标路径、`graph`/`digraph` |
| 排程 | `rectangle`/patch 构造甘特图 |
| 分类/预测 | confusion chart、ROC/PR、residual |

3D 曲面只在 z 维具有真实空间/机理含义且二维等值图不能表达时使用。

## 2. 统一样式

复制 `assets/cumcm_plot_style.m` 后：

```matlab
fig = figure("Color", "w");
tl = tiledlayout(fig, 1, 2, "TileSpacing", "compact", ...
    "Padding", "compact");
ax1 = nexttile(tl);
ax2 = nexttile(tl);
style = cumcm_plot_style(fig, [ax1 ax2], ...
    cfg.figure_font, cfg.palette_set);
```

`cfg.palette_set` 必须由团队在开始出图前显式选为 `SET-A`、`SET-B`、`SET-C` 或 `SET-D`，并记录到运行清单。全文只使用该组且保持对象映射一致，不提供自动默认，也不得逐图换组。四组均按统一的 CIELAB L* 单调阶梯与逐组色相旋转设计，相邻系列实测 ΔL* 不低于 12，同一彩色角色跨组色相距不低于 60°；具体色值和色相性格见写作 Skill 的图表手册。不得退回 MATLAB 默认高饱和 `ColorOrder`；颜色之外仍同时使用线型、标记、纹理或直接标签作为冗余编码。

`cfg.figure_font` 必须是在当前机器上验证过的中文字体。记录字体名和 MATLAB 版本；导出 PDF 后检查是否发生替换。

## 3. 原始点、拟合线和区间

```matlab
scatter(ax, x, y, 24, style.colors(1,:), "filled", ...
    "MarkerFaceAlpha", 0.75);
hold(ax, "on");
plot(ax, xGrid, yHat, "Color", style.colors(2,:), ...
    "LineWidth", 1.6);
```

置信区间可用 `patch` 绘制半透明带。原始点不能被平滑线隐藏；排除异常点时以不同标记保留并记录规则。

## 4. 多组与多子图

- 不超过约 4 组时共轴比较；
- 更多组使用 `tiledlayout` 小多图或突出重点组、其余置灰；
- 比较型子图使用相同 `xlim`/`ylim`；
- 使用一个公共图例，子图标 `(a)(b)(c)`；
- 最终版文字过小时拆图或移入附录。

不要用一张图容纳十余条难以区分的曲线。

## 5. 空间、几何与机理图

- 使用 `axis(ax, "equal")` 保持几何比例；
- 标出坐标、边界、角度、尺寸、方向和关键点；
- 连续场默认 `colormap(ax, style.sequential)`；正负中心场使用 `style.diverging` 和对称 `clim`；
- 禁止 `jet`；
- 有正负中心时使用对称 `clim` 和含义明确的双向色带；
- `colorbar` 必须写变量名和单位；
- 路径、障碍和可行域同时用线型/填充区分。

## 6. 优化、收敛和敏感性

```matlab
semilogy(ax, iteration, errorValue, ...
    "Color", style.colors(1,:), "LineWidth", 1.5);
yline(ax, cfg.tol, "--", "容差", ...
    "Color", style.colors(5,:));
```

标出达到容差的位置、baseline、推荐解、可行边界和稳定区间。启发式算法同时画目标与约束违反量，不能用下降曲线证明全局最优。

## 7. 预测和分类

- 在时序图中用背景分区或竖线区分训练、验证和测试；
- 点预测配预测区间；
- 残差图包含零线和时间顺序；
- 混淆矩阵同时保存原始计数和归一化比例；
- 类别不平衡时画 PR 曲线并标实际阈值；
- 多 seed 结果用箱线、区间或 ECDF，不挑最好一次。

## 8. 柱图、饼图和双轴

- 柱图默认从零起；
- 需要放大非零差异时改用点图/区间图；
- 饼图只在极少类别且“部分—整体”是唯一问题时使用，禁止 3D/爆炸饼；
- 双纵轴只有在量纲不同且关系确实必须共图时使用，并明确两侧颜色和尺度；
- 不用面积或体积编码精确数值。

## 9. 导出

```matlab
exportgraphics(fig, "figures/fig_q2_sensitivity.pdf", ...
    "ContentType", "vector", "BackgroundColor", "white");
exportgraphics(fig, "figures/fig_q2_sensitivity.png", ...
    "Resolution", 320, "BackgroundColor", "white");
```

保存对应的 `.mat`/CSV 图源数据、绘图函数、配置、命令和输出哈希。文件名使用 ASCII。只有真实栅格场才依赖 PNG；线图、流程图和几何示意优先矢量 PDF。

## 10. 视觉 QA

从论文最终 PDF 检查：

- 中文、公式和负号字体正确；
- 最终尺寸下字号约不低于 8 pt；
- 线型、标记和颜色在灰度下可分；
- 图表登记使用同一个 `palette_set`，没有逐图换组或混入默认高饱和色；
- 图例不遮挡数据，单位和色条完整；
- 柱轴、对数尺度、平滑和归一化已说明；
- 没有软件界面、个人路径、水印或低清截图；
- 图中数字能回到冻结 table/MAT；
- 正文引用每张图并给出定量结论。
