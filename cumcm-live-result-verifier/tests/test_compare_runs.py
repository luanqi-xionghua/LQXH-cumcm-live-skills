from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "compare_runs.py"


def make_run(
    root: Path,
    name: str,
    *,
    score: str = "1.0",
    note: str = "frozen\n",
) -> Path:
    run = root / name
    run.mkdir()
    (run / "metrics.csv").write_text(
        f"id,value\nQ1,{score}\n",
        encoding="utf-8",
    )
    (run / "summary.json").write_text(
        json.dumps({"question": "Q1", "score": float(score)}),
        encoding="utf-8",
    )
    (run / "note.txt").write_text(note, encoding="utf-8")
    return run


def run_compare(
    reference: Path,
    *rechecks: Path,
    extra_args: tuple[str, ...] = (),
) -> tuple[subprocess.CompletedProcess[str], dict]:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(reference),
            *(str(path) for path in rechecks),
            "--json",
            *extra_args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout) if completed.stdout else {}
    return completed, report


def test_two_identical_rechecks_pass(tmp_path: Path) -> None:
    initial = make_run(tmp_path, "initial")
    recheck_a = make_run(tmp_path, "recheck-a")
    recheck_b = make_run(tmp_path, "recheck-b")

    completed, report = run_compare(initial, recheck_a, recheck_b)

    assert completed.returncode == 0
    assert report["status"] == "PASS"
    assert report["mismatch_count"] == 0
    assert [run["status"] for run in report["runs"]] == ["PASS", "PASS"]


def test_numeric_values_within_declared_tolerance_pass(tmp_path: Path) -> None:
    initial = make_run(tmp_path, "initial", score="1.0")
    recheck = make_run(tmp_path, "recheck", score="1.000000001")

    completed, report = run_compare(
        initial,
        recheck,
        extra_args=("--rtol", "1e-8", "--atol", "0"),
    )

    assert completed.returncode == 0
    assert report["status"] == "PASS"


def test_numeric_drift_blocks_and_is_reported(tmp_path: Path) -> None:
    initial = make_run(tmp_path, "initial", score="1.0")
    recheck = make_run(tmp_path, "recheck", score="1.1")

    completed, report = run_compare(
        initial,
        recheck,
        extra_args=("--rtol", "1e-9", "--atol", "0"),
    )

    assert completed.returncode == 1
    assert report["status"] == "BLOCKED"
    assert any(
        mismatch["code"] == "numeric-drift"
        for mismatch in report["mismatches"]
    )


def test_missing_and_extra_files_block(tmp_path: Path) -> None:
    initial = make_run(tmp_path, "initial")
    recheck = make_run(tmp_path, "recheck")
    (recheck / "note.txt").unlink()
    (recheck / "extra.txt").write_text("unexpected\n", encoding="utf-8")

    completed, report = run_compare(initial, recheck)
    codes = {mismatch["code"] for mismatch in report["mismatches"]}

    assert completed.returncode == 1
    assert {"missing-file", "extra-file"}.issubset(codes)


def test_non_tabular_file_hash_mismatch_blocks(tmp_path: Path) -> None:
    initial = make_run(tmp_path, "initial", note="frozen\n")
    recheck = make_run(tmp_path, "recheck", note="changed\n")

    completed, report = run_compare(initial, recheck)

    assert completed.returncode == 1
    assert any(
        mismatch["code"] == "hash-mismatch"
        and mismatch["path"] == "note.txt"
        for mismatch in report["mismatches"]
    )


def test_nonexistent_path_returns_exit_two(tmp_path: Path) -> None:
    initial = make_run(tmp_path, "initial")
    missing = tmp_path / "missing"

    completed, report = run_compare(initial, missing)

    assert completed.returncode == 2
    assert report == {}
    assert "directory does not exist" in completed.stderr


def test_empty_reference_returns_exit_two(tmp_path: Path) -> None:
    initial = tmp_path / "initial"
    recheck = tmp_path / "recheck"
    initial.mkdir()
    recheck.mkdir()

    completed, report = run_compare(initial, recheck)

    assert completed.returncode == 2
    assert report == {}
    assert "no comparable files" in completed.stderr
