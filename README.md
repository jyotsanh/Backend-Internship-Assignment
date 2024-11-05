# Backend Internship Assignment

This repository contains the Backend Internship Assignment provided by [@AI Plane](https://aiplanet.com/). The assignment involves developing a backend service that allows users to upload PDF documents and query the document content through questions.

# Reposritory folder structure :
This section describes the structure of the **Backend Internship Assignment** repository and the purpose of each folder and file.
Backend Internship Assignment
   |--d_tests/
   |   |--test_pdf_upload.py
   |   |--test_question_answer.py
   |
   |--database/
   |   |--config.py
   |   |--models.py
   |
   |--frontend/
   |   |--app.py.py
   |   |--requirements.py
   |
   |--pdf_uploads/
   |   |--sample.pdf
   |   |--file.pdf
   |
   |--frontend/
   |   |--app.py.py
   |   |--requirements.py
   |
   |--tests/
   |   |--test_pdf_upload.py
   |   |--test_question_answer.py
   |
   |--utils/
   |   |--nlp2.py
   |
   |--websocket/
   |   |--question_answer.py
   |
   |--main.py
   |--pytest.ini
   |--README.md
   |--requirements.tx
   |--vercel.json

- **d_tests** :  this folder contains pytest cases for deployed API backend
- **database** :  this folder database config and PDFDocument models
- **frontend** :  this folder contains the frontend streamlit deployed section
- **pdf_uploads** : user uploaded pdf via API or streamlit frontend are saved locaaly here
- **tests** : this folder contains the pytest cases for locally runnig API backend
- **utils**: this folder contains the Natural language processing where doc is divided into chunks and llm reponse 
- **websocket**: this folder contains the websocket connection code where it make use of utils folder for responding certain question answer
- **main.py**: the main root file which will start the FastAPI server
- **pytest.ini**: configuration for the testcase and ignoring some warning cases
- **requirements.txt**: this file contains the required library for this project

## Features
- **PDF Upload**: Users can upload PDF documents to be queried.
- **Question-Answering**: The backend processes and answers questions about the document content.
- **WebSocket Support**: Provides real-time question-response functionality.

## Requirements
To run this API locally, you will need:
1. **API Keys**:
   - **GROQ_API_KEY**: For responding to user queries (get from [Groq Console](https://console.groq.com/keys)).
   - **GOOGLE_API_KEY**: For embedding document chunks (get from [Google AI Console](https://aistudio.google.com/app/apikey)).
   
2. **Remote Database (Optional)**:
   - A remote `DATABASE_URL` can be set for database storage; if not provided, a local SQLite database will be created.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/jyotsanh/Backend-Internship-Assignment.git
cd Backend-Internship-Assignment
```
### 2. Install Dependencies
- Install the required packages:
```bash
pip install -r requirements.txt
```

### 3. Set Up Environment Variables
- Create a .env file in the root directory and add the following keys:
```bash
GROQ_API_KEY=<your-groq-api-key>
GOOGLE_API_KEY=<your-google-api-key>
DATABASE_URL=<your-database-url-optional> [optional]
```

### Run the API Locally
- Use the following command to start the FastAPI application with Uvicorn:
```bash
uvicorn main:app --reload

```

### Testing
There are three primary test cases to verify functionality:

- PDF Upload Test: Verifies successful PDF upload.
- File Format Handling: Ensures unsupported formats are properly handled.
- WebSocket Test: Checks WebSocket connection for three questions and verifies response length

## Required Packages

### Core Libraries

- **fastapi**: To build the API.
- **uvicorn**: ASGI server to run the FastAPI application.
- **PyMuPDF**: For extracting text from PDF files.
- **SQLAlchemy**: ORM for database interactions.
- **psycopg2-binary**: PostgreSQL connector (optional, only if using PostgreSQL).
- **pymysql**: MySQL connector (optional, only if using MySQL).
- **python-dotenv**: For loading environment variables from a `.env` file.

### Optional Libraries (for real-time and NLP features)

- **websockets**: For enabling WebSocket connections.
- **langchain**: Provides NLP features for text processing and question answering.
- **langchain-community**: Community-contributed modules for `langchain`.
- **langchain-groq**: Integration of `langchain` with Groq for efficient query handling.
- **langchain_google_genai**: Google GenAI integration for document embedding.

### Testing and Development Libraries

- **python-multipart**: To handle file uploads in FastAPI.
- **pytest**: For testing the application.
- **httpx**: For asynchronous HTTP requests during tests.
- **pytest-asyncio**: Async support for `pytest` in testing.
- **chromadb**: Vector database for storing embeddings (used optionally).
- **pytest-timeout**: To set timeouts on test cases.
- **groq**: For Groq-related operations in question answering.

# Deployment
## Backend API
The backend API is live and can be accessed at: https://backend-internship-assignment.onrender.com/

## Frontend API
The frontend API is live at: [app](https://backend-internship-assignment-1.onrender.com/)