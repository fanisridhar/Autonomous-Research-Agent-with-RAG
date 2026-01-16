"""Document parser for extracting text from various file formats."""
import fitz  # PyMuPDF
from bs4 import BeautifulSoup
import markdown
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from app.services.storage import storage_service


class DocumentParser:
    """Service for parsing documents and extracting text with metadata."""
    
    def parse_pdf(self, file_path: str) -> Dict:
        """
        Parse PDF and extract text with page-level metadata.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Dictionary with 'text', 'pages', 'metadata'
        """
        file_content = storage_service.get_file(file_path)
        doc = fitz.open(stream=file_content, filetype="pdf")
        
        pages = []
        full_text = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            
            # Store page-level information
            page_data = {
                "page_number": page_num + 1,
                "text": text,
                "char_start": len("\n".join(full_text)),
                "char_end": len("\n".join(full_text)) + len(text),
            }
            pages.append(page_data)
            full_text.append(text)
        
        # Extract metadata
        metadata = doc.metadata
        title = metadata.get("title", "") or Path(file_path).stem
        author = metadata.get("author", "")
        
        doc.close()
        
        return {
            "text": "\n".join(full_text),
            "pages": pages,
            "metadata": {
                "title": title,
                "author": author,
                "page_count": len(pages),
            },
        }
    
    def parse_html(self, file_path: str) -> Dict:
        """
        Parse HTML and extract text with structure metadata.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Dictionary with 'text', 'metadata'
        """
        file_content = storage_service.get_file(file_path)
        soup = BeautifulSoup(file_content, "html.parser")
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text(separator="\n", strip=True)
        
        # Extract metadata
        title = soup.title.string if soup.title else ""
        if not title:
            title_tag = soup.find("h1")
            title = title_tag.get_text() if title_tag else Path(file_path).stem
        
        return {
            "text": text,
            "pages": [{"page_number": 1, "text": text, "char_start": 0, "char_end": len(text)}],
            "metadata": {
                "title": title,
                "author": None,
                "page_count": 1,
            },
        }
    
    def parse_markdown(self, file_path: str) -> Dict:
        """
        Parse Markdown file.
        
        Args:
            file_path: Path to Markdown file
            
        Returns:
            Dictionary with 'text', 'metadata'
        """
        file_content = storage_service.get_file(file_path)
        text = file_content.decode("utf-8")
        
        # Try to extract title from first heading
        lines = text.split("\n")
        title = Path(file_path).stem
        for line in lines[:10]:  # Check first 10 lines
            if line.startswith("#"):
                title = line.lstrip("#").strip()
                break
        
        return {
            "text": text,
            "pages": [{"page_number": 1, "text": text, "char_start": 0, "char_end": len(text)}],
            "metadata": {
                "title": title,
                "author": None,
                "page_count": 1,
            },
        }
    
    def parse_text(self, file_path: str) -> Dict:
        """
        Parse plain text file.
        
        Args:
            file_path: Path to text file
            
        Returns:
            Dictionary with 'text', 'metadata'
        """
        file_content = storage_service.get_file(file_path)
        text = file_content.decode("utf-8")
        
        return {
            "text": text,
            "pages": [{"page_number": 1, "text": text, "char_start": 0, "char_end": len(text)}],
            "metadata": {
                "title": Path(file_path).stem,
                "author": None,
                "page_count": 1,
            },
        }
    
    def parse(self, file_path: str, document_type: str) -> Dict:
        """
        Parse document based on type.
        
        Args:
            file_path: Path to document
            document_type: Type of document (pdf, html, markdown, text)
            
        Returns:
            Parsed document data
        """
        document_type = document_type.lower()
        
        if document_type == "pdf":
            return self.parse_pdf(file_path)
        elif document_type == "html":
            return self.parse_html(file_path)
        elif document_type == "markdown":
            return self.parse_markdown(file_path)
        elif document_type == "text":
            return self.parse_text(file_path)
        else:
            raise ValueError(f"Unsupported document type: {document_type}")


document_parser = DocumentParser()

