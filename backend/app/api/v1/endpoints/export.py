"""Export endpoints for generating summaries and references."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.qa_session import QASession, QAResponse
from app.services.auth import get_current_active_user
from datetime import datetime

router = APIRouter()


@router.get("/summary/{project_id}")
def export_summary(
    project_id: int,
    format: str = "markdown",  # markdown or bibtex
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Export project summary with citations."""
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all documents
    from app.models.document import Document
    documents = db.query(Document).filter(Document.project_id == project_id).all()
    
    # Get all QA sessions and responses
    sessions = db.query(QASession).filter(QASession.project_id == project_id).all()
    all_responses = []
    for session in sessions:
        responses = db.query(QAResponse).filter(QAResponse.session_id == session.id).all()
        all_responses.extend(responses)
    
    if format == "markdown":
        return _generate_markdown_summary(project, documents, all_responses)
    elif format == "bibtex":
        return _generate_bibtex(project, documents)
    else:
        raise HTTPException(status_code=400, detail="Unsupported format. Use 'markdown' or 'bibtex'")


def _generate_markdown_summary(project: Project, documents: list, responses: list) -> dict:
    """Generate Markdown summary."""
    lines = []
    
    # Title
    lines.append(f"# {project.name}")
    lines.append("")
    if project.description:
        lines.append(project.description)
        lines.append("")
    
    # Documents section
    lines.append("## Documents")
    lines.append("")
    for doc in documents:
        lines.append(f"- **{doc.title or doc.original_filename}**")
        if doc.author:
            lines.append(f"  - Author: {doc.author}")
        if doc.page_count:
            lines.append(f"  - Pages: {doc.page_count}")
        if doc.source_url:
            lines.append(f"  - Source: {doc.source_url}")
        lines.append(f"  - Uploaded: {doc.created_at.strftime('%Y-%m-%d')}")
        lines.append("")
    
    # QA Summary
    if responses:
        lines.append("## Research Questions and Answers")
        lines.append("")
        
        # Group responses by session
        sessions_dict = {}
        db = SessionLocal()
        for resp in responses:
            if resp.session_id not in sessions_dict:
                session = db.query(QASession).filter(QASession.id == resp.session_id).first()
                sessions_dict[resp.session_id] = session
        db.close()
        
        current_session = None
        for resp in responses:
            session = sessions_dict.get(resp.session_id)
            if session and session.id != current_session:
                if current_session is not None:
                    lines.append("")
                current_session = session.id if session else None
                if session and session.title:
                    lines.append(f"### {session.title}")
                    lines.append("")
            
            lines.append(f"**Q:** {resp.question}")
            lines.append("")
            lines.append(f"**A:** {resp.answer}")
            lines.append("")
            
            # Citations
            if resp.citations:
                lines.append("**Sources:**")
                for cit in resp.citations:
                    page_str = f", Page {cit['page_number']}" if cit.get('page_number') else ""
                    para_str = f", Paragraph {cit['paragraph_number']}" if cit.get('paragraph_number') else ""
                    lines.append(f"- [{cit.get('document_filename', 'Unknown')}]{page_str}{para_str}")
                    if cit.get('snippet'):
                        lines.append(f"  > {cit['snippet'][:200]}...")
                lines.append("")
    
    # Bibliography
    lines.append("## Bibliography")
    lines.append("")
    for doc in documents:
        citation_line = f"- "
        if doc.author:
            citation_line += f"{doc.author}. "
        citation_line += f"*{doc.title or doc.original_filename}*"
        if doc.source_url:
            citation_line += f". {doc.source_url}"
        citation_line += f" (Accessed: {doc.created_at.strftime('%Y-%m-%d')})"
        lines.append(citation_line)
    
    content = "\n".join(lines)
    
    return {
        "content": content,
        "filename": f"{project.name}_summary.md",
        "mime_type": "text/markdown",
    }


def _generate_bibtex(project: Project, documents: list) -> dict:
    """Generate BibTeX references."""
    lines = []
    
    for doc in documents:
        # Generate BibTeX key
        key_parts = []
        if doc.author:
            # Use first author's last name
            author_parts = doc.author.split()
            if author_parts:
                key_parts.append(author_parts[-1].lower())
        
        title_words = (doc.title or doc.original_filename).split()[:3]
        key_parts.extend([w.lower()[:4] for w in title_words])
        bib_key = "".join(key_parts)[:20] + str(doc.id)
        
        # Determine entry type
        entry_type = "misc"  # Default
        if doc.document_type == "pdf":
            entry_type = "article"  # or "book" depending on content
        
        lines.append(f"@misc{{{bib_key},")
        if doc.title:
            lines.append(f"  title = {{{doc.title}}},")
        if doc.author:
            lines.append(f"  author = {{{doc.author}}},")
        if doc.source_url:
            lines.append(f"  url = {{{doc.source_url}}},")
        lines.append(f"  note = {{Uploaded: {doc.created_at.strftime('%Y-%m-%d')}}},")
        lines.append(f"}}")
        lines.append("")
    
    content = "\n".join(lines)
    
    return {
        "content": content,
        "filename": f"{project.name}_references.bib",
        "mime_type": "text/x-bibtex",
    }

