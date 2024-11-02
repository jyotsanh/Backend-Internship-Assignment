"""
Test PDF upload endpoint

This test module contains tests for the PDF upload endpoint. It
tests for successful upload of a PDF file and for an error when
uploading a file of an unsupported format.
"""

import pytest
from httpx._client import AsyncClient
from fastapi import status
from main import app
import os


@pytest.mark.asyncio
async def test_upload_pdf_success():
    """
    Test successful upload of a PDF file
    """
    # Path to a sample PDF file
    pdf_path = "tests/file.pdf"
    
    # Only create a temporary PDF file if the real one doesn't exist
    if not os.path.exists(pdf_path):
        print(f"Creating temporary PDF file at {pdf_path}")
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

    async with AsyncClient(app=app, base_url="https://backend-internship-assignment.onrender.com") as client:
        # Open the sample PDF file in binary mode and upload it
        with open(pdf_path, "rb") as pdf_file:
            files = {"file": ("sample.pdf", pdf_file, "application/pdf")}
            response = await client.post("/upload-pdf/", files=files)

    # Check response for successful upload
    assert response.status_code == status.HTTP_200_OK
    print(response.json())
    assert response.json()["message"] == "PDF uploaded successfully"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_upload_unsupported_file_format():
    """
    Test error on uploading a file of an unsupported format
    """
    # Path to a sample text file
    text_path = "tests/sample.txt"
    
    # Create a temporary text file for testing
    with open(text_path, "w") as f:
        f.write("This is a test text file.")

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Open the sample text file and attempt to upload it
        with open(text_path, "rb") as text_file:
            files = {"file": ("sample.txt", text_file, "text/plain")}
            response = await client.post("/upload-pdf/", files=files)

    # Check response for error on unsupported file type
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "File must be a PDF."

