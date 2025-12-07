# src/utils/storage.py
"""
Object Storage Client (MinIO/S3)
================================
Handles uploading/downloading files to MinIO

Why not save files on disk?
- Scalable (can store TB of data)
- Reliable (built-in redundancy)
- S3-compatible (easy to migrate to AWS)
- Works same in dev and production
"""

from minio import Minio
from minio.error import S3Error
from src.config import get_settings
import io
from typing import BinaryIO, Optional, List
import logging
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
settings = get_settings()

class StorageClient:
    """MinIO/S3 storage client for file management"""
    
    def __init__(self):
        """
        Initialize MinIO client
        
        Connects to MinIO using settings from .env:
        - MINIO_ENDPOINT: localhost:9000
        - MINIO_ACCESS_KEY: minioadmin
        - MINIO_SECRET_KEY: minioadmin
        """
        logger.info(f"Connecting to MinIO at {settings.MINIO_ENDPOINT}")
        
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE  # False = HTTP, True = HTTPS
        )
        
        self.bucket_name = settings.MINIO_BUCKET
        self._ensure_bucket_exists()
        
        logger.info(f"✅ Connected to MinIO, using bucket: {self.bucket_name}")
    
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"Created bucket: {self.bucket_name}")
            else:
                logger.debug(f"Bucket already exists: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Error with bucket: {e}")
            raise
    
    def upload_file(
        self,
        file_data: BinaryIO,
        object_name: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Upload file to MinIO
        
        Args:
            file_data: File-like object (bytes)
            object_name: Path in bucket (e.g., "meetings/abc123.wav")
            content_type: MIME type (e.g., "audio/wav")
        
        Returns:
            Full path: "meeting-audio/meetings/abc123.wav"
        
        Example:
            with open("meeting.wav", "rb") as f:
                path = storage.upload_file(f, "meetings/test.wav", "audio/wav")
        """
        try:
            # Get file size
            file_data.seek(0, 2)  # Seek to end
            file_size = file_data.tell()
            file_data.seek(0)  # Seek back to start
            
            logger.info(f"Uploading {object_name} ({file_size} bytes)")
            
            # Upload to MinIO
            self.client.put_object(
                self.bucket_name,
                object_name,
                file_data,
                file_size,
                content_type=content_type
            )
            
            full_path = f"{self.bucket_name}/{object_name}"
            logger.info(f"✅ Uploaded: {full_path}")
            
            return full_path
            
        except S3Error as e:
            logger.error(f"Upload failed: {e}")
            raise Exception(f"Failed to upload file: {e}")
    
    def download_file(self, object_name: str) -> bytes:
        """
        Download file from MinIO
        
        Args:
            object_name: Path in bucket (e.g., "meetings/abc123.wav")
        
        Returns:
            File content as bytes
        
        Example:
            data = storage.download_file("meetings/test.wav")
            with open("local_file.wav", "wb") as f:
                f.write(data)
        """
        try:
            logger.info(f"Downloading {object_name}")
            
            response = self.client.get_object(self.bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"✅ Downloaded: {object_name} ({len(data)} bytes)")
            return data
            
        except S3Error as e:
            logger.error(f"Download failed: {e}")
            raise Exception(f"Failed to download file: {e}")
    
    def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        """
        Generate presigned URL for temporary access to a file.
        
        Args:
            object_name: Path to object in bucket
            expires: Expiration time in seconds (default: 1 hour)
    
        Returns:
            Presigned URL string
        """
        try:
            logger.info(f"Generating presigned URL for {object_name}")
            
            url = self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=timedelta(seconds=expires)  # ✅ Fixed
            )
        
            logger.info(f"✅ Generated presigned URL (expires in {expires}s)")
            return url
        
        except Exception as e:
            logger.error(f"❌ Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(self, object_name: str) -> bool:
        """
        Delete file from storage
        
        Args:
            object_name: Path in bucket
        
        Returns:
            True if successful
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"✅ Deleted: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def list_files(self, prefix: str = "") -> List[str]:
        """
        List files in bucket
        
        Args:
            prefix: Filter by prefix (e.g., "meetings/" shows only meeting files)
        
        Returns:
            List of file paths
        
        Example:
            files = storage.list_files("meetings/")
            # Returns: ["meetings/abc.wav", "meetings/def.wav", ...]
        """
        try:
            objects = self.client.list_objects(
                self.bucket_name,
                prefix=prefix,
                recursive=True
            )
            files = [obj.object_name for obj in objects]
            logger.info(f"Listed {len(files)} files with prefix '{prefix}'")
            return files
        except S3Error as e:
            logger.error(f"List failed: {e}")
            return []
    
    def file_exists(self, object_name: str) -> bool:
        """Check if file exists"""
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False

# ============================================
# SINGLETON INSTANCE
# ============================================

_storage_client: Optional[StorageClient] = None

def get_storage_client() -> StorageClient:
    """
    Get storage client (singleton pattern)
    
    Usage:
        from src.utils.storage import get_storage_client
        storage = get_storage_client()
        storage.upload_file(...)
    """
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client