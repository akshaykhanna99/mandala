# PDF Extraction Instructions

The FCA Handbook PDFs need to be extracted and their content pasted into `FCA_EXCERPTS.md`.

## PDFs to Extract

1. **COBS 9 Suitability**
   - Location: `/Users/akshaykhanna/Downloads/COBS 9 Suitability (including basic advice) (other than MiFID and insurance-based investment products).pdf`
   - Paste content under the "COBS 9: Suitability" section in `FCA_EXCERPTS.md`

2. **SYSC 7 Risk Control**
   - Location: `/Users/akshaykhanna/Downloads/SYSC 7 Risk control.pdf`
   - Paste content under the "SYSC 7: Risk Control" section in `FCA_EXCERPTS.md`

## Extraction Methods

### Option 1: Manual Copy-Paste
1. Open each PDF in a PDF viewer
2. Select all text (Cmd+A / Ctrl+A)
3. Copy and paste into the appropriate section in `FCA_EXCERPTS.md`

### Option 2: Python Script (if pypdf is available)
```bash
cd /Users/akshaykhanna/Desktop/Mandala/mandala
pip install pypdf
python3 -c "
import pypdf
with open('/Users/akshaykhanna/Downloads/COBS 9 Suitability (including basic advice) (other than MiFID and insurance-based investment products).pdf', 'rb') as f:
    reader = pypdf.PdfReader(f)
    text = '\n'.join([page.extract_text() for page in reader.pages])
    print(text)
" > docs/regulatory/COBS_9_raw.txt
```

### Option 3: Online PDF to Text Converter
Use an online tool to convert PDFs to text, then paste into `FCA_EXCERPTS.md`

## After Extraction

Once content is pasted, the `regulatory_retriever.py` module will be able to chunk and retrieve relevant sections for the LLM prompt.
