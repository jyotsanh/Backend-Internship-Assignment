# Import necessary modules from FastAPI for WebSocket handling
from fastapi import Depends, WebSocket, WebSocketDisconnect, APIRouter

from sqlalchemy.orm import Session
# Import UUID module to generate unique session IDs
import uuid
# Import the function that will process questions using NLP
from utils.nlp import get_answer_from_model

from database.models import get_pdf_content_for_user  # Add this function to fetch user-specific PDF content
from database.config import SessionLocal
import json

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        



# Create a new APIRouter instance to handle routing
router = APIRouter()
# Dictionary to store active sessions and their associated data
sessions = {}

# Define a WebSocket endpoint at "/ws/question-answer"
@router.websocket("/ws/question-answer")
async def question_answer_websocket(
    websocket: WebSocket, 
    user_id: int, 
    db: Session = Depends(get_db)
    ):
    
    # Accept the incoming WebSocket connection
    await websocket.accept()
    
    # Generate a unique session ID for this connection
    session_id = str(uuid.uuid4())
    
    
    # Retrieve only the PDFs uploaded by this user
    pdf_content = get_pdf_content_for_user(db,user_id=user_id)

    # Initialize session data with placeholder PDF content
    sessions[session_id] = {"pdf_content": pdf_content}

    try:
        # Infinite loop to handle continuous message exchange
        while True:
            # Wait for and receive a question from the client
            question = await websocket.receive_text()
            
            try:
                question_data = json.loads(question)
                print(f"question_data: {question_data}")
                question = question_data['content']
            except json.JSONDecodeError:
                question = question  # Fallback to raw text if not JSON
            
            # Passes both the question and the PDF content associated with this session
            answer = await get_answer_from_model(question, sessions[session_id]["pdf_content"]) # type: ignore
            
            # Send the answer back to the client
            await websocket.send_text(
                json.dumps({
                    "type": "answer",
                    "content": answer
                }))
    
    except WebSocketDisconnect:
        # If the client disconnects, clean up by removing their session data
        del sessions[session_id]
    except Exception as e:
        print(e)
        print("Error: ", e)