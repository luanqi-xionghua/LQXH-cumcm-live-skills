import json
import importlib.util
import subprocess
import sys
import zipfile
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_ROOT / "scripts" / "layout_preflight.py"


def load_preflight_module():
    spec = importlib.util.spec_from_file_location("layout_preflight", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_preflight(pdf: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(pdf),
            "--json",
            "--skip-external-tools",
            *extra,
        ],
        check=False,
        text=True,
        capture_output=True,
    )


def write_minimal_pdf(path: Path) -> None:
    path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n")


def test_safe_pdf_and_source_only_precheck_pass(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    source = tmp_path / "paper.tex"
    write_minimal_pdf(pdf)
    source.write_text(r"\section{Model} Final content.", encoding="utf-8")

    result = run_preflight(pdf, "--source", str(source))
    report = json.loads(result.stdout)

    assert result.returncode == 0
    assert report["status"] == "PRECHECK_PASS"
    assert report["visual_qa_required"] is True


def test_invalid_pdf_header_is_blocked(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    pdf.write_bytes(b"not a pdf\n%%EOF\n")

    result = run_preflight(pdf)
    report = json.loads(result.stdout)

    assert result.returncode == 1
    assert any(item["code"] == "invalid-pdf-header" for item in report["issues"])


def test_placeholder_in_source_is_blocked(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    source = tmp_path / "paper.tex"
    write_minimal_pdf(pdf)
    source.write_text("结论为【待复核】。", encoding="utf-8")

    result = run_preflight(pdf, "--source", str(source))
    report = json.loads(result.stdout)

    assert result.returncode == 1
    assert any(item["code"] == "placeholder" for item in report["issues"])


def test_latex_log_hard_warning_is_blocked(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    source = tmp_path / "source"
    source.mkdir()
    write_minimal_pdf(pdf)
    (source / "paper.log").write_text(
        "LaTeX Warning: There were undefined references.\n"
        "Overfull \\hbox (10.0pt too wide)\n",
        encoding="utf-8",
    )

    result = run_preflight(pdf, "--source", str(source))
    report = json.loads(result.stdout)
    codes = {item["code"] for item in report["issues"]}

    assert result.returncode == 1
    assert {"undefined-reference", "overfull-box"}.issubset(codes)


def test_docx_comments_and_tracked_changes_are_blocked(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    docx = tmp_path / "paper.docx"
    write_minimal_pdf(pdf)
    with zipfile.ZipFile(docx, "w") as archive:
        archive.writestr(
            "word/document.xml",
            '<w:document xmlns:w="x"><w:body><w:ins><w:t>text</w:t></w:ins>'
            '<w:commentRangeStart w:id="0"/></w:body></w:document>',
        )
        archive.writestr("word/comments.xml", "<w:comments/>")

    result = run_preflight(pdf, "--source", str(docx))
    report = json.loads(result.stdout)
    codes = {item["code"] for item in report["issues"]}

    assert result.returncode == 1
    assert "word-tracked-changes" in codes
    assert "word-comments" in codes


def test_missing_pdf_path_returns_exit_2(tmp_path: Path) -> None:
    result = run_preflight(tmp_path / "missing.pdf")

    assert result.returncode == 2
    assert "不存在" in result.stderr


def test_pdffonts_fixed_width_parser_detects_unembedded_font() -> None:
    module = load_preflight_module()
    output = (
        "name                                 type              encoding         emb sub uni object ID\n"
        "------------------------------------ ----------------- ---------------- --- --- --- ---------\n"
        "ABCDEE+CMR10                        Type 1            Builtin          yes yes yes      5  0\n"
        "SimSun                               TrueType          WinAnsi          no  no  yes      8  0\n"
    )

    unembedded = module.find_unembedded_fonts(output)

    assert len(unembedded) == 1
    assert "SimSun" in unembedded[0]


def test_30_body_pages_with_unlimited_appendix_passes(tmp_path: Path) -> None:
    module = load_preflight_module()
    issues = []
    warnings = []

    result = module.evaluate_page_limit(
        total_pages=47,
        main_start_page=1,
        appendix_start_page=31,
        max_main_pages=30,
        pdf=tmp_path / "paper.pdf",
        issues=issues,
        warnings=warnings,
    )

    assert result["status"] == "PASS"
    assert result["main_body_pages"] == 30
    assert result["appendix_pages"] == 17
    assert issues == []


def test_31_body_pages_is_blocked_even_with_appendix(tmp_path: Path) -> None:
    module = load_preflight_module()
    issues = []
    warnings = []

    result = module.evaluate_page_limit(
        total_pages=47,
        main_start_page=1,
        appendix_start_page=32,
        max_main_pages=30,
        pdf=tmp_path / "paper.pdf",
        issues=issues,
        warnings=warnings,
    )

    assert result["status"] == "BLOCKED"
    assert result["main_body_pages"] == 31
    assert any(item["code"] == "main-body-over-page-limit" for item in issues)


def test_no_appendix_counts_body_through_last_page(tmp_path: Path) -> None:
    module = load_preflight_module()
    issues = []
    warnings = []

    result = module.evaluate_page_limit(
        total_pages=31,
        main_start_page=1,
        appendix_start_page=None,
        max_main_pages=30,
        pdf=tmp_path / "paper.pdf",
        issues=issues,
        warnings=warnings,
    )

    assert result["appendix_pages"] == 0
    assert result["main_body_pages"] == 31
    assert result["status"] == "BLOCKED"


def test_cli_cannot_relax_30_page_hard_limit(tmp_path: Path) -> None:
    pdf = tmp_path / "paper.pdf"
    write_minimal_pdf(pdf)

    result = run_preflight(pdf, "--max-main-pages", "31")

    assert result.returncode == 2
    assert "不能放宽 30 页硬门" in result.stderr
