#!/usr/bin/env python3
"""Extract text from FCA PDFs and update FCA_EXCERPTS.md"""
import sys
from pathlib import Path

# Try to use backend venv
backend_venv = Path(__file__).parent.parent.parent / "backend" / ".venv" / "bin" / "python3"
if backend_venv.exists():
    sys.executable = str(backend_venv)

try:
    import pypdf
    PDF_LIB = "pypdf"
except ImportError:
    try:
        import PyPDF2
        PDF_LIB = "PyPDF2"
    except ImportError:
        try:
            import pdfplumber
            PDF_LIB = "pdfplumber"
        except ImportError:
            print("❌ No PDF library found. Please install one:")
            print("   pip install pypdf")
            print("   OR")
            print("   pip install PyPDF2")
            print("   OR")
            print("   pip install pdfplumber")
            sys.exit(1)

def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        with open(pdf_path, 'rb') as f:
            if PDF_LIB == "pypdf":
                import pypdf
                reader = pypdf.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)
                return "\n\n".join(text_parts)
            elif PDF_LIB == "PyPDF2":
                import PyPDF2
                reader = PyPDF2.PdfReader(f)
                text_parts = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text.strip():
                        text_parts.append(text)
                return "\n\n".join(text_parts)
            elif PDF_LIB == "pdfplumber":
                import pdfplumber
                text_parts = []
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text and text.strip():
                            text_parts.append(text)
                return "\n\n".join(text_parts)
    except Exception as e:
        print(f"❌ Error extracting {pdf_path}: {e}")
        import traceback
        traceback.print_exc()
        return ""

def update_fca_excerpts():
    """Extract PDFs and update FCA_EXCERPTS.md"""
    regulatory_dir = Path(__file__).parent
    
    # Find PDFs
    cobs_pdf = regulatory_dir / "COBS 9 Suitability (including basic advice) (other than MiFID and insurance-based investment products).pdf"
    sysc_pdf = regulatory_dir / "SYSC 7 Risk control.pdf"
    
    excerpts_file = regulatory_dir / "FCA_EXCERPTS.md"
    
    if not cobs_pdf.exists():
        print(f"❌ COBS 9 PDF not found at: {cobs_pdf}")
        return
    
    if not sysc_pdf.exists():
        print(f"❌ SYSC 7 PDF not found at: {sysc_pdf}")
        return
    
    print("📄 Extracting COBS 9 PDF...")
    cobs_text = extract_pdf_text(cobs_pdf)
    print(f"   Extracted {len(cobs_text)} characters")
    
    print("📄 Extracting SYSC 7 PDF...")
    sysc_text = extract_pdf_text(sysc_pdf)
    print(f"   Extracted {len(sysc_text)} characters")
    
    # Read current excerpts file
    if excerpts_file.exists():
        content = excerpts_file.read_text(encoding="utf-8")
    else:
        content = """# FCA Handbook Excerpts

This file contains extracted text from relevant FCA Handbook sections for use in the Geopolitical Health Scan feature.

## COBS 9: Suitability (including basic advice)

---

## SYSC 7: Risk Control

---

## Consumer Duty

---

## DISP: Complaints and Evidence

---
"""
    
    # Replace COBS 9 section
    import re
    cobs_pattern = r"## COBS 9: Suitability.*?(?=---|\n## |$)"
    cobs_replacement = f"## COBS 9: Suitability (including basic advice)\n\n{cobs_text}\n\n---"
    
    if re.search(cobs_pattern, content, re.DOTALL):
        content = re.sub(cobs_pattern, cobs_replacement, content, flags=re.DOTALL)
    else:
        # Insert after COBS 9 heading
        content = re.sub(
            r"(## COBS 9: Suitability.*?\n)",
            rf"\1\n{cobs_text}\n\n---\n",
            content,
            flags=re.DOTALL
        )
    
    # Replace SYSC 7 section
    sysc_pattern = r"## SYSC 7: Risk Control.*?(?=---|\n## |$)"
    sysc_replacement = f"## SYSC 7: Risk Control\n\n{sysc_text}\n\n---"
    
    if re.search(sysc_pattern, content, re.DOTALL):
        content = re.sub(sysc_pattern, sysc_replacement, content, flags=re.DOTALL)
    else:
        # Insert after SYSC 7 heading
        content = re.sub(
            r"(## SYSC 7: Risk Control.*?\n)",
            rf"\1\n{sysc_text}\n\n---\n",
            content,
            flags=re.DOTALL
        )
    
    # Write updated file
    excerpts_file.write_text(content, encoding="utf-8")
    print(f"✅ Updated {excerpts_file}")
    print(f"   Total content: {len(content)} characters")

if __name__ == "__main__":
    update_fca_excerpts()
