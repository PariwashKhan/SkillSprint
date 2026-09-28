"""
Document Parser – PDF + DOCX with full source traceability
Mandatory formats: PDF and DOCX
"""

import os
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional
import pdfplumber
from docx import Document as DocxDocument
from pathlib import Path


def generate_doc_id(filename: str, content: bytes) -> str:
    """Create stable Document ID"""
    h = hashlib.md5(content).hexdigest()[:8]
    name = Path(filename).stem.upper().replace(" ", "_")[:20]
    return f"DOC-{name}-{h}"


def parse_pdf(file_path: str, doc_id: str, version: str = "1.0", 
              effective_date: str = None, category: str = "Policy") -> Dict[str, Any]:
    """Extract text + structure from PDF with page references"""
    chunks = []
    full_text = []
    
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if not text.strip():
                continue
            full_text.append(text)
            
            # Simple section detection by headings
            lines = text.split("\n")
            current_section = f"Page-{page_num}"
            section_text = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                # Heuristic: short uppercase or numbered lines as headings
                if (len(line) < 80 and (line.isupper() or line[:2].isdigit())) or line.endswith(":"):
                    if section_text:
                        chunks.append({
                            "chunk_id": f"{doc_id}-P{page_num}-C{len(chunks)+1}",
                            "document_id": doc_id,
                            "section": current_section,
                            "heading": current_section,
                            "page": page_num,
                            "text": "\n".join(section_text),
                            "source_location": f"Page {page_num}"
                        })
                        section_text = []
                    current_section = line[:100]
                else:
                    section_text.append(line)
            
            if section_text:
                chunks.append({
                    "chunk_id": f"{doc_id}-P{page_num}-C{len(chunks)+1}",
                    "document_id": doc_id,
                    "section": current_section,
                    "heading": current_section,
                    "page": page_num,
                    "text": "\n".join(section_text),
                    "source_location": f"Page {page_num}"
                })
    
    return {
        "document_id": doc_id,
        "filename": os.path.basename(file_path),
        "file_type": "pdf",
        "version": version,
        "effective_date": effective_date or datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "total_pages": len(pdf.pages) if 'pdf' in dir() else 0,
        "full_text": "\n\n".join(full_text),
        "chunks": chunks,
        "chunk_count": len(chunks)
    }


def parse_docx(file_path: str, doc_id: str, version: str = "1.0",
               effective_date: str = None, category: str = "Policy") -> Dict[str, Any]:
    """Extract text + structure from DOCX with paragraph references"""
    doc = DocxDocument(file_path)
    chunks = []
    full_text = []
    current_section = "Introduction"
    section_paras = []
    para_idx = 0
    
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        full_text.append(text)
        para_idx += 1
        
        # Detect headings
        style_name = para.style.name if para.style else ""
        if "Heading" in style_name or (len(text) < 80 and text.isupper()):
            if section_paras:
                chunks.append({
                    "chunk_id": f"{doc_id}-S{len(chunks)+1}",
                    "document_id": doc_id,
                    "section": current_section,
                    "heading": current_section,
                    "page": None,
                    "paragraph": para_idx,
                    "text": "\n".join(section_paras),
                    "source_location": f"Paragraph ~{para_idx}"
                })
                section_paras = []
            current_section = text[:100]
        else:
            section_paras.append(text)
    
    if section_paras:
        chunks.append({
            "chunk_id": f"{doc_id}-S{len(chunks)+1}",
            "document_id": doc_id,
            "section": current_section,
            "heading": current_section,
            "page": None,
            "paragraph": para_idx,
            "text": "\n".join(section_paras),
            "source_location": f"Paragraph ~{para_idx}"
        })
    
    return {
        "document_id": doc_id,
        "filename": os.path.basename(file_path),
        "file_type": "docx",
        "version": version,
        "effective_date": effective_date or datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "total_pages": None,
        "full_text": "\n\n".join(full_text),
        "chunks": chunks,
        "chunk_count": len(chunks)
    }


def parse_document(file_path: str, version: str = "1.0", 
                   effective_date: str = None, category: str = "Policy") -> Dict[str, Any]:
    """Main entry – supports PDF and DOCX only (mandatory)"""
    with open(file_path, "rb") as f:
        content = f.read()
    
    doc_id = generate_doc_id(os.path.basename(file_path), content)
    ext = Path(file_path).suffix.lower()
    
    if ext == ".pdf":
        return parse_pdf(file_path, doc_id, version, effective_date, category)
    elif ext in [".docx", ".doc"]:
        return parse_docx(file_path, doc_id, version, effective_date, category)
    else:
        raise ValueError(f"Unsupported format: {ext}. Only PDF and DOCX are mandatory.")
