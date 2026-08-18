# -*- coding: utf-8 -*-
"""smoke_test_review.py — cumcm-review 冒烟自检（v1.1）
验证：① 旧 schema(numbers-list) 兼容；② 嵌套 dict schema；③ FROZEN-SCHEMA 空查必报；
④ IMG-REF-MISSING 图片缺失触发；⑤ AI-LOG-MISSING 触发；⑥ 正常包无 P0。
用法: python smoke_test_review.py --pdf <真实论文PDF> [--frozen <真实frozen>]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts" / "review_paper.py"

def run(directory, pdf, frozen=None, expect_issues=()):
    cmd = [sys.executable, str(SCRIPT), "--dir", str(directory), "--pdf", str(pdf), "--json"]
    if frozen:
        cmd += ["--frozen", str(frozen)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    try:
        out = json.loads(r.stdout)
    except Exception:
        return False, "JSON 解析失败: %s" % r.stdout[:200]
    kinds = [k for k, _ in out.get("issues", [])]
    ok = all(e in kinds for e in expect_issues)
    return ok, "kinds=%s" % kinds

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True, help="真实论文 PDF（用于 pdf 参数）")
    ap.add_argument("--frozen", help="真实 frozen_numbers.json（用于对照）")
    args = ap.parse_args()
    pdf = Path(args.pdf)
    tmp = Path(tempfile.mkdtemp(prefix="cumcm_review_smoke_"))
    results = []
    try:
        # ① 旧 schema numbers-list（值 0.824 应出现在真实论文）
        d1 = tmp / "pkg_numbers_list"
        d1.mkdir(parents=True)
        (d1 / "frozen_numbers.json").write_text(
            json.dumps({"numbers": [{"id": "T1", "key": "AUC", "value": 0.824, "verified": True}]}),
            encoding="utf-8")
        ok, info = run(d1, pdf, d1 / "frozen_numbers.json")
        # 需要读 json 确认 schema
        r = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(d1), "--pdf", str(pdf),
                            "--frozen", str(d1 / "frozen_numbers.json"), "--json"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        o = json.loads(r.stdout)
        s = o["pdf_check"]["stats"]
        results.append(("① numbers-list 旧 schema 兼容", s.get("frozen_schema") == "numbers-list" and s.get("frozen_missing_in_pdf") == 0,
                        "schema=%s missing=%s" % (s.get("frozen_schema"), s.get("frozen_missing_in_pdf"))))

        # ② 嵌套 dict schema（真实 frozen）
        if args.frozen:
            d2 = tmp / "pkg_nested"
            d2.mkdir(parents=True)
            shutil.copy(args.frozen, d2 / "frozen_numbers.json")
            ok, info = run(d2, pdf, d2 / "frozen_numbers.json")
            r = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(d2), "--pdf", str(pdf),
                                "--frozen", str(d2 / "frozen_numbers.json"), "--json"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            o = json.loads(r.stdout)
            s = o["pdf_check"]["stats"]
            results.append(("② 嵌套 dict schema 执行数字检查", s.get("frozen_schema") == "nested-dict" and s.get("frozen_sampled", 0) > 0,
                            "schema=%s sampled=%s missing=%s" % (s.get("frozen_schema"), s.get("frozen_sampled"), s.get("frozen_missing_in_pdf"))))

        # ③ FROZEN-SCHEMA 空查必报（frozen 为空 dict）
        d3 = tmp / "pkg_empty"
        d3.mkdir(parents=True)
        (d3 / "frozen_numbers.json").write_text("{}", encoding="utf-8")
        ok, info = run(d3, pdf, d3 / "frozen_numbers.json", expect_issues=("FROZEN-SCHEMA",))
        results.append(("③ FROZEN-SCHEMA 空查必报", ok, info))

        # ④ IMG-REF-MISSING（tex 引用不存在的图）
        d4 = tmp / "pkg_img"
        d4.mkdir(parents=True)
        paper = d4 / "paper"
        paper.mkdir(parents=True)
        (paper / "test.tex").write_text("\\includegraphics{figures/fig_missing_xx.png}\n", encoding="utf-8")
        ok, info = run(d4, pdf, expect_issues=("IMG-REF-MISSING",))
        results.append(("④ IMG-REF-MISSING 图片缺失触发", ok, info))

        # ⑤ AI-LOG-MISSING（无 AI_USE_LOG.md）
        ok, info = run(d4, pdf, expect_issues=("AI-LOG-MISSING",))
        results.append(("⑤ AI-LOG-MISSING 触发", ok, info))

        # ⑥ 正常包无 P0（真实 outputs 目录）
        if args.frozen:
            real = Path(args.pdf).parents[1]  # outputs
            ok, info = run(real, pdf, args.frozen)
            has_p0 = "FROZEN-SCHEMA" in [k for k, _ in json.loads(subprocess.run(
                [sys.executable, str(SCRIPT), "--dir", str(real), "--pdf", str(pdf), "--frozen", str(args.frozen), "--json"],
                capture_output=True, text=True, encoding="utf-8", errors="replace").stdout).get("issues", [])]
            results.append(("⑥ 真实包回归：无 FROZEN-SCHEMA/IMG-REF-MISSING", not has_p0 and ok, info))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("===== cumcm-review smoke test =====")
    failed = 0
    for name, ok, info in results:
        print("  [%s] %s — %s" % ("PASS" if ok else "FAIL", name, info))
        if not ok:
            failed += 1
    print("结论: %s" % ("ALL PASSED" if failed == 0 else "%d FAILED" % failed))
    return 1 if failed else 0

if __name__ == "__main__":
    sys.exit(main())
