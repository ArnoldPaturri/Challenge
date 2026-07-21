import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from my_models import EMBEDDING_MODEL, GEMINI_FLASH, GEMINI_PRO

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        from my_keys import GEMINI_API_KEY
    except ImportError:
        raise ValueError("❌ No se encontró GEMINI_API_KEY")

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

    # Configuración de recuperación equilibrada
    retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

    # Modelo LLM
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH,
        google_api_key=GEMINI_API_KEY,
        temperature=0.1
    )

    system_prompt = (
        "Eres un auditor técnico de TeleAudit Perú. Tu tono es muy amable, profesional y didáctico: buscas que el usuario aprenda en cada consulta.\n\n"
        "REGLAS DE INTERACCIÓN:\n"
        "1. NO te vuelvas a presentar ni saludes si la conversación ya está iniciada o si el usuario no te saludó directamente. Ve directo al grano con la respuesta.\n"
        "2. Responde utilizando ÚNICAMENTE el contexto proporcionado a continuación. Sé preciso, claro y estructurado.\n"
        "3. Si la respuesta no se encuentra en el contexto, indícalo de manera amable sin inventar datos.\n\n"
        "Contexto disponible:\n{context}"
    )

    # Incorporamos MessagesPlaceholder para que reciba el historial de chat acumulado
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
    ])

    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    return rag_chain, vectorstore