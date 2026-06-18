"""
Document Dataclass — Phase 1A Prototype

This is NOT the final production model.
This is an early prototype to understand the concept of converting
PDFs, DOCX files, images, and TXT files into a common internal
representation (a unified Document object).

In a real system, every ingested file — regardless of its original
format — would be transformed into one of these Document objects so
that downstream processing (search, analysis, extraction) can work
with a single, predictable structure.
"""

from dataclasses import dataclass, field


@dataclass
class Document:
    """
    A unified internal representation of any ingested document.

    Fields
    ------
    doc_id : str
        A unique identifier for this document (e.g. UUID or hash).

    source_type : str
        The category of the original file: "PDF", "DOCX", "TXT",
        "IMAGE", or "SCANNED_PDF".

    source_path : str
        The filesystem path from which the document was loaded.

    raw_text : str
        The full extracted text content of the document.

    title : str
        An optional human-readable title (extracted from metadata
        or assigned manually).

    language : str
        The detected or assumed language of the document
        (e.g. "en", "hi").

    page_count : int
        Number of pages in the original document (0 for formats
        that don't have pages, like plain text or images).

    metadata : dict
        A flexible dictionary for any extra metadata — author,
        creation date, OCR confidence scores, etc.
    """

    doc_id: str
    source_type: str
    source_path: str
    raw_text: str
    title: str = ""
    language: str = ""
    page_count: int = 0
    metadata: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Example: How to instantiate the Document dataclass
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Suppose we just extracted text from a 3-page PDF
    sample_doc = Document(
        doc_id="doc-001",
        source_type="PDF",
        source_path="/path/to/report.pdf",
        raw_text="This is the full extracted text from the PDF...",
        title="Quarterly Threat Assessment — Q3 2025",
        language="en",
        page_count=3,
        metadata={
            "author": "Intelligence Bureau",
            "created": "2025-07-01",
            "producer": "LaTeX / pdfTeX",
        },
    )

    print("=== Document Object ===")
    print(f"  ID          : {sample_doc.doc_id}")
    print(f"  Type        : {sample_doc.source_type}")
    print(f"  Path        : {sample_doc.source_path}")
    print(f"  Title       : {sample_doc.title}")
    print(f"  Language    : {sample_doc.language}")
    print(f"  Pages       : {sample_doc.page_count}")
    print(f"  Text Length : {len(sample_doc.raw_text)} characters")
    print(f"  Metadata    : {sample_doc.metadata}")
    print()
    print("This demonstrates that any file — PDF, DOCX, image, etc.")
    print("— can be normalised into one common Document structure.")
