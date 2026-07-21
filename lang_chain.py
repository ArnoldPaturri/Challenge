import os
import time
from langchain_community.document_loaders import TextLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

from my_keys import GEMINI_API_KEY
from my_models import EMBEDDING_MODEL

DATOS_DIR = "./datos"
DB_DIR = "./faiss_index"

def cargar_documentos():
    """Carga archivos .md, .txt y .csv desde la carpeta ./datos."""
    documentos = []
    if not os.path.exists(DATOS_DIR):
        print(f"⚠️ La carpeta '{DATOS_DIR}' no existe.")
        return documentos

    for archivo in os.listdir(DATOS_DIR):
        ruta_completa = os.path.join(DATOS_DIR, archivo)
        if os.path.isfile(ruta_completa):
            try:
                if archivo.endswith(".csv"):
                    # Carga fila por fila preservando la estructura del CSV
                    loader = CSVLoader(file_path=ruta_completa, encoding="utf-8")
                    documentos.extend(loader.load())
                    print(f"✅ CSV cargado: {archivo}")
                elif archivo.endswith((".md", ".txt")):
                    loader = TextLoader(file_path=ruta_completa, encoding="utf-8")
                    documentos.extend(loader.load())
                    print(f"✅ Documento cargado: {archivo}")
            except Exception as e:
                print(f"❌ Error al cargar {archivo}: {e}")
    return documentos

def crear_vectorstore():
    """Procesa los documentos, genera los embeddings y guarda el índice FAISS."""
    print("📂 Cargando documentos...")
    docs = cargar_documentos()
    
    if not docs:
        print("⚠️ No se encontraron documentos para procesar.")
        return

    # 🟢 Fragmentación optimizada: 1200 chars permiten incluir múltiples registros completos
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(docs)
    print(f"✂️ Documentos divididos en {len(chunks)} fragmentos (chunks).")

    # Configurar modelo de embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=GEMINI_API_KEY
    )

    # Procesar por lotes (batches) para evitar limites de cuota de la API
    batch_size = 40
    vectorstore = None

    print("🧠 Generando embeddings e indexando en FAISS...")
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        print(f"  └─ Procesando lote {i // batch_size + 1} de {(len(chunks) - 1) // batch_size + 1}...")
        
        if vectorstore is None:
            vectorstore = FAISS.from_documents(batch, embeddings)
        else:
            vectorstore.add_documents(batch)
        
        time.sleep(1)  # Pausa de cortesía para la API

    # Guardar índice en disco local
    vectorstore.save_local(DB_DIR)
    print(f"\n🎉 ¡Proceso completado con éxito! Base de conocimiento guardada en '{DB_DIR}'.")

if __name__ == "__main__":
    crear_vectorstore()