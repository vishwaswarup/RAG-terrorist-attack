# Offline Multimodal RAG Intelligence Analysis System

> **Status:** Core Pipeline & UI Integrated  
> **Objective:** A fully offline, end-to-end multimodal intelligence analysis system integrating document ingestion, LLM-powered event extraction, hybrid vector search, and a visual dashboard.

---

## Project Purpose

This project is an advanced **intelligence analysis environment** capable of parsing multimodal documents (PDFs, images, raw text), extracting structured incident records using Local LLMs, indexing them into an offline vector database, and providing a unified RAG (Retrieval-Augmented Generation) search interface.

Key Capabilities:
1. **Multimodal Ingestion**: Processes PDFs, DOCX, TXT, and runs OCR and vision models on images.
2. **LLM Extraction**: Automatically structures raw text into `Incident` objects (locations, dates, casualties, groups, etc.).
3. **Hybrid Search**: Combines strict metadata filtering with dense semantic vector search via ChromaDB.
4. **Interactive Dashboard**: A Streamlit UI for querying the intelligence database, analyzing datasets, and uploading new documents.

---

## Project Structure

```text
intelligence_system/
│
├── ingestion/       ← Standardized document ingestors (PDF, DOCX, TXT, Image OCR)
├── extraction/      ← LLM-powered entity extraction and event clustering
├── models/          ← Core data schemas (Document, Incident, ImageAsset)
├── rag/             ← Retrieval-Augmented Generation & LLM integrations
├── retrieval/       ← Hybrid vector search engine (ChromaDB & embeddings)
├── storage/         ← Persistent local vector database & SQLite
├── ui/              ← Streamlit Dashboard interface
├── scripts/         ← Evaluation, benchmarking, and diagnostic tools
├── test_files/      ← Sample multimodal test files for ingestion
│
├── pipeline.py          ← CLI entry point for testing document ingestion
├── incident_pipeline.py ← CLI entry point for testing incident extraction
├── requirements.txt
└── README.md
```

---

## Installation

### 1. Create a virtual environment

```bash
cd intelligence_system
python3 -m venv .venv
```

### 2. Activate the virtual environment

**macOS / Linux:**
```bash
source .venv/bin/activate
```
**Windows:**
```cmd
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. System Dependencies

**Poppler** is required by `pdf2image` to handle scanned PDFs:
- **macOS:** `brew install poppler`
- **Ubuntu:** `sudo apt-get install poppler-utils`

---

## Usage

### 1. The Interactive Dashboard (Recommended)
The primary way to interact with the intelligence system is through the Streamlit UI.

```bash
streamlit run ui/app.py
```
This launches a local web application where you can:
- Explore the Intelligence Database.
- Upload and analyze new multimodal documents.
- Run hybrid queries via the unified RAG interface.

### 2. CLI Ingestion Testing
To test the low-level ingestion of a single file (without extracting incidents):

```bash
python pipeline.py
```
*Prompts for a file path (e.g., `test_files/pulmawa_mixed.pdf`) and prints the extracted text and metadata.*

### 3. CLI Extraction Testing
To test the LLM event clustering on a single file:

```bash
python incident_pipeline.py
```
*Prompts for a file path, ingests it, runs the LLM extractor, and prints the structured `Incident` records.*

### 4. Diagnostics & Benchmarking
All standalone metric and evaluation scripts have been moved to the `scripts/` directory. For example, to test retrieval accuracy:

```bash
python scripts/diagnostic_retrieval.py
```

---

## Architecture Flow

```text
Input File (PDF, Image, TXT)
    ↓
Ingestion Pipeline (PyMuPDF, PaddleOCR, OpenCLIP, BLIP)
    ↓
Document Object
    ↓
LLM Extraction Pipeline (Event Clustering)
    ↓
Incident Records & Image Assets
    ↓
ChromaDB (Dense Vector Search + Metadata Filters)
    ↓
RAG Engine & Streamlit Dashboard
```
