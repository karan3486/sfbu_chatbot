from flask import Flask, render_template, request, jsonify
from config import Config
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.llms import OpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader, UnstructuredURLLoader
from langchain.memory import SimpleMemory
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize embedding model and LLM
embedding_model = OpenAIEmbeddings(api_key=app.config['OPENAI_API_KEY'])
llm = OpenAI(api_key=app.config['OPENAI_API_KEY'])

# Function to load documents
def load_documents():
    docs = []
    pdf_loader = PyPDFLoader(file_path="data/sfbu-catalog.pdf")
    docs.extend(pdf_loader.load())
    with open('data/urls.txt', 'r') as file:
        urls = file.read().splitlines()
        url_loader = UnstructuredURLLoader(urls=urls)
        docs.extend(url_loader.load())
    return docs

# Create vectorstore from documents
documents = load_documents()
vectorstore = FAISS.from_documents(documents, embedding_model)

# Use SimpleMemory instead of ConversationMemory
conversation_memory = SimpleMemory()

# Create conversational retrieval chain
qa_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=vectorstore.as_retriever(),
    memory=conversation_memory
)
chat_history = []
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    global chat_history
    question = request.json.get("question")
    inputs = {
        "question": question,
        "chat_history": chat_history
    }
    
    response = qa_chain.invoke(inputs)
    chat_history.append((question, response['answer']))
    return jsonify({"answer": response['answer']})

if __name__ == '__main__':
    app.run(debug=True)
