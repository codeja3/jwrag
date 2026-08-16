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


def test_pdf_parser_heuristic_fallback(mocker) -> None:
    # Simulate a PDF page with 'Page 45' at the top
    mock_page_top = mocker.MagicMock()
    mock_page_top.extract_text.return_value = "Page 45\n\nSome actual paragraph content.\n\nMore text."
    
    # Simulate a PDF page with roman numeral 'ix' at the bottom
    mock_page_bottom = mocker.MagicMock()
    mock_page_bottom.extract_text.return_value = "Content here.\n\nix"
    
    mock_reader = mocker.MagicMock()
    mock_reader.pages = [mock_page_top, mock_page_bottom]
    # NO page_labels provided to force fallback
    mock_reader.page_labels = []
    
    parser = PdfParser()
    mocker.patch("jwrag.parsers.pypdf.PdfReader", return_value=mock_reader)
    mocker.patch("builtins.open", mocker.mock_open())
    result = parser.extract_text_with_metadata(Path("dummy.pdf"))
    
    assert result[0]["markers"]["page"] == "45"
    # The bottom marker should be pulled for the second page
    assert result[-1]["markers"]["page"] == "ix"


def test_pdf_parser_index_calibration(mocker) -> None:
    # Simulate a 10-page document
    # Page 0-2: Front matter
    # Page 3: Content page (Absolute 3, Printed 1), containing 'Apples'
    # Page 4: Content page (Absolute 4, Printed 2), containing 'Bananas'
    # Page 9: Index page containing 'Apples 1', 'Bananas 2'
    
    mock_reader = mocker.MagicMock()
    pages = [mocker.MagicMock() for _ in range(10)]
    for i, p in enumerate(pages):
        p.extract_text.return_value = f"Dummy text for page {i}"
        
    pages[3].extract_text.return_value = "We love Apples. They are great."
    pages[4].extract_text.return_value = "Bananas are yellow."
    pages[9].extract_text.return_value = "Index\nApples ........ 1\nBananas ........ 2"
    
    mock_reader.pages = pages
    mock_reader.page_labels = []
    
    parser = PdfParser()
    mocker.patch("jwrag.parsers.pypdf.PdfReader", return_value=mock_reader)
    mocker.patch("builtins.open", mocker.mock_open())
    
    result = parser.extract_text_with_metadata(Path("dummy.pdf"))
    
    # Offset should be: Absolute(3) - Printed(1) = 2
    # Front-matter pages (0, 1, 2) should receive Roman numerals:
    assert result[0]["markers"]["page"] == "i"
    assert result[1]["markers"]["page"] == "ii"
    assert result[2]["markers"]["page"] == "iii"
    # Page 3 -> printed '1'
    assert result[3]["markers"]["page"] == "1"
    # Page 4 -> printed '2'
    assert result[4]["markers"]["page"] == "2"
    # Page 9 -> printed '7'
    assert result[9]["markers"]["page"] == "7"


def test_pdf_parser_bypasses_synthetic_page_labels_when_pagelabels_missing_from_root(mocker) -> None:
    # When pypdf defaults page_labels to ["1", "2", ...], but root_object has no /PageLabels
    mock_reader = mocker.MagicMock()
    pages = [mocker.MagicMock() for _ in range(10)]
    for i, p in enumerate(pages):
        p.extract_text.return_value = f"Dummy text for page {i}"
        
    pages[3].extract_text.return_value = "We love Apples. They are great."
    pages[9].extract_text.return_value = "Index\nApples ........ 1"
    
    mock_reader.pages = pages
    # Synthetic default page_labels generated by pypdf
    mock_reader.page_labels = [str(i + 1) for i in range(10)]
    # root_object does NOT have /PageLabels
    mock_reader.root_object = {}
    mock_reader.trailer = {"/Root": {}}
    
    parser = PdfParser()
    mocker.patch("jwrag.parsers.pypdf.PdfReader", return_value=mock_reader)
    mocker.patch("builtins.open", mocker.mock_open())
    
    result = parser.extract_text_with_metadata(Path("dummy.pdf"))
    
    # Pre-offset pages get roman numerals
    assert result[0]["markers"]["page"] == "i"
    assert result[1]["markers"]["page"] == "ii"
    assert result[2]["markers"]["page"] == "iii"
    # Offset calibrated page 3 becomes printed 1
    assert result[3]["markers"]["page"] == "1"


def test_markdown_parser_extracts_chapter_and_section(temp_dir: Path) -> None:
    md_file = temp_dir / "chapter_test.md"
    md_file.write_text("# Chapter 1: Introduction\n\nWelcome to chapter one.\n\n## Section 3: Policies\n\nStrict compliance required.\n\n# Chapter 2: Methods\n\nMethodology details.")
    
    parser = TextMarkdownParser()
    result = parser.extract_text_with_metadata(md_file)
    
    # 0. Header paragraph
    assert result[0]["markers"]["chapter"] == "1"
    assert result[0]["markers"]["paragraph"] == "1"
    
    # 1. Intro content paragraph
    assert result[1]["markers"]["chapter"] == "1"
    assert "Welcome to chapter one" in result[1]["text"]
    assert result[1]["markers"]["paragraph"] == "2"
    
    # 2. Section header paragraph
    assert result[2]["markers"]["chapter"] == "1"
    assert result[2]["markers"]["section"] == "3"
    assert result[2]["markers"]["paragraph"] == "3"
    
    # 3. Section content paragraph
    assert result[3]["markers"]["chapter"] == "1"
    assert result[3]["markers"]["section"] == "3"
    assert result[3]["markers"]["paragraph"] == "4"
    
    # 4. Chapter 2 header paragraph
    assert result[4]["markers"]["chapter"] == "2"
    assert "section" not in result[4]["markers"]
    assert result[4]["markers"]["paragraph"] == "5"


def test_pdf_parser_extracts_chapter_headings(mocker) -> None:
    mock_page1 = mocker.MagicMock()
    mock_page1.extract_text.return_value = "Chapter 4: Risk Assessment\n\nFirst paragraph of assessment."
    mock_page2 = mocker.MagicMock()
    mock_page2.extract_text.return_value = "§ 4.2 Mitigation\n\nMitigation steps details."
    
    mock_reader = mocker.MagicMock()
    mock_reader.pages = [mock_page1, mock_page2]
    mock_reader.page_labels = []
    mock_reader.root_object = {}
    
    parser = PdfParser()
    mocker.patch("jwrag.parsers.pypdf.PdfReader", return_value=mock_reader)
    mocker.patch("builtins.open", mocker.mock_open())
    
    result = parser.extract_text_with_metadata(Path("dummy.pdf"))
    
    # Page 1
    assert result[0]["markers"]["chapter"] == "4"
    assert result[0]["markers"]["paragraph"] == "1"
    assert result[1]["markers"]["chapter"] == "4"
    assert result[1]["markers"]["paragraph"] == "2"
    
    # Page 2
    assert result[2]["markers"]["chapter"] == "4"
    assert result[2]["markers"]["section"] == "4.2"
    assert result[2]["markers"]["paragraph"] == "1"
    assert result[3]["markers"]["chapter"] == "4"
    assert result[3]["markers"]["section"] == "4.2"
    assert result[3]["markers"]["paragraph"] == "2"

