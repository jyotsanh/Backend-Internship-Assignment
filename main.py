from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import fitz  # PyMuPDF
from pathlib import Path
import os
import random
import aiofiles
import hashlib
from typing import Optional
import logging
from functools import lru_cache

# Local imports
from database.config import SessionLocal
from database.models import PDFDocument
from websocket.question_answer import router as ws_router  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(ws_router)

# Constants
UPLOAD_DIRECTORY = Path("pdf_uploads")
UPLOAD_DIRECTORY.mkdir(exist_ok=True)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB limit
ALLOWED_MIME_TYPES = {'application/pdf'}
CHUNK_SIZE = 8192  # Optimal chunk size for file operations

class PDFProcessor:
    def __init__(self):
        self.text_cache = {}

    @lru_cache(maxsize=100)
    def get_file_hash(self, file_content: bytes) -> str:
        return hashlib.sha256(file_content).hexdigest()

    async def process_pdf(self, file_content: bytes) -> str:
        """Process PDF content and extract text with caching."""
        file_hash = self.get_file_hash(file_content)
        
        if file_hash in self.text_cache:
            return self.text_cache[file_hash]

        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            pdf_text = ""
            for page in doc:
                pdf_text += page.get_text()
            doc.close()
            
            self.text_cache[file_hash] = pdf_text
            return pdf_text
        except Exception as e:
            logger.error(f"PDF processing error: {str(e)}")
            raise HTTPException(status_code=500, detail="Error processing PDF file")

pdf_processor = PDFProcessor()

async def validate_pdf(file: UploadFile) -> None:
    """Validate PDF file before processing."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Check file size
    first_chunk = await file.read(MAX_FILE_SIZE + 1)
    await file.seek(0)  # Reset file pointer
    
    if len(first_chunk) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

async def save_file(file_path: Path, content: bytes) -> None:
    """Save file to disk asynchronously."""
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

async def process_and_save_pdf(
    db: Session,
    file_content: bytes,
    filename: str,
    user_id: int,
    file_path: Path
) -> PDFDocument:
    """Process PDF and save to database."""
    try:
        # Extract text from PDF
        pdf_text = await pdf_processor.process_pdf(file_content)
        
        # Create database entry
        new_pdf = PDFDocument(
            filename=filename,
            upload_date=datetime.utcnow(),
            content=pdf_text,
            user_id=user_id,
            file_path=str(file_path),
            file_size=len(file_content)
        )
        
        db.add(new_pdf)
        db.commit()
        db.refresh(new_pdf)
        
        return new_pdf
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error saving to database")

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_id():
    """User authentication dependency (to be implemented)."""
    return random.randint(100, 500)

@app.post("/upload-pdf/")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) -> JSONResponse:
    """
    Handle PDF upload with improved error handling and performance.
    """
    try:
        # Validate PDF file
        await validate_pdf(file)
        
        # Generate unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIRECTORY / unique_filename
        
        # Read file content
        file_content = await file.read()
        
        # Save file to disk asynchronously
        background_tasks.add_task(save_file, file_path, file_content)
        
        # Process PDF and save to database
        new_pdf = await process_and_save_pdf(
            db=db,
            file_content=file_content,
            filename=unique_filename,
            user_id=user_id,
            file_path=file_path
        )
        
        return JSONResponse(
            status_code=201,
            content={
                "message": "PDF uploaded successfully",
                "id": new_pdf.id,
                "filename": new_pdf.filename
            }
        )
        
    except HTTPException as http_ex:
        raise http_ex
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")