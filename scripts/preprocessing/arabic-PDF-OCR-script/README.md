
# Arabic PDF OCR Tool for Google Colab

![Python](https://img.shields.io/badge/Python-3.6+-blue.svg)
![Google Colab](https://img.shields.io/badge/Google%20Colab-Compatible-brightgreen.svg)
![License](https://img.shields.io/badge/License-MIT-orange.svg)

## 📌 Overview

An interactive Google Colab notebook that extracts Arabic text from PDF documents using:
- Tesseract OCR with Arabic language support
- Arabic text reshaping for proper character connections
- Bidirectional text algorithm for RTL display

## 🚀 Quick Start

1. **Open new note in Colab**:
2. **copy requirements.txt in the first cell**
3. **copy OCT-Script.ipynb in the second cell** 
4. **Run all cells** (Runtime → Run all)
4. Follow the interactive prompts to:
   - Select input source (local/Drive)
   - Choose PDF files
   - Select output destination

## 🔧 Installation

```python
# First cell in Colab:
!apt-get install -y poppler-utils tesseract-ocr tesseract-ocr-ara
!pip install pdf2image arabic_reshaper python-bidi ipywidgets google-colab --quiet
!pip install --quiet pdf2image pytesseract arabic_reshaper python-bidi ipywidgets google-colab

!apt-get update


```

## 🛠️ How It Works

### Core OCR Function
```python
def ocr_pdf_to_text(pdf_path):
    images = convert_from_path(pdf_path)  # PDF to images
    extracted_text = ""
    
    for image in images:
        raw_text = pytesseract.image_to_string(image, lang='ara')  # Arabic OCR
        reshaped_text = arabic_reshaper.reshape(raw_text)  # Fix character shapes
        bidi_text = get_display(reshaped_text)  # Apply RTL formatting
        extracted_text += bidi_text + "\n\n"
    
    return extracted_text
```

### Interactive Workflow
1. **Input Selection**:
   ```python
   input_source = widgets.RadioButtons(
       options=[('Local upload', 'local'), 
                ('Google Drive', 'drive')]
   )
   ```

2. **File Handling**:
   - Local uploads saved to `/content/uploads`
   - Drive files accessed via `/content/drive`

3. **Output Options**:
   - Direct download (ZIP)
   - Google Drive save (persistent storage)

## 📂 File Processing
```python
def process_files():
    for pdf_path in uploaded_files:
        text = ocr_pdf_to_text(pdf_path)
        output_file = Path(pdf_path).stem + '.txt'
        
        if output_dest == 'local':
            with open(f'/content/output/{output_file}', 'w') as f:
                f.write(text)
            files.download(f'/content/output/{output_file}')
        
        elif output_dest == 'drive':
            drive_path = f'{output_folder_drive}/{output_file}'
            with open(drive_path, 'w') as f:
                f.write(text)
```

## 🌍 Supported Languages
1. Primarily Arabic, but can be modified for other RTL languages by changing Tesseract language code (`ara`)
2. Adjusting reshaping parameters

## ⚠️ Limitations
| Issue | Workaround |
|-------|------------|
| Low-quality PDFs | Pre-process with image enhancement |
| Mixed LTR/RTL text | Manual post-processing needed |
| Large files | Split PDFs before processing |

## 📜 License
MIT License - Free for academic and commercial use

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/improvement`)
3. Commit changes (`git commit -m 'Add some feature'`)
4. Push to branch (`git push origin feature/improvement`)
5. Open a Pull Request

## 📊 Performance Tips
- For 100+ page PDFs:
  ```python
  convert_from_path(pdf_path, thread_count=4)  # Multi-thread processing
  ```
- To improve OCR accuracy:
  ```python
  pytesseract.image_to_string(image, lang='ara', config='--psm 6')
  ```
```
