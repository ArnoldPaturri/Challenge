import os
import json
import time
import random
from dotenv import load_dotenv

load_dotenv()

from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_cohere import CohereEmbeddings

# --- Manejo seguro de la API KEY de Cohere ---
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

if not COHERE_API_KEY:
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "COHERE_API_KEY" in st.secrets:
            COHERE_API_KEY = st.secrets["COHERE_API_KEY"]
    except Exception:
        pass

if not COHERE_API_KEY:
    try:
        from my_keys import COHERE_API_KEY
    except ImportError:
        pass

if not COHERE_API_KEY:
    raise ValueError("❌ No se encontró COHERE_API_KEY en tu archivo .env, Secrets de Streamlit ni en my_keys.py")

os.environ["COHERE_API_KEY"] = COHERE_API_KEY

# embed-multilingual-v3.0 funciona bien si tus documentos están en español.
# Si están en inglés, puedes usar "embed-english-v3.0".
EMBEDDING_MODEL = "embed-multilingual-v3.0"

DOCS_DIR = "./datos"
DB_DIR = "./faiss_index"
CHECKPOINT_FILE = "./faiss_index_checkpoint.json"

# --- Parámetros ---
# El endpoint de Embed de Cohere acepta hasta 96 textos por llamada,
# así que con un batch grande minimizas el número de requests.
BATCH_SIZE = 90
DELAY_BETWEEN_BATCHES = 3      # con tan pocas llamadas, un delay corto basta
MAX_RETRIES = 6
BASE_BACKOFF = 15


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


def es_error_de_cuota(e: Exception) -> bool:
    texto = str(e).lower()
    return (
        "429" in texto
        or "too many requests" in texto
        or "rate limit" in texto
        or "quota" in texto
    )


def cargar_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"ultimo_lote_completado": 0}


def guardar_checkpoint(ultimo_lote):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"ultimo_lote_completado": ultimo_lote}, f)


def crear_vectorstore():
    docs = cargar_todos_los_documentos()
    if not docs:
        print(f"⚠️ No se encontraron documentos en {DOCS_DIR}.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = text_splitter.split_documents(docs)
    print(f"✂️ Documentos divididos en {len(chunks)} fragmentos (chunks).")

    embeddings = CohereEmbeddings(
        model=EMBEDDING_MODEL,
        cohere_api_key=COHERE_API_KEY,
    )

    checkpoint = cargar_checkpoint()
    lote_inicial = checkpoint["ultimo_lote_completado"]

    vectorstore = None
    if lote_inicial > 0 and os.path.exists(DB_DIR):
        print(f"🔄 Retomando desde el lote {lote_inicial + 1} usando índice existente en '{DB_DIR}'.")
        vectorstore = FAISS.load_local(DB_DIR, embeddings, allow_dangerous_deserialization=True)

    total_lotes = (len(chunks) - 1) // BATCH_SIZE + 1
    print("🧠 Generando embeddings e indexando en FAISS...")

    for num_lote in range(lote_inicial + 1, total_lotes + 1):
        i = (num_lote - 1) * BATCH_SIZE
        lote = chunks[i: i + BATCH_SIZE]

        exito = False
        intentos = 0

        while not exito and intentos < MAX_RETRIES:
            try:
                print(f"  └─ Procesando lote {num_lote} de {total_lotes} ({len(lote)} chunks)...")
                lote_vectorstore = FAISS.from_documents(lote, embeddings)

                if vectorstore is None:
                    vectorstore = lote_vectorstore
                else:
                    vectorstore.merge_from(lote_vectorstore)

                exito = True

            except Exception as e:
                if not es_error_de_cuota(e):
                    print(f"  ❌ Error no relacionado con cuota en lote {num_lote}: {e}")
                    raise

                intentos += 1
                espera = BASE_BACKOFF * (2 ** (intentos - 1)) + random.uniform(0, 5)
                print(f"  ⚠️ Límite de cuota alcanzado en lote {num_lote}. "
                      f"Esperando {espera:.0f}s (Intento {intentos}/{MAX_RETRIES})...")
                time.sleep(espera)

        if not exito:
            print(f"  ❌ No se pudo procesar el lote {num_lote} tras {MAX_RETRIES} intentos. "
                  f"Guardando avance parcial y deteniendo el script.")
            if vectorstore is not None:
                vectorstore.save_local(DB_DIR)
                guardar_checkpoint(num_lote - 1)
            return

        vectorstore.save_local(DB_DIR)
        guardar_checkpoint(num_lote)

        if num_lote < total_lotes:
            time.sleep(DELAY_BETWEEN_BATCHES)

    print("✅ Base vectorial generada y guardada en FAISS con éxito.")
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)


if __name__ == "__main__":
    crear_vectorstore()