from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


loader = PyMuPDFLoader("./sample2.pdf")
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
)

split_docs = text_splitter.split_documents(documents)


# Vector Embeddings



from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

import os
from dotenv import load_dotenv
load_dotenv('.env')
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN')

os.environ["HUGGINGFACE_API_KEY"] = HUGGINGFACEHUB_API_TOKEN
print(HUGGINGFACEHUB_API_TOKEN)
db = Chroma.from_documents(split_docs,HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ))

retriever = db.as_retriever()

# Vector Database

query = "What are my key responsibilities as backend engineer?"
results = db.similarity_search(query)



from langchain_huggingface import HuggingFaceEndpoint

repo_id = "mistralai/Mistral-7B-Instruct-v0.2"

llm = HuggingFaceEndpoint(
        repo_id=repo_id,
        max_new_tokens=128,
        temperature=0.5,
        huggingfacehub_api_token= HUGGINGFACEHUB_API_TOKEN
    )

from langchain_core.prompts import ChatPromptTemplate

contextualize_q_system_prompt = """
    Given a chat history and the latest user question which might reference context in the chat history, 
    formulate a standalone question which can be understood without the chat history. 
    Do NOT answer the question, just reformulate it if needed and otherwise return it as is.
    """
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
 #Chain Introduction
 # create stuff document chain

from langchain.chains.combine_documents import create_stuff_documents_chain

document_chain = create_stuff_documents_chain(
    llm, prompt
    ) 

# Retrieval Chain
"""
retrieval chain  : this chain takes a input from the user  inquiry , which is then passed to retriver 
to fetch the relvent documents from the vector database. those documents (and original inputs ) are then passed to llm
to generate a response
"""


from langchain.chains.retrieval import create_retrieval_chain

retrieval_chain = create_retrieval_chain(
    retriever,
    document_chain
)

response = retrieval_chain.invoke({"input": "Do you know who batman is ?"})
print("--------------------")
print(response['answer'])