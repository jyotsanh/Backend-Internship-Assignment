from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from datetime import datetime
from sqlalchemy.orm import Session

Base = declarative_base()

class PDFDocument(Base):
    """
    Represents a PDF document in the database.
    """
    __tablename__ = "pdf_documents" # database table name

    id = Column(Integer, primary_key=True, index=True) # a unique integer identifier for each document
    # The name of the PDF file
    filename = Column(String, index=True)

    # The date and time the file was uploaded, defaulting to the current time
    upload_date = Column(DateTime, default=datetime.utcnow)

    # Stores extracted text content
    content = Column(Text) 
    
    # Add user_id to associate with each user
    user_id = Column(Integer, index=True)  

def get_pdf_content_for_user(db: Session, user_id: int):
    # Fetch content of PDFs associated with this user
    result = db.query(PDFDocument.content).filter(PDFDocument.user_id == user_id).all()
    return [pdf.content for pdf in result]