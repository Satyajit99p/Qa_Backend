from typing import List, Optional
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    doc_id: str
    filename: str


class ExtractRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(5, ge=1, le=50)


class ExtractResult(BaseModel):
    chunk_id: int
    score: float
    text: str
    source: str


class ExtractResponse(BaseModel):
    results: List[ExtractResult]


class AnswerRequest(BaseModel):
    query: str = Field(..., min_length=1)
    top_k: Optional[int] = Field(3, ge=1, le=10)


class AnswerSource(BaseModel):
    filename: str
    chunk_id: int
    score: float


class AnswerResponse(BaseModel):
    answer: str
    sources: List[AnswerSource]


class DocumentMeta(BaseModel):
    doc_id: str
    filename: str
    chunks: int