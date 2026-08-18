#!/usr/bin/env python3
"""Read-only static preflight for CUMCM paper sources and a final PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


PLACEHOLDER_PATTERNS = (
    re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE),
    re.compile(r"【[^】]*】"),
    re.compile(r"(?:待补|待复核|待冻结|待填写|占位符|模板提示)"),
)
LATEX_HARD_PATTERNS = {
    "latex-error": re.compile(r"(?:^|[\r\n])!\s+(?:LaTeX|Package|Class)?\s*Error", re.I),
    "undefined-control-sequence": re.compile(r"Undefined control sequence", re.I),
    "fatal-tex-error": re.compile(r"(?:Emergency stop|Fatal error occurred)", re.I),
    "undefined-reference": re.compile(
        r"(?:There were undefined references|Reference .+ undefined|Citation .+ undefined)",
        re.I,
    ),
    "missing-character": re.compile(r"Missing character:", re.I),
    "overfull-box": re.compile(r"Overfull \\[hv]box", re.I),
}
TEXT_EXTENSIONS = {".tex", ".log", ".md", ".txt", ".bib", ".sty", ".cls"}


def issue(code: str, path: Path, detail: str, severity: str = "P1") -> dict[str, str]:
    return {
        "code": code,
        "severity": severity,
        "path": str(path),
        "detail": detail,
    }


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def scan_placeholders(text: str, path: Path, issues: list[dict[str, str]]) -> None:
    for pattern in PLACEHOLDER_PATTERNS:
        match = pattern.search(text)
        if match:
            issues.append(
                issue(
                    "placeholder",
                    path,
                    f"发现未清理占位内容：{match.group(0)[:80]}",
                    "P1",
                )
            )
            return


def scan_docx(path: Path, issues: list[dict[str, str]]) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = set(archive.namelist())
            if "word/comments.xml" in names:
                issues.append(issue("word-comments", path, "DOCX 仍包含批注。"))
            document = archive.read("word/document.xml").decode("utf-8", errors="replace")
    except (OSError, KeyError, zipfile.BadZipFile) as exc:
        issues.append(issue("invalid-docx", path, f"无法读取 DOCX OOXML：{exc}", "P0"))
        return

    if re.search(r"<w:(?:ins|del)\b", document):
        issues.append(issue("word-tracked-changes", path, "DOCX 仍包含修订标记。"))
    if re.search(r"<w:(?:commentRangeStart|commentReference)\b", document):
        issues.append(issue("word-comments", path, "DOCX 正文仍包含批注引用。"))
    plain = re.sub(r"<[^>]+>", "", document)
    scan_placeholders(plain, path, issues)


def scan_source(source: Path, issues: list[dict[str, str]], warnings: list[str]) -> None:
    paths = [source] if source.is_file() else sorted(p for p in source.rglob("*") if p.is_file())
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".docm":
            issues.append(issue("macro-enabled-document", path, "不允许把宏文档作为提交主稿。", "P0"))
            continue
        if suffix == ".docx":
            scan_docx(path, issues)
            continue
        if suffix not in TEXT_EXTENSIONS:
            continue
        text = read_text(path)
        scan_placeholders(text, path, issues)
        if suffix == ".log":
            for code, pattern in LATEX_HARD_PATTERNS.items():
                if pattern.search(text):
                    severity = "P0" if code in {"latex-error", "undefined-control-sequence", "fatal-tex-error"} else "P1"
                    issues.append(issue(code, path, f"LaTeX 日志命中：{code}", severity))
            if re.search(r"Underfull \\[hv]box", text, re.I):
                warnings.append(f"{path}: underfull-box 需在真实 PDF 中人工判断")


def run_tool(command: list[str]) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )
    return completed.returncode, completed.stdout


def find_unembedded_fonts(output: str) -> list[str]:
    """Parse the fixed-width `pdffonts` table without guessing split columns."""
    lines = output.splitlines()
    header_index = next((i for i, line in enumerate(lines) if " emb " in line), None)
    if header_index is None:
        return []
    header = lines[header_index]
    emb_start = header.find("emb")
    sub_start = header.find("sub", emb_start + 3)
    if emb_start < 0 or sub_start < 0:
        return []
    unembedded: list[str] = []
    for line in lines[header_index + 2 :]:
        if not line.strip():
            continue
        if line[emb_start:sub_start].strip().lower() == "no":
            unembedded.append(line.strip())
    return unembedded


def evaluate_page_limit(
    total_pages: int | None,
    main_start_page: int,
    appendix_start_page: int | None,
    max_main_pages: int,
    pdf: Path,
    issues: list[dict[str, str]],
    warnings: list[str],
) -> dict[str, Any]:
    """Evaluate the physical-PDF-page boundary between body and appendix."""
    result: dict[str, Any] = {
        "status": "UNVERIFIED",
        "max_main_pages": max_main_pages,
        "main_start_pdf_page": main_start_page,
        "appendix_start_pdf_page": appendix_start_page,
        "total_pdf_pages": total_pages,
        "main_body_pages": None,
        "appendix_pages": None,
    }
    if total_pages is None:
        warnings.append("无法自动取得 PDF 总页数；Round B 必须人工核验正文不超过 30 页。")
        return result

    appendix_start = appendix_start_page or total_pages + 1
    result["appendix_start_pdf_page"] = appendix_start
    if not (1 <= main_start_page < appendix_start <= total_pages + 1):
        issues.append(
            issue(
                "invalid-body-appendix-boundary",
                pdf,
                "正文起始页、附录起始页与 PDF 总页数的关系无效。",
                "P0",
            )
        )
        result["status"] = "BLOCKED"
        return result

    main_pages = appendix_start - main_start_page
    appendix_pages = total_pages - appendix_start + 1 if appendix_start <= total_pages else 0
    result["main_body_pages"] = main_pages
    result["appendix_pages"] = appendix_pages
    if main_pages > max_main_pages:
        issues.append(
            issue(
                "main-body-over-page-limit",
                pdf,
                f"正文 {main_pages} 页，超过 {max_main_pages} 页上限；附录页数不计入上限。",
                "P0",
            )
        )
        result["status"] = "BLOCKED"
    else:
        result["status"] = "PASS"
    return result


def external_pdf_checks(
    pdf: Path,
    issues: list[dict[str, str]],
    warnings: list[str],
    tool_status: dict[str, str],
) -> dict[str, Any]:
    metadata: dict[str, Any] = {}
    for name in ("pdfinfo", "pdffonts", "pdftotext"):
        tool_status[name] = "available" if shutil.which(name) else "unavailable"

    if tool_status["pdfinfo"] == "available":
        code, output = run_tool(["pdfinfo", str(pdf)])
        if code != 0:
            issues.append(issue("pdfinfo-failed", pdf, output.strip()[:400], "P0"))
        else:
            for line in output.splitlines():
                if ":" not in line:
                    continue
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                if key in {"pages", "page_size", "encrypted", "pdf_version"}:
                    metadata[key] = value.strip()
            if metadata.get("encrypted", "").lower() not in {"", "no"}:
                issues.append(issue("encrypted-pdf", pdf, "PDF 已加密，可能无法按要求评阅。", "P0"))
            try:
                if int(metadata.get("pages", "1")) <= 0:
                    issues.append(issue("invalid-page-count", pdf, "PDF 页数不是正数。", "P0"))
            except ValueError:
                warnings.append("pdfinfo 页数字段无法解析，需人工确认。")

    if tool_status["pdffonts"] == "available":
        code, output = run_tool(["pdffonts", str(pdf)])
        if code != 0:
            warnings.append(f"pdffonts 无法完成字体检查：{output.strip()[:200]}")
        else:
            metadata["font_table_checked"] = True
            for line in find_unembedded_fonts(output):
                issues.append(issue("font-not-embedded", pdf, f"字体未嵌入：{line[:240]}", "P1"))

    if tool_status["pdftotext"] == "available":
        with tempfile.TemporaryDirectory(prefix="cumcm-layout-") as temp_dir:
            text_path = Path(temp_dir) / "paper.txt"
            code, output = run_tool(["pdftotext", str(pdf), str(text_path)])
            if code != 0 or not text_path.exists():
                warnings.append(f"pdftotext 无法提取文本：{output.strip()[:200]}")
            else:
                extracted = read_text(text_path)
                metadata["extracted_text_chars"] = len(extracted)
                scan_placeholders(extracted, pdf, issues)
                if not extracted.strip():
                    warnings.append("PDF 未提取到文字；需要确认是否为扫描件或字体编码异常。")
    return metadata


def build_report(
    pdf: Path,
    source: Path | None,
    max_pdf_mb: float | None,
    main_start_page: int,
    appendix_start_page: int | None,
    max_main_pages: int,
    skip_external_tools: bool,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    warnings: list[str] = []
    tool_status: dict[str, str] = {}
    size = pdf.stat().st_size
    header = pdf.read_bytes()[:8]
    tail = pdf.read_bytes()[-2048:]

    if not header.startswith(b"%PDF-"):
        issues.append(issue("invalid-pdf-header", pdf, "文件不以 %PDF- 开头。", "P0"))
    if b"%%EOF" not in tail:
        issues.append(issue("missing-pdf-eof", pdf, "文件尾部未发现 %%EOF。", "P0"))
    if max_pdf_mb is not None and size > max_pdf_mb * 1024 * 1024:
        issues.append(
            issue(
                "pdf-over-size-limit",
                pdf,
                f"{size} bytes 超过 {max_pdf_mb} MiB 限制。",
                "P0",
            )
        )
    if source is not None:
        scan_source(source, issues, warnings)

    metadata: dict[str, Any] = {}
    if skip_external_tools:
        tool_status = {"pdfinfo": "skipped", "pdffonts": "skipped", "pdftotext": "skipped"}
    elif header.startswith(b"%PDF-"):
        metadata = external_pdf_checks(pdf, issues, warnings, tool_status)

    total_pages: int | None = None
    try:
        if "pages" in metadata:
            total_pages = int(metadata["pages"])
    except (TypeError, ValueError):
        warnings.append("PDF 总页数字段无法解析；Round B 必须人工核验页数。")
    page_limit = evaluate_page_limit(
        total_pages,
        main_start_page,
        appendix_start_page,
        max_main_pages,
        pdf,
        issues,
        warnings,
    )

    return {
        "status": "BLOCKED" if issues else "PRECHECK_PASS",
        "visual_qa_required": True,
        "pdf": str(pdf),
        "pdf_sha256": sha256(pdf),
        "pdf_size_bytes": size,
        "source": str(source) if source else None,
        "issues": issues,
        "warnings": warnings,
        "tools": tool_status,
        "metadata": metadata,
        "page_limit": page_limit,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--max-pdf-mb", type=float)
    parser.add_argument(
        "--main-start-page",
        type=int,
        default=1,
        help="正文在最终 PDF 中的起始物理页，默认 1。",
    )
    parser.add_argument(
        "--appendix-start-page",
        type=int,
        help="附录在最终 PDF 中的起始物理页；无附录时省略。",
    )
    parser.add_argument(
        "--max-main-pages",
        type=int,
        default=30,
        help="正文页数上限，默认且最高为 30；只允许按更严格规则调低，附录不计入。",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--skip-external-tools",
        action="store_true",
        help="仅用于受控测试；真实复核不要跳过可用的 PDF 工具。",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if not args.pdf.is_file():
        print(f"错误：PDF 路径不存在或不是文件：{args.pdf}", file=sys.stderr)
        return 2
    if args.source is not None and not args.source.exists():
        print(f"错误：源文件路径不存在：{args.source}", file=sys.stderr)
        return 2
    if args.max_pdf_mb is not None and args.max_pdf_mb <= 0:
        print("错误：--max-pdf-mb 必须大于 0。", file=sys.stderr)
        return 2
    if args.main_start_page <= 0:
        print("错误：--main-start-page 必须大于 0。", file=sys.stderr)
        return 2
    if args.appendix_start_page is not None and args.appendix_start_page <= 0:
        print("错误：--appendix-start-page 必须大于 0。", file=sys.stderr)
        return 2
    if not 1 <= args.max_main_pages <= 30:
        print("错误：--max-main-pages 必须在 1–30 之间，不能放宽 30 页硬门。", file=sys.stderr)
        return 2

    report = build_report(
        args.pdf.resolve(),
        args.source.resolve() if args.source else None,
        args.max_pdf_mb,
        args.main_start_page,
        args.appendix_start_page,
        args.max_main_pages,
        args.skip_external_tools,
    )
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"status={report['status']}")
        print(f"visual_qa_required={str(report['visual_qa_required']).lower()}")
        print(f"pdf_sha256={report['pdf_sha256']}")
        print(f"page_limit_status={report['page_limit']['status']}")
        print(f"main_body_pages={report['page_limit']['main_body_pages']}")
        for found in report["issues"]:
            print(f"{found['severity']} {found['code']}: {found['path']} - {found['detail']}")
        for warning in report["warnings"]:
            print(f"WARN: {warning}")
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
