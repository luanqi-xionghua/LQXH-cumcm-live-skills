#!/usr/bin/env python3
"""Compare frozen result directories from repeated CUMCM runs."""

from __future__ import annotations

import argparse
import csv
import fnmatch
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


NUMBER_RE = re.compile(
    r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?$"
)
LEADING_ZERO_INTEGER_RE = re.compile(r"^[+-]?0\d+$")


@dataclass
class MismatchCollector:
    max_items: int
    items: list[dict[str, Any]] = field(default_factory=list)
    total: int = 0

    def add(self, **item: Any) -> None:
        self.total += 1
        if len(self.items) < self.max_items:
            self.items.append(item)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_ignored(relative_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(relative_path, pattern) for pattern in patterns)


def collect_files(
    root: Path,
    ignore_patterns: list[str],
) -> tuple[dict[str, Path], list[str]]:
    files: dict[str, Path] = {}
    symlinks: list[str] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if is_ignored(relative, ignore_patterns):
            continue
        if path.is_symlink():
            symlinks.append(relative)
        elif path.is_file():
            files[relative] = path
    return files, symlinks


def short_value(value: Any, limit: int = 160) -> str:
    rendered = repr(value)
    if len(rendered) <= limit:
        return rendered
    return rendered[: limit - 3] + "..."


def numeric_text(value: str) -> float | None:
    stripped = value.strip()
    if not NUMBER_RE.fullmatch(stripped):
        return None
    if LEADING_ZERO_INTEGER_RE.fullmatch(stripped):
        return None
    number = float(stripped)
    return number


def compare_scalar(
    expected: Any,
    actual: Any,
    *,
    run: str,
    path: str,
    location: str,
    rtol: float,
    atol: float,
    collector: MismatchCollector,
) -> None:
    expected_is_number = (
        isinstance(expected, (int, float)) and not isinstance(expected, bool)
    )
    actual_is_number = (
        isinstance(actual, (int, float)) and not isinstance(actual, bool)
    )
    if expected_is_number and actual_is_number:
        expected_number = float(expected)
        actual_number = float(actual)
        if not math.isfinite(expected_number) or not math.isfinite(actual_number):
            collector.add(
                run=run,
                path=path,
                code="non-finite-number",
                location=location,
                expected=short_value(expected),
                actual=short_value(actual),
            )
            return
        if not math.isclose(
            expected_number,
            actual_number,
            rel_tol=rtol,
            abs_tol=atol,
        ):
            collector.add(
                run=run,
                path=path,
                code="numeric-drift",
                location=location,
                expected=expected_number,
                actual=actual_number,
                absolute_difference=abs(expected_number - actual_number),
            )
        return

    if type(expected) is not type(actual) or expected != actual:
        collector.add(
            run=run,
            path=path,
            code="value-mismatch",
            location=location,
            expected=short_value(expected),
            actual=short_value(actual),
        )


def compare_json_values(
    expected: Any,
    actual: Any,
    *,
    run: str,
    path: str,
    location: str,
    rtol: float,
    atol: float,
    collector: MismatchCollector,
) -> None:
    if isinstance(expected, dict) and isinstance(actual, dict):
        expected_keys = set(expected)
        actual_keys = set(actual)
        for key in sorted(expected_keys - actual_keys):
            collector.add(
                run=run,
                path=path,
                code="missing-json-key",
                location=f"{location}.{key}",
            )
        for key in sorted(actual_keys - expected_keys):
            collector.add(
                run=run,
                path=path,
                code="extra-json-key",
                location=f"{location}.{key}",
            )
        for key in sorted(expected_keys & actual_keys):
            compare_json_values(
                expected[key],
                actual[key],
                run=run,
                path=path,
                location=f"{location}.{key}",
                rtol=rtol,
                atol=atol,
                collector=collector,
            )
        return

    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            collector.add(
                run=run,
                path=path,
                code="json-length-mismatch",
                location=location,
                expected=len(expected),
                actual=len(actual),
            )
        for index, (expected_item, actual_item) in enumerate(
            zip(expected, actual)
        ):
            compare_json_values(
                expected_item,
                actual_item,
                run=run,
                path=path,
                location=f"{location}[{index}]",
                rtol=rtol,
                atol=atol,
                collector=collector,
            )
        return

    compare_scalar(
        expected,
        actual,
        run=run,
        path=path,
        location=location,
        rtol=rtol,
        atol=atol,
        collector=collector,
    )


def reject_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON constant: {value}")


def compare_json_files(
    expected_path: Path,
    actual_path: Path,
    *,
    run: str,
    relative_path: str,
    rtol: float,
    atol: float,
    collector: MismatchCollector,
) -> None:
    try:
        expected = json.loads(
            expected_path.read_text(encoding="utf-8"),
            parse_constant=reject_json_constant,
        )
        actual = json.loads(
            actual_path.read_text(encoding="utf-8"),
            parse_constant=reject_json_constant,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        collector.add(
            run=run,
            path=relative_path,
            code="json-parse-error",
            detail=str(error),
        )
        return

    compare_json_values(
        expected,
        actual,
        run=run,
        path=relative_path,
        location="$",
        rtol=rtol,
        atol=atol,
        collector=collector,
    )


def read_table(path: Path, delimiter: str) -> list[list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.reader(handle, delimiter=delimiter))


def compare_table_files(
    expected_path: Path,
    actual_path: Path,
    *,
    run: str,
    relative_path: str,
    delimiter: str,
    rtol: float,
    atol: float,
    collector: MismatchCollector,
) -> None:
    try:
        expected_rows = read_table(expected_path, delimiter)
        actual_rows = read_table(actual_path, delimiter)
    except (OSError, UnicodeDecodeError, csv.Error) as error:
        collector.add(
            run=run,
            path=relative_path,
            code="table-parse-error",
            detail=str(error),
        )
        return

    if len(expected_rows) != len(actual_rows):
        collector.add(
            run=run,
            path=relative_path,
            code="row-count-mismatch",
            expected=len(expected_rows),
            actual=len(actual_rows),
        )

    for row_index, (expected_row, actual_row) in enumerate(
        zip(expected_rows, actual_rows),
        start=1,
    ):
        if len(expected_row) != len(actual_row):
            collector.add(
                run=run,
                path=relative_path,
                code="column-count-mismatch",
                location=f"row {row_index}",
                expected=len(expected_row),
                actual=len(actual_row),
            )
        for column_index, (expected_cell, actual_cell) in enumerate(
            zip(expected_row, actual_row),
            start=1,
        ):
            if expected_cell == actual_cell:
                continue
            expected_number = numeric_text(expected_cell)
            actual_number = numeric_text(actual_cell)
            location = f"row {row_index}, column {column_index}"
            if expected_number is not None and actual_number is not None:
                compare_scalar(
                    expected_number,
                    actual_number,
                    run=run,
                    path=relative_path,
                    location=location,
                    rtol=rtol,
                    atol=atol,
                    collector=collector,
                )
            else:
                collector.add(
                    run=run,
                    path=relative_path,
                    code="value-mismatch",
                    location=location,
                    expected=short_value(expected_cell),
                    actual=short_value(actual_cell),
                )


def compare_file(
    expected_path: Path,
    actual_path: Path,
    *,
    run: str,
    relative_path: str,
    rtol: float,
    atol: float,
    collector: MismatchCollector,
) -> None:
    suffix = expected_path.suffix.lower()
    if suffix == ".json":
        compare_json_files(
            expected_path,
            actual_path,
            run=run,
            relative_path=relative_path,
            rtol=rtol,
            atol=atol,
            collector=collector,
        )
    elif suffix in {".csv", ".tsv"}:
        compare_table_files(
            expected_path,
            actual_path,
            run=run,
            relative_path=relative_path,
            delimiter="," if suffix == ".csv" else "\t",
            rtol=rtol,
            atol=atol,
            collector=collector,
        )
    else:
        expected_hash = sha256_file(expected_path)
        actual_hash = sha256_file(actual_path)
        if expected_hash != actual_hash:
            collector.add(
                run=run,
                path=relative_path,
                code="hash-mismatch",
                expected_sha256=expected_hash,
                actual_sha256=actual_hash,
            )


def compare_directory(
    reference: Path,
    recheck: Path,
    *,
    ignore_patterns: list[str],
    rtol: float,
    atol: float,
    collector: MismatchCollector,
) -> dict[str, Any]:
    before = collector.total
    reference_files, reference_symlinks = collect_files(
        reference, ignore_patterns
    )
    recheck_files, recheck_symlinks = collect_files(recheck, ignore_patterns)
    run = str(recheck)

    for relative_path in reference_symlinks:
        collector.add(
            run=str(reference),
            path=relative_path,
            code="symlink-blocked",
        )
    for relative_path in recheck_symlinks:
        collector.add(
            run=run,
            path=relative_path,
            code="symlink-blocked",
        )

    reference_names = set(reference_files)
    recheck_names = set(recheck_files)
    for relative_path in sorted(reference_names - recheck_names):
        collector.add(
            run=run,
            path=relative_path,
            code="missing-file",
        )
    for relative_path in sorted(recheck_names - reference_names):
        collector.add(
            run=run,
            path=relative_path,
            code="extra-file",
        )

    for relative_path in sorted(reference_names & recheck_names):
        compare_file(
            reference_files[relative_path],
            recheck_files[relative_path],
            run=run,
            relative_path=relative_path,
            rtol=rtol,
            atol=atol,
            collector=collector,
        )

    mismatch_count = collector.total - before
    return {
        "recheck_dir": run,
        "files_compared": len(reference_names & recheck_names),
        "mismatch_count": mismatch_count,
        "status": "PASS" if mismatch_count == 0 else "BLOCKED",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compare one frozen result directory with one or more repeated runs."
        )
    )
    parser.add_argument("reference", help="Initial frozen result directory")
    parser.add_argument(
        "rechecks",
        nargs="+",
        help="One or more repeated-run result directories",
    )
    parser.add_argument("--rtol", type=float, default=1e-9)
    parser.add_argument("--atol", type=float, default=1e-12)
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="Relative glob to ignore; may be repeated",
    )
    parser.add_argument("--max-mismatches", type=int, default=100)
    parser.add_argument("--json", action="store_true")
    return parser


def validate_arguments(args: argparse.Namespace) -> tuple[Path, list[Path]]:
    if (
        not math.isfinite(args.rtol)
        or not math.isfinite(args.atol)
        or args.rtol < 0
        or args.atol < 0
    ):
        raise ValueError("rtol and atol must be finite and non-negative")
    if args.max_mismatches <= 0:
        raise ValueError("max-mismatches must be positive")

    reference = Path(args.reference).expanduser().resolve()
    rechecks = [Path(path).expanduser().resolve() for path in args.rechecks]
    for path in [reference, *rechecks]:
        if not path.exists():
            raise ValueError(f"directory does not exist: {path}")
        if not path.is_dir():
            raise ValueError(f"not a directory: {path}")
    return reference, rechecks


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        reference, rechecks = validate_arguments(args)
        collector = MismatchCollector(max_items=args.max_mismatches)
        reference_files, reference_symlinks = collect_files(
            reference, args.ignore
        )
        if not reference_files:
            raise ValueError(
                "reference contains no comparable files after ignores"
            )
        run_reports = [
            compare_directory(
                reference,
                recheck,
                ignore_patterns=args.ignore,
                rtol=args.rtol,
                atol=args.atol,
                collector=collector,
            )
            for recheck in rechecks
        ]
        report = {
            "status": "PASS" if collector.total == 0 else "BLOCKED",
            "reference_dir": str(reference),
            "recheck_dirs": [str(path) for path in rechecks],
            "reference_file_count": len(reference_files),
            "reference_symlink_count": len(reference_symlinks),
            "rtol": args.rtol,
            "atol": args.atol,
            "ignored_patterns": args.ignore,
            "runs": run_reports,
            "mismatch_count": collector.total,
            "mismatches_returned": len(collector.items),
            "truncated": collector.total > len(collector.items),
            "mismatches": collector.items,
        }
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"status={report['status']}")
        print(f"reference={report['reference_dir']}")
        print(f"rechecks={len(report['recheck_dirs'])}")
        print(f"mismatches={report['mismatch_count']}")
        for mismatch in report["mismatches"]:
            location = mismatch.get("location", "")
            suffix = f" ({location})" if location else ""
            print(
                f"- {mismatch['code']}: {mismatch['path']}{suffix}"
            )

    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
