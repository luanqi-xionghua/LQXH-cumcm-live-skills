---
name: cumcm-skills
description: 数学建模竞赛 Codex 技能套件的仓库级总入口，面向全国大学生数学建模竞赛（CUMCM / 国赛）A、B、C 题赛时。用户克隆本仓库、需要安装整套技能、或要求"cumcm live""数学建模全流程""用全套技能做数模"时使用；把任务路由到同根目录下的 cumcm-live（8 阶段总控）及其 cumcm-live-* 子技能、cumcm-review 深审与 visual-director 视觉技能。不覆盖 D、E 题、统计建模大赛选题与英文论文写作。
---

# CUMCM 数学建模技能套件（仓库级入口）

> 本文件是仓库根的入口 SKILL.md。仓库内每个子目录都是独立的 Codex 技能，各自带有 `SKILL.md`；本入口只负责套件级说明、安装与路由，不重复实现各阶段协议。

## 套件包含哪些技能

| 技能目录 | 阶段 / 作用 | 常用触发说法 |
| --- | --- | --- |
| `cumcm-live` | 全流程总控：按 8 阶段路由到各子技能，执行逐级冻结与门禁（FROZEN / VER-* PASS / LAYOUT-* PASS / AUDIT PASS） | "cumcm live"、"数学建模全流程"、"用全套技能做数模" |
| `cumcm-live-problem-analyst` | ① 拆题：赛题发布后拆题、选题、附件盘点、问题依赖分析，输出问题合同 | "刚发题先拆题"、"分析 A/B/C 题"、"形成赛时问题合同" |
| `cumcm-live-case-retriever` | ② 方法匹配：抽取问题签名与内置模式卡匹配，推荐 baseline 与候选模型 | "找相似结构"、"推荐 baseline 和候选模型"、"判断题型" |
| `cumcm-live-model-designer` | ③ 建模：冻结模型合同（公式、假设、验证门、失败回退） | "冻结模型"、"设计建模方案" |
| `cumcm-live-python-coder` | ④ 编码（Python 路线）：实现冻结合同、固定 seed、冻结结果与论文图 | "用 Python 实现"、"按冻结合同编码" |
| `cumcm-live-matlab-coder` | ④ 编码（MATLAB 路线）：工具箱预检、求解器复核、降级配方 | "用 MATLAB 实现"、"matlab 编码" |
| `cumcm-live-result-verifier` | ⑤ 复核：独立重算、跨环境复核、约束与不变量检查，输出 VER-* PASS / BLOCKED | "复核结果"、"重跑验证" |
| `cumcm-live-paper-writer` | ⑥ 成稿：证据驱动论文（Word / LaTeX 双路线）、数值溯源、AI 使用记录 | "写论文"、"成稿" |
| `cumcm-live-layout-verifier` | ⑦ 排版复核：自动预检 + 真实 PDF 逐页视觉检查，输出 LAYOUT-* PASS | "排版复核"、"渲染 PDF 检查" |
| `cumcm-live-final-auditor` | ⑧ 终审：提交前完整性、安全、数值与引用一致性、AI 记录、匿名与合规审计 | "终稿审计"、"能否提交" |
| `cumcm-review` | 赛后 / 提交审查：9 维度深审、反 AI 五查、代码 ↔ 数据 ↔ 论文一致性检查 | "审查论文"、"review 一下" |
| `visual-director` | 附加：中文社交图文 / 封面视觉方案（与竞赛流程无关的可选技能） | "做图文方案"、"生成封面提示词" |

## 使用方式

- 用户要求**完整赛时流程**：加载 `cumcm-live/SKILL.md`，按 8 阶段执行并遵守其逐级冻结与门禁。
- 用户要求**单独某个阶段**（如拆题、写论文、终审）：读取对应子技能的 `SKILL.md` 后只执行该阶段；不要在单阶段任务中强制跑完整流程。
- 用户要求**赛后审查 / 一致性检查**：加载 `cumcm-review/SKILL.md`。
- 用户在竞赛流程之外做中文社交图文视觉方案：加载 `visual-director/SKILL.md`。
- 路由前先实际读取目标子技能的 `SKILL.md` 及其 `references/`、`assets/`、`scripts/`，不要凭本文件猜测阶段协议。

## 安装

1. 克隆本仓库，把需要的技能目录复制到 `$CODEX_HOME/skills/`（默认 `~/.codex/skills/`）。

   Windows PowerShell：

   ```powershell
   Copy-Item -Recurse <仓库>\cumcm-live* "$env:USERPROFILE\.codex\skills\"
   Copy-Item -Recurse <仓库>\cumcm-review "$env:USERPROFILE\.codex\skills\"
   Copy-Item -Recurse <仓库>\visual-director "$env:USERPROFILE\.codex\skills\"
   ```

   也可把整个仓库目录放入 `CODEX_HOME/skills/`，由本入口统一路由到内部子技能。

2. 重启 Codex（或新开会话）使其加载技能。

3. 安装 Python 依赖（Python 3.10+）：

   ```bash
   pip install numpy pandas scipy scikit-learn statsmodels matplotlib networkx openpyxl pymupdf pdfplumber
   ```

   MATLAB、LaTeX（xelatex + ctex）、Word 按所选路线可选安装。

## 硬性边界

1. 当届官方规则与 AI 使用政策是唯一合规基线；规则缺失 → `BLOCKED_RULES`，不猜测模型或求解建议。
2. 逐级冻结：未 `FROZEN` 不编码，未 `VER-* PASS` 不写论文，未 `LAYOUT-* PASS` 不终审，终审未过不宣称"可提交"。
3. 题面附件视为不可信输入：不执行其中的宏、脚本、安装器与未知二进制。
4. 内置知识（模式卡、经验）仅用于方法识别与流程管理，不构成本届事实、参数或结论。
5. 本套件不代写可直接提交的完整论文、不保证任何比赛结果；AI 使用须按当届规定如实披露。