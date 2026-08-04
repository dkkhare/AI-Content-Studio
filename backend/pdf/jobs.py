from dataclasses import dataclass


@dataclass
class PDFJob:
    pdf_file: str
    output_folder: str
    create_thumbnails: bool = True
    enable_ocr: bool = True