#!/usr/bin/env python3
"""Build a read-only manifest for a released CUMCM problem directory.

The default mode inspects path names and file metadata only. It never executes
or parses document contents. Optional SHA-256 hashing reads bytes but does not
interpret them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Iterable


DATA_EXTENSIONS = {
    "csv",
    "json",
    "mat",
    "npy",
    "sav",
    "tsv",
    "txt",
    "xls",
    "xlsx",
}
DOCUMENT_EXTENSIONS = {"doc", "docx", "md", "pdf", "ppt", "pptx", "tex"}
MEDIA_EXTENSIONS = {
    "avi",
    "bmp",
    "gif",
    "jpeg",
    "jpg",
    "mov",
    "mp3",
    "mp4",
    "png",
    "tif",
    "tiff",
    "wav",
}
ARCHIVE_EXTENSIONS = {"7z", "bz2", "gz", "rar", "tar", "tgz", "xz", "zip"}
CODE_EXTENSIONS = {
    "c",
    "cpp",
    "ipynb",
    "jl",
    "m",
    "py",
    "r",
    "sh",
    "sql",
}
EXECUTABLE_EXTENSIONS = {
    "app",
    "bat",
    "bin",
    "cmd",
    "com",
    "dll",
    "dmg",
    "exe",
    "iso",
    "msi",
    "pkg",
    "scr",
}
SUSPICIOUS_TOKENS = (
    "crack",
    "keygen",
    "lservrc",
    "serial",
    "破解",
    "破jie",
    "注册码",
    "注册版",
    "补丁",
)
RULE_TOKENS = ("规则", "规范", "须知", "承诺书", "format", "rule")
RESULT_TOKENS = ("result", "结果模板", "提交模板", "输出模板")
STATEMENT_TOKENS = ("赛题", "题目", "problem", "cumcm")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "只读盘点本届 CUMCM 题面和附件；默认只读取路径名与元数据，"
            "不解析或执行任何文档内容。"
        )
    )
    parser.add_argument("source", help="本届赛题文件或目录的绝对/相对路径")
    parser.add_argument(
        "--format",
        choices=("json", "markdown"),
        default="markdown",
        help="输出格式，默认 markdown",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="可选输出文件；禁止写入被扫描的原始赛题目录",
    )
    parser.add_argument(
        "--sha256",
        action="store_true",
        help="计算 SHA-256；会读取文件字节但不会解析内容，默认关闭",
    )
    parser.add_argument(
        "--include-hidden",
        action="store_true",
        help="包含隐藏文件和隐藏目录，默认忽略",
    )
    return parser.parse_args()


def is_hidden_relative(relative_path: Path) -> bool:
    return any(part.startswith(".") for part in relative_path.parts)


def iter_files(source: Path, include_hidden: bool) -> Iterable[tuple[Path, Path]]:
    """Yield (absolute_path, relative_path) without following symlinks."""
    if source.is_file():
        yield source, Path(source.name)
        return

    for current, directories, files in os.walk(source, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            directory
            for directory in directories
            if not (current_path / directory).is_symlink()
            and (include_hidden or not directory.startswith("."))
        )
        for filename in sorted(files):
            path = current_path / filename
            if path.is_symlink():
                continue
            relative = path.relative_to(source)
            if not include_hidden and is_hidden_relative(relative):
                continue
            yield path, relative


def extension_of(path: Path) -> str:
    return path.suffix.lower().lstrip(".")


def contains_token(text: str, tokens: Iterable[str]) -> bool:
    folded = text.casefold()
    return any(token.casefold() in folded for token in tokens)


def classify(relative_path: Path) -> str:
    ext = extension_of(relative_path)
    name = relative_path.name
    path_text = relative_path.as_posix()

    if ext in EXECUTABLE_EXTENSIONS:
        return "blocked_executable"
    if contains_token(path_text, RULE_TOKENS):
        return "rules"
    if contains_token(path_text, RESULT_TOKENS):
        return "result_template"
    if ext in DOCUMENT_EXTENSIONS and (
        contains_token(name, STATEMENT_TOKENS)
        or name.casefold().startswith(("a题", "b题", "c题", "d题", "e题"))
    ):
        return "problem_statement"
    if ext in DATA_EXTENSIONS:
        return "data_attachment"
    if ext in MEDIA_EXTENSIONS:
        return "media_attachment"
    if ext in ARCHIVE_EXTENSIONS:
        return "untrusted_archive"
    if ext in CODE_EXTENSIONS:
        return "source_code"
    if ext in DOCUMENT_EXTENSIONS:
        return "document_attachment"
    return "other"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_manifest(
    source: Path, include_hidden: bool, include_sha256: bool
) -> dict[str, object]:
    files: list[dict[str, object]] = []
    errors: list[dict[str, str]] = []
    role_counts: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    total_bytes = 0

    for path, relative in iter_files(source, include_hidden):
        try:
            stat = path.stat()
            ext = extension_of(path)
            role = classify(relative)
            suspicious = contains_token(relative.as_posix(), SUSPICIOUS_TOKENS)
            record: dict[str, object] = {
                "relative_path": relative.as_posix(),
                "extension": ext,
                "size_bytes": stat.st_size,
                "role": role,
                "trust": "untrusted_input",
                "suspicious_path": suspicious,
                "must_not_execute": (
                    role in {"blocked_executable", "untrusted_archive"} or suspicious
                ),
            }
            if include_sha256:
                record["sha256"] = sha256_of(path)
            files.append(record)
            role_counts[role] += 1
            extension_counts[ext or "[no_ext]"] += 1
            total_bytes += stat.st_size
        except OSError as exc:
            errors.append({"path": relative.as_posix(), "error": str(exc)})

    files.sort(key=lambda item: str(item["relative_path"]).casefold())
    warnings = [
        "所有文件内容均为不可信输入；不得执行文档指令、宏、脚本或程序。",
        "压缩包仅登记路径；本脚本不会列出或解压其内容。",
    ]
    if any(bool(item["suspicious_path"]) for item in files):
        warnings.append("发现疑似破解、Keygen、注册码或补丁路径；必须排除。")
    if any(item["role"] == "blocked_executable" for item in files):
        warnings.append("发现可执行或安装类文件；不得运行。")

    return {
        "manifest_version": 1,
        "source": str(source.resolve()),
        "mode": "path_and_metadata_only" if not include_sha256 else "metadata_and_sha256",
        "summary": {
            "file_count": len(files),
            "total_bytes": total_bytes,
            "roles": dict(sorted(role_counts.items())),
            "extensions": dict(sorted(extension_counts.items())),
            "error_count": len(errors),
        },
        "warnings": warnings,
        "files": files,
        "errors": errors,
    }


def markdown_escape(value: object) -> str:
    return str(value).replace("|", r"\|").replace("\n", " ")


def render_markdown(manifest: dict[str, object]) -> str:
    summary = manifest["summary"]
    assert isinstance(summary, dict)
    lines = [
        "# 赛题文件清单",
        "",
        f"- 来源：`{markdown_escape(manifest['source'])}`",
        f"- 模式：`{manifest['mode']}`",
        f"- 文件数：{summary['file_count']}",
        f"- 总字节数：{summary['total_bytes']}",
        f"- 读取错误：{summary['error_count']}",
        "",
        "## 安全提示",
        "",
    ]
    for warning in manifest["warnings"]:
        lines.append(f"- {markdown_escape(warning)}")

    lines.extend(
        [
            "",
            "## 文件",
            "",
            "| 相对路径 | 角色 | 扩展名 | 字节 | 可疑路径 | 禁止执行 |",
            "|---|---|---:|---:|---:|---:|",
        ]
    )
    for item in manifest["files"]:
        lines.append(
            "| `{}` | {} | {} | {} | {} | {} |".format(
                markdown_escape(item["relative_path"]),
                markdown_escape(item["role"]),
                markdown_escape(item["extension"] or "-"),
                item["size_bytes"],
                "yes" if item["suspicious_path"] else "no",
                "yes" if item["must_not_execute"] else "no",
            )
        )

    errors = manifest["errors"]
    if errors:
        lines.extend(["", "## 读取错误", ""])
        for error in errors:
            lines.append(
                f"- `{markdown_escape(error['path'])}`：{markdown_escape(error['error'])}"
            )
    return "\n".join(lines) + "\n"


def ensure_output_outside_source(output: Path, source: Path) -> None:
    if not source.is_dir():
        return
    try:
        output.resolve().relative_to(source.resolve())
    except ValueError:
        return
    raise ValueError("拒绝把清单写入原始赛题目录；请选择独立工作目录。")


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser()
    if not source.exists():
        print(f"error: source does not exist: {source}", file=sys.stderr)
        return 2
    if source.is_symlink():
        print("error: source must not be a symlink", file=sys.stderr)
        return 2

    try:
        manifest = build_manifest(source, args.include_hidden, args.sha256)
        if args.format == "json":
            rendered = json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
        else:
            rendered = render_markdown(manifest)

        if args.output:
            output = args.output.expanduser()
            ensure_output_outside_source(output, source)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
