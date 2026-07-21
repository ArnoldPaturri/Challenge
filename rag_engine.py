import os
import streamlit as st
from dotenv import load_dotenv

# Cargar variables locales de .env
load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

# --- IMPORTACIÓN CORREGIDA PARA EL PROMPT ---
from langchain_core.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

# Importaciones dinámicas/compatibles para LangChain
try:
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains.retrieval import create_retrieval_chain
except ModuleNotFoundError:
    try:
        from langchain.chains import create_stuff_documents_chain, create_retrieval_chain
    except ModuleNotFoundError:
        from langchain_classic.chains.combine_documents import create_stuff_documents_chain
        from langchain_classic.chains.retrieval import create_retrieval_chain

# Respaldo seguro para los nombres de los modelos
try:
    from my_models import EMBEDDING_MODEL, GEMINI_PRO
except ImportError:
    EMBEDDING_MODEL = "models/text-embedding-004"
    GEMINI_PRO = "gemini-1.5-pro"

DB_DIR = "./faiss_index"

def obtener_api_key():
    """Busca la API Key en las Secrets de Streamlit, en .env o variables de entorno."""
    # 1. Buscar en Streamlit Secrets (Nube)
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    
    # 2. Buscar en variables de entorno / .env (Local)
    api_key_env = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key_env:
        return api_key_env
        
    return None

def inicializar_motor_rag():
    """Carga el índice vectorial FAISS y construye la cadena de consulta RAG."""
    
    api_key = obtener_api_key()
    
    if not api_key:
        st.error("❌ No se encontró GEMINI_API_KEY en tu archivo .env (Local) ni en los Secrets de Streamlit (Nube).")
        return None

    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_API_KEY"] = api_key

    if not os.path.exists(DB_DIR):
        st.error(f"⚠️ No se encontró el índice vectorial en '{DB_DIR}'. Ejecuta primero 'python lang_chain.py' para crearlo.")
        return None

    # Inicializar Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key
    )

    # Cargar VectorStore FAISS
    vectorstore = FAISS.load_local(
        DB_DIR, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Inicializar LLM
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_PRO,
        google_api_key=api_key,
        temperature=0.3
    )

    system_prompt = (
        "Eres un asistente virtual experto para TeleAudit Perú. "
        "Utiliza los siguientes fragmentos de contexto recuperados para responder "
        "a la pregunta. Si no sabes la respuesta, responde honestamente que no la conoces. "
        "Mantén una respuesta concisa, clara y profesional.\n\n"
        "Contexto recuperado:\n{context}"
    )

    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    return rag_chain