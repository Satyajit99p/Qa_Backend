from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import Body
from fastapi.responses import JSONResponse
from pathlib import Path
import json
from app.storage.manager import save_upload, delete_file
from app.services import parser, vector_store
from app.models.schemas import (
    UploadResponse, ExtractRequest, ExtractResponse, ExtractResult,
    AnswerRequest, AnswerResponse, AnswerSource, DocumentMeta
)
from app.core.config import DATA_DIR

router = APIRouter()

# in-memory documents store
# doc_store[doc_id] = {"filename": str, "filepath": Path, "chunks": List[str], "store": SimpleTfidfStore}
_doc_store = {}


@router.post("/upload-file", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    try:
        doc_id, dest = save_upload(file)
        ext = dest.suffix.lower()
        if ext == ".pdf":
            raw = parser.extract_text_from_pdf(dest)
        elif ext == ".docx":
            raw = parser.extract_text_from_docx(dest)
        else:
            raw = parser.extract_text_from_txt(dest)

        chunks = parser.chunk_text(raw)
        store = vector_store.SimpleTfidfStore(chunks)

        _doc_store[doc_id] = {"filename": file.filename, "filepath": dest, "chunks": chunks, "store": store}

        # persist minimal metadata
        meta = {"doc_id": doc_id, "filename": file.filename, "chunks_count": len(chunks)}
        meta_path = DATA_DIR / f"{doc_id}.json"
        meta_path.write_text(json.dumps(meta))

        return UploadResponse(doc_id=doc_id, filename=file.filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract", response_model=ExtractResponse)
async def extract(req: ExtractRequest = Body(...)):
    # If no documents uploaded, inform the user
    if not _doc_store:
        raise HTTPException(status_code=404, detail="No documents available. Upload documents first.")

    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Collect top matches from each document
    aggregated = []
    for doc_id, doc in _doc_store.items():
        store = doc.get("store")
        if not store:
            continue
        results = store.top_k(req.query, k=req.top_k)
        for r in results:
            aggregated.append({
                "doc_id": doc_id,
                "chunk_id": r["chunk_id"],
                "score": r["score"],
                "text": r["text"],
                "source": doc["filename"]
            })

    # Sort across all docs and return top_k overall
    aggregated.sort(key=lambda x: x["score"], reverse=True)
    topk = aggregated[: req.top_k]

    out = [ExtractResult(**r) for r in topk]
    return ExtractResponse(results=out)


@router.post("/answer", response_model=AnswerResponse)
async def answer(req: AnswerRequest = Body(...)):
    # If no documents uploaded, inform the user
    if not _doc_store:
        raise HTTPException(status_code=404, detail="No documents available. Upload documents first.")

    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    # Collect top matches from each document
    aggregated = []
    for doc_id, doc in _doc_store.items():
        store = doc.get("store")
        if not store:
            continue
        results = store.top_k(req.query, k=req.top_k)
        for r in results:
            aggregated.append({
                "doc_id": doc_id,
                "chunk_id": r["chunk_id"],
                "score": r["score"],
                "text": r["text"],
                "filename": doc["filename"]
            })

    # If nothing found
    if not aggregated:
        return AnswerResponse(answer="No relevant passages found in the uploaded documents.", sources=[])

    # Sort across all docs and take overall top_k
    aggregated.sort(key=lambda x: x["score"], reverse=True)
    topk = aggregated[: req.top_k]

    # Build concise answer from top passages
    top_texts = [item["text"].strip() for item in topk if item.get("score", 0) > 0]
    if not top_texts:
        answer_text = "No relevant passages found in the uploaded documents."
    else:
        joined = "\n\n---\n\n".join(top_texts)
        if len(joined) > 3000:
            answer_text = joined[:3000].rsplit(" ", 1)[0] + "..."
        else:
            answer_text = joined

    # Build sources list
    sources = [
        AnswerSource(filename=item["filename"], chunk_id=item["chunk_id"], score=item["score"])
        for item in topk
    ]

    return AnswerResponse(answer=answer_text, sources=sources)


@router.get("/documents")
async def list_documents():
    items = []
    for k, v in _doc_store.items():
        items.append(DocumentMeta(doc_id=k, filename=v["filename"], chunks=len(v.get("chunks", []))))
    return {"documents": items}


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    doc = _doc_store.pop(doc_id, None)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    delete_file(doc.get("filepath"))
    meta = DATA_DIR / f"{doc_id}.json"
    if meta.exists():
        meta.unlink()
    return {"detail": "deleted"}