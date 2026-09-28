"""Tests for document parser + uploader."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.document_processing.uploader import validate_file


def test_valid_pdf_passes():
    ok, msg = validate_file("policy.pdf", b"fake_pdf_content")
    assert ok is True


def test_valid_docx_passes():
    ok, msg = validate_file("policy.docx", b"fake_docx_content")
    assert ok is True


def test_invalid_extension_rejected():
    ok, msg = validate_file("policy.exe", b"fake")
    assert ok is False
    assert "Unsupported" in msg


def test_empty_file_rejected():
    ok, msg = validate_file("policy.pdf", b"")
    assert ok is False
    assert "Empty" in msg


def test_oversized_file_rejected():
    big = b"x" * (25 * 1024 * 1024)  # 25 MB > 20 MB limit
    ok, msg = validate_file("policy.pdf", big)
    assert ok is False
    assert "too large" in msg.lower()