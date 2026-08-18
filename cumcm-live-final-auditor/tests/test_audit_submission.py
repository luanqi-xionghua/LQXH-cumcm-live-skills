from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "audit_submission.py"
FIXTURE = Path(__file__).parent / "fixtures" / "fake_submission"


def prepare_submission(
    tmp_path: Path,
    *,
    include_exe: bool = False,
    include_keygen_name: bool = False,
) -> Path:
    submission = tmp_path / "submission"
    shutil.copytree(FIXTURE, submission)
    if not include_exe:
        (submission / "evil.exe").unlink()
    if not include_keygen_name:
        (submission / "注册机.txt").unlink()
    return submission


def run_audit(
    submission: Path,
    *extra_args: str,
) -> tuple[subprocess.CompletedProcess[str], dict]:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(submission),
            "--json",
            *extra_args,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    report = json.loads(completed.stdout) if completed.stdout else {}
    return completed, report


def test_normal_submission_passes_with_exit_zero(tmp_path: Path) -> None:
    submission = prepare_submission(tmp_path)

    completed, report = run_audit(submission)

    assert completed.returncode == 0
    assert report["status"] == "PASS"
    assert report["checks"]["has_valid_pdf"]["passed"] is True
    assert report["checks"]["no_dangerous_items"]["passed"] is True


def test_missing_pdf_blocks_has_valid_pdf(tmp_path: Path) -> None:
    submission = prepare_submission(tmp_path)
    (submission / "paper.pdf").unlink()

    completed, report = run_audit(submission)

    assert completed.returncode == 1
    assert report["status"] == "BLOCKED"
    assert report["checks"]["has_valid_pdf"]["passed"] is False


def test_exe_blocks_no_dangerous_items(tmp_path: Path) -> None:
    submission = prepare_submission(tmp_path, include_exe=True)

    completed, report = run_audit(submission)

    assert completed.returncode == 1
    assert report["checks"]["no_dangerous_items"]["passed"] is False
    evil = next(item for item in report["files"] if item["path"] == "evil.exe")
    assert evil["dangerous"] is True
    assert "windows-executable" in evil["risk_flags"]


def test_keygen_name_is_dangerous(tmp_path: Path) -> None:
    submission = prepare_submission(tmp_path, include_keygen_name=True)

    completed, report = run_audit(submission)

    assert completed.returncode == 1
    flagged = next(
        item for item in report["files"] if item["path"] == "注册机.txt"
    )
    assert flagged["dangerous"] is True
    assert "keygen-name" in flagged["risk_flags"]


def test_pdf_over_max_size_limit_is_flagged(tmp_path: Path) -> None:
    submission = prepare_submission(tmp_path)

    completed, report = run_audit(
        submission,
        "--max-pdf-mb",
        "0.000001",
    )

    assert completed.returncode == 1
    assert report["checks"]["pdf_size_limit"]["passed"] is False
    pdf = next(item for item in report["files"] if item["path"] == "paper.pdf")
    assert "pdf-over-size-limit" in pdf["risk_flags"]


def test_nonexistent_directory_returns_exit_two(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"

    completed, report = run_audit(missing)

    assert completed.returncode == 2
    assert report == {}
    assert "directory does not exist" in completed.stderr
