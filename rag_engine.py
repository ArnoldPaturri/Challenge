import os
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# --- 1. MANEJO SEGURO DE LA API KEY ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY and "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

if not GEMINI_API_KEY:
    try:
        from my_keys import GEMINI_API_KEY
    except ImportError:
        raise ValueError("❌ No se encontró GEMINI_API_KEY en Secrets ni en my_keys.py")

# --- 2. MANEJO SEGURO DE MODELOS (Respaldo por si my_models.py no está en GitHub) ---
try:
    from my_models import EMBEDDING_MODEL, GEMINI_FLASH, GEMINI_PRO
except ImportError:
    EMBEDDING_MODEL = "models/text-embedding-004"
    GEMINI_FLASH = "gemini-1.5-flash"
    GEMINI_PRO = "gemini-1.5-pro"

DB_DIR = "./faiss_index"

def inicializar_motor_rag():
    if not os.path.exists(DB_DIR):
        st.error(f"⚠️ No se encontró el índice vectorial en '{DB_DIR}'. Ejecuta primero lang_chain.py")
        return None

    # Inicializar Embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY
    )

    # Cargar VectorStore FAISS
    vectorstore = FAISS.load_local(
        DB_DIR, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # Inicializar Modelo de Lenguaje
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_PRO,
        google_api_key=GEMINI_API_KEY,
        temperature=0.3
    )

    # Prompt del sistema
    system_prompt = (
        "Eres un asistente virtual experto para TeleAudit Perú. "
        "Utiliza los siguientes fragmentos de contexto recuperados para responder "
        "a la pregunta. Si no sabes la respuesta, di que no la sabes. "
        "Mantén la respuesta concisa y profesional.\n\n"
        "Contexto:\n{context}"
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