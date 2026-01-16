"""QA schemas."""
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


class Citation(BaseModel):
    """Citation schema."""
    source_num: int
    chunk_id: str
    document_id: Optional[int] = None
    document_filename: str
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    snippet: str


class QASessionCreate(BaseModel):
    """QA session creation schema."""
    project_id: int
    title: Optional[str] = None
    context: Optional[str] = None


class QASessionResponse(BaseModel):
    """QA session response schema."""
    id: int
    project_id: int
    user_id: int
    title: Optional[str] = None
    context: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class QuestionRequest(BaseModel):
    """Question request schema."""
    question: str
    session_id: Optional[int] = None
    project_id: Optional[int] = None
    top_k: Optional[int] = None


class QAResponseSchema(BaseModel):
    """QA response schema."""
    id: int
    session_id: int
    question: str
    answer: str
    citations: List[Citation]
    retrieved_chunk_ids: List[str]
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    type: str  # "token", "citation", "done"
    content: Optional[str] = None
    citations: Optional[List[Citation]] = None

