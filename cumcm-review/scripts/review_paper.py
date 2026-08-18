# -*- coding: utf-8 -*-
"""review_paper.py — CUMCM-Review 机器预检（客观项）v1.1

用法:
  python review_paper.py --dir <论文包或工作区> [--pdf <主PDF>] [--frozen <frozen_numbers.json>] [--json]

检查:
  1. PDF 页数结构（总页数/第1页摘要关键词/第2页目录/正文起止）
  2. PDF 文本质量（??/TODO/【待复核】/内部文件名/强词）
  3. 数字一致性（有 --frozen 时，关键数值是否出现在论文文本；兼容 numbers-list 与嵌套 dict 两种 schema；
     提取到 0 个数值 → FROZEN-SCHEMA WARN，绝不静默 PASS）
  4. 图表完整性（figures/*.pdf 数量、drawio/tex 源与 PDF 并存；tex/MD 引用的图片路径 vs 实际文件 diff）
  5. 提交包结构（submission/ 论文/代码/数据/支撑材料、AI_USE_LOG.md）

输出: 默认人类可读；--json 输出 JSON（写 checks/cumcm-review-precheck.json）
退出码: 0=无机器级 P0；1=存在 P0 类问题（如 PDF 缺失/摘要页异常）；2=参数错误
"""
import argparse
import hashlib
import sys

# 强制 UTF-8 输出（避免 Windows GBK 管道/控制台乱码）
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import json
import os
import re
import sys
from pathlib import Path

STRONG_WORDS = ["首次提出", "首次发现", "完美", "最优的", "无可比拟", "前所未有", "开创性", "革命性", "填补空白", "100%"]
INTERNAL_NAMES = ["RESULTS.md", "frozen_numbers", "all_results.json", "deepening.json", "MODELING_REPORT",
                  "PROBLEM_ANALYSIS", "latex_includes", "run-manifest", "R2025B", "RID-", "cumcm-t2", "workspace"]

# ---------- 基础 ----------

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def find_pdf(directory):
    cands = []
    for sub in ("", "paper", "submission", "submission/论文", "outputs"):
        d = Path(directory) / sub
        if d.exists():
            cands += sorted(d.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not cands:
        for d in Path(directory).rglob("*.pdf"):
            cands.append(d)
    return cands[0] if cands else None


# ---------- frozen_numbers：双 schema 兼容 ----------

def collect_frozen_numbers(frozen_path):
    """兼容两种 frozen schema：
    1) numbers: [{id,key,value,unit,...}] 列表（cumcm-t2 官方模板）
    2) 嵌套 dict（如 {"Q1":{...},"Q2":{...}}）
    返回 (values, schema, labels)；schema ∈ numbers-list / nested-dict / NONE / ERROR
    """
    try:
        fz = json.load(open(frozen_path, encoding="utf-8"))
    except Exception as e:
        return [], "ERROR", [("读取失败", str(e))]
    values = []
    labels = []
    if isinstance(fz, dict) and isinstance(fz.get("numbers"), list):
        schema = "numbers-list"
        for item in fz["numbers"]:
            v = item.get("value")
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                values.append(float(v))
                labels.append(str(item.get("key") or item.get("id") or ""))
    elif isinstance(fz, dict):
        schema = "nested-dict"

        def walk(d, path):
            if isinstance(d, dict):
                for k, v in d.items():
                    walk(v, path + [str(k)])
            elif isinstance(d, list):
                for i, v in enumerate(d):
                    walk(v, path + [str(i)])
            elif isinstance(d, (int, float)) and not isinstance(d, bool):
                values.append(float(d))
                labels.append(".".join(path))
        walk(fz, [])
    else:
        schema = "NONE"
    return values, schema, labels


# ---------- PDF 文本与数字一致性 ----------

def pdf_text(pdf, res):
    """fitz 优先，pdfplumber 降级；返回全文与页数"""
    try:
        import fitz
        doc = fitz.open(str(pdf))
        pages = doc.page_count
        page_texts = [doc[i].get_text() for i in range(pages)]
        doc.close()
        res["stats"]["pdf_engine"] = "fitz"
        return pages, page_texts
    except Exception:
        pass
    try:
        import pdfplumber
        with pdfplumber.open(str(pdf)) as doc:
            pages = len(doc.pages)
            page_texts = [p.extract_text() or "" for p in doc.pages]
        res["stats"]["pdf_engine"] = "pdfplumber"
        return pages, page_texts
    except Exception as e:
        res["issues"].append(("PDF-MODULE-MISSING", "fitz 与 pdfplumber 均不可用: %s" % e))
        return 0, []


def check_pdf(pdf, frozen=None):
    res = {"pdf": str(pdf), "sha256": sha256(pdf), "issues": [], "stats": {}}
    pages, page_texts = pdf_text(pdf, res)
    if pages == 0:
        return res
    res["stats"]["pages"] = pages
    if pages > 0:
        t1 = page_texts[0]
        res["stats"]["page1_has_abstract"] = "摘要" in t1
        # 兼容“关键词”与模板常用的“关键字”两种写法
        res["stats"]["page1_has_keywords"] = ("关键词" in t1) or ("关键字" in t1)
        res["stats"]["keywords_page"] = None
        for pi in range(min(pages, 3)):
            if ("关键词" in page_texts[pi]) or ("关键字" in page_texts[pi]):
                res["stats"]["keywords_page"] = pi + 1
                break
    # 目录位置不固定（可能在第2-4页），扫描前几页
    res["stats"]["toc_page"] = None
    for pi in range(min(pages, 4)):
        if "目录" in page_texts[pi]:
            res["stats"]["toc_page"] = pi + 1
            break
    res["stats"]["page2_is_toc"] = (res["stats"]["toc_page"] == 2)
    full = "\n".join(page_texts)
    res["stats"]["chars"] = len(full)
    # 归一化 Unicode 减号/连字符，提升数值匹配（PDF 文本常用 U+2212）
    full_norm = full.replace("\u2212", "-").replace("\u2013", "-").replace("\u2212", "-")

    for pat, label in [(r"\?\?", "?? 占位"), (r"TODO", "TODO"), (r"【待复核】", "待复核占位"),
                       (r"\\ref\{[^}]*\?\}", "悬空 ref")]:
        n = len(re.findall(pat, full))
        if n:
            res["issues"].append(("PLACEHOLDER", "%s 出现 %d 次" % (label, n)))
    for w in INTERNAL_NAMES:
        if w.lower() in full.lower():
            res["issues"].append(("META-LEAK", "内部文件名/标识出现在正文: %s" % w))
    for w in STRONG_WORDS:
        if w in full:
            res["issues"].append(("OVERCLAIM", "强词: %s" % w))

    if frozen:
        fz_path = Path(frozen)
        if not fz_path.exists():
            res["issues"].append(("FROZEN-MISSING", "frozen_numbers 路径不存在: %s" % frozen))
        else:
            values, schema, labels = collect_frozen_numbers(fz_path)
            res["stats"]["frozen_schema"] = schema
            res["stats"]["frozen_total"] = len(values)
            if schema in ("ERROR", "NONE") or len(values) == 0:
                res["issues"].append(("FROZEN-SCHEMA",
                                      "frozen_numbers 未提取到任何数值（schema=%s，共%d个）——数字一致性未执行。"
                                      "请核对 frozen 文件结构（numbers 列表或嵌套 dict），并手动确认。" % (schema, len(values))))
            else:
                # 提取论文文本中的数值（支持负号与科学计数法）
                text_nums = []
                for m in re.finditer(r"-?\d+(?:[.,]\d+)*(?:[eE][+-]?\d+)?", full_norm):
                    try:
                        text_nums.append((float(m.group().replace(",", "")), m.start()))
                    except ValueError:
                        pass
                sampled = list(zip(values[:30], labels[:30]))
                miss = []
                trace = []
                for v, lab in sampled:
                    tol = max(0.001, abs(v) * 0.001)
                    hit = None
                    for tv, pos in text_nums:
                        if abs(v - tv) <= tol:
                            hit = (tv, pos)
                            break
                    if hit is None:
                        miss.append("%g" % v)
                        trace.append({"value": v, "label": lab, "found": False, "context": ""})
                    else:
                        ctx = full[max(0, hit[1] - 25):hit[1] + 25].replace("\n", " ")
                        trace.append({"value": v, "label": lab, "found": True, "context": ctx})
                res["stats"]["frozen_sampled"] = len(sampled)
                res["stats"]["frozen_missing_in_pdf"] = len(miss)
                res["stats"]["frozen_trace"] = trace
                if miss:
                    res["issues"].append(("NUM-TRACE",
                                          "论文文本未找到 %d 个冻结数值（容差=0.001 或相对0.1%%，抽样%d个）: %s"
                                          % (len(miss), len(sampled), ", ".join(miss[:10]))))
    return res


# ---------- 图表引用 vs 实际文件 diff（v1.1 新增） ----------

def check_image_refs(directory):
    """扫描 tex/MD 中引用的图片路径，与磁盘实际文件 diff，输出缺失清单"""
    res = {"referenced": 0, "missing": []}
    pat_tex = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{(?P<path>[^}]+)\}")
    pat_md = re.compile(r"!\[[^\]]*\]\((?P<path>[^)]+)\)")
    files = []
    for sub in ("paper", "outputs", ""):
        d = Path(directory) / sub
        if d.exists():
            files += list(d.rglob("*.tex")) + list(d.rglob("*.md"))
    seen = set()
    paper_root = Path(directory) / "paper" if (Path(directory) / "paper").exists() else None
    for f in files:
        if f in seen:
            continue
        seen.add(f)
        try:
            text = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for m in list(pat_tex.finditer(text)) + list(pat_md.finditer(text)):
            ref = m.group("path").strip()
            if not ref:
                continue
            res["referenced"] += 1
            if ref.startswith(("figures/", "figure/")) or ref.startswith(("fig_", "tikz_")):
                if paper_root is not None:
                    cand = (paper_root / "figures" / ref) if not ref.startswith("figures/") else (paper_root / ref)
                    if not cand.exists():
                        cand2 = Path(directory) / ref
                        if not cand2.exists():
                            res["missing"].append({"file": str(f), "ref": ref, "resolved": str(cand)})
                else:
                    cand = f.parent / ref
                    if not cand.exists():
                        res["missing"].append({"file": str(f), "ref": ref, "resolved": str(cand)})
            else:
                # 多基准解析：tex 所在目录 / paper 编译目录 / 工作区根 / 去 ../ 后的工作区路径
                cands = [f.parent / ref]
                if paper_root is not None:
                    cands.append(paper_root / ref)
                cands.append(Path(directory) / ref)
                norm = ref.replace("../", "").replace("./", "")
                cands.append(Path(directory) / norm)
                if not any(c.exists() for c in cands if c is not None):
                    res["missing"].append({"file": str(f), "ref": ref, "resolved": str(cands[0])})
    return res


# ---------- 提交包结构 ----------

def check_assets(directory):
    res = {"figures_pdf": 0, "figures_drawio": 0, "figures_tex": 0, "ai_use_log": None, "issues": []}
    figdir = Path(directory) / "figures"
    if figdir.exists():
        res["figures_pdf"] = len(list(figdir.glob("*.pdf")))
        res["figures_drawio"] = len(list(figdir.glob("*.drawio")))
        res["figures_tex"] = len(list(figdir.glob("tikz_*.tex")))
        if res["figures_drawio"] and res["figures_pdf"] < res["figures_drawio"]:
            res["issues"].append(("FIG-SRC-PDF", "drawio 源 %d 个但 PDF 只有 %d 个" % (res["figures_drawio"], res["figures_pdf"])))
    # AI 使用记录（v1.1 新增）：常见子目录 + 一层 glob 兜底
    for sub in ("paper", "submission", "outputs", "支撑材料", "支撑材料/检查", ""):
        cand = Path(directory) / sub / "AI_USE_LOG.md"
        if cand.exists():
            res["ai_use_log"] = str(cand)
            break
    if res["ai_use_log"] is None:
        for cand in Path(directory).glob("*/AI_USE_LOG.md"):
            res["ai_use_log"] = str(cand)
            break
    if res["ai_use_log"] is None:
        res["issues"].append(("AI-LOG-MISSING", "未找到 AI_USE_LOG.md（AI 使用记录，国赛需随论文披露）"))
    sub = Path(directory) / "submission"
    if sub.exists():
        for need in ("论文", "代码", "数据", "支撑材料"):
            if not (sub / need).exists():
                res["issues"].append(("SUBMIT-MISSING", "submission 缺 %s/" % need))
    return res


# ---------- main ----------

def main(argv=None):
    ap = argparse.ArgumentParser(description="CUMCM-Review 机器预检")
    ap.add_argument("--dir", required=True, help="论文包/工作区目录")
    ap.add_argument("--pdf", help="主 PDF 路径（默认自动发现）")
    ap.add_argument("--frozen", help="frozen_numbers.json 路径（用于数字一致性）")
    ap.add_argument("--json", action="store_true", help="输出 JSON 并写入 checks/")
    ap.add_argument("--no-consistency", action="store_true", help="跳过三方一致性核对（默认自动运行）")
    args = ap.parse_args(argv)

    directory = Path(args.dir)
    if not directory.exists():
        print("目录不存在: %s" % directory, file=sys.stderr)
        return 2
    pdf = Path(args.pdf) if args.pdf else find_pdf(directory)
    out = {"directory": str(directory), "pdf": str(pdf) if pdf else None}
    if pdf is None:
        out["issues"] = [("PDF-MISSING", "未找到论文 PDF")]
        print(json.dumps(out, ensure_ascii=False, indent=2) if args.json else "PDF-MISSING")
        return 1
    out["pdf_check"] = check_pdf(pdf, args.frozen)
    out["assets"] = check_assets(directory)
    out["image_refs"] = check_image_refs(directory)
    # 三方一致性核对（代码 ↔ 数据 ↔ 论文），检测到 code/ 或 results/ 即自动运行
    import subprocess
    consistency = None
    if not args.no_consistency:
        cc = Path(__file__).resolve().parent / "consistency_check.py"
        code_dir = directory / "code"
        res_dir = directory / "results"
        if cc.exists() and (code_dir.exists() or res_dir.exists()):
            try:
                r = subprocess.run([sys.executable, str(cc), "--dir", str(directory), "--json"],
                                   capture_output=True, text=True, encoding="utf-8",
                                   errors="replace", timeout=600)
                consistency = json.loads(r.stdout) if r.stdout.strip() else {"error": (r.stderr or "")[:200]}
            except Exception as e:
                consistency = {"error": str(e)[:200]}
    out["consistency"] = consistency
    out["issues"] = (out["pdf_check"]["issues"] + out["assets"]["issues"]
                     + [("IMG-REF-MISSING", "引用的图片不存在: %s (源 %s)" % (m["ref"], m["file"]))
                        for m in out["image_refs"]["missing"]]
                     + (consistency.get("issues", []) if consistency else []))
    if args.json:
        checks_dir = Path(directory) / "checks"
        checks_dir.mkdir(exist_ok=True)
        (checks_dir / "cumcm-review-precheck.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        pc = out["pdf_check"]
        print("PDF: %s" % out["pdf"])
        print("  页数: %d | 引擎: %s | 摘要页1: %s | 关键词在第%d页 | 目录在第%d页" % (
            pc["stats"].get("pages"), pc["stats"].get("pdf_engine"),
            pc["stats"].get("page1_has_abstract"),
            pc["stats"].get("keywords_page") or 0,
            pc["stats"].get("toc_page") or 0))
        print("  冻结数字: schema=%s 总数=%d 抽样=%d 未命中=%d" % (
            pc["stats"].get("frozen_schema"), pc["stats"].get("frozen_total"),
            pc["stats"].get("frozen_sampled"), pc["stats"].get("frozen_missing_in_pdf")))
        print("  图表: PDF %d | drawio %d | tikz %d | 引用图片 %d | 缺失 %d | AI_USE_LOG: %s" % (
            out["assets"]["figures_pdf"], out["assets"]["figures_drawio"], out["assets"]["figures_tex"],
            out["image_refs"]["referenced"], len(out["image_refs"]["missing"]),
            out["assets"]["ai_use_log"] or "未找到"))
        if out.get("consistency"):
            c = out["consistency"]
            print("  三方一致性: 代码参数 %s | 冻结 %s | 数据文件 %s | 矛盾 %d 项" % (
                c.get("params_found"), c.get("report", {}).get("frozen", {}).get("sampled"),
                c.get("data_files"), len(c.get("issues", []))))
        if out["issues"]:
            print("  问题 %d 项:" % len(out["issues"]))
            for kind, msg in out["issues"]:
                print("    - [%s] %s" % (kind, msg))
        else:
            print("  机器预检：无 P0 类问题")
    p0 = [i for i in out["issues"] if i[0] in ("PDF-MISSING", "NUM-TRACE", "FROZEN-SCHEMA")]
    return 1 if p0 else 0


if __name__ == "__main__":
    sys.exit(main())





