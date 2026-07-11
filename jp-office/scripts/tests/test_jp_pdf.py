import pytest
from fpdf import FPDF

import jp_pdf


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
    pdf.add_page()  # 텍스트 없는 페이지
    p = tmp_path / "blank.pdf"
    pdf.output(str(p))
    with pytest.raises(jp_pdf.NoTextError):
        jp_pdf.extract_text(p)
