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

    def _calibrate_page_offset(self, reader: pypdf.PdfReader) -> int:
        """Attempts to find the subject index, extract terms, and calculate the page offset."""
        num_pages = len(reader.pages)
        if num_pages < 5: return 0
        
        # 1. Scan last 20% of pages for an index
        start_index_scan = max(0, int(num_pages * 0.8))
        index_text = ""
        for i in range(start_index_scan, num_pages):
            t = reader.pages[i].extract_text() or ""
            if "Index" in t or "index" in t:
                index_text += t + "\n"
                
        if not index_text: return 0
        
        # 2. Extract terms: Word(s) followed by dots/spaces and a number
        pattern = re.compile(r'^([A-Za-z]+(?:[ \t]+[A-Za-z]+){0,2})[ \t]*(?:\.+|,|[ \t])[ \t]*(\d+)$', re.MULTILINE)
        matches = pattern.findall(index_text)
        
        # 3. Find terms in the document to establish offset consensus
        offsets = []
        # Cache the text of early pages to speed up search (avoid re-extracting)
        page_texts = {}
        
        for term, printed_page_str in matches[:10]:
            term_clean = term.strip()
            printed_page = int(printed_page_str)
            if printed_page <= 0: continue
            
            # We expect the absolute page to be somewhere around printed_page + offset (offset usually 0 to 50)
            # Let's just search pages 0 to min(printed_page + 100, num_pages)
            search_limit = min(printed_page + 100, num_pages)
            for abs_page in range(search_limit):
                if abs_page not in page_texts:
                    page_texts[abs_page] = reader.pages[abs_page].extract_text() or ""
                    
                # Simple substring match (case insensitive)
                if term_clean.lower() in page_texts[abs_page].lower():
                    offset = abs_page - (printed_page - 1)  # offset = abs_page - printed_index (0-based)
                    if offset >= 0:
                        offsets.append(offset)
                        break # Move to next term
                        
        if offsets:
            # Return the most common offset (consensus)
            from collections import Counter
            most_common = Counter(offsets).most_common(1)
            if most_common[0][1] >= 2: # At least 2 terms agree
                return most_common[0][0]
        return 0

    def extract_text_with_metadata(self, filepath: Path) -> List[Dict[str, Any]]:
        extracted_pages = []
        try:
            with open(filepath, "rb") as f:
                reader = pypdf.PdfReader(f)
                page_labels = getattr(reader, "page_labels", [])
                calibration_offset = self._calibrate_page_offset(reader)
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    
                    # 1. Try native PDF labels
                    if page_labels and page_num < len(page_labels):
                        page_label = str(page_labels[page_num])
                    # 2. Try index-based calibration
                    elif calibration_offset > 0 and (page_num - calibration_offset + 1) > 0:
                        page_label = str(page_num - calibration_offset + 1)
                    # 3. Try heuristic text extraction from header/footer
                    elif text and self._extract_printed_page_number(text):
                        page_label = self._extract_printed_page_number(text)
                    # 4. Fallback to absolute index
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
