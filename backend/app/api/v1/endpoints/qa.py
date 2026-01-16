"""QA endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.qa_session import QASession, QAResponse as QAResponseModel
from app.schemas.qa import (
    QASessionCreate,
    QASessionResponse,
    QuestionRequest,
    QAResponseSchema,
)
from app.services.auth import get_current_active_user
from app.services.rag import rag_service
from datetime import datetime

router = APIRouter()


@router.post("/sessions", response_model=QASessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    session_data: QASessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create a new QA session."""
    # Verify project ownership
    from app.models.project import Project
    project = db.query(Project).filter(
        Project.id == session_data.project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    db_session = QASession(
        project_id=session_data.project_id,
        user_id=current_user.id,
        title=session_data.title,
        context=session_data.context,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/sessions", response_model=List[QASessionResponse])
def list_sessions(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List QA sessions. Optionally filter by project."""
    query = db.query(QASession).filter(QASession.user_id == current_user.id)
    if project_id:
        query = query.filter(QASession.project_id == project_id)
    sessions = query.order_by(QASession.updated_at.desc()).all()
    return sessions


@router.get("/sessions/{session_id}", response_model=QASessionResponse)
def get_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific QA session."""
    session = db.query(QASession).filter(
        QASession.id == session_id,
        QASession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/ask", response_model=QAResponseSchema)
def ask_question(
    question_data: QuestionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Ask a question and get an answer with citations."""
    # Determine project_id and session_id
    project_id = question_data.project_id
    session_id = question_data.session_id
    
    # If session_id provided, get project from session
    if session_id:
        session = db.query(QASession).filter(
            QASession.id == session_id,
            QASession.user_id == current_user.id,
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        project_id = session.project_id
    elif project_id:
        # Verify project ownership
        from app.models.project import Project
        project = db.query(Project).filter(
            Project.id == project_id,
            Project.user_id == current_user.id,
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
    else:
        raise HTTPException(
            status_code=400,
            detail="Either project_id or session_id must be provided",
        )
    
    # Get or create session
    if not session_id:
        # Create new session
        session = QASession(
            project_id=project_id,
            user_id=current_user.id,
            title=question_data.question[:100],  # Use first 100 chars as title
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        session_id = session.id
    
    # Retrieve context using RAG
    try:
        contexts = rag_service.retrieve_context(
            question=question_data.question,
            top_k=question_data.top_k,
            project_id=project_id,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving context: {str(e)}",
        )
    
    if not contexts:
        raise HTTPException(
            status_code=404,
            detail="No relevant documents found. Please upload documents first.",
        )
    
    # Generate answer
    try:
        result = rag_service.generate_answer(
            question=question_data.question,
            contexts=contexts,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating answer: {str(e)}",
        )
    
    # Save response to database
    db_response = QAResponseModel(
        session_id=session_id,
        question=question_data.question,
        answer=result["answer"],
        citations=result["citations"],
        retrieved_chunk_ids=result["retrieved_chunks"],
        model_used=rag_service.llm.model_name if rag_service.llm else None,
    )
    db.add(db_response)
    
    # Update session timestamp
    session = db.query(QASession).filter(QASession.id == session_id).first()
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(db_response)
    
    # Format response
    return QAResponseSchema(
        id=db_response.id,
        session_id=db_response.session_id,
        question=db_response.question,
        answer=db_response.answer,
        citations=result["citations"],
        retrieved_chunk_ids=db_response.retrieved_chunk_ids or [],
        model_used=db_response.model_used,
        tokens_used=db_response.tokens_used,
        created_at=db_response.created_at,
    )


@router.get("/sessions/{session_id}/responses", response_model=List[QAResponseSchema])
def get_session_responses(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get all responses for a QA session."""
    # Verify session ownership
    session = db.query(QASession).filter(
        QASession.id == session_id,
        QASession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    responses = db.query(QAResponseModel).filter(
        QAResponseModel.session_id == session_id,
    ).order_by(QAResponseModel.created_at).all()
    
    # Convert to response schema
    result = []
    for resp in responses:
        result.append(QAResponseSchema(
            id=resp.id,
            session_id=resp.session_id,
            question=resp.question,
            answer=resp.answer,
            citations=resp.citations if resp.citations else [],
            retrieved_chunk_ids=resp.retrieved_chunk_ids or [],
            model_used=resp.model_used,
            tokens_used=resp.tokens_used,
            created_at=resp.created_at,
        ))
    
    return result

