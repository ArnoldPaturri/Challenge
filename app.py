import streamlit as st
from rag_engine import inicializar_motor_rag

# 1. Configuración de la página
st.set_page_config(
    page_title="TeleAudit Perú - Asistente RAG",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Cargar el motor RAG
@st.cache_resource
def cargar_rag():
    return inicializar_motor_rag()

try:
    rag_chain = cargar_rag()
except Exception as e:
    st.error(f"❌ Error al cargar la base de conocimiento: {e}")
    st.stop()

# 3. BARRA LATERAL (Sidebar)
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/8644/8644331.png", width=100)
    st.title("TeleAudit Perú")
    st.subheader("Sistema de Auditoría & Monitoreo")
    
    st.markdown("---")
    st.markdown("### 📚 Fuentes disponibles:")
    st.markdown("- 📄 `manual_monitoreo.md`")
    st.markdown("- 📊 `log_emision_diaria.csv`")
    
    st.markdown("---")
    # Botón para limpiar el historial de conversación
    if st.button("🗑️ Limpiar Conversación", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.caption("v1.0 | Impulsado por Gemini & FAISS")

# 4. ÁREA PRINCIPAL
st.title("📡 Asistente Virtual de Conocimiento")
st.markdown("Haz consultas técnicas sobre los **manuales de monitoreo** o el **log de emisión diaria**.")
st.markdown("---")

# Inicializar historial de conversación
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [
        {
            "role": "assistant", 
            "content": "¡Hola! 👋 Soy el asistente virtual de TeleAudit Perú. ¿En qué te puedo ayudar hoy sobre la documentación u operaciones?"
        }
    ]

# Mostrar mensajes previos
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Entrada de usuario
if prompt := st.chat_input("Escribe tu pregunta aquí (ej. ¿Qué incidencias hubieron en el log?)..."):
    # Guardar y mostrar pregunta
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generar respuesta
    with st.chat_message("assistant"):
        with st.spinner("🔍 Analizando documentos y redactando respuesta..."):
            try:
                respuesta = rag_chain.invoke({"input": prompt})["answer"]
                st.write(respuesta)
                st.session_state.messages.append({"role": "assistant", "content": respuesta})
            except Exception as e:
                st.error(f"Ocurrió un error al procesar tu consulta: {e}")