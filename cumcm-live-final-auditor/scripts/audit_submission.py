#!/usr/bin/env python3
"""Read-only static audit for a CUMCM submission candidate directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


MODEL_SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cxx",
    ".f",
    ".f03",
    ".f08",
    ".f90",
    ".f95",
    ".for",
    ".go",
    ".h",
    ".hpp",
    ".ipynb",
    ".java",
    ".jl",
    ".js",
    ".lg4",
    ".lgo",
    ".lng",
    ".lp",
    ".lua",
    ".m",
    ".mlx",
    ".mod",
    ".nb",
    ".py",
    ".qmd",
    ".r",
    ".rmd",
    ".sas",
    ".scala",
    ".sh",
    ".slx",
    ".sps",
    ".sql",
    ".stan",
    ".ts",
    ".vba",
    ".wl",
    ".do",
}

PAPER_SOURCE_SUFFIXES = {
    ".bib",
    ".doc",
    ".docx",
    ".dot",
    ".dotx",
    ".latex",
    ".md",
    ".odt",
    ".rtf",
    ".tex",
}

DANGEROUS_SUFFIX_FLAGS = {
    ".app": "executable-bundle",
    ".bat": "executable-script",
    ".cmd": "executable-script",
    ".com": "windows-executable",
    ".dll": "binary-library",
    ".dmg": "disk-image",
    ".exe": "windows-executable",
    ".iso": "disk-image",
    ".lnk": "windows-shortcut",
    ".msi": "windows-installer",
    ".pkg": "installer-package",
    ".ps1": "executable-script",
    ".scr": "windows-executable",
    ".vbs": "executable-script",
}

MACRO_SUFFIXES = {
    ".docm",
    ".dotm",
    ".ppam",
    ".ppsm",
    ".pptm",
    ".xlam",
    ".xlsb",
    ".xlsm",
    ".xltm",
}

LEGACY_OFFICE_SUFFIXES = {".doc", ".dot", ".ppt", ".pps", ".xls"}
ARCHIVE_SUFFIXES = {".7z", ".rar", ".tar", ".tgz", ".zip"}

DANGEROUS_NAME_TOKENS = {
    "activator": "activation-tool-name",
    "crack": "crack-name",
    "keygen": "keygen-name",
    "kmsauto": "activation-tool-name",
    "patcher": "patcher-name",
    "serialkey": "license-bypass-name",
    "激活器": "activation-tool-name",
    "注册机": "keygen-name",
    "破解": "crack-name",
}

CLUTTER_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}
CLUTTER_PARTS = {"__macosx", "__pycache__", ".ipynb_checkpoints"}


def positive_float(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a number") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be greater than zero")
    return parsed


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only scan of a CUMCM submission directory. Lists files, sizes, "
            "SHA-256 values, mandatory artifacts, and security risks."
        )
    )
    parser.add_argument("submission_dir", help="submission candidate directory")
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON",
    )
    parser.add_argument(
        "--max-pdf-mb",
        type=positive_float,
        default=None,
        metavar="MB",
        help=(
            "maximum size for each PDF in decimal MB; provide only when the user "
            "or current official rules specify a limit"
        ),
    )
    return parser.parse_args(argv)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def has_pdf_header(path: Path) -> bool:
    try:
        with path.open("rb") as handle:
            return handle.read(5) == b"%PDF-"
    except OSError:
        return False


def iter_entries(root: Path) -> Iterable[Path]:
    for current, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        filenames.sort()
        current_path = Path(current)

        symlink_dirs: list[str] = []
        for dirname in dirnames:
            candidate = current_path / dirname
            if candidate.is_symlink():
                symlink_dirs.append(dirname)
                yield candidate
        if symlink_dirs:
            blocked = set(symlink_dirs)
            dirnames[:] = [name for name in dirnames if name not in blocked]

        for filename in filenames:
            yield current_path / filename


def risk_flags(relative_path: str, suffix: str, is_symlink: bool) -> list[str]:
    flags: list[str] = []
    lower_path = relative_path.casefold()
    lower_name = Path(relative_path).name.casefold()
    parts = {part.casefold() for part in Path(relative_path).parts}

    if is_symlink:
        flags.append("symlink")
    if suffix in DANGEROUS_SUFFIX_FLAGS:
        flags.append(DANGEROUS_SUFFIX_FLAGS[suffix])
    if suffix in MACRO_SUFFIXES:
        flags.append("macro-enabled-office")
    if suffix in LEGACY_OFFICE_SUFFIXES:
        flags.append("legacy-office-binary")
    if suffix in ARCHIVE_SUFFIXES:
        flags.append("archive-needs-review")
    if lower_name in CLUTTER_NAMES or parts.intersection(CLUTTER_PARTS):
        flags.append("packaging-clutter")
    if lower_name.startswith("~$"):
        flags.append("office-temporary-file")
    if suffix in {".pyc", ".pyo"}:
        flags.append("compiled-cache")

    for token, flag in DANGEROUS_NAME_TOKENS.items():
        if token in lower_path:
            flags.append(flag)

    return sorted(set(flags))


def is_dangerous(flags: list[str]) -> bool:
    nonblocking = {
        "archive-needs-review",
        "compiled-cache",
        "legacy-office-binary",
        "office-temporary-file",
        "packaging-clutter",
    }
    return any(flag not in nonblocking for flag in flags)


def audit(root: Path, max_pdf_mb: float | None) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    errors: list[str] = []
    valid_pdf_count = 0
    invalid_pdf_count = 0
    model_source_count = 0
    paper_source_count = 0
    dangerous_count = 0
    oversized_pdf_count = 0
    total_size = 0
    max_pdf_bytes = (
        int(max_pdf_mb * 1_000_000) if max_pdf_mb is not None else None
    )

    for path in iter_entries(root):
        relative = path.relative_to(root).as_posix()
        suffix = path.suffix.casefold()
        symlink = path.is_symlink()
        flags = risk_flags(relative, suffix, symlink)
        entry: dict[str, Any] = {
            "path": relative,
            "size_bytes": None,
            "sha256": None,
            "suffix": suffix,
            "risk_flags": flags,
            "dangerous": is_dangerous(flags),
        }

        try:
            stat_result = path.lstat()
            entry["size_bytes"] = stat_result.st_size
            total_size += stat_result.st_size
            if not symlink and path.is_file():
                entry["sha256"] = sha256_file(path)
        except OSError as exc:
            message = f"{relative}: {exc}"
            entry["error"] = str(exc)
            errors.append(message)

        if suffix == ".pdf" and not symlink:
            if has_pdf_header(path):
                entry["valid_pdf_header"] = True
                valid_pdf_count += 1
            else:
                entry["valid_pdf_header"] = False
                entry["risk_flags"] = sorted(
                    set(entry["risk_flags"] + ["invalid-pdf-header"])
                )
                invalid_pdf_count += 1

            if (
                max_pdf_bytes is not None
                and isinstance(entry["size_bytes"], int)
                and entry["size_bytes"] > max_pdf_bytes
            ):
                entry["risk_flags"] = sorted(
                    set(entry["risk_flags"] + ["pdf-over-size-limit"])
                )
                oversized_pdf_count += 1

        if suffix in MODEL_SOURCE_SUFFIXES and not symlink:
            model_source_count += 1
        if suffix in PAPER_SOURCE_SUFFIXES and not symlink:
            paper_source_count += 1
        if entry["dangerous"]:
            dangerous_count += 1

        files.append(entry)

    checks = {
        "has_valid_pdf": {
            "passed": valid_pdf_count > 0,
            "count": valid_pdf_count,
        },
        "all_pdf_extensions_valid": {
            "passed": invalid_pdf_count == 0,
            "invalid_count": invalid_pdf_count,
        },
        "has_model_source_code": {
            "passed": model_source_count > 0,
            "count": model_source_count,
        },
        "no_dangerous_items": {
            "passed": dangerous_count == 0,
            "count": dangerous_count,
        },
        "pdf_size_limit": {
            "passed": max_pdf_bytes is None or oversized_pdf_count == 0,
            "limit_mb": max_pdf_mb,
            "oversized_count": oversized_pdf_count,
            "not_evaluated": max_pdf_bytes is None,
        },
        "scan_complete": {
            "passed": not errors,
            "error_count": len(errors),
        },
    }

    passed = all(check["passed"] for check in checks.values())
    return {
        "schema_version": 1,
        "root": str(root),
        "scanned_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if passed else "BLOCKED",
        "checks": checks,
        "summary": {
            "file_count": len(files),
            "total_size_bytes": total_size,
            "valid_pdf_count": valid_pdf_count,
            "invalid_pdf_count": invalid_pdf_count,
            "model_source_count": model_source_count,
            "paper_source_count": paper_source_count,
            "dangerous_count": dangerous_count,
            "oversized_pdf_count": oversized_pdf_count,
        },
        "files": files,
        "errors": errors,
    }


def print_human(report: dict[str, Any]) -> None:
    print("CUMCM submission static audit")
    print(f"Status: {report['status']}")
    print(f"Root: {report['root']}")
    print(f"Scanned at UTC: {report['scanned_at_utc']}")
    print()
    print("Checks:")
    for name, result in report["checks"].items():
        state = "PASS" if result["passed"] else "BLOCKED"
        detail_parts = [
            f"{key}={value}"
            for key, value in result.items()
            if key != "passed"
        ]
        detail = f" ({', '.join(detail_parts)})" if detail_parts else ""
        print(f"- {name}: {state}{detail}")

    print()
    print("Files:")
    for entry in report["files"]:
        flags = ",".join(entry["risk_flags"]) or "-"
        size = entry["size_bytes"]
        digest = entry["sha256"] or "-"
        print(f"- {entry['path']}")
        print(f"  size_bytes={size} sha256={digest} risk_flags={flags}")

    if report["errors"]:
        print()
        print("Scan errors:")
        for error in report["errors"]:
            print(f"- {error}")

    print()
    print(
        "Note: PASS covers only this static scan; current official rules, content "
        "consistency, reproducibility, AI disclosure, and rendered PDF still "
        "require manual audit."
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.submission_dir).expanduser().resolve()
    if not root.exists():
        print(f"error: directory does not exist: {root}", file=sys.stderr)
        return 2
    if not root.is_dir():
        print(f"error: target is not a directory: {root}", file=sys.stderr)
        return 2

    report = audit(root, args.max_pdf_mb)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(report)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
