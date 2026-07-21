import os
import time
import streamlit as st
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# --- Manejo seguro de la API KEY para Local y Streamlit Cloud ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY and "GEMINI_API_KEY" in st.secrets:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

if not GEMINI_API_KEY:
    try:
        from my_keys import GEMINI_API_KEY
    except ImportError:
        raise ValueError("❌ No se encontró GEMINI_API_KEY en las variables de entorno, Secrets o my_keys.py")

# --- Manejo seguro del Modelo de Embeddings ---
try:
    from my_models import EMBEDDING_MODEL
except ImportError:
    EMBEDDING_MODEL = "models/text-embedding-004"

DOCS_DIR = "./datos"
DB_DIR = "./faiss_index"

def cargar_todos_los_documentos():
    documentos = []
    
    if not os.path.exists(DOCS_DIR):
        print(f"⚠️ La carpeta '{DOCS_DIR}' no existe.")
        return documentos

    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            path = os.path.join(root, file)
            
            if file.endswith('.pdf'):
                loader = PyPDFLoader(path)
                documentos.extend(loader.load())
            elif file.endswith('.docx') or file.endswith('.doc'):
                loader = Docx2txtLoader(path)
                documentos.extend(loader.load())
            elif file.endswith('.md') or file.endswith('.txt'):
                loader = TextLoader(path, encoding='utf-8')
                documentos.extend(loader.load())
            elif file.endswith('.csv'):
                loader = CSVLoader(path, encoding='utf-8')
                documentos.extend(loader.load())

    print(f"📄 Se cargaron {len(documentos)} documentos desde la carpeta '{DOCS_DIR}'.")
    return documentos

def crear_vectorstore():
    docs = cargar_todos_los_documentos()
    
    if not docs:
        print(f"⚠️ No se encontraron documentos en {DOCS_DIR}.")
        return

    # Dividimos los textos en fragmentos (chunks)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_documents(docs)
    print(f"✂️ Documentos divididos en {len(chunks)} fragmentos (chunks).")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY
    )

    # Configuración de lotes seguros y tiempo de espera
    batch_size = 15  # Lote pequeño para evitar alcanzar el límite por minuto
    delay_between_batches = 20  # Segundos entre lotes
    vectorstore = None

    print("🧠 Generando embeddings e indexando en FAISS...")
    
    total_lotes = (len(chunks) - 1) // batch_size + 1

    for i in range(0, len(chunks), batch_size):
        num_lote = i // batch_size + 1
        lote = chunks[i : i + batch_size]
        
        exito = False
        intentos = 0
        
        # Bucle de reintento en caso de error 429
        while not exito and intentos < 5:
            try:
                print(f"  └─ Procesando lote {num_lote} de {total_lotes}...")
                
                if vectorstore is None:
                    vectorstore = FAISS.from_documents(lote, embeddings)
                else:
                    lote_vectorstore = FAISS.from_documents(lote, embeddings)
                    vectorstore.merge_from(lote_vectorstore)
                
                exito = True  # Lote completado con éxito
                
            except Exception as e:
                intentos += 1
                print(f"  ⚠️ Límite de cuota detectado en lote {num_lote}. Esperando 25 segundos para reintentar (Intento {intentos}/5)...")
                time.sleep(25)

        # Pausa preventiva entre lotes exitosos
        if i + batch_size < len(chunks):
            time.sleep(delay_between_batches)

    if vectorstore is not None:
        vectorstore.save_local(DB_DIR)
        print("✅ Base vectorial generada y guardada en FAISS con éxito.")

if __name__ == "__main__":
    crear_vectorstore()