from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

from backend.talking_head import BookImportError, BookImporter


class Page:
    def __init__(self, text):
        self.text = text

    def get_text(self, mode):
        return self.text


class Document:
    def __init__(self, pages, toc=()):
        self.pages = [Page(value) for value in pages]
        self.page_count = len(self.pages)
        self.toc = list(toc)
        self.closed = False

    def load_page(self, index):
        return self.pages[index]

    def get_toc(self, simple=True):
        return self.toc

    def close(self):
        self.closed = True


class BookImportTests(unittest.TestCase):
    def test_text_import_keeps_chapters_and_all_content(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.txt"
            path.write_text(
                "CHAPTER 1\nOpening text.\n\nCHAPTER 2\nEnding text.",
                encoding="utf-8",
            )
            result = BookImporter().import_book(path)
            self.assertEqual([item.title for item in result.blocks], ["CHAPTER 1", "CHAPTER 2"])
            self.assertIn("Opening text.", result.text)
            self.assertIn("Ending text.", result.text)

    def test_pdf_bookmarks_create_ordered_nonoverlapping_blocks(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.pdf"
            path.write_bytes(b"%PDF-test")
            document = Document(
                ["front " * 30, "chapter one " * 30, "chapter two " * 30],
                [(1, "Chapter One", 2), (1, "Chapter Two", 3)],
            )
            result = BookImporter(pdf_opener=lambda value: document).import_book(path)
            self.assertEqual(
                [item.title for item in result.blocks],
                ["Front matter", "Chapter One", "Chapter Two"],
            )
            self.assertEqual(result.page_count, 3)
            self.assertTrue(document.closed)
            combined = result.text
            self.assertEqual(combined.count("chapter one"), 30)
            self.assertEqual(combined.count("chapter two"), 30)

    def test_scanned_pdf_requires_ocr(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "scan.pdf"
            path.write_bytes(b"%PDF-test")
            document = Document(["", "12"])
            with self.assertRaisesRegex(BookImportError, "Run OCR first"):
                BookImporter(pdf_opener=lambda value: document).import_book(path)

    def test_docx_heading_styles_preserve_sections(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "book.docx"
            xml = """<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:body>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Chapter One</w:t></w:r></w:p>
<w:p><w:r><w:t>First paragraph.</w:t></w:r></w:p>
<w:p><w:pPr><w:pStyle w:val="Heading1"/></w:pPr><w:r><w:t>Chapter Two</w:t></w:r></w:p>
<w:p><w:r><w:t>Second paragraph.</w:t></w:r></w:p>
</w:body></w:document>"""
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("word/document.xml", xml)
            result = BookImporter().import_book(path)
            self.assertEqual([item.title for item in result.blocks], ["Chapter One", "Chapter Two"])
            self.assertEqual(result.blocks[1].text, "Second paragraph.")

    def test_unsupported_and_non_utf8_inputs_are_actionable(self):
        with tempfile.TemporaryDirectory() as folder:
            bad = Path(folder) / "book.bin"
            bad.write_bytes(b"data")
            with self.assertRaisesRegex(BookImportError, "Unsupported"):
                BookImporter().import_book(bad)
            text = Path(folder) / "book.txt"
            text.write_bytes(b"\xff\xfe")
            with self.assertRaisesRegex(BookImportError, "UTF-8"):
                BookImporter().import_book(text)


if __name__ == "__main__":
    unittest.main()
