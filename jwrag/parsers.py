import re
from pathlib import Path
from typing import List, Dict, Any
import pypdf
from loguru import logger
from jwrag.interfaces import IDocumentParser


def int_to_roman(n: int) -> str:
    """Converts a positive integer to lowercase Roman numeral."""
    if n <= 0:
        return str(n)
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syms = ["m", "cm", "d", "cd", "c", "xc", "l", "xl", "x", "ix", "v", "iv", "i"]
    roman_num = ""
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syms[i]
            n -= val[i]
        i += 1
    return roman_num


def split_paragraphs(text: str) -> List[str]:
    """Splits raw text into distinct paragraphs using double newlines and numbered paragraph markers."""
    text = text.replace('\xa0', ' ')
    lines = text.split('\n')
    paragraphs = []
    current_para = []
    
    num_pattern = re.compile(r'^(?:¶\s*)?(\d+)\.\s+')
    paren_pattern = re.compile(r'^\(([0-9]+|[a-z])\)\s+')
    heading_pattern = re.compile(r'^(?:#+\s*)?(?:CHAPTER|Chapter|SECTION|Section|§)\s+', re.I)
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_para:
                paragraphs.append('\n'.join(current_para))
                current_para = []
            continue
        
        if (num_pattern.match(stripped) or paren_pattern.match(stripped) or heading_pattern.match(stripped)) and current_para:
            paragraphs.append('\n'.join(current_para))
            current_para = []
            
        current_para.append(stripped)
        
    if current_para:
        paragraphs.append('\n'.join(current_para))
    return [p for p in paragraphs if p.strip()]


def extract_paragraph_number(paragraph: str, fallback_index: int) -> str:
    """Extracts explicit printed paragraph numbers if present, otherwise returns fallback index."""
    num_pattern = re.compile(r'^(?:¶\s*)?(\d+)\.\s+')
    paren_pattern = re.compile(r'^\(([0-9]+|[a-z])\)\s+')
    
    m = num_pattern.match(paragraph.strip())
    if m:
        return m.group(1)
    m_paren = paren_pattern.match(paragraph.strip())
    if m_paren:
        return f"({m_paren.group(1)})"
    return str(fallback_index)


class TextMarkdownParser(IDocumentParser):
    """Parser for standard text (.txt) and Markdown (.md) files."""

    SUPPORTED_EXTENSIONS = {".txt", ".md"}

    def can_parse(self, filepath: Path) -> bool:
        """Checks if the file extension is supported."""
        return filepath.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def extract_text_with_metadata(self, filepath: Path) -> List[Dict[str, Any]]:
        """Extracts raw text from a text or markdown file, tagging paragraphs and chapters."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                text = f.read()
            
            paragraphs = split_paragraphs(text)
            extracted = []
            current_chapter = None
            current_section = None
            
            ch_pattern = re.compile(r'(?:^|\n)(?:#+\s*)?(?:Chapter|CHAPTER)\s+([0-9IVXLCDMivxlcdm]+)', re.IGNORECASE)
            sec_pattern = re.compile(r'(?:^|\n)(?:#+\s*)?(?:Section|SECTION|§)\s*([0-9.]+)', re.IGNORECASE)
            
            for i, p in enumerate(paragraphs):
                ch_match = ch_pattern.search(p)
                if ch_match:
                    current_chapter = ch_match.group(1)
                    current_section = None  # Reset section on new chapter
                    
                sec_match = sec_pattern.search(p)
                if sec_match:
                    current_section = sec_match.group(1)
                    
                para_num = extract_paragraph_number(p, i + 1)
                markers: Dict[str, str] = {
                    "page": "1",
                    "paragraph": para_num
                }
                if current_chapter:
                    markers["chapter"] = current_chapter
                if current_section:
                    markers["section"] = current_section
                    
                extracted.append({
                    "text": p,
                    "markers": markers
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

    def _has_native_page_labels(self, reader: pypdf.PdfReader) -> bool:
        """Checks if the PDF metadata contains explicit /PageLabels or non-trivial custom labels."""
        try:
            root = getattr(reader, "root_object", {})
            if root and "/PageLabels" in root:
                return True
            trailer = getattr(reader, "trailer", {})
            if trailer:
                root_dict = trailer.get("/Root", {})
                if isinstance(root_dict, dict) and "/PageLabels" in root_dict:
                    return True
            page_labels = getattr(reader, "page_labels", [])
            if page_labels and len(reader.pages) > 0:
                default_labels = [str(i + 1) for i in range(len(reader.pages))]
                if list(page_labels) != default_labels:
                    return True
        except Exception:
            pass
        return False

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
        
        start_index_scan = max(0, int(num_pages * 0.8))
        index_text = ""
        for i in range(start_index_scan, num_pages):
            t = reader.pages[i].extract_text() or ""
            if "Index" in t or "index" in t:
                index_text += t + "\n"
                
        if not index_text: return 0
        
        pattern = re.compile(r'^([A-Za-z]+(?:[ \t]+[A-Za-z]+){0,2})[ \t]*(?:\.+|,|[ \t])[ \t]*(\d+)$', re.MULTILINE)
        matches = pattern.findall(index_text)
        
        offsets = []
        page_texts = {}
        
        for term, printed_page_str in matches[:10]:
            term_clean = term.strip()
            printed_page = int(printed_page_str)
            if printed_page <= 0: continue
            
            search_limit = min(printed_page + 100, num_pages)
            for abs_page in range(search_limit):
                if abs_page not in page_texts:
                    page_texts[abs_page] = reader.pages[abs_page].extract_text() or ""
                    
                if term_clean.lower() in page_texts[abs_page].lower():
                    offset = abs_page - (printed_page - 1)
                    if offset >= 0:
                        offsets.append(offset)
                        break
                        
        if offsets:
            from collections import Counter
            most_common = Counter(offsets).most_common(1)
            if most_common[0][1] >= 1:
                return most_common[0][0]
        return 0

    def _detect_frontmatter_offset(self, reader: pypdf.PdfReader) -> int:
        """Detects the index where body content (Chapter 1) begins after front matter."""
        num_pages = len(reader.pages)
        found_frontmatter = False
        
        fm_patterns = [
            re.compile(r'©\s*\d{4}|Watch\s*Tower|This publication is not for sale|All rights reserved', re.I),
            re.compile(r'^\s*Contents\s*$|^\s*CONTENTS\s*$', re.M),
            re.compile(r'^\s*Introduction\s*$|^\s*INTRODUCTION\s*$', re.M)
        ]
        ch1_pattern = re.compile(r'CHAPTER\s*(?:1|I)\b|Chapter\s*(?:1|I)\b', re.I)
        
        for i in range(min(10, num_pages)):
            text = (reader.pages[i].extract_text() or '').replace('\xa0', ' ')
            if any(p.search(text) for p in fm_patterns):
                found_frontmatter = True
            if ch1_pattern.search(text):
                if found_frontmatter:
                    return i
                break
        return 0

    def extract_text_with_metadata(self, filepath: Path) -> List[Dict[str, Any]]:
        extracted_pages = []
        try:
            with open(filepath, "rb") as f:
                reader = pypdf.PdfReader(f)
                has_native_labels = self._has_native_page_labels(reader)
                page_labels = getattr(reader, "page_labels", []) if has_native_labels else []
                calibration_offset = self._calibrate_page_offset(reader)
                fm_offset = self._detect_frontmatter_offset(reader)
                effective_offset = calibration_offset if calibration_offset > 0 else fm_offset
                
                current_chapter = None
                current_section = None
                ch_pattern = re.compile(r'(?:^|\n)(?:#+\s*)?(?:Chapter|CHAPTER)\s+([0-9IVXLCDMivxlcdm]+)', re.IGNORECASE)
                sec_pattern = re.compile(r'(?:^|\n)(?:#+\s*)?(?:Section|SECTION|§)\s*([0-9.]+)', re.IGNORECASE)
                
                for page_num in range(len(reader.pages)):
                    page = reader.pages[page_num]
                    text = page.extract_text()
                    
                    # 1. Try native PDF labels
                    if page_labels and page_num < len(page_labels):
                        page_label = str(page_labels[page_num])
                    # 2. Try index-based or front-matter calibration
                    elif effective_offset > 0:
                        if page_num < effective_offset:
                            page_label = int_to_roman(page_num + 1)
                        else:
                            page_label = str(page_num - effective_offset + 1)
                    # 3. Try heuristic text extraction from header/footer
                    elif text and self._extract_printed_page_number(text):
                        page_label = self._extract_printed_page_number(text)
                    # 4. Fallback to absolute index
                    else:
                        page_label = str(page_num + 1)
                        
                    if text:
                        paragraphs = split_paragraphs(text)
                        for i, p in enumerate(paragraphs):
                            ch_match = ch_pattern.search(p)
                            if ch_match:
                                current_chapter = ch_match.group(1)
                                current_section = None
                                
                            sec_match = sec_pattern.search(p)
                            if sec_match:
                                current_section = sec_match.group(1)
                                
                            para_num = extract_paragraph_number(p, i + 1)
                            markers: Dict[str, str] = {
                                "page": page_label,
                                "paragraph": para_num
                            }
                            if current_chapter:
                                markers["chapter"] = current_chapter
                            if current_section:
                                markers["section"] = current_section
                                
                            extracted_pages.append({
                                "text": p,
                                "markers": markers
                            })
            logger.info(f"Successfully parsed PDF file: {filepath} ({len(extracted_pages)} paragraphs extracted from {len(reader.pages)} pages)")
        except Exception as e:
            logger.error(f"Failed to parse PDF file {filepath}: {e}")
            raise
            
        return extracted_pages
