import pytest
from pathlib import Path
from jwrag.parsers import TextMarkdownParser, PdfParser


@pytest.fixture
def text_file(temp_dir: Path) -> Path:
    """Creates a temporary .txt file for testing."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("This is paragraph one.\n\nThis is paragraph two.")
    return file_path


@pytest.fixture
def md_file(temp_dir: Path) -> Path:
    """Creates a temporary .md file for testing."""
    file_path = temp_dir / "test.md"
    file_path.write_text("# Header\n\nSome markdown content here.")
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
    assert len(result) == 2
    assert result[0]["text"] == "This is paragraph one."
    assert result[0]["markers"]["page"] == "1"
    assert result[0]["markers"]["paragraph"] == "1"
    assert result[1]["text"] == "This is paragraph two."
    assert result[1]["markers"]["page"] == "1"
    assert result[1]["markers"]["paragraph"] == "2"


def test_md_parser_extract_content(md_file: Path) -> None:
    parser = TextMarkdownParser()
    result = parser.extract_text_with_metadata(md_file)
    assert len(result) == 2
    assert "# Header" in result[0]["text"]
    assert result[0]["markers"]["paragraph"] == "1"
    assert "Some markdown content here." in result[1]["text"]
    assert result[1]["markers"]["paragraph"] == "2"


def test_pdf_parser_can_parse(pdf_file: Path) -> None:
    parser = PdfParser()
    assert parser.can_parse(pdf_file) is True


def test_pdf_parser_extract_content(pdf_file: Path) -> None:
    parser = PdfParser()
    result = parser.extract_text_with_metadata(pdf_file)
    # A blank PDF page usually returns empty string, which we filter out.
    assert len(result) == 0


def test_pdf_parser_extracts_paragraphs(mocker) -> None:
    mock_page = mocker.MagicMock()
    mock_page.extract_text.return_value = "Page 1 Para 1.\n\nPage 1 Para 2."
    mock_reader = mocker.MagicMock()
    mock_reader.pages = [mock_page, mock_page]
    
    parser = PdfParser()
    mocker.patch("jwrag.parsers.pypdf.PdfReader", return_value=mock_reader)
    mocker.patch("builtins.open", mocker.mock_open())
    result = parser.extract_text_with_metadata(Path("dummy.pdf"))
    
    assert len(result) == 4
    assert result[0]["markers"]["paragraph"] == "1"
    assert result[0]["markers"]["page"] == "1"
    assert result[1]["markers"]["paragraph"] == "2"
    assert result[1]["markers"]["page"] == "1"
    assert result[2]["markers"]["paragraph"] == "1"
    assert result[2]["markers"]["page"] == "2"
    assert result[3]["markers"]["paragraph"] == "2"
    assert result[3]["markers"]["page"] == "2"


def test_pdf_parser_extracts_page_labels(mocker) -> None:
    mock_page = mocker.MagicMock()
    mock_page.extract_text.return_value = "Some text."
    mock_reader = mocker.MagicMock()
    mock_reader.pages = [mock_page, mock_page, mock_page]
    # Simulate PDF with roman numeral intro and then page 1
    mock_reader.page_labels = ["i", "ii", "1"]
    
    parser = PdfParser()
    mocker.patch("jwrag.parsers.pypdf.PdfReader", return_value=mock_reader)
    mocker.patch("builtins.open", mocker.mock_open())
    result = parser.extract_text_with_metadata(Path("dummy.pdf"))
    
    assert len(result) == 3
    assert result[0]["markers"]["page"] == "i"
    assert result[1]["markers"]["page"] == "ii"
    assert result[2]["markers"]["page"] == "1"
