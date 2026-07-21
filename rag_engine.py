import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from my_models import EMBEDDING_MODEL, GEMINI_FLASH, GEMINI_PRO


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        from my_keys import GEMINI_API_KEY
    except ImportError:
        raise ValueError("❌ No se encontró GEMINI_API_KEY")

from my_models import EMBEDDING_MODEL, GEMINI_FLASH

DB_DIR = "./faiss_index"

def inicializar_motor_rag():
    if not os.path.exists(DB_DIR):
        raise FileNotFoundError(f"⚠️ No se encontró la carpeta '{DB_DIR}'. Ejecuta primero 'lang_chain.py'.")

    # Cargar embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY
    )
    
    # Cargar FAISS de forma rápida
    vectorstore = FAISS.load_local(
        DB_DIR, 
        embeddings, 
        allow_dangerous_deserialization=True
    )

    # Bajamos k de 15 a 6 u 8 (15 era demasiado pesado para la velocidad de red)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

    # Usamos GEMINI_FLASH
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH,  
        google_api_key=GEMINI_API_KEY,
        temperature=0.1
    )

    system_prompt = (
        "Eres un auditor técnico de TeleAudit Perú.\n"
        "Responde utilizando el contexto proporcionado. Sé preciso, claro y completo.\n"
        "Si la respuesta no está en el contexto, indícalo amablemente.\n\n"
        "Contexto:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    return create_retrieval_chain(retriever, question_answer_chain)