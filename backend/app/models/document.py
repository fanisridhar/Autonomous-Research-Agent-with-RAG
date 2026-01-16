"""Document and document chunk models."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class DocumentStatus(str, enum.Enum):
    """Document processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"


class DocumentType(str, enum.Enum):
    """Document type enumeration."""
    PDF = "pdf"
    HTML = "html"
    MARKDOWN = "markdown"
    TEXT = "text"
    DOCX = "docx"


class Document(Base):
    """Document model for storing uploaded files and metadata."""
    
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # File metadata
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    mime_type = Column(String, nullable=False)
    document_type = Column(Enum(DocumentType), nullable=False)
    
    # Content metadata
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    page_count = Column(Integer, nullable=True)
    
    # Processing status
    status = Column(Enum(DocumentStatus), default=DocumentStatus.UPLOADED, nullable=False)
    processing_error = Column(Text, nullable=True)
    
    # Source information
    source_url = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """Document chunk model for storing text chunks with embedding metadata."""
    
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    
    # Chunk content
    content = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    
    # Citation metadata for precise source tracking
    page_number = Column(Integer, nullable=True)  # Page number (for PDFs)
    paragraph_number = Column(Integer, nullable=True)  # Paragraph index
    char_start = Column(Integer, nullable=True)  # Character start position in original
    char_end = Column(Integer, nullable=True)  # Character end position in original
    
    # Embedding metadata
    embedding_id = Column(String, nullable=True)  # ID in vector DB
    embedding_model = Column(String, nullable=True)
    
    # Retrieval metadata
    retrieval_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="chunks")

