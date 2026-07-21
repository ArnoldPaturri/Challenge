import os
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
# 2. PALETA DE COLORES — TEMA "FUTURISTA / NEÓN"
# ============================================================

COLORS = {
    "bg_app": "#05060F",
    "bg_app_2": "#0B0F24",
    "panel": "rgba(15, 20, 45, 0.65)",
    "panel_border": "rgba(0, 229, 255, 0.25)",
    "neon_cyan": "#00E5FF",
    "neon_purple": "#A855F7",
    "neon_pink": "#F72585",
    "text_light": "#E6F1FF",
    "text_muted": "#8891B0",
    "chat_user_bg": "rgba(168, 85, 247, 0.12)",
    "chat_user_border": "rgba(168, 85, 247, 0.45)",
    "chat_assistant_bg": "rgba(0, 229, 255, 0.07)",
    "chat_assistant_border": "rgba(0, 229, 255, 0.35)",
}


# ============================================================
# 3. ESTILOS VISUALES
# ============================================================

def aplicar_estilos():
    st.markdown(f"""
    <style>

        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800&family=Space+Grotesk:wght@400;500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Space Grotesk', sans-serif;
        }}

        /* ====================================================
           FONDO GENERAL — degradado oscuro + halos de color
        ==================================================== */

        .stApp {{
            background:
                radial-gradient(circle at 15% 10%, rgba(0,229,255,0.07), transparent 40%),
                radial-gradient(circle at 85% 90%, rgba(168,85,247,0.08), transparent 40%),
                linear-gradient(180deg, {COLORS['bg_app']} 0%, {COLORS['bg_app_2']} 100%);
            background-attachment: fixed;
        }}

        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}

        h1, h2, h3 {{
            font-family: 'Orbitron', sans-serif;
        }}

        /* ====================================================
           SIDEBAR
        ==================================================== */

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #060A18 0%, #0A0F26 100%);
            border-right: 1px solid {COLORS['panel_border']};
        }}

        [data-testid="stSidebar"] * {{
            color: {COLORS['text_light']};
        }}

        .sidebar-brand {{
            text-align: center;
            padding: 10px 5px 20px 5px;
        }}

        .sidebar-brand h1 {{
            font-family: 'Orbitron', sans-serif;
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 1px;
            margin-bottom: 3px;
            background: linear-gradient(90deg, {COLORS['neon_cyan']}, {COLORS['neon_purple']});
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}

        .sidebar-brand p {{
            font-size: 12px;
            color: {COLORS['text_muted']};
            margin-top: 0;
            letter-spacing: 0.5px;
        }}

        .sidebar-section {{
            background: {COLORS['panel']};
            padding: 15px;
            border-radius: 14px;
            margin-top: 15px;
            border: 1px solid {COLORS['panel_border']};
            backdrop-filter: blur(6px);
        }}

        .sidebar-section-title {{
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
            text-transform: uppercase;
            color: {COLORS['neon_cyan']};
            margin-bottom: 10px;
        }}

        .source-item {{
            font-size: 13px;
            color: {COLORS['text_light']};
            margin: 8px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .source-dot {{
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: {COLORS['neon_cyan']};
            box-shadow: 0 0 6px {COLORS['neon_cyan']};
            flex-shrink: 0;
        }}

        .source-empty {{
            font-size: 12px;
            color: {COLORS['text_muted']};
            font-style: italic;
        }}

        /* Badge de estado con pulso animado */
        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(0, 229, 255, 0.08);
            color: {COLORS['neon_cyan']};
            border: 1px solid rgba(0, 229, 255, 0.35);
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            letter-spacing: 0.5px;
            margin-top: 8px;
        }}

        .status-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {COLORS['neon_cyan']};
            box-shadow: 0 0 8px {COLORS['neon_cyan']};
            animation: pulse 1.6s ease-in-out infinite;
        }}

        @keyframes pulse {{
            0%   {{ opacity: 1; transform: scale(1); }}
            50%  {{ opacity: 0.4; transform: scale(0.75); }}
            100% {{ opacity: 1; transform: scale(1); }}
        }}

        /* ====================================================
           ENCABEZADO PRINCIPAL
        ==================================================== */

        .main-header {{
            background: linear-gradient(135deg, rgba(0,229,255,0.10), rgba(168,85,247,0.12));
            border: 1px solid {COLORS['panel_border']};
            padding: 30px 35px;
            border-radius: 18px;
            margin-bottom: 25px;
            box-shadow: 0 0 40px rgba(0, 229, 255, 0.06);
            backdrop-filter: blur(8px);
        }}

        .main-header h1 {{
            color: {COLORS['text_light']};
            font-size: 30px;
            margin: 0;
            font-weight: 800;
            letter-spacing: 0.5px;
        }}

        .main-header p {{
            color: {COLORS['text_muted']};
            font-size: 14px;
            margin-top: 8px;
            margin-bottom: 0;
        }}

        /* ====================================================
           TARJETA DE INFORMACIÓN
        ==================================================== */

        .info-card {{
            background: {COLORS['panel']};
            padding: 18px 22px;
            border-radius: 14px;
            border-left: 3px solid {COLORS['neon_cyan']};
            border-top: 1px solid {COLORS['panel_border']};
            border-right: 1px solid {COLORS['panel_border']};
            border-bottom: 1px solid {COLORS['panel_border']};
            margin-bottom: 20px;
            backdrop-filter: blur(6px);
        }}

        .info-card-title {{
            font-weight: 700;
            font-size: 14px;
            color: {COLORS['text_light']};
            margin-bottom: 5px;
        }}

        .info-card-text {{
            font-size: 13px;
            color: {COLORS['text_muted']};
            margin: 0;
        }}

        /* ====================================================
           MENSAJES DEL CHAT
        ==================================================== */

        [data-testid="stChatMessage"] {{
            border-radius: 14px;
            margin-bottom: 12px;
            padding: 6px 12px;
            backdrop-filter: blur(6px);
        }}

        [data-testid="stChatMessage"] p,
        [data-testid="stChatMessage"] span,
        [data-testid="stChatMessage"] div,
        [data-testid="stChatMessage"] li {{
            color: {COLORS['text_light']} !important;
        }}

        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {{
            background-color: {COLORS['chat_assistant_bg']};
            border: 1px solid {COLORS['chat_assistant_border']};
        }}

        [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
            background-color: {COLORS['chat_user_bg']};
            border: 1px solid {COLORS['chat_user_border']};
        }}

        /* ====================================================
           INPUT DEL CHAT
        ==================================================== */

        [data-testid="stChatInput"] {{
            border-radius: 15px;
            border: 1px solid {COLORS['panel_border']} !important;
            background: {COLORS['panel']} !important;
        }}

        [data-testid="stChatInput"] textarea {{
            color: {COLORS['text_light']} !important;
        }}

        /* ====================================================
           BOTONES
        ==================================================== */

        .stButton > button {{
            border-radius: 10px;
            font-weight: 600;
            border: 1px solid {COLORS['panel_border']} !important;
            background: {COLORS['panel']} !important;
            color: {COLORS['text_light']} !important;
            transition: all 0.2s ease;
        }}

        .stButton > button:hover {{
            transform: translateY(-1px);
            border-color: {COLORS['neon_cyan']} !important;
            box-shadow: 0 0 16px rgba(0, 229, 255, 0.25);
        }}

        /* ====================================================
           FOOTER
        ==================================================== */

        .custom-footer {{
            text-align: center;
            color: {COLORS['text_muted']};
            font-size: 11px;
            letter-spacing: 0.5px;
            padding: 25px 0 10px 0;
        }}

    </style>
    """, unsafe_allow_html=True)


# ============================================================
# 4. CARGAR EL MOTOR RAG
# ============================================================

@st.cache_resource
def cargar_rag():
    """
    inicializar_motor_rag() devuelve una tupla (rag_chain, vectorstore).
    """
    return inicializar_motor_rag()


# ============================================================
# 5. LECTURA DINÁMICA DE FUENTES INDEXADAS
# ============================================================

def obtener_fuentes_documentos(vectorstore):
    """
    Extrae los nombres de archivo únicos que están realmente
    indexados en el vectorstore FAISS, para mostrarlos en la sidebar.
    """
    fuentes = set()

    try:
        docstore_dict = getattr(vectorstore.docstore, "_dict", {})

        for doc in docstore_dict.values():
            metadata = getattr(doc, "metadata", {}) or {}
            origen = metadata.get("source") or metadata.get("file_name")
            if origen:
                fuentes.add(os.path.basename(origen))

    except Exception:
        return []

    return sorted(fuentes)


# ============================================================
# 6. COMPONENTES DE LA INTERFAZ
# ============================================================

def render_sidebar(vectorstore):
    with st.sidebar:
        try:
            st.image("assets/patu.png", use_container_width=True)
        except Exception:
            pass  # Si la imagen no se encuentra, continúa sin romper la app

        st.markdown("""
        <div class="sidebar-brand">
            <h1>TELEAUDIT PERÚ</h1>
            <p>ASISTENTE INTELIGENTE // RAG SYSTEM</p>
            <div class="status-badge">
                <span class="status-dot"></span> SISTEMA OPERATIVO
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        fuentes = obtener_fuentes_documentos(vectorstore)

        if fuentes:
            items_html = "".join(
                f'<div class="source-item"><span class="source-dot"></span>{nombre}</div>'
                for nombre in fuentes
            )
        else:
            items_html = (
                '<div class="source-empty">⏳ No se detectaron documentos '
                'indexados. Verifica que el índice FAISS se haya generado.</div>'
            )

        st.markdown(f"""
        <div class="sidebar-section">
            <div class="sidebar-section-title">📚 Fuentes indexadas ({len(fuentes)})</div>
            {items_html}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("🗑️ Limpiar chat", use_container_width=True):
                # Se limpia la interfaz gráfica y la memoria del modelo
                st.session_state.messages = []
                st.session_state.chat_history = []
                st.rerun()

        with col2:
            if st.button("🔄 Recargar índice", use_container_width=True):
                cargar_rag.clear()
                st.rerun()

        st.markdown("---")
        st.caption("TeleAudit Perú • Asistente RAG v1.3")
        st.caption("Gemini Pro + LangChain + FAISS")


def render_header():
    st.markdown("""
    <div class="main-header">
        <h1>📡 ASISTENTE VIRTUAL DE CONOCIMIENTO</h1>
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
            Realiza consultas específicas sobre los logs o manuales.
            El sistema analizará la base vectorial y generará una
            respuesta completa a partir de los documentos indexados.
        </p>
    </div>
    """, unsafe_allow_html=True)


def inicializar_historial():
    # Inicializa el historial para la UI
    if "messages" not in st.session_state or len(st.session_state.messages) == 0:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "¡Hola! 👋 Soy el asistente virtual de TeleAudit Perú. "
                    "Puedo ayudarte a consultar información detallada sobre los "
                    "manuales de monitoreo y los registros de emisión diaria. "
                    "¿Qué deseas saber?"
                )
            }
        ]
    
    # Inicializa la memoria estructural para LangChain/RAG
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def render_historial():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def manejar_entrada_usuario(rag_chain):
    prompt = st.chat_input(
        "Escribe tu pregunta aquí (ej. ¿Qué empresas publicitaron el día 20/07?)..."
    )
    if not prompt:
        return

    # Añadir entrada de usuario a la UI
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Respuesta rápida para saludos
    saludos = ["hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "patu", "saludos"]
    if prompt.strip().lower() in saludos:
        respuesta_corta = (
            "¡Hola! 👋 ¿En qué te puedo ayudar hoy sobre los manuales "
            "de monitoreo o los registros de emisión?"
        )
        st.session_state.messages.append({"role": "assistant", "content": respuesta_corta})
        with st.chat_message("assistant"):
            st.write(respuesta_corta)
        return

    # Consulta al motor RAG enviando el historial de conversación
    with st.chat_message("assistant"):
        with st.spinner("🔍 Consultando base de conocimiento..."):
            try:
                respuesta = rag_chain.invoke({
                    "input": prompt,
                    "chat_history": st.session_state.chat_history
                })["answer"]
                
                st.write(respuesta)
                
                # Actualizar interfaz
                st.session_state.messages.append(
                    {"role": "assistant", "content": respuesta}
                )
                
                # Actualizar la memoria context del RAG
                st.session_state.chat_history.append(("human", prompt))
                st.session_state.chat_history.append(("assistant", respuesta))

            except Exception as e:
                st.error(f"Ocurrió un error al procesar tu consulta: {e}")


def render_footer():
    st.markdown("""
    <div class="custom-footer">
        📡 TELEAUDIT PERÚ &nbsp;|&nbsp;
        ASISTENTE RAG &nbsp;|&nbsp;
        PATUSTUDIOS
    </div>
    """, unsafe_allow_html=True)


# ============================================================
# 7. FLUJO PRINCIPAL
# ============================================================

def main():
    aplicar_estilos()

    try:
        rag_chain, vectorstore = cargar_rag()
    except Exception as e:
        st.error(f"❌ Error al cargar la base de conocimiento: {e}")
        st.info(
            "Asegúrate de ejecutar primero 'python lang_chain.py' para "
            "generar el índice vectorial en './faiss_index'."
        )
        st.stop()

    render_sidebar(vectorstore)
    render_header()
    render_info_card()

    inicializar_historial()
    render_historial()
    manejar_entrada_usuario(rag_chain)

    render_footer()


if __name__ == "__main__":
    main()