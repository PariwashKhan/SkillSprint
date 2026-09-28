"""
Document Upload + Validation
"""

import os
import hashlib
from pathlib import Path
from typing import Tuple, Optional
from config.settings import settings


ALLOWED_EXTENSIONS = {".pdf", ".docx"}
MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def validate_file(file_name: str, file_bytes: bytes) -> Tuple[bool, str]:
    """Validate file type, size, empty"""
    ext = Path(file_name).suffix.lower()
    
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Unsupported file type: {ext}. Only PDF and DOCX allowed."
    
    if len(file_bytes) == 0:
        return False, "Empty document not allowed."
    
    if len(file_bytes) > MAX_SIZE:
        return False, f"File too large. Max {settings.MAX_FILE_SIZE_MB} MB."
    
    return True, "OK"


def save_upload(file_name: str, file_bytes: bytes, upload_dir: str = None) -> str:
    """Save file and return path"""
    upload_dir = upload_dir or settings.UPLOAD_FOLDER
    os.makedirs(upload_dir, exist_ok=True)
    
    # Avoid name collision
    stem = Path(file_name).stem
    ext = Path(file_name).suffix
    safe_name = f"{stem}_{hashlib.md5(file_bytes).hexdigest()[:6]}{ext}"
    path = os.path.join(upload_dir, safe_name)
    
    with open(path, "wb") as f:
        f.write(file_bytes)
    
    return path


def is_duplicate(file_bytes: bytes, existing_hashes: set) -> bool:
    h = hashlib.md5(file_bytes).hexdigest()
    return h in existing_hashes
