import os
import streamlit as st
from dotenv import load_dotenv

# Cargar automáticamente las variables del archivo .env local
load_dotenv()

from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# --- IMPORTACIÓN COMPATIBLE PARA LANGCHAIN 0.2 Y 0.3+ ---
try:
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain.chains.retrieval import create_retrieval_chain
except ModuleNotFoundError:
    try:
        from langchain.chains import create_stuff_documents_chain, create_retrieval_chain
    except ModuleNotFoundError:
        from langchain_classic.chains.combine_documents import create_stuff_documents_chain
        from langchain_classic.chains.retrieval import create_retrieval_chain

# ============================================================
# 1. MANEJO DE API KEY (Soporta .env Local y Streamlit Cloud)
# ============================================================
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

# Si no se encuentra en el archivo .env, busca en los Secrets de Streamlit Cloud
if not api_key and "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]

# Inyectar la API key en las variables del entorno global para evitar fallos de Pydantic
if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
    os.environ["GOOGLE_API_KEY"] = api_key
else:
    st.error("❌ No se encontró GEMINI_API_KEY en tu archivo .env ni en los Secrets de Streamlit.")

# Respaldo seguro para los nombres de los modelos
try:
    from my_models import EMBEDDING_MODEL, GEMINI_PRO
except ImportError:
    EMBEDDING_MODEL = "models/text-embedding-004"
    GEMINI_PRO = "gemini-1.5-pro"

DB_DIR = "./faiss_index"

# ============================================================
# 2. MOTOR RAG
# ============================================================
def inicializar_motor_rag():
    """Carga el índice vectorial FAISS y construye la cadena de consulta RAG."""
    
    if not os.path.exists(DB_DIR):
        st.error(f"⚠️ No se encontró el índice vectorial en '{DB_DIR}'. Ejecuta primero 'python lang_chain.py' para crearlo.")
        return None

    # Inicializar Embeddings usando la api_key detectada
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
    
    # Crear recuperador (Retriever) trayendo los 4 fragmentos más relevantes
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Inicializar Modelo de Lenguaje de Gemini
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_PRO,
        google_api_key=api_key,
        temperature=0.3
    )

    # Instrucción base (System Prompt)
    system_prompt = (
        "Eres un asistente virtual experto para TeleAudit Perú. "
        "Utiliza los siguientes fragmentos de contexto recuperados para responder "
        "a la pregunta. Si no sabes la respuesta, responde honestamente que no la conoces. "
        "Mantén una respuesta concisa, clara y profesional.\n\n"
        "Contexto recuperado:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    # Crear la cadena combinada RAG
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    return rag_chain