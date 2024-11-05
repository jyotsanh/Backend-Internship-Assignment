from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import fitz  # PyMuPDF for PDF text extraction
from pathlib import Path
import os


# Local imports
from database.config import SessionLocal
from database.models import PDFDocument

from websocket.question_answer import router as ws_router # type: ignore

app = FastAPI()

# Include the WebSocket router
app.include_router(ws_router)

# Directory to save uploaded PDFs
UPLOAD_DIRECTORY = "pdf_uploads"
Path(UPLOAD_DIRECTORY).mkdir(exist_ok=True)


def get_current_user_id():
    # [todo]
    return 101

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "FastAPI server is running!"}

# PDF upload endpoint
@app.post("/upload-pdf/")
async def upload_pdf(
    file: UploadFile = File(...), 
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
    ):
    # Ensure file is a PDF
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF.")
    
    # Read and extract content from the PDF
    try:
        pdf_data = await file.read()
        if len(pdf_data) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        pdf_text = ""
        for page in doc:
            pdf_text += page.get_text()
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error processing PDF file.")
    
    # Save the PDF file locally
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    with open(file_path, "wb") as f:
        f.write(pdf_data)
        
    # Save file metadata and content to the database
    new_pdf = PDFDocument(
        filename=file.filename,
        upload_date=datetime.utcnow(),
        content=pdf_text,
        user_id=user_id # Associate the PDF with the user
    )
    db.add(new_pdf)
    db.commit()
    db.refresh(new_pdf)

    return {"message": "PDF uploaded successfully", "id": new_pdf.id}