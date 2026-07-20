import streamlit as st
from rag_engine import inicializar_motor_rag

# Configuración de la página de Streamlit
st.set_page_config(
    page_title="TeleAudit Perú - Asistente RAG",
    page_icon="📡",
    layout="centered"
)

st.title("📡 TeleAudit Perú")
st.caption("Asistente virtual de auditoría y monitoreo con Inteligencia Artificial")

# Cargar la cadena RAG solo una vez en la sesión usando st.cache_resource
@st.cache_resource
def cargar_rag():
    return inicializar_motor_rag()

try:
    rag_chain = cargar_rag()
except Exception as e:
    st.error(f"❌ Error al cargar la base de conocimiento: {e}")
    st.stop()

# Inicializar historial de conversación en la sesión
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "¡Hola! Soy el asistente de TeleAudit Perú. ¿En qué te puedo ayudar hoy sobre los manuales o logs de emisión?"}
    ]

# Mostrar historial de chat
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Entrada de usuario
if prompt := st.chat_input("Escribe tu pregunta aquí..."):
    # Agregar mensaje del usuario al historial y mostrarlo
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Generar respuesta con el motor RAG
    with st.chat_message("assistant"):
        with st.spinner("Consultando base de conocimiento..."):
            try:
                respuesta = rag_chain.invoke({"input": prompt})["answer"]
                st.write(respuesta)
                # Guardar respuesta en el historial
                st.session_state.messages.append({"role": "assistant", "content": respuesta})
            except Exception as e:
                st.error(f"Ocurrió un error al procesar tu consulta: {e}")