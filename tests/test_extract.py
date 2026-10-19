import logging

from odf.extract import extract_text
from odf.extract.clean import clean_text
from tests.helpers import make_docx, make_pdf


def test_extracts_docx_paragraphs_and_tables(tmp_path):
    path = make_docx(
        tmp_path / "invoice.docx",
        paragraphs=["Invoice INV-2024-001", "Payment due in 30 days"],
        table=[["Item", "Price"], ["Consulting", "1200"]],
    )
    text = extract_text(path, ".docx")
    for expected in ("INV-2024-001", "Payment due in 30 days", "Consulting", "1200"):
        assert expected in text


def test_extracts_pdf_text(tmp_path):
    path = make_pdf(tmp_path / "memo.pdf", "Quarterly budget report for marketing")
    assert "Quarterly budget report for marketing" in extract_text(path, ".pdf")


def test_corrupt_file_extracts_to_empty_string_and_is_logged(tmp_path, caplog):
    bad = tmp_path / "broken.pdf"
    bad.write_bytes(b"not really a pdf")
    with caplog.at_level(logging.WARNING, logger="odf"):
        assert extract_text(str(bad), ".pdf") == ""
    assert any(r.levelname == "WARNING" and str(bad) in r.getMessage() for r in caplog.records)


def test_clean_text_collapses_whitespace_strips_control_chars_and_caps_length():
    assert clean_text("a \n\n b\t\x00c\x07") == "a b c"
    assert len(clean_text("x" * 150_000)) == 100_000




def test_unsupported_extension_extracts_nothing(tmp_path):
    other = tmp_path / "sheet.xlsx"
    other.write_bytes(b"x")
    assert extract_text(str(other)) == ""


def test_extension_is_inferred_from_path(tmp_path):
    path = make_docx(tmp_path / "Report.DOCX", paragraphs=["Upper-case extension"])
    assert "Upper-case extension" in extract_text(path)
