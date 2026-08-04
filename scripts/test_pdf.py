from backend.pdf.importer import PDFImporter
from backend.pdf.extractor import TextExtractor
from backend.pdf.analyzer import PDFAnalyzer


pdf = PDFImporter()

doc = pdf.open("sample.pdf")

doc.pages = TextExtractor().extract("sample.pdf")

print(doc.page_count)

print(PDFAnalyzer.is_scanned(doc))