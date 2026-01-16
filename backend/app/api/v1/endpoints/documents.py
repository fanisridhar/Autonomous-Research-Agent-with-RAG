"""Document endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.document import Document, DocumentStatus, DocumentType
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentChunkResponse
from app.services.auth import get_current_active_user
from app.services.storage import storage_service
from app.workers.tasks import process_document_task
import mimetypes
from pathlib import Path

router = APIRouter()


def get_document_type(filename: str, mime_type: str) -> DocumentType:
    """Determine document type from filename and MIME type."""
    ext = Path(filename).suffix.lower()
    
    if ext == ".pdf" or mime_type == "application/pdf":
        return DocumentType.PDF
    elif ext in [".html", ".htm"] or mime_type == "text/html":
        return DocumentType.HTML
    elif ext in [".md", ".markdown"] or mime_type == "text/markdown":
        return DocumentType.MARKDOWN
    elif ext == ".txt" or mime_type == "text/plain":
        return DocumentType.TEXT
    elif ext == ".docx" or mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return DocumentType.DOCX
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}",
        )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    title: Optional[str] = Form(None),
    source_url: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a document for processing."""
    # Validate project ownership
    from app.models.project import Project
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Read file content
    content = await file.read()
    file_size = len(content)
    
    # Check file size limit (50MB default)
    max_size = 50 * 1024 * 1024  # 50MB
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {max_size / 1024 / 1024}MB",
        )
    
    # Determine document type
    try:
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        doc_type = get_document_type(file.filename, mime_type)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error determining file type: {str(e)}")
    
    # Save file
    try:
        file_path = storage_service.save_file(content, file.filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")
    
    # Create document record
    db_document = Document(
        project_id=project_id,
        user_id=current_user.id,
        filename=file_path,
        original_filename=file.filename,
        file_path=file_path,
        file_size=file_size,
        mime_type=mime_type,
        document_type=doc_type,
        title=title or Path(file.filename).stem,
        source_url=source_url,
        status=DocumentStatus.UPLOADED,
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Trigger background processing
    try:
        process_document_task.delay(db_document.id)
    except Exception as e:
        # Log error but don't fail the upload
        print(f"Error triggering background task: {str(e)}")
    
    return db_document


@router.get("", response_model=List[DocumentResponse])
def list_documents(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """List documents. Optionally filter by project."""
    query = db.query(Document).filter(Document.user_id == current_user.id)
    if project_id:
        query = query.filter(Document.project_id == project_id)
    documents = query.order_by(Document.created_at.desc()).all()
    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get a specific document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/chunks", response_model=List[DocumentChunkResponse])
def get_document_chunks(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Get chunks for a specific document."""
    # Verify document ownership
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    from app.models.document import DocumentChunk
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == document_id,
    ).order_by(DocumentChunk.chunk_index).all()
    return chunks


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a document."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id,
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file from storage
    storage_service.delete_file(document.file_path)
    
    # Delete document (cascade will delete chunks)
    db.delete(document)
    db.commit()
    return None

