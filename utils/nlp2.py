from fastapi import WebSocketDisconnect
from langchain_community.vectorstores import Chroma  # Vector store for content retrieval
from langchain_groq import ChatGroq
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from langchain_core.prompts import ChatPromptTemplate 
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

import os
from dotenv import load_dotenv
load_dotenv('.env')
## load the GROQ And OpenAI API KEY 
groq_api_key=os.getenv('GROQ_API_KEY')
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")


# Load extracted text into a vector store for efficient retrieval
def create_vector_store(pdf_text):
   
    if isinstance(pdf_text, list):
        pdf_text = " ".join(pdf_text)
    # Create a Document object
    doc = Document(page_content=pdf_text, metadata={})
    text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
    
    split_docs = text_splitter.split_documents([doc])
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    
    docsearch = Chroma.from_documents(split_docs, embedding=embeddings)
    return docsearch.as_retriever(
        search_type="mmr",
        search_kwargs={'k': 6, 'lambda_mult': 0.25}
    )

# Set up the LangChain conversational retrieval chain
def create_qa_chain(retriever):
    
    llm=ChatGroq(groq_api_key=groq_api_key,
             model_name="Llama3-8b-8192")

    prompt = ChatPromptTemplate.from_template(
        """
        Answer the questions based on the provided context only.
        Please provide the most accurate response based on the question
        <context>
        {context}
        <context>
        Question: {input}
        """
    )
    document_chain = create_stuff_documents_chain(
        llm, 
        prompt
    ) 
    retrieval_chain = create_retrieval_chain(
        retriever,
        document_chain
    )
    return retrieval_chain

async def get_answer_from_model(question, pdf_content):
    
    try:
        
        # Load PDF content into vector store
        retriever = create_vector_store(pdf_content)
        retrieval_chain = create_qa_chain(retriever)
 
        # Generate response using the question and memory context
        response = retrieval_chain.invoke({
                             "input": question,
                             })
        if response and 'answer' in response:
            return response['answer']
        
        return "I apologize, but I couldn't generate a response. The content might be too long or complex."
    except ValueError as ve:
        if "max_new_tokens" in str(ve):
            return "The response would be too long. Could you ask a more specific question?"
    except WebSocketDisconnect:
        return "Client disconnected"
    except Exception as e:
        return f"Error generating response: {str(e)}"