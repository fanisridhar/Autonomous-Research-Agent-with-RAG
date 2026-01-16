"""Document schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.document import DocumentStatus, DocumentType


class DocumentBase(BaseModel):
    """Base document schema."""
    title: Optional[str] = None
    source_url: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Document creation schema."""
    project_id: int
    filename: str
    document_type: DocumentType


class DocumentUpdate(BaseModel):
    """Document update schema."""
    title: Optional[str] = None
    status: Optional[DocumentStatus] = None


class DocumentResponse(DocumentBase):
    """Document response schema."""
    id: int
    project_id: int
    user_id: int
    filename: str
    original_filename: str
    file_size: int
    mime_type: str
    document_type: DocumentType
    status: DocumentStatus
    author: Optional[str] = None
    page_count: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    indexed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DocumentChunkResponse(BaseModel):
    """Document chunk response schema."""
    id: int
    document_id: int
    content: str
    chunk_index: int
    page_number: Optional[int] = None
    paragraph_number: Optional[int] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    
    class Config:
        from_attributes = True

