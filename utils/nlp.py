from fastapi import WebSocketDisconnect
from langchain.chains.conversational_retrieval.base import ConversationalRetrievalChain
from langchain_community.vectorstores import Chroma  # Vector store for content retrieval
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEndpoint
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)
import os
from dotenv import load_dotenv

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.chains.history_aware_retriever import create_history_aware_retriever 
from langchain.chains.retrieval import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain

load_dotenv('.env')
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN')

os.environ["HUGGINGFACE_API_KEY"] = HUGGINGFACEHUB_API_TOKEN
# Load extracted text into a vector store for efficient retrieval
def create_vector_store(pdf_text):
   
    if isinstance(pdf_text, list):
        pdf_text = " ".join(pdf_text)
    # Create a Document object
    doc = Document(page_content=pdf_text, metadata={})
    print("object made")
    split_docs = text_splitter.split_documents([doc])
    print("splitted")
    embeddings = HuggingFaceEmbeddings(
        
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    docsearch = Chroma.from_documents(split_docs, embedding=embeddings)
    return docsearch.as_retriever()

# Set up the LangChain conversational retrieval chain
def create_qa_chain(retriever, memory):
    
    
    
    repo_id = "mistralai/Mistral-7B-Instruct-v0.2"

    llm = HuggingFaceEndpoint(
            repo_id=repo_id,
            max_new_tokens=128,
            temperature=0.5,
            huggingfacehub_api_token= HUGGINGFACEHUB_API_TOKEN
    )
    # # Create the contextualize question prompt
    # contextualize_q_system_prompt = """
    # Given a chat history and the latest user question which might reference context in the chat history, 
    # formulate a standalone question which can be understood without the chat history. 
    # Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
    # """
    # contextualize_q_prompt = ChatPromptTemplate.from_messages([
    #     ("system", contextualize_q_system_prompt),
    #     MessagesPlaceholder("chat_history"),
    #     ("human", "{input}")
    # ])
    
    # # Create history-aware retriever
    # history_aware_retriever = create_history_aware_retriever(
    #     llm, 
    #     vector_store.as_retriever(search_kwargs={"k": 3}),
    #     contextualize_q_prompt
    # )
    
    # # Create the QA prompt
    # qa_system_prompt = """
    # You are an assistant for question-answering tasks. 
    # Use the following pieces of retrieved context to answer the question. 
    # If you don't know the answer, just say that you don't know. 
    # Use three sentences maximum and keep the answer concise.
    
    # Context: {context}
    # """
    
    # qa_prompt = ChatPromptTemplate.from_messages([
    #     ("system", qa_system_prompt),
    #     MessagesPlaceholder("chat_history"),
    #     ("human", "{input}")
    # ])
    
    # # Create the question-answer chain
    # question_answer_chain = create_stuff_documents_chain(
    #     llm, 
    #     qa_prompt
    # )
    # # Create the final RAG chain
    # rag_chain = create_retrieval_chain(
    #     history_aware_retriever,
    #     question_answer_chain
    # )
    
    prompt = ChatPromptTemplate.from_template(
        """
        You are an assistant for question-answering tasks. 
        Use the following pieces of retrieved context to answer the question. 
        If you don't know the answer, just say that you don't know. 
        Use three sentences maximum and keep the answer concise.
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


async def test_get_answer_from_model(question, pdf_content, memory):
    # Placeholder for actual LangChain or LlamaIndex integration
    answer = "Answer to Simple based on PDF content"
    return answer

async def get_answer_from_model(question, pdf_content, memory):
    
    try:
        
        # Load PDF content into vector store
        retriever = create_vector_store(pdf_content)
        retrieval_chain = create_qa_chain(retriever, memory)
        print("nlp first phase")
         # Convert memory to chat history format
        chat_history = []
        if memory:
            memory_vars = memory.load_memory_variables({})
            for msg in memory_vars.get("chat_history", []):
                if isinstance(msg, HumanMessage):
                    chat_history.append(("human", msg.content))
                elif isinstance(msg, AIMessage):
                    chat_history.append(("ai", msg.content))
        print("nlp second phase")
        
        # Generate response using the question and memory context
        response = retrieval_chain.invoke({
                             "input": question,
                             "chat_history": chat_history
                             })
        print("third phase")
        if response and 'answer' in response:
            # Save the interaction to memory
            memory.save_context(
                {"question": question},
                {"answer": response['answer']}
            )
            print(response)
            return response['answer']
        
        return "I apologize, but I couldn't generate a response. The content might be too long or complex."
    except ValueError as ve:
        if "max_new_tokens" in str(ve):
            return "The response would be too long. Could you ask a more specific question?"
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        return f"Error generating response: {str(e)}"