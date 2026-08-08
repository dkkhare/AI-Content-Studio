from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from xml.etree import ElementTree

from .episodes import SourceBlock


class BookImportError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class BookImportResult:
    source: str
    format: str
    blocks: tuple[SourceBlock, ...]
    page_count: int = 0
    warnings: tuple[str, ...] = ()

    @property
    def text(self) -> str:
        return "\n\n".join(item.text for item in self.blocks)


_HEADING = re.compile(
    r"^(?:chapter|part|book|section|अध्याय|भाग|खंड|प्रकरण)\s+"
    r"(?:[\divxlcdm०-९]+|[\w-]+)(?:\s*[:.—-]\s*.*|\s+.*)?$",
    re.IGNORECASE,
)


def _clean_lines(value: str) -> list[str]:
    return [line.strip() for line in value.replace("\r\n", "\n").split("\n")]


def _looks_like_heading(line: str) -> bool:
    value = line.strip()
    if not value or len(value) > 160:
        return False
    if _HEADING.match(value):
        return True
    letters = [char for char in value if char.isalpha()]
    return (
        2 <= len(letters) <= 80
        and value == value.upper()
        and not value.endswith((".", "।", "!", "?"))
    )


def blocks_from_text(value: str, *, prefix: str = "section") -> tuple[SourceBlock, ...]:
    """Retain all text while using explicit-looking lines as logical boundaries."""
    lines = _clean_lines(value)
    blocks: list[SourceBlock] = []
    title = ""
    body: list[str] = []

    def close() -> None:
        nonlocal body
        text = "\n".join(body).strip()
        if text:
            blocks.append(
                SourceBlock(
                    f"{prefix}-{len(blocks) + 1:04d}",
                    title or f"Section {len(blocks) + 1}",
                    text,
                )
            )
        body = []

    for line in lines:
        if _looks_like_heading(line):
            close()
            title = line
        else:
            body.append(line)
    close()
    if not blocks:
        text = value.strip()
        if not text:
            raise BookImportError("The selected book contains no readable text.")
        blocks.append(SourceBlock(f"{prefix}-0001", "Book", text))
    return tuple(blocks)


class BookImporter:
    SUPPORTED = {".pdf", ".txt", ".md", ".docx"}

    def __init__(self, *, pdf_opener: Callable | None = None):
        self.pdf_opener = pdf_opener

    def import_book(self, path: str | Path) -> BookImportResult:
        source = Path(path).resolve()
        if not source.is_file():
            raise FileNotFoundError(f"Book file not found: {source}")
        suffix = source.suffix.lower()
        if suffix not in self.SUPPORTED:
            raise BookImportError(
                "Unsupported book format. Select PDF, DOCX, TXT, or Markdown."
            )
        if suffix == ".pdf":
            return self._pdf(source)
        if suffix == ".docx":
            return self._docx(source)
        try:
            value = source.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError as exc:
            raise BookImportError(
                "Text books must be UTF-8 encoded."
            ) from exc
        return BookImportResult(
            str(source), suffix.lstrip("."), blocks_from_text(value)
        )

    def _open_pdf(self, source: Path):
        if self.pdf_opener:
            return self.pdf_opener(str(source))
        try:
            import fitz
        except ImportError as exc:
            raise BookImportError(
                "PyMuPDF is required to import PDF books."
            ) from exc
        return fitz.open(str(source))

    @staticmethod
    def _page_text(document, index: int) -> str:
        page = document.load_page(index)
        return str(page.get_text("text") or "").strip()

    def _pdf(self, source: Path) -> BookImportResult:
        document = self._open_pdf(source)
        try:
            page_count = getattr(document, "page_count", None)
            count = int(page_count if page_count is not None else len(document))
            pages = [self._page_text(document, index) for index in range(count)]
            readable = sum(char.isalnum() for text in pages for char in text)
            if readable < 100:
                raise BookImportError(
                    "This PDF has little or no extractable text. Run OCR first, "
                    "then import the OCR text or searchable PDF."
                )
            toc = document.get_toc(simple=True) if hasattr(document, "get_toc") else []
        finally:
            close = getattr(document, "close", None)
            if callable(close):
                close()

        warnings: list[str] = []
        entries: list[tuple[int, str, int]] = []
        for item in toc or []:
            if len(item) < 3:
                continue
            level, title, page = int(item[0]), str(item[1]).strip(), int(item[2]) - 1
            if title and 0 <= page < count:
                entries.append((max(1, level), title, page))
        # Page-granular extraction cannot safely separate two TOC entries that
        # begin on the same page. Keep the first so no page is duplicated.
        unique: list[tuple[int, str, int]] = []
        for entry in entries:
            if unique and entry[2] <= unique[-1][2]:
                warnings.append(
                    f"Ignored overlapping PDF bookmark {entry[1]!r}; "
                    "its page remains in the preceding section."
                )
                continue
            unique.append(entry)

        blocks: list[SourceBlock] = []
        if unique:
            if unique[0][2] > 0:
                text = "\n\n".join(pages[: unique[0][2]]).strip()
                if text:
                    blocks.append(SourceBlock("pdf-0001", "Front matter", text))
            for position, (level, title, start) in enumerate(unique):
                end = unique[position + 1][2] if position + 1 < len(unique) else count
                text = "\n\n".join(pages[start:end]).strip()
                if text:
                    blocks.append(
                        SourceBlock(
                            f"pdf-{len(blocks) + 1:04d}", title, text, level
                        )
                    )
        else:
            blocks = list(blocks_from_text("\n\n".join(pages), prefix="pdf"))
            warnings.append(
                "PDF has no usable bookmarks; chapter headings were inferred from text."
            )
        if not blocks:
            raise BookImportError("The PDF contains no usable ordered text blocks.")
        return BookImportResult(
            str(source), "pdf", tuple(blocks), count, tuple(warnings)
        )

    def _docx(self, source: Path) -> BookImportResult:
        try:
            with zipfile.ZipFile(source) as archive:
                xml = archive.read("word/document.xml")
        except (zipfile.BadZipFile, KeyError, OSError) as exc:
            raise BookImportError("The DOCX file is invalid or incomplete.") from exc
        root = ElementTree.fromstring(xml)
        namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        ns = {"w": namespace}
        blocks: list[SourceBlock] = []
        title = ""
        body: list[str] = []

        def close() -> None:
            nonlocal body
            text = "\n".join(body).strip()
            if text:
                blocks.append(
                    SourceBlock(
                        f"docx-{len(blocks) + 1:04d}",
                        title or f"Section {len(blocks) + 1}",
                        text,
                    )
                )
            body = []

        for paragraph in root.findall(".//w:body/w:p", ns):
            text = "".join(
                node.text or "" for node in paragraph.findall(".//w:t", ns)
            ).strip()
            if not text:
                body.append("")
                continue
            style = paragraph.find("./w:pPr/w:pStyle", ns)
            style_value = (
                style.get(f"{{{namespace}}}val", "") if style is not None else ""
            )
            if style_value.lower().startswith(("heading", "title")) or _looks_like_heading(text):
                close()
                title = text
            else:
                body.append(text)
        close()
        if not blocks:
            raise BookImportError("The DOCX file contains no readable text.")
        return BookImportResult(str(source), "docx", tuple(blocks))
