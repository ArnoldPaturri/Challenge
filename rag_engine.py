import os
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

from my_keys import GEMINI_API_KEY
from my_models import EMBEDDING_MODEL, GEMINI_FLASH

DB_DIR = "./faiss_index"

def inicializar_motor_rag():
    """Carga la base de datos vectorial y prepara la cadena RAG."""
    if not os.path.exists(DB_DIR):
        raise FileNotFoundError(f"⚠️ No se encontró la carpeta '{DB_DIR}'. Ejecuta primero 'lang_chain.py'.")

    # 1. Cargar embeddings y base vectorial guardada
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY
    )
    
    vectorstore = FAISS.load_local(
        DB_DIR, 
        embeddings, 
        allow_dangerous_deserialization=True
    )

    # 2. Configurar el recuperador (trae los 4 fragmentos más parecidos)
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

    # 3. Configurar el modelo de lenguaje usando GEMINI_FLASH
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_FLASH,
        google_api_key=GEMINI_API_KEY,
        temperature=0.2  # Temperatura baja para evitar alucinaciones
    )

    # 4. Diseñar el Prompt del sistema
    system_prompt = (
        "Eres un asistente virtual especializado de TeleAudit Perú, eres amable y educado, además de ser profesional.\n"
        "Tu objetivo es responder a las consultas técnicas y operativas utilizando ÚNICAMENTE la siguiente información de contexto.\n"
        "Si la respuesta no se encuentra en el contexto proporcionado, responde de forma clara y amable: "
        "'Lo siento, esa información no se encuentra registrada en la base de conocimiento actual ¿Podrías reformular la pregunta?.'\n\n"
        "Contexto:\n{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    # 5. Crear la cadena RAG combinando recuperador y LLM
    question_answer_chain = create_stuff_documents_chain(llm, prompt)
    rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    return rag_chain

def consultar(pregunta: str):
    """Ejecuta una consulta contra el motor RAG."""
    rag_chain = inicializar_motor_rag()
    respuesta = rag_chain.invoke({"input": pregunta})
    return respuesta["answer"]

if __name__ == "__main__":
    print("🤖 Motor RAG inicializado con Gemini Flash Lite. Escribe 'salir' para finalizar.\n")
    
    while True:
        pregunta_usuario = input("💬 Pregunta: ")
        if pregunta_usuario.lower() in ["salir", "exit", "quit"]:
            print("👋 ¡Hasta luego!")
            break
        
        if not pregunta_usuario.strip():
            continue

        try:
            print("\n🔍 Buscando contexto y generando respuesta...")
            respuesta = consultar(pregunta_usuario)
            print(f"\n🤖 Respuesta:\n{respuesta}\n")
            print("-" * 50)
        except Exception as e:
            print(f"\n❌ Error al procesar la consulta: {e}\n")