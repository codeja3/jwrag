import re
from pathlib import Path
from typing import List, Dict, Any
import pypdf
from loguru import logger
from jwrag.interfaces import IDocumentParser


class TextMarkdownParser(IDocumentParser):
    """Parser for standard text (.txt) and Markdown (.md) files."""

    SUPPORTED_EXTENSIONS = {".txt", ".md"}

    def can_parse(self, filepath: Path) -> bool:
        """Checks if the file extension is supported.
        
        Args:
            filepath: The path to the file to check.
            
        Returns:
            True if the file extension matches supported types, False otherwise.
        """
        return filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def extract_text_with_metadata(self, filepath: Path) -> List[Dict[str, Any]]:
        """Extracts raw text from a text or markdown file.
        
        Args:
            filepath: The path to the file to parse.
            
        Returns:
            A list containing a single dict with the extracted text and page_number 1.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
            extracted = []
            for i, p in enumerate(paragraphs):
                extracted.append({
                    "text": p,
                    "markers": {
                        "page": "1",
                        "paragraph": str(i + 1)
                    }
                })
                
            logger.info(f"Successfully parsed text/markdown file: {filepath} ({len(extracted)} paragraphs)")
            return extracted
        except Exception as e:
            logger.error(f"Failed to parse text/markdown file {filepath}: {e}")
            raise


class PdfParser(IDocumentParser):
    """Parser for searchable PDF files using pypdf."""

    SUPPORTED_EXTENSIONS = {".pdf"}

    def can_parse(self, filepath: Path) -> bool:
        """Checks if the file extension is supported."""
        return filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _extract_printed_page_number(self, text: str) -> str:
        """Heuristically scans header/footer for page numbers."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if not lines:
            return ""
            
        # Match digits or roman numerals, optionally prefixed with 'Page '
        pattern = re.compile(r'^(?:Page\s*)?(\d+|[ivxlc]+)$', re.IGNORECASE)
        
        match_top = pattern.match(lines[0])
        if match_top:
            return match_top.group(1)
            
        if len(lines) > 1:
            match_bottom = pattern.match(lines[-1])
            if match_bottom:
                return match_bottom.group(1)
                
        return ""

    def extract_text_with_metadata(self, filepath: Path) -> List[Dict[str, Any]]:
        extracted_pages = []
        try:
            with open(filepath, "rb") as f:
                reader = pypdf.PdfReader(f)
                page_labels = getattr(reader, "page_labels", [])
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    
                    # 1. Try native PDF labels
                    if page_labels and page_num < len(page_labels):
                        page_label = str(page_labels[page_num])
                    # 2. Try heuristic text extraction from header/footer
                    elif text and self._extract_printed_page_number(text):
                        page_label = self._extract_printed_page_number(text)
                    # 3. Fallback to absolute index
                    else:
                        page_label = str(page_num + 1)
                        
                    if text:
                        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                        for i, p in enumerate(paragraphs):
                            extracted_pages.append({
                                "text": p,
                                "markers": {
                                    "page": page_label,
                                    "paragraph": str(i + 1)
                                }
                            })
            logger.info(f"Successfully parsed PDF file: {filepath} ({len(extracted_pages)} paragraphs extracted from {len(reader.pages)} pages)")
        except Exception as e:
            logger.error(f"Failed to parse PDF file {filepath}: {e}")
            raise
            
        return extracted_pages
