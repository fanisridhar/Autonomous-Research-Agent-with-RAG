"""Celery tasks for background processing."""
from app.workers.celery_app import celery_app
from app.database import SessionLocal
from app.models.document import Document, DocumentStatus, DocumentChunk
from app.services.document_parser import document_parser
from app.services.chunker import chunker
from app.services.embeddings import embedding_service
from app.services.vector_db import vector_db_service
from sqlalchemy.orm import Session


def get_db_session() -> Session:
    """Get database session for worker tasks."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@celery_app.task(name="process_document", bind=True, max_retries=3)
def process_document_task(self, document_id: int):
    """
    Process a document: parse, chunk, embed, and index.
    
    Args:
        document_id: ID of document to process
    """
    db = SessionLocal()
    try:
        # Get document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        # Update status to processing
        document.status = DocumentStatus.PROCESSING
        db.commit()
        
        try:
            # Parse document
            parsed_data = document_parser.parse(
                file_path=document.file_path,
                document_type=document.document_type.value,
            )
            
            # Update document metadata
            if parsed_data.get("metadata"):
                meta = parsed_data["metadata"]
                if meta.get("title"):
                    document.title = meta["title"]
                if meta.get("author"):
                    document.author = meta["author"]
                if meta.get("page_count"):
                    document.page_count = meta["page_count"]
            
            # Get full text and pages
            full_text = parsed_data["text"]
            pages = parsed_data.get("pages", [])
            
            # Chunk document
            all_chunks = []
            
            if pages:
                # Process page by page to preserve page-level citations
                for page_data in pages:
                    page_chunks = chunker.chunk_text(
                        text=page_data["text"],
                        page_number=page_data.get("page_number"),
                        char_offset=page_data.get("char_start", 0),
                    )
                    all_chunks.extend(page_chunks)
            else:
                # Process entire document
                all_chunks = chunker.chunk_text(text=full_text)
            
            # Generate embeddings
            chunk_texts = [chunk["content"] for chunk in all_chunks]
            embeddings = embedding_service.embed_documents(chunk_texts)
            
            # Store chunks in database and vector DB
            documents_for_vector_db = []
            metadatas_for_vector_db = []
            ids_for_vector_db = []
            
            for i, chunk_data in enumerate(all_chunks):
                # Create chunk in database
                db_chunk = DocumentChunk(
                    document_id=document.id,
                    content=chunk_data["content"],
                    chunk_index=chunk_data["chunk_index"],
                    page_number=chunk_data.get("page_number"),
                    paragraph_number=chunk_data.get("paragraph_number"),
                    char_start=chunk_data.get("char_start"),
                    char_end=chunk_data.get("char_end"),
                )
                db.add(db_chunk)
                db.flush()  # Get chunk ID
                
                # Prepare for vector DB
                chunk_id = f"chunk_{db_chunk.id}"
                db_chunk.embedding_id = chunk_id
                db_chunk.embedding_model = embedding_service.embeddings.model if embedding_service.embeddings else None
                
                # Build metadata for vector DB
                metadata = {
                    "chunk_id": str(db_chunk.id),
                    "document_id": document.id,
                    "document_filename": document.original_filename,
                    "project_id": document.project_id,
                    "page_number": chunk_data.get("page_number"),
                    "paragraph_number": chunk_data.get("paragraph_number"),
                    "char_start": chunk_data.get("char_start"),
                    "char_end": chunk_data.get("char_end"),
                    "chunk_index": chunk_data["chunk_index"],
                }
                
                documents_for_vector_db.append(chunk_data["content"])
                metadatas_for_vector_db.append(metadata)
                ids_for_vector_db.append(chunk_id)
            
            # Add to vector DB
            vector_db_service.add_documents(
                documents=documents_for_vector_db,
                metadatas=metadatas_for_vector_db,
                ids=ids_for_vector_db,
            )
            
            # Update document status
            document.status = DocumentStatus.INDEXED
            from datetime import datetime
            document.indexed_at = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            # Update status to failed
            document.status = DocumentStatus.FAILED
            document.processing_error = str(e)
            db.commit()
            raise
        
    except Exception as e:
        # Retry task
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()

