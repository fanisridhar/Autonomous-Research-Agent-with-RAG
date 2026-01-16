"""QA session and response models."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class QASession(Base):
    """QA session model to track conversation context."""
    
    __tablename__ = "qa_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Session metadata
    title = Column(String, nullable=True)  # Auto-generated from first question
    context = Column(Text, nullable=True)  # Optional session context
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="qa_sessions")
    responses = relationship("QAResponse", back_populates="session", cascade="all, delete-orphan")


class QAResponse(Base):
    """QA response model for storing question-answer pairs with citations."""
    
    __tablename__ = "qa_responses"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("qa_sessions.id"), nullable=False)
    
    # Question and answer
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    
    # Citations - stored as JSON for flexibility
    # Format: [{"chunk_id": 1, "document_id": 1, "page": 2, "paragraph": 3, "snippet": "..."}, ...]
    citations = Column(JSON, nullable=False, default=list)
    
    # Retrieval metadata
    retrieved_chunk_ids = Column(JSON, nullable=True)  # IDs of chunks used
    model_used = Column(String, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session = relationship("QASession", back_populates="responses")

