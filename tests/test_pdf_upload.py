"""
Test PDF upload endpoint with proper async configuration.
"""

import pytest
from httpx import AsyncClient
from fastapi import status
from main import app, MAX_FILE_SIZE
import os
from pathlib import Path
import shutil
from datetime import datetime
import asyncio
import logging
from typing import AsyncGenerator

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test constants
TEST_DIR = Path("tests")
UPLOAD_DIR = Path("pdf_uploads")
SAMPLE_PDF_SIZE = 2048  # 2KB

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
async def setup_cleanup():
    """Setup test environment and cleanup after tests."""
    # Create test directories
    TEST_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    yield
    
    # Cleanup test files
    try:
        if TEST_DIR.exists():
            shutil.rmtree(TEST_DIR)
        if UPLOAD_DIR.exists():
            shutil.rmtree(UPLOAD_DIR)
    except Exception as e:
        logger.warning(f"Cleanup error: {str(e)}")

@pytest.fixture
async def sample_pdf_path():
    """Create a sample PDF file for testing."""
    pdf_path = TEST_DIR / "sample.pdf"
    
    # Create a minimal valid PDF file
    minimal_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f\n0000000009 00000 n\n0000000052 00000 n\n0000000101 00000 n\n"
        b"trailer<</Size 4/Root 1 0 R>>\n"
        b"startxref\n183\n"
        b"%%EOF\n"
    )
    
    with open(pdf_path, "wb") as f:
        f.write(minimal_pdf)
    
    yield pdf_path
    
    # Cleanup
    if pdf_path.exists():
        pdf_path.unlink()

@pytest.fixture
async def large_pdf_path():
    """Create a PDF file larger than the maximum allowed size."""
    pdf_path = TEST_DIR / "large.pdf"
    
    # Create a large PDF file
    with open(pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n" * (MAX_FILE_SIZE + 1024))
    
    yield pdf_path
    
    # Cleanup
    if pdf_path.exists():
        pdf_path.unlink()

@pytest.fixture
async def client():
    """Create an async client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

async def test_upload_pdf_success(client: AsyncClient, sample_pdf_path: Path):
    """Test successful upload of a valid PDF file."""
    with open(sample_pdf_path, "rb") as pdf_file:
        files = {"file": ("test.pdf", pdf_file, "application/pdf")}
        response = await client.post("/upload-pdf/", files=files)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["message"] == "PDF uploaded successfully"
    assert "id" in response.json()
    assert "filename" in response.json()

async def test_upload_unsupported_file_format(client: AsyncClient):
    """Test error on uploading a file with unsupported format."""
    text_path = TEST_DIR / "sample.txt"
    
    with open(text_path, "w") as f:
        f.write("This is a test text file.")

    with open(text_path, "rb") as text_file:
        files = {"file": ("sample.txt", text_file, "text/plain")}
        response = await client.post("/upload-pdf/", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid file type" in response.json()["detail"]

async def test_upload_large_pdf(client: AsyncClient, large_pdf_path: Path):
    """Test error on uploading a PDF file larger than the maximum allowed size."""
    with open(large_pdf_path, "rb") as pdf_file:
        files = {"file": ("large.pdf", pdf_file, "application/pdf")}
        response = await client.post("/upload-pdf/", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "File too large" in response.json()["detail"]

async def test_upload_empty_pdf(client: AsyncClient):
    """Test error on uploading an empty PDF file."""
    empty_pdf_path = TEST_DIR / "empty.pdf"
    
    with open(empty_pdf_path, "wb") as f:
        f.write(b"")

    with open(empty_pdf_path, "rb") as pdf_file:
        files = {"file": ("empty.pdf", pdf_file, "application/pdf")}
        response = await client.post("/upload-pdf/", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "empty" in response.json()["detail"].lower()

async def test_upload_corrupted_pdf(client: AsyncClient, sample_pdf_path: Path):
    """Test error on uploading a corrupted PDF file."""
    corrupted_pdf_path = TEST_DIR / "corrupted.pdf"
    shutil.copy(sample_pdf_path, corrupted_pdf_path)
    
    with open(corrupted_pdf_path, "ab") as f:
        f.write(b"corrupted content")

    with open(corrupted_pdf_path, "rb") as pdf_file:
        files = {"file": ("corrupted.pdf", pdf_file, "application/pdf")}
        response = await client.post("/upload-pdf/", files=files)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error processing PDF file" in response.json()["detail"]

async def test_concurrent_uploads(client: AsyncClient, sample_pdf_path: Path):
    """Test multiple concurrent PDF uploads."""
    tasks = []
    for i in range(3):  # Test 3 concurrent uploads
        with open(sample_pdf_path, "rb") as pdf_file:
            files = {"file": (f"test_{i}.pdf", pdf_file, "application/pdf")}
            tasks.append(client.post("/upload-pdf/", files=files))
    
    responses = await asyncio.gather(*tasks)
    
    # Check all uploads were successful
    for response in responses:
        assert response.status_code == status.HTTP_201_CREATED
        assert "id" in response.json()

async def test_upload_without_file(client: AsyncClient):
    """Test error when no file is provided."""
    response = await client.post("/upload-pdf/")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

async def test_upload_with_invalid_mime_type(client: AsyncClient, sample_pdf_path: Path):
    """Test error when uploading a PDF with incorrect MIME type."""
    with open(sample_pdf_path, "rb") as pdf_file:
        files = {"file": ("test.pdf", pdf_file, "application/octet-stream")}
        response = await client.post("/upload-pdf/", files=files)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid file type" in response.json()["detail"]