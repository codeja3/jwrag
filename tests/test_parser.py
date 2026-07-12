import pytest
from pathlib import Path
from jwrag.parsers import TextMarkdownParser, PdfParser


@pytest.fixture
def text_file(temp_dir: Path) -> Path:
    """Creates a temporary .txt file for testing."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("This is a test document.\nIt has multiple lines.")
    return file_path


@pytest.fixture
def md_file(temp_dir: Path) -> Path:
    """Creates a temporary .md file for testing."""
    file_path = temp_dir / "test.md"
    file_path.write_text("# Header\nSome markdown content here.")
    return file_path


@pytest.fixture
def pdf_file(temp_dir: Path) -> Path:
    """Creates a minimal valid PDF for testing pypdf."""
    import io
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    file_path = temp_dir / "test.pdf"
    with open(file_path, "wb") as f:
        writer.write(f)
    return file_path


def test_text_parser_can_parse(text_file: Path) -> None:
    parser = TextMarkdownParser()
    assert parser.can_parse(text_file) is True


def test_md_parser_can_parse(md_file: Path) -> None:
    parser = TextMarkdownParser()
    assert parser.can_parse(md_file) is True


def test_text_parser_extract_content(text_file: Path) -> None:
    parser = TextMarkdownParser()
    result = parser.extract_text_with_metadata(text_file)
    assert len(result) == 1
    assert result[0]["text"] == "This is a test document.\nIt has multiple lines."
    assert result[0]["page_number"] == 1


def test_md_parser_extract_content(md_file: Path) -> None:
    parser = TextMarkdownParser()
    result = parser.extract_text_with_metadata(md_file)
    assert len(result) == 1
    assert "# Header" in result[0]["text"]
    assert "Some markdown content here." in result[0]["text"]


def test_pdf_parser_can_parse(pdf_file: Path) -> None:
    parser = PdfParser()
    assert parser.can_parse(pdf_file) is True


def test_pdf_parser_extract_content(pdf_file: Path) -> None:
    parser = PdfParser()
    result = parser.extract_text_with_metadata(pdf_file)
    # A blank PDF page usually returns empty string, which we filter out.
    assert len(result) == 0
