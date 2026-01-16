"""Storage service for handling file uploads (local filesystem or S3)."""
import os
import uuid
from pathlib import Path
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError
from app.config import settings


class StorageService:
    """Service for storing and retrieving files."""
    
    def __init__(self):
        self.storage_type = settings.STORAGE_TYPE
        if self.storage_type == "s3":
            self.s3_client = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION,
            )
            self.bucket_name = settings.AWS_S3_BUCKET
        else:
            # Local filesystem storage
            self.storage_path = Path(settings.STORAGE_PATH)
            self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, folder: str = "documents") -> str:
        """
        Save file and return the file path or S3 key.
        
        Args:
            file_content: File content as bytes
            filename: Original filename
            folder: Folder/subdirectory name
            
        Returns:
            File path (local) or S3 key
        """
        # Generate unique filename
        file_ext = Path(filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        
        if self.storage_type == "s3":
            s3_key = f"{folder}/{unique_filename}"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
            )
            return s3_key
        else:
            # Local storage
            folder_path = self.storage_path / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            file_path = folder_path / unique_filename
            file_path.write_bytes(file_content)
            return str(file_path.relative_to(self.storage_path))
    
    def get_file(self, file_path: str) -> bytes:
        """
        Retrieve file content.
        
        Args:
            file_path: File path (local) or S3 key
            
        Returns:
            File content as bytes
        """
        if self.storage_type == "s3":
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_path)
            return response["Body"].read()
        else:
            full_path = self.storage_path / file_path
            return full_path.read_bytes()
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file.
        
        Args:
            file_path: File path (local) or S3 key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.storage_type == "s3":
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            else:
                full_path = self.storage_path / file_path
                if full_path.exists():
                    full_path.unlink()
            return True
        except Exception:
            return False
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get presigned URL for file access (S3) or local path.
        
        Args:
            file_path: File path or S3 key
            expires_in: URL expiration in seconds (S3 only)
            
        Returns:
            URL string or None
        """
        if self.storage_type == "s3":
            try:
                url = self.s3_client.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self.bucket_name, "Key": file_path},
                    ExpiresIn=expires_in,
                )
                return url
            except ClientError:
                return None
        else:
            # For local storage, return relative path (frontend will handle)
            return f"/api/v1/files/{file_path}"


storage_service = StorageService()

