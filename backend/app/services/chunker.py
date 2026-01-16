"""Text chunking service with overlap and metadata tracking."""
from typing import List, Dict, Optional
from app.config import settings


class Chunker:
    """Service for chunking text with overlap and preserving metadata."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
    
    def chunk_text(
        self,
        text: str,
        page_number: Optional[int] = None,
        char_offset: int = 0,
        paragraph_number: Optional[int] = None,
    ) -> List[Dict]:
        """
        Chunk text with overlap and preserve citation metadata.
        
        Args:
            text: Text to chunk
            page_number: Page number (for PDFs)
            char_offset: Character offset in original document
            paragraph_number: Paragraph number
            
        Returns:
            List of chunk dictionaries with metadata
        """
        if not text or len(text.strip()) == 0:
            return []
        
        chunks = []
        text_length = len(text)
        
        # Split by paragraphs first for better chunking
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        current_chunk = ""
        current_char_start = char_offset
        chunk_index = 0
        
        for para_idx, paragraph in enumerate(paragraphs):
            # If adding this paragraph exceeds chunk size, save current chunk
            if current_chunk and len(current_chunk) + len(paragraph) + 2 > self.chunk_size:
                # Save current chunk
                chunks.append({
                    "content": current_chunk.strip(),
                    "chunk_index": chunk_index,
                    "page_number": page_number,
                    "paragraph_number": paragraph_number if paragraph_number is not None else para_idx,
                    "char_start": current_char_start,
                    "char_end": current_char_start + len(current_chunk),
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, self.chunk_overlap)
                current_chunk = overlap_text + "\n\n" + paragraph if overlap_text else paragraph
                current_char_start = char_offset + (chunks[-1]["char_end"] - len(overlap_text)) if overlap_text else char_offset
                chunk_index += 1
            
            # If single paragraph exceeds chunk size, split it
            elif len(paragraph) > self.chunk_size:
                # First, save current chunk if exists
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "chunk_index": chunk_index,
                        "page_number": page_number,
                        "paragraph_number": paragraph_number if paragraph_number is not None else para_idx,
                        "char_start": current_char_start,
                        "char_end": current_char_start + len(current_chunk),
                    })
                    chunk_index += 1
                
                # Split large paragraph
                para_chunks = self._split_large_text(
                    paragraph,
                    chunk_index,
                    page_number,
                    paragraph_number if paragraph_number is not None else para_idx,
                    current_char_start if not current_chunk else chunks[-1]["char_end"] - self.chunk_overlap,
                )
                chunks.extend(para_chunks)
                chunk_index += len(para_chunks)
                
                # Start new chunk with overlap
                if para_chunks:
                    current_chunk = self._get_overlap_text(para_chunks[-1]["content"], self.chunk_overlap)
                    current_char_start = para_chunks[-1]["char_end"] - len(current_chunk) if current_chunk else para_chunks[-1]["char_end"]
                else:
                    current_chunk = ""
                    current_char_start = char_offset
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                    current_char_start = char_offset
        
        # Save last chunk
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "page_number": page_number,
                "paragraph_number": paragraph_number if paragraph_number is not None else len(paragraphs) - 1,
                "char_start": current_char_start,
                "char_end": current_char_start + len(current_chunk),
            })
        
        return chunks
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Extract overlap text from end of text."""
        if len(text) <= overlap_size:
            return text
        # Try to overlap at sentence boundary
        overlap_text = text[-overlap_size:]
        # Find last sentence boundary
        last_period = overlap_text.rfind(".")
        last_newline = overlap_text.rfind("\n")
        split_pos = max(last_period, last_newline)
        if split_pos > overlap_size // 2:  # Only if reasonable split found
            return overlap_text[split_pos + 1:].strip()
        return overlap_text.strip()
    
    def _split_large_text(
        self,
        text: str,
        start_chunk_index: int,
        page_number: Optional[int],
        paragraph_number: Optional[int],
        char_offset: int,
    ) -> List[Dict]:
        """Split large text into multiple chunks."""
        chunks = []
        text_length = len(text)
        current_pos = 0
        chunk_index = start_chunk_index
        
        while current_pos < text_length:
            chunk_end = min(current_pos + self.chunk_size, text_length)
            
            # Try to split at sentence boundary
            if chunk_end < text_length:
                # Look for sentence boundary in last 20% of chunk
                search_start = int(chunk_end - self.chunk_size * 0.2)
                period_pos = text.rfind(".", search_start, chunk_end)
                newline_pos = text.rfind("\n", search_start, chunk_end)
                
                split_pos = max(period_pos, newline_pos)
                if split_pos > search_start:
                    chunk_end = split_pos + 1
            
            chunk_text = text[current_pos:chunk_end].strip()
            if chunk_text:
                chunks.append({
                    "content": chunk_text,
                    "chunk_index": chunk_index,
                    "page_number": page_number,
                    "paragraph_number": paragraph_number,
                    "char_start": char_offset + current_pos,
                    "char_end": char_offset + chunk_end,
                })
                chunk_index += 1
            
            # Move to next chunk with overlap
            current_pos = chunk_end - self.chunk_overlap if chunk_end < text_length else chunk_end
        
        return chunks


chunker = Chunker()

