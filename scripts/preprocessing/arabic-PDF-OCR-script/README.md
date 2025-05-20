# Arabic PDF OCR Tool

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![Google Colab](https://img.shields.io/badge/Google%20Colab-Compatible-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-orange.svg)

An interactive tool for extracting Arabic text from PDF documents using OCR (Optical Character Recognition) with proper Arabic text reshaping and bidirectional text handling.

## Features

- **Arabic OCR Processing**: Uses Tesseract OCR with specialized Arabic language support
- **Text Correction**: Applies Arabic reshaping and bidirectional text algorithm for proper display
- **Flexible Input/Output**:
  - Input from local computer upload or Google Drive
  - Output to local download or Google Drive storage
- **User-Friendly Interface**: Interactive workflow with clear prompts in Google Colab
- **Batch Processing**: Handles multiple PDF files in one operation

## Requirements

- Google Colab environment
- Python 3.6+
- Required packages (automatically installed in Colab):
  - `pdf2image`
  - `pytesseract`
  - `arabic-reshaper`
  - `python-bidi`
  - `ipywidgets`

## Installation

1. Open the notebook in Google Colab
2. Run the first cell to install dependencies:
   ```python
   !apt install tesseract-ocr-ara poppler-utils
   !pip install pdf2image pytesseract arabic-reshaper python-bidi ipywidgets
