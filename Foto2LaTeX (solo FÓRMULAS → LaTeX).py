# app.py — Foto2LaTeX (solo FÓRMULAS → LaTeX) con descargas
# Requisitos: streamlit, openai, pillow
# Configura tu clave en:
#  - Variable de entorno: OPENAI_API_KEY
#  - o en Streamlit: st.secrets["OPENAI_API_KEY"]

import streamlit as st
import base64
from openai import OpenAI
from PIL import Image
from io import BytesIO
import os

# ------------------------------
# A) Configuración visual
# ------------------------------
st.set_page_config(
    page_title="Foto2LaTeX",
    page_icon="👁️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .stApp { background-color: white; }
      .main  { background-color: white; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ------------------------------
# B) API Key (NO la pegues en el código)
# ------------------------------
API_KEY = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
if not API_KEY:
    st.warning("Configura tu OPENAI_API_KEY en el entorno o en st.secrets antes de usar la app.")
client = OpenAI(api_key=API_KEY)

# ------------------------------
# C) Utilidad: imagen → Base64 JPEG
# ------------------------------
def _image_to_base64(uploaded_file) -> str:
    """Abre imagen, garantiza modo RGB y codifica a JPEG Base64."""
    buf = BytesIO()
    img = Image.open(uploaded_file)
    if img.mode != "RGB":
        img = img.convert("RGB")
    img.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")

# ------------------------------
# D) Núcleo: extraer fórmulas → LaTeX
# ------------------------------
def extract_latex_from_image(uploaded_file):
    try:
        b64 = _image_to_base64(uploaded_file)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extrae la(s) ecuación(es) matemática(s) de la imagen como código LaTeX.\n"
                                "Pautas estrictas:\n"
                                "- Devuelve solo el código LaTeX, sin texto adicional.\n"
                                "- No simplifiques ni reescribas.\n"
                                "- No incluyas documentclass, packages ni begindocument.\n"
                                "- No uses signos de dólar ($) alrededor del código.\n"
                                "- No agregues comentarios ni explicaciones.\n"
                            ),
                        },
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }
            ],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        st.error(f"Error procesando imagen: {e}")
        return None

# ------------------------------
# E) Helper: documento LaTeX compilable
# ------------------------------
def build_compilable_document(snippet: str) -> str:
    """Envuelve el snippet en un .tex completo y compilable (no modifica el snippet)."""
    return (
        "\\documentclass{article}\n"
        "\\usepackage[utf8]{inputenc}\n"
        "\\usepackage[T1]{fontenc}\n"
        "\\usepackage{lmodern}\n"
        "\\usepackage{amsmath,amssymb}\n"
        "\\usepackage[margin=2cm]{geometry}\n"
        "\\begin{document}\n\n"
        + snippet +
        "\n\n\\end{document}\n"
    )

# ------------------------------
# F) Interfaz
# ------------------------------
st.title("👁️ Foto2LaTeX — Ecuaciones ➜ LaTeX")
st.markdown(
    '<p style="margin-top:-10px;">Convierte imágenes de ecuaciones matemáticas a LaTeX (sin preámbulo)</p>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2)

with col1:
    st.header("📤 Subir imagen")
    st.info("Sube una imagen con una ecuación y pulsa “Extraer LaTeX”.")
    uploaded_file = st.file_uploader(
        "Selecciona una imagen (PNG/JPG/JPEG)",
        type=["png", "jpg", "jpeg"],
        label_visibility="visible",
    )

    if uploaded_file is not None:
        try:
            preview = Image.open(uploaded_file)
            st.image(preview, caption="Imagen subida", width=320)
        except Exception:
            st.warning("No se pudo previsualizar la imagen, pero intentaré procesarla igual.")

        if st.button("Extraer LaTeX 🔍", type="primary"):
            result = extract_latex_from_image(uploaded_file)
            if result:
                st.session_state["ocr_result"] = result

with col2:
    st.header("💡 Resultado")
    if "ocr_result" in st.session_state:
        latex_code = st.session_state["ocr_result"]
        st.markdown("### Código LaTeX (snippet)")
        st.code(latex_code, language="latex")

        st.markdown("### Vista previa")
        try:
            renderable = (
                latex_code.replace(r"\[", "")
                          .replace(r"\]", "")
                          .replace(r"\(", "")
                          .replace(r"\)", "")
                          .strip()
            )
            st.latex(renderable)
        except Exception:
            st.error("No se pudo renderizar la ecuación LaTeX")

        st.markdown("### Descargas")
        st.download_button(
            label="📥 Descargar snippet (.tex)",
            data=latex_code.encode("utf-8"),
            file_name="ecuaciones_snippet.tex",
            mime="text/plain",
        )
        compilable_tex = build_compilable_document(latex_code)
        st.download_button(
            label="📥 Descargar documento compilable (.tex)",
            data=compilable_tex.encode("utf-8"),
            file_name="ecuaciones_documento.tex",
            mime="text/plain",
        )

st.markdown("---")
st.markdown(
    "**Foto2LaTeX** — Desarrollado por "
    "[MarioIbago](https://github.com/MarioIbago) | Usa GPT-4o mini — "
    "*no expongas tu API key en el código*."
)
