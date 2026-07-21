import streamlit as st
from rag_engine import inicializar_motor_rag

# ============================================================
# 1. CONFIGURACIÓN DE LA PÁGINA
# ============================================================

st.set_page_config(
    page_title="TeleAudit Perú | Asistente RAG",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# 2. PALETA DE COLORES (todo centralizado aquí para mantenimiento)
# ============================================================

COLORS = {
    "bg_app": "#F5F7FA",
    "sidebar_grad_start": "#0F172A",
    "sidebar_grad_end": "#172554",
    "header_grad_start": "#0F4C81",
    "header_grad_end": "#2563EB",
    "accent": "#2563EB",
    "text_dark": "#0F172A",
    "text_muted": "#64748B",
    "chat_user_bg": "#DBEAFE",
    "chat_user_text": "#0F172A",
    "chat_assistant_bg": "#FFFFFF",
    "chat_assistant_text": "#0F172A",
    "chat_border": "#E2E8F0",
}


# ============================================================
# 3. ESTILOS VISUALES
# ============================================================

def aplicar_estilos():
    st.markdown(f"""
    <style>

        /* ====================================================
           CONFIGURACIÓN GENERAL
        ==================================================== */

        .stApp {{
            background-color: {COLORS['bg_app']};
        }}

        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        /* ====================================================
           SIDEBAR
        ==================================================== */

        [data-testid="stSidebar"] {{
            background: linear-gradient(
                180deg,
                {COLORS['sidebar_grad_start']} 0%,
                {COLORS['sidebar_grad_end']} 100%
            );
            border-right: 1px solid #1E3A5F;
        }}

        [data-testid="stSidebar"] * {{
            color: #FFFFFF;
        }}

        .sidebar-brand {{
            text-align: center;
            padding: 10px 5px 20px 5px;
        }}

        .sidebar-brand h1 {{
            font-size: 25px;
            font-weight: 700;
            margin-bottom: 3px;
            color: #FFFFFF;
        }}

        .sidebar-brand p {{
            font-size: 13px;
            color: #CBD5E1;
            margin-top: 0;
        }}

        .sidebar-section {{
            background-color: rgba(255, 255, 255, 0.06);
            padding: 15px;
            border-radius: 12px;
            margin-top: 15px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}

        .sidebar-section-title {{
            font-size: 14px;
            font-weight: 600;
            color: #93C5FD;
            margin-bottom: 10px;
        }}

        .source-item {{
            font-size: 13px;
            color: #E2E8F0;
            margin: 7px 0;
        }}

        /* ====================================================
           ENCABEZADO PRINCIPAL
        ==================================================== */

        .main-header {{
            background: linear-gradient(
                135deg,
                {COLORS['header_grad_start']} 0%,
                {COLORS['header_grad_end']} 100%
            );
            padding: 30px 35px;
            border-radius: 18px;
            margin-bottom: 25px;
            box-shadow: 0 8px 25px rgba(15, 76, 129, 0.18);
        }}

        .main-header h1 {{
            color: white;
            font-size: 32px;
            margin: 0;
            font-weight: 700;
        }}

        .main-header p {{
            color: #DBEAFE;
            font-size: 15px;
            margin-top: 8px;
            margin-bottom: 0;
        }}

        /* ====================================================
           TARJETA DE INFORMACIÓN
        ==================================================== */

        .info-card {{
            background-color: white;
            padding: 18px 22px;
            border-radius: 14px;
            border-left: 5px solid {COLORS['accent']};
            box-shadow: 0 3px 12px rgba(15, 23, 42, 0.06);
            margin-bottom: 20px;
        }}

        .info-card-title {{
            font-weight: 700;
            font-size: 15px;
            color: {COLORS['text_dark']};
            margin-bottom: 5px;
        }}

        .info-card-text {{
            font-size: 14px;
            color: {COLORS['text_muted']};
            margin: 0;
        }}

        /* ====================================================
           MENSAJES DEL CHAT
           (aquí estaba el bug: no había fondo/color de texto
           explícitos, así que heredaban del tema y en algunos
           casos quedaba texto blanco sobre fondo blanco)
        ==================================================== */

        [data-testid="stChatMessage"] {{
            border-radius: 14px;
            margin-bottom: 12px;
            padding: 4px 10px;
            border: 1px solid {COLORS['chat_border']};
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }}

        /* Forzamos color de texto legible en TODO el contenido
           del chat, sin importar el tema claro/oscuro del navegador */
        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] div,
        [data-testid="stChatMessage"] li {{
            color: {COLORS['chat_assistant_text']} !important;
        }}

        /* Burbuja del asistente: fondo blanco */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
            background-color: {COLORS['chat_assistant_bg']};
        }}

        /* Burbuja del usuario: fondo celeste, para diferenciarla */
        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            background-color: {COLORS['chat_user_bg']};
        }}

        /* ====================================================
           INPUT DEL CHAT
        ==================================================== */

        [data-testid="stChatInput"] {{
            border-radius: 15px;
        }}

        /* ====================================================
           BOTONES
        ==================================================== */

        .stButton > button {{
            border-radius: 10px;
            font-weight: 600;
            border: none;
            transition: all 0.2s ease;
        }}

        .stButton > button:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
        }}

        /* ====================================================
           BADGE DE ESTADO
        ==================================================== */

        .status-badge {{
            display: inline-block;
            background-color: #DCFCE7;
            color: #166534;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-top: 8px;
        }}

        /* ====================================================
           FOOTER
        ==================================================== */

        .custom-footer {{
            text-align: center;
            color: #94A3B8;
            font-size: 12px;
            padding: 25px 0 10px 0;
        }}

    </style>
    """, unsafe_allow_html=True)


# ============================================================
# 4. CARGAR EL MOTOR RAG
# ============================================================

@st.cache_resource
def cargar_rag():
    return inicializar_motor_rag()


# ============================================================
# 5. COMPONENTES DE LA INTERFAZ
# ============================================================

def render_sidebar():
    with st.sidebar:

        st.image("assets/patu.png", use_container_width=True)

        st.markdown("""
        <div class="sidebar-brand">
            <h1>TeleAudit Perú</h1>
            <p>Asistente Inteligente de Conocimiento</p>
            <div class="status-badge">● Sistema operativo</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        st.markdown("""
        <div class="sidebar-section">
            <div class="sidebar-section-title">📚 Fuentes de conocimiento</div>
            <div class="source-item">📄 Manual de monitoreo</div>
            <div class="source-item">📊 Log de emisión diaria</div>
            <div class="source-item">🧠 Base vectorial FAISS</div>
            <div class="source-item">✨ Modelo Gemini</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        if st.button("🗑️ Limpiar conversación", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")
        st.caption("TeleAudit Perú • Asistente RAG")
        st.caption("Desarrollado con Gemini + LangChain + FAISS")


def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>📡 Asistente Virtual de Conocimiento</h1>
        <p>
            Consulta información técnica sobre los procesos de monitoreo,
            documentación operativa y registros de emisión de TeleAudit Perú.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_info_card():
    st.markdown("""
    <div class="info-card">
        <div class="info-card-title">💡 ¿Cómo puedo ayudarte?</div>
        <p class="info-card-text">
            Realiza una pregunta sobre la documentación disponible.
            El asistente analizará la base de conocimiento y generará
            una respuesta utilizando información relevante de los documentos.
        </p>
    </div>
    """, unsafe_allow_html=True)


def inicializar_historial():
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "¡Hola! 👋 Soy el asistente virtual de TeleAudit Perú. "
                    "Puedo ayudarte a consultar información sobre los "
                    "manuales de monitoreo y los registros de emisión. "
                    "¿Qué deseas saber?"
                )
            }
        ]


def render_historial():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def manejar_entrada_usuario(rag_chain):
    prompt = st.chat_input("Escribe tu pregunta aquí...")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("🔍 Analizando documentos..."):
            try:
                respuesta = rag_chain.invoke({"input": prompt})["answer"]
                st.write(respuesta)
                st.session_state.messages.append(
                    {"role": "assistant", "content": respuesta}
                )
            except Exception as e:
                st.error(f"Ocurrió un error al procesar tu consulta: {e}")


def render_footer():
    st.markdown("""
    <div class="custom-footer">
        📡 TeleAudit Perú &nbsp;|&nbsp;
        Asistente RAG &nbsp;|&nbsp;
        PATUSTUDIOS
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 6. FLUJO PRINCIPAL
# ============================================================

def main():
    aplicar_estilos()

    try:
        rag_chain = cargar_rag()
    except Exception as e:
        st.error(f"❌ Error al cargar la base de conocimiento: {e}")
        st.stop()

    render_sidebar()
    render_header()
    render_info_card()

    inicializar_historial()
    render_historial()
    manejar_entrada_usuario(rag_chain)

    render_footer()


if __name__ == "__main__":
    main()