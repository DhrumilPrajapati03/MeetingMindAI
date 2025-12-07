# scripts/test_storage.py
"""Test MinIO storage client"""

import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.storage import get_storage_client
import io
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_storage():
    """Test storage operations"""
    logger.info("=" * 50)
    logger.info("Testing Storage Client")
    logger.info("=" * 50)
    
    storage = get_storage_client()
    
    # Test 1: Upload
    logger.info("\n1. Testing upload...")
    test_data = b"Hello, this is a test file!"
    file_obj = io.BytesIO(test_data)
    path = storage.upload_file(file_obj, "test/hello.txt", "text/plain")
    logger.info(f"   ✅ Uploaded: {path}")
    
    # Test 2: Download
    logger.info("\n2. Testing download...")
    downloaded = storage.download_file("test/hello.txt")
    assert downloaded == test_data, "Downloaded data doesn't match!"
    logger.info(f"   ✅ Downloaded: {len(downloaded)} bytes")
    
    # Test 3: List files
    logger.info("\n3. Testing list files...")
    files = storage.list_files("test/")
    logger.info(f"   ✅ Found {len(files)} files: {files}")
    
    # Test 4: Presigned URL
    logger.info("\n4. Testing presigned URL...")
    url = storage.get_presigned_url("test/hello.txt")
    logger.info(f"   ✅ URL: {url[:50]}...")
    
    # Test 5: Delete
    logger.info("\n5. Testing delete...")
    success = storage.delete_file("test/hello.txt")
    logger.info(f"   ✅ Deleted: {success}")
    
    logger.info("\n" + "=" * 50)
    logger.info("✅ All storage tests passed!")
    logger.info("=" * 50)

if __name__ == "__main__":
    try:
        test_storage()
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        sys.exit(1)