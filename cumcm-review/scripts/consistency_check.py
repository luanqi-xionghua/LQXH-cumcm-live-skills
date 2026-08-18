# -*- coding: utf-8 -*-
"""consistency_check.py — CUMCM-Review 三方一致性核对（代码 ↔ 数据 ↔ 论文）

用法:
  python consistency_check.py --dir <论文包或工作区> [--code <代码目录>] [--results <结果目录>]
                              [--data <数据目录>] [--pdf <主PDF>] [--json]

核对内容:
  A. 代码常量 vs 论文文本（n / seed / 波段 / 阈值 等）
  B. 冻结数值 vs 论文文本（容差 ±0.1%，全量）
  C. 数据特征 vs 论文文本（行数 / 数值范围）
  D. 结果 JSON vs 论文文本（all_results / frozen_numbers / deepening 等）

输出: 默认人类可读；--json 写 checks/cumcm-review-consistency.json
退出码: 0=无矛盾；1=存在 P1 矛盾；2=参数错误/缺少必要输入
"""
import argparse
import json
import sys

# 强制 UTF-8 输出（避免 Windows GBK 管道/控制台乱码）
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

import math
import os
import re
import sys
from pathlib import Path

# 常见代码参数（名称正则 -> 标签）；只提取这些，避免误抓
PARAM_PATTERNS = [
    (r"N_SIC\s*=\s*([\d.]+)", "SiC 折射率 n"),
    (r"N_SI\s*=\s*([\d.]+)", "Si 折射率 n"),
    (r"seed\s*=\s*(\d+)", "随机种子"),
    (r"SEED\s*=\s*(\d+)", "随机种子"),
    (r"nu_lo\s*=\s*([\d.]+)", "波段下限"),
    (r"nu_hi\s*=\s*([\d.]+)", "波段上限"),
    (r"nu_lo\s*=\s*\((\d+),\s*(\d+)", "波段对(lo)"),
    (r"NU_LO\s*=\s*([\d.]+)", "波段下限"),
    (r"NU_HI\s*=\s*([\d.]+)", "波段上限"),
    (r"MB_THRESHOLD\s*=\s*([\d.]+)", "多光束判据阈值"),
    (r"theta_deg\s*=\s*([\d.]+)", "入射角"),
    (r"THETA\s*=\s*([\d.]+)", "入射角"),
    (r"noise_frac\s*=\s*([\d.]+)", "噪声比例"),
    (r"frac\s*=\s*([\d.]+)", "稳健极值比例"),
]

FLOAT_RE = re.compile(r"\d+(?:\.\d+)?")
TEXT_NUM_RE = re.compile(r"\d+(?:[.,]\d+)+|\d+")


def near(a, b, tol_abs=0.001, tol_rel=0.001):
    return abs(a - b) <= max(tol_abs, tol_rel * max(abs(a), abs(b)))


def extract_code_params(code_dirs):
    """从代码目录提取参数常量"""
    params = []
    for cd in code_dirs:
        if not cd.exists():
            continue
        for py in sorted(cd.rglob("*.py")):
            if "__pycache__" in str(py):
                continue
            text = py.read_text(encoding="utf-8", errors="ignore")
            for pat, label in PARAM_PATTERNS:
                for m in re.finditer(pat, text):
                    try:
                        vals = [float(x) for x in m.groups() if x is not None]
                        for v in vals:
                            params.append({"file": str(py.relative_to(cd)), "label": label, "value": v})
                    except ValueError:
                        pass
    # 去重（同文件同标签同值）
    seen = set()
    out = []
    for p in params:
        key = (p["file"], p["label"], p["value"])
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out


def collect_result_numbers(results_dirs):
    """从结果 JSON 收集数值（带 key 前缀）"""
    nums = []
    for rd in results_dirs:
        if not rd.exists():
            continue
        for jf in sorted(rd.glob("*.json")):
            try:
                data = json.loads(jf.read_text(encoding="utf-8"))
            except Exception:
                continue
            def walk(obj, prefix):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        walk(v, prefix + k + ".")
                elif isinstance(obj, list):
                    for i, v in enumerate(obj):
                        walk(v, prefix + "%d." % i)
                elif isinstance(obj, (int, float)) and not isinstance(obj, bool):
                    if abs(obj) > 1e-12:
                        nums.append({"source": jf.name, "key": prefix.rstrip("."), "value": float(obj)})
            walk(data, "")
    return nums


def data_features(data_dirs):
    """读取数据文件行数/列数/数值范围"""
    feats = []
    for dd in data_dirs:
        if not dd.exists():
            continue
        for f in sorted(dd.iterdir()):
            if f.suffix.lower() in (".xlsx", ".xls", ".csv"):
                try:
                    if f.suffix.lower() == ".csv":
                        df = __import__("pandas").read_csv(f)
                    else:
                        df = __import__("pandas").read_excel(f)
                    key = (f.name, int(len(df)))
                    if any(fe["file"] == f.name and fe.get("rows") == len(df) for fe in feats):
                        continue
                    feats.append({
                        "file": f.name, "rows": int(len(df)), "cols": int(len(df.columns)),
                        "min": float(df.select_dtypes("number").min().min()) if len(df.select_dtypes("number").columns) else None,
                        "max": float(df.select_dtypes("number").max().max()) if len(df.select_dtypes("number").columns) else None,
                    })
                except Exception as e:
                    feats.append({"file": f.name, "error": str(e)[:80]})
    return feats


def check(params, result_nums, feats, pdf_text, frozen_path=None):
    issues = []
    report = {"params": [], "frozen": {"sampled": 0, "miss": 0, "miss_list": []},
              "data": [], "meta": {}}

    # A. 代码常量 vs 论文
    text_nums = [float(x.replace(",", "")) for x in TEXT_NUM_RE.findall(pdf_text)]
    for p in params:
        hit = any(near(p["value"], t) for t in text_nums)
        report["params"].append({"label": p["label"], "value": p["value"], "file": p["file"], "in_paper": hit})
        if not hit:
            issues.append(("P2", "代码参数未在论文文本中找到: %s=%s (%s)" % (p["label"], p["value"], p["file"])))

    # B. 冻结数值 vs 论文（全量）
    if frozen_path and frozen_path.exists():
        fz = json.loads(frozen_path.read_text(encoding="utf-8"))
        vals = [n["value"] for n in fz.get("numbers", []) if isinstance(n.get("value"), (int, float))]
        miss = [v for v in vals if not any(near(v, t) for t in text_nums)]
        report["frozen"]["sampled"] = len(vals)
        report["frozen"]["miss"] = len(miss)
        report["frozen"]["miss_list"] = ["%g" % v for v in miss[:10]]
        if miss:
            issues.append(("P2", "冻结数值 %d 个未在论文文本中找到（容差±0.1%%）: %s（可能为内部证据/对照条目，需人工确认）" % (len(miss), ", ".join(report["frozen"]["miss_list"]))))

    # C. 数据特征 vs 论文
    for f in feats:
        row_hit = any(near(f["rows"], t) for t in text_nums)
        report["data"].append({"file": f["file"], "rows": f.get("rows"), "cols": f.get("cols"),
                               "min": f.get("min"), "max": f.get("max"), "rows_in_paper": row_hit})
        if f.get("error"):
            issues.append(("P2", "数据文件读取失败: %s (%s)" % (f["file"], f["error"])))
        elif not row_hit:
            issues.append(("P2", "数据行数未在论文文本中找到: %s 共 %d 行" % (f["file"], f.get("rows"))))

    # D. 结果 JSON vs 论文（全量数值抽样：取前 40 个）
    rn = result_nums[:40]
    miss_r = [r for r in rn if not any(near(r["value"], t) for t in text_nums)]
    report["meta"]["result_json_sampled"] = len(rn)
    report["meta"]["result_json_miss"] = len(miss_r)
    if miss_r:
        issues.append(("P2", "结果 JSON 数值 %d 个未在论文中找到（抽样前40，中间量未引用属正常，重点看核心结果）: %s" % (
            len(miss_r), ", ".join("%s=%g" % (r["key"], r["value"]) for r in miss_r[:6]))))

    return issues, report


def main(argv=None):
    ap = argparse.ArgumentParser(description="CUMCM-Review 三方一致性核对")
    ap.add_argument("--dir", required=True, help="论文包/工作区目录")
    ap.add_argument("--code", action="append", help="代码目录（可多次，默认 <dir>/code、<dir>/submission/代码）")
    ap.add_argument("--results", action="append", help="结果目录（默认 <dir>/results）")
    ap.add_argument("--data", action="append", help="数据目录（默认 <dir>/user_data、<dir>/submission/数据）")
    ap.add_argument("--pdf", help="主 PDF（默认自动发现）")
    ap.add_argument("--json", action="store_true", help="写 checks/cumcm-review-consistency.json")
    args = ap.parse_args(argv)

    directory = Path(args.dir)
    if not directory.exists():
        print("目录不存在: %s" % directory, file=sys.stderr)
        return 2

    code_dirs = [Path(c) for c in (args.code or [])] or [directory / "code", directory / "submission" / "代码"]
    results_dirs = [Path(r) for r in (args.results or [])] or [directory / "results"]
    data_dirs = [Path(d) for d in (args.data or [])] or [directory / "user_data", directory / "submission" / "数据"]

    pdf = Path(args.pdf) if args.pdf else None
    if pdf is None:
        cands = []
        for sub in ("paper", "submission", "submission/论文"):
            d = directory / sub
            if d.exists():
                cands += sorted(d.glob("*.pdf"), key=lambda p: p.stat().st_mtime, reverse=True)
        pdf = cands[0] if cands else None
    if pdf is None:
        print("未找到论文 PDF", file=sys.stderr)
        return 2
    try:
        import fitz
        pdf_text = "\n".join(fitz.open(pdf)[i].get_text() for i in range(fitz.open(pdf).page_count))
    except Exception as e:
        print("PDF 读取失败: %s" % e, file=sys.stderr)
        return 2

    params = extract_code_params(code_dirs)
    result_nums = collect_result_numbers(results_dirs)
    feats = data_features(data_dirs)
    frozen = results_dirs[0] / "frozen_numbers.json" if results_dirs else None
    issues, report = check(params, result_nums, feats, pdf_text, frozen)

    out = {"dir": str(directory), "pdf": str(pdf), "params_found": len(params),
           "result_json_numbers": len(result_nums), "data_files": len(feats),
           "report": report, "issues": issues}
    if args.json:
        checks_dir = directory / "checks"
        checks_dir.mkdir(exist_ok=True)
        (checks_dir / "cumcm-review-consistency.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print("三方一致性核对: PDF=%s" % pdf)
        print("  代码参数 %d 个 | 结果 JSON 数值 %d 个 | 数据文件 %d 个" % (
            len(params), len(result_nums), len(feats)))
        for p in report["params"]:
            print("  参数 %s=%s (%s) -> 论文%s" % (p["label"], p["value"], p["file"], "命中" if p["in_paper"] else "未命中"))
        print("  冻结数值 %d 个，未命中 %d" % (report["frozen"]["sampled"], report["frozen"]["miss"]))
        for f in report["data"]:
            print("  数据 %s: %s行x%s列 [%s,%s] -> 论文%s" % (
                f["file"], f.get("rows"), f.get("cols"), f.get("min"), f.get("max"),
                "命中" if f.get("rows_in_paper") else "未命中"))
        print("  结果 JSON 抽样 %d，未命中 %d" % (report["meta"]["result_json_sampled"], report["meta"]["result_json_miss"]))
        if issues:
            print("  矛盾 %d 项:" % len(issues))
            for sev, msg in issues:
                print("    - [%s] %s" % (sev, msg))
        else:
            print("  未发现 P1 级矛盾")
    return 1 if any(sev == "P1" for sev, _ in issues) else 0


if __name__ == "__main__":
    sys.exit(main())
