# DRDO Phase 1A — Library Exploration & Data Ingestion Research

> **Status:** Phase 1A — Experimentation Sandbox  
> **Objective:** Learn how different document ingestion libraries behave *before* integrating them into a larger system.

---

## Project Purpose

This project is an **experimentation environment** for Phase 1 of an Offline Multimodal Intelligence Analysis System (DRDO-style).

It is intentionally **not** a production pipeline. There are no vector databases, no embeddings, no LLM integrations, and no RAG architecture here. The sole goal is to:

1. **Understand** how each library reads and processes different file formats.
2. **Observe** the raw outputs (text, metadata, OCR detections) first-hand.
3. **Build intuition** about edge cases, limitations, and failure modes.

Once this exploration phase is complete, the learnings will feed into the design of the real ingestion pipeline.

---

## Project Structure

```text
drdo_phase1/
│
├── test_files/                    ← Drop sample PDFs, DOCX, TXT, images here
│
├── experiments/
│   ├── test_file_classifier.py    ← Experiment 1: MIME-based file classification
│   ├── test_pdf.py                ← Experiment 2: PDF text extraction (PyMuPDF)
│   ├── test_docx.py               ← Experiment 3: DOCX paragraph extraction
│   ├── test_txt.py                ← Experiment 4: Plain text reading
│   ├── test_image.py              ← Experiment 5: Image OCR (EasyOCR)
│   └── test_scanned_pdf.py        ← Experiment 6: Scanned PDF → images → OCR
│
├── models/
│   └── document.py                ← Prototype Document dataclass
│
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Create a virtual environment

```bash
cd drdo_phase1
python -m venv .venv
```

### 2. Activate the virtual environment

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows (PowerShell):**

```powershell
.venv\Scripts\Activate.ps1
```

**Windows (CMD):**

```cmd
.venv\Scripts\activate.bat
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. System dependency — poppler (for pdf2image)

`pdf2image` requires the **poppler** command-line tools to convert PDF pages into images.

**macOS:**

```bash
brew install poppler
```

**Ubuntu / Debian:**

```bash
sudo apt-get install poppler-utils
```

**Windows:**

Download poppler from https://github.com/oschwartz10612/poppler-windows/releases and add the `bin/` folder to your system PATH.

---

## Running Experiments

Each experiment is a standalone script. Run them from the project root:

### Experiment 1 — File Classification

```bash
python experiments/test_file_classifier.py
```

Classifies any file by its actual binary content (magic bytes), not the extension.  
Categories: `PDF`, `DOCX`, `TXT`, `IMAGE`, `UNKNOWN`.

### Experiment 2 — PDF Extraction

```bash
python experiments/test_pdf.py
```

Opens a PDF with PyMuPDF, prints metadata and extracts text page-by-page.

### Experiment 3 — DOCX Extraction

```bash
python experiments/test_docx.py
```

Reads all paragraphs from a Word document using python-docx.

### Experiment 4 — TXT Extraction

```bash
python experiments/test_txt.py
```

Reads a plain text file and prints line/character counts.

### Experiment 5 — Image OCR

```bash
python experiments/test_image.py
```

Runs EasyOCR on an image and prints detected text, confidence scores, and bounding boxes.  
*(First run will download EasyOCR model weights — this is expected.)*

### Experiment 6 — Scanned PDF OCR

```bash
python experiments/test_scanned_pdf.py
```

Converts each page of a scanned PDF to an image, then runs EasyOCR on every page.  
Requires poppler (see Installation above).

### Document Dataclass Demo

```bash
python models/document.py
```

Shows how different file types can be converted into a single unified `Document` object.

---

## Libraries Used

| Library        | Import         | Purpose                                        |
| -------------- | -------------- | ---------------------------------------------- |
| python-magic   | `magic`        | Detect file type from binary content            |
| PyMuPDF        | `fitz`         | Read and extract text from PDF files            |
| python-docx    | `docx`         | Read paragraphs from DOCX files                 |
| EasyOCR        | `easyocr`      | Optical Character Recognition on images          |
| Pillow         | `PIL`          | Image handling (used by EasyOCR and pdf2image)   |
| pdf2image      | `pdf2image`    | Convert PDF pages to images (requires poppler)   |

---

## Future Architecture

Eventually, this system will evolve into a full offline intelligence-analysis pipeline:

```text
Input File
    ↓
File Classifier          ← Experiment 1
    ↓
Format-Specific Loader   ← Experiments 2–6
    ↓
Text Extraction
    ↓
Document Object          ← models/document.py
    ↓
Incident Extraction      ← (future phase)
    ↓
Incident Records
    ↓
Embeddings               ← (future phase)
    ↓
Retrieval                ← (future phase)
```

**This project intentionally stops at the Document Object stage.**  
Everything below that line (incident extraction, embeddings, retrieval) is for later phases.

---

## Notes

- Place your sample test files in the `test_files/` directory.
- The `temp_pages/` folder is created automatically by Experiment 6 and can be deleted safely.
- All experiments use `gpu=False` for EasyOCR to ensure they run on any machine.
- Each script handles errors gracefully and prints helpful messages on failure.
