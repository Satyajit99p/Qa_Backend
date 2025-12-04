from fastapi import UploadFile, HTTPException
from pathlib import Path
import shutil
from uuid import uuid4
from app.core.config import UPLOAD_DIR




def save_upload(file: UploadFile) -> (str, Path):
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    ext = Path(file.filename).suffix.lower()
    if ext not in [".pdf", ".docx", ".txt"]:
        raise HTTPException(status_code=400, detail="Unsupported file type. Supported: pdf, docx, txt")
    doc_id = str(uuid4())
    dest = UPLOAD_DIR / f"{doc_id}{ext}"
    try:
        with dest.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    return doc_id, dest




def delete_file(path: Path):
    try:
        if path.exists():
            path.unlink()
    except Exception:
        # swallow but log if desired
        pass