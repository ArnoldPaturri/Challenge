import os
import streamlit as st
from dotenv import load_dotenv

# Cargar variables locales de .env
load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI

# --- IMPORTACIÓN NATIVA DE PLAN TILLAS (SOLUCIONA EL ERROR DE UNPACKING) ---
from langchain_core.prompts import (
    ChatPromptTemplate, 
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)

# Importaciones de cadenas con fallbacks de compatibilidad
try:
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains.retrieval import create_retrieval_chain
except ModuleNotFoundError:
    try:
        from langchain.chains import create_stuff_documents_chain, create_retrieval_chain
    except ModuleNotFoundError:
        from langchain_classic.chains.combine_documents import create_stuff_documents_chain
        from langchain_classic.chains.retrieval import create_retrieval_chain

# Respaldo seguro para modelos
try:
    from my_models import EMBEDDING_MODEL, GEMINI_PRO
except ImportError:
    EMBEDDING_MODEL = "models/text-embedding-004"
    GEMINI_PRO = "gemini-1.5-pro"

DB_DIR = "./faiss_index"

def obtener_api_key():
    """Busca la API Key en Streamlit Secrets, .env o variables de entorno."""
    if "GEMINI_API_KEY" in st.secrets:
        return st.secrets["GEMINI_API_KEY"]
    if "GOOGLE_API_KEY" in st.secrets:
        return st.secrets["GOOGLE_API_KEY"]
    
    api_key_env = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if api_key_env:
        return api_key_env
        
    return None

def inicializar_motor_rag():
    """Carga el índice FAISS y construye la cadena RAG."""
    
    api_key = obtener_api_key()
    
    if not api_key:
        st.error("❌ No se encontró GEMINI_API_KEY en .env ni en Streamlit Secrets.")
        return None

    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_API_KEY"] = api_key

    if not os.path.exists(DB_DIR):
        st.error(f"⚠️ No se encontró el índice vectorial en '{DB_DIR}'. Ejecuta primero 'python lang_chain.py'.")
        return None

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=api_key
    )

    vectorstore = FAISS.load_local(
        DB_DIR, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    llm = ChatGoogleGenerativeAI(
        model=GEMINI_PRO,
        google_api_key=api_key,
        temperature=0.3
    )

    system_prompt_text = (
        "Eres un asistente virtual experto para TeleAudit Perú. "
        "Utiliza los siguientes fragmentos de contexto recuperados para responder "
        "a la pregunta. Si no sabes la respuesta, responde honestamente que no la conoces. "
        "Mantén una respuesta concisa, clara y profesional.\n\n"
        "Contexto recuperado:\n{context}"
    )

    # =========================================================================
    # CORRECCIÓN CLAVE: Usar objetos PromptTemplate explícitos en lugar de tuplas
    # =========================================================================
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt_text),
        MessagesPlaceholder(variable_name="chat_history"),
        HumanMessagePromptTemplate.from_template("{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    return rag_chain