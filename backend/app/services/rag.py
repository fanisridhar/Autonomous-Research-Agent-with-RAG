"""RAG service for question answering with citations."""
from typing import List, Dict, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import json
from app.config import settings
from app.services.vector_db import vector_db_service
from app.services.embeddings import embedding_service


class RAGService:
    """Service for RAG-based question answering with citation tracking."""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model_name=settings.OPENAI_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
                temperature=0.0,
                max_tokens=settings.MAX_TOKENS,
            )
        else:
            self.llm = None
    
    def retrieve_context(self, question: str, top_k: int = None, project_id: Optional[int] = None) -> List[Dict]:
        """
        Retrieve relevant context chunks for a question.
        
        Args:
            question: User question
            top_k: Number of chunks to retrieve
            project_id: Optional project ID to filter documents
            
        Returns:
            List of context dictionaries with metadata
        """
        top_k = top_k or settings.TOP_K_RETRIEVAL
        
        # Build filter if project_id provided
        filter_dict = None
        if project_id:
            filter_dict = {"project_id": project_id}
        
        # Query vector database
        # ChromaDB will use the embedding function to embed the query text automatically
        results = vector_db_service.query(
            query_texts=[question],
            n_results=top_k,
            filter_dict=filter_dict,
        )
        
        # Format results
        contexts = []
        for i, (doc_id, doc_text, metadata, distance) in enumerate(zip(
            results["ids"],
            results["documents"],
            results["metadatas"],
            results["distances"],
        )):
            contexts.append({
                "chunk_id": doc_id,
                "content": doc_text,
                "metadata": metadata,
                "score": 1 - distance if distance else None,  # Convert distance to similarity
                "rank": i + 1,
            })
        
        return contexts
    
    def generate_answer(
        self,
        question: str,
        contexts: List[Dict],
    ) -> Dict:
        """
        Generate answer with citations from retrieved contexts.
        
        Args:
            question: User question
            contexts: List of retrieved context dictionaries
            
        Returns:
            Dictionary with 'answer', 'citations', 'sources'
        """
        if not self.llm:
            raise ValueError("LLM not configured")
        
        # Build context string with source information
        context_parts = []
        source_refs = []
        
        for i, ctx in enumerate(contexts):
            source_num = i + 1
            metadata = ctx.get("metadata", {})
            doc_name = metadata.get("document_filename", "Unknown")
            page = metadata.get("page_number", "")
            para = metadata.get("paragraph_number", "")
            
            # Build source reference
            source_ref = f"[{source_num}]"
            source_info = {
                "source_num": source_num,
                "chunk_id": ctx["chunk_id"],
                "document_id": metadata.get("document_id"),
                "document_filename": doc_name,
                "page_number": page,
                "paragraph_number": para,
                "char_start": metadata.get("char_start"),
                "char_end": metadata.get("char_end"),
                "snippet": ctx["content"][:200] + "..." if len(ctx["content"]) > 200 else ctx["content"],
            }
            source_refs.append(source_info)
            
            # Build context text
            context_text = f"{source_ref} {ctx['content']}"
            context_parts.append(context_text)
        
        context_str = "\n\n".join(context_parts)
        
        # Build prompt
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a research assistant that answers questions using provided source documents. 
Always cite your sources using [1], [2], etc. format when referencing information from the provided contexts.
Be precise and factual. If information is not in the contexts, say so clearly.

After your answer, provide a SOURCES section listing all citations used in the format:
SOURCES:
[1] Document: filename.pdf, Page: X, Paragraph: Y
[2] Document: filename2.pdf, Page: A, Paragraph: B"""),
            HumanMessage(content=f"""Contexts:

{context_str}

Question: {question}

Provide a comprehensive answer with citations. Include a SOURCES section at the end.""")
        ])
        
        # Generate answer
        messages = prompt_template.format_messages()
        response = self.llm.invoke(messages)
        answer_text = response.content
        
        # Parse answer and extract citations
        answer, citations = self._parse_answer_with_citations(answer_text, source_refs)
        
        return {
            "answer": answer,
            "citations": citations,
            "sources": source_refs,
            "retrieved_chunks": [ctx["chunk_id"] for ctx in contexts],
        }
    
    def _parse_answer_with_citations(self, answer_text: str, source_refs: List[Dict]) -> tuple[str, List[Dict]]:
        """
        Parse answer text and extract citations.
        
        Args:
            answer_text: Generated answer text
            source_refs: List of source reference dictionaries
            
        Returns:
            Tuple of (clean_answer, citations_list)
        """
        # Split answer and sources section
        if "SOURCES:" in answer_text or "Sources:" in answer_text:
            parts = answer_text.split("SOURCES:", 1)
            if len(parts) == 1:
                parts = answer_text.split("Sources:", 1)
            answer = parts[0].strip()
            sources_text = parts[1].strip() if len(parts) > 1 else ""
        else:
            answer = answer_text
            sources_text = ""
        
        # Extract citations from answer (find [1], [2], etc.)
        citations = []
        import re
        citation_pattern = r'\[(\d+)\]'
        matches = re.finditer(citation_pattern, answer)
        
        for match in matches:
            source_num = int(match.group(1))
            # Find corresponding source
            source = next((s for s in source_refs if s["source_num"] == source_num), None)
            if source:
                citations.append({
                    "source_num": source_num,
                    "chunk_id": source["chunk_id"],
                    "document_id": source["document_id"],
                    "document_filename": source["document_filename"],
                    "page_number": source["page_number"],
                    "paragraph_number": source["paragraph_number"],
                    "char_start": source["char_start"],
                    "char_end": source["char_end"],
                    "snippet": source["snippet"],
                })
        
        # Remove duplicate citations
        seen = set()
        unique_citations = []
        for cit in citations:
            key = cit["chunk_id"]
            if key not in seen:
                seen.add(key)
                unique_citations.append(cit)
        
        return answer, unique_citations


rag_service = RAGService()

