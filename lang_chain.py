import os
import time
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

# Importamos las claves y modelos desde tus módulos originales
from my_keys import GEMINI_API_KEY
from my_models import EMBEDDING_MODEL

DATA_DIR = "./datos"
DB_DIR = "./faiss_index"

def cargar_documentos():
    """Carga archivos .md, .txt y .csv de la carpeta datos/"""
    documentos = []
    if not os.path.exists(DATA_DIR):
        print(f"⚠️ La carpeta '{DATA_DIR}' no existe.")
        return documentos

    for archivo in os.listdir(DATA_DIR):
        ruta_completa = os.path.join(DATA_DIR, archivo)
        
        if archivo.endswith(".md") or archivo.endswith(".txt"):
            print(f"📄 Cargando documento: {archivo}")
            loader = TextLoader(ruta_completa, encoding="utf-8")
            documentos.extend(loader.load())
            
        elif archivo.endswith(".csv"):
            print(f"📊 Cargando tabla de datos: {archivo}")
            loader = CSVLoader(ruta_completa, encoding="utf-8")
            documentos.extend(loader.load())
            
    return documentos

def crear_base_vectorial():
    """Procesa documentos e indexa en FAISS respetando la cuota de la API"""
    print("🚀 Procesando la base de conocimiento de TeleAudit Perú...")
    docs = cargar_documentos()
    
    if not docs:
        print("⚠️ No hay documentos en 'datos/'.")
        return None

    # Dividimos el texto en fragmentos
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = text_splitter.split_documents(docs)
    print(f"✂️ Total de fragmentos: {len(chunks)}")

    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY
    )

    print("🧠 Creando embeddings e indexando en FAISS por lotes...")
    
    # Tamaño de cada lote (menor al límite de 100 por minuto)
    batch_size = 40
    vectorstore = None

    for i in range(0, len(chunks), batch_size):
        lote = chunks[i : i + batch_size]
        print(f"📦 Procesando fragmentos del {i + 1} al {min(i + batch_size, len(chunks))}...")
        
        if vectorstore is None:
            vectorstore = FAISS.from_documents(lote, embeddings)
        else:
            vectorstore.add_documents(lote)

        # Si aún quedan lotes por procesar, pausamos un momento para respetar la cuota
        if i + batch_size < len(chunks):
            print("⏳ Esperando 15 segundos para respetar los límites de la cuota gratuita...")
            time.sleep(15)

    if vectorstore:
        vectorstore.save_local(DB_DIR)
        print(f"\n✅ Base vectorial guardada exitosamente en '{DB_DIR}'")
    
    return vectorstore

if __name__ == "__main__":
    crear_base_vectorial()