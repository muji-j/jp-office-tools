from pathlib import Path

import pytest
from fpdf import FPDF

import jp_pdf
from jp_office_common import run_cli


@pytest.fixture
def sample_pdf(tmp_path):
    pdf = FPDF()
    for page_text in ("HELLO JP OFFICE", "SECOND PAGE"):
        pdf.add_page()
        pdf.set_font("helvetica", size=24)
        pdf.cell(text=page_text)
    p = tmp_path / "sample.pdf"
    pdf.output(str(p))
    return p

def test_extract_all(sample_pdf):
    text = jp_pdf.extract_text(sample_pdf)
    assert "HELLO JP OFFICE" in text and "SECOND PAGE" in text
    assert "--- p.1 ---" in text and "--- p.2 ---" in text

def test_extract_page_range(sample_pdf):
    text = jp_pdf.extract_text(sample_pdf, pages="2")
    assert "SECOND PAGE" in text and "HELLO JP OFFICE" not in text

def test_no_text_error(tmp_path):
    pdf = FPDF()
    pdf.add_page()  # テキストのないページ
    p = tmp_path / "blank.pdf"
    pdf.output(str(p))
    with pytest.raises(jp_pdf.NoTextError):
        jp_pdf.extract_text(p)

def test_extract_page_zero_rejected(sample_pdf):
    with pytest.raises(jp_pdf.PageRangeError):
        jp_pdf.extract_text(sample_pdf, pages="0")

def test_extract_page_out_of_range_rejected(sample_pdf):
    with pytest.raises(jp_pdf.PageRangeError):
        jp_pdf.extract_text(sample_pdf, pages="99")

def test_blank_page_in_textful_doc_not_scan_error(tmp_path):
    from fpdf import FPDF
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("helvetica", size=24); pdf.cell(text="PAGE ONE")
    pdf.add_page()  # blank page 2
    p = tmp_path / "mixed.pdf"
    pdf.output(str(p))
    # selecting the blank page 2 must NOT raise NoTextError (doc has text on p.1)
    result = jp_pdf.extract_text(p, pages="2")
    assert result == ""  # no text on p.2, but not a scan-PDF misdiagnosis


def test_render_pages_creates_pngs(sample_pdf):
    paths = jp_pdf.render_pages(sample_pdf)
    assert len(paths) == 2
    for p in paths:
        assert Path(p).exists()
        assert Path(p).stat().st_size > 0
        assert Path(p).suffix == ".png"

def test_render_page_range(sample_pdf):
    paths = jp_pdf.render_pages(sample_pdf, pages="2")
    assert len(paths) == 1
    assert Path(paths[0]).name == "sample_p2.png"
    assert Path(paths[0]).exists()

def test_render_default_out_dir_is_source_folder(sample_pdf):
    paths = jp_pdf.render_pages(sample_pdf, pages="1")
    assert Path(paths[0]).parent == sample_pdf.parent

def test_render_custom_out_dir(sample_pdf, tmp_path):
    out_dir = tmp_path / "rendered"
    out_dir.mkdir()
    paths = jp_pdf.render_pages(sample_pdf, out_dir=out_dir, pages="1")
    assert Path(paths[0]).parent == out_dir

def test_render_does_not_modify_source(sample_pdf):
    before = sample_pdf.read_bytes()
    jp_pdf.render_pages(sample_pdf)
    after = sample_pdf.read_bytes()
    assert before == after

def test_render_rejects_bad_page_range(sample_pdf):
    with pytest.raises(jp_pdf.PageRangeError):
        jp_pdf.render_pages(sample_pdf, pages="99")

def test_render_cli(sample_pdf, tmp_path, capsys):
    rc = jp_pdf.main(["jp_pdf.py", "render", str(sample_pdf), "--out-dir", str(tmp_path)])
    assert rc == 0
    lines = [l for l in capsys.readouterr().out.splitlines() if l]
    assert len(lines) == 2
    for l in lines:
        assert Path(l).exists()

def test_no_text_error_message_guides_to_render_and_ocr(tmp_path):
    pdf = FPDF()
    pdf.add_page()
    p = tmp_path / "blank.pdf"
    pdf.output(str(p))
    with pytest.raises(jp_pdf.NoTextError) as exc_info:
        jp_pdf.extract_text(p)
    msg = str(exc_info.value)
    assert "render" in msg and "--ocr" in msg

def test_ocr_unavailable_raises(sample_pdf):
    # this environment has no tesseract system binary installed — real (non-mocked) path
    with pytest.raises(jp_pdf.OcrUnavailableError):
        jp_pdf.ocr_text(sample_pdf)

@pytest.mark.skipif(not jp_pdf.ocr_available(), reason="tesseract not installed in this environment")
def test_ocr_roundtrip(sample_pdf):
    text = jp_pdf.ocr_text(sample_pdf)
    assert "--- p.1 (OCR) ---" in text
    assert "--- p.2 (OCR) ---" in text

def test_extract_cli_ocr_unavailable_prints_clean_message_no_traceback(sample_pdf, capsys):
    # T5: OcrUnavailableError は main() 内で捕捉せず run_cli に委譲するようになったため、
    # main() を直接呼ぶとその場で例外送出される。CLI 経路(run_cli 越し)で検証する。
    rc = run_cli(jp_pdf.main, ["jp_pdf.py", "extract", str(sample_pdf), "--ocr"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "tesseract" in err
    assert "Traceback" not in err


def test_render_creates_missing_out_dir(sample_pdf):
    out = sample_pdf.parent / "renders" / "sub"
    assert not out.exists()
    saved = jp_pdf.render_pages(sample_pdf, out_dir=out, pages="1")
    assert len(saved) == 1
    assert Path(saved[0]).exists() and Path(saved[0]).stat().st_size > 0
