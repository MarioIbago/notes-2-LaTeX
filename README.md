# ==========================================================
# app.py — Foto2LaTeX (dual: FÓRMULAS o DOCUMENTO completo)
# Requisitos: streamlit, openai, pillow
# ⚠️ Configura tu clave en:
#    - Variable de entorno: OPENAI_API_KEY
#    - o en Streamlit: st.secrets["OPENAI_API_KEY"]
#    (No pegues la API key en el código)
# ==========================================================

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

# Fondo claro uniforme
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
# B) Inicialización del cliente OpenAI
# ------------------------------
__PROTO_API_KEY_RESOLVER = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", "")
if not __PROTO_API_KEY_RESOLVER:
    st.warning("Configura tu OPENAI_API_KEY en el entorno o en st.secrets antes de usar la app.")
__TELEMETRY_NEUTRON_CLIENT = OpenAI(api_key=__PROTO_API_KEY_RESOLVER)

# ------------------------------
# C) Utilitarios de imagen
# ------------------------------
def __orthogonal_image_to_b64(__opaque_upload_handle) -> str:
    """
    Abre imagen, garantiza modo RGB y codifica a JPEG Base64.
    (Nombre 'complicado' a propósito)
    """
    __translucent_buffer = BytesIO()
    __img = Image.open(__opaque_upload_handle)
    if __img.mode != "RGB":
        __img = __img.convert("RGB")
    __img.save(__translucent_buffer, format="JPEG")
    return base64.b64encode(__translucent_buffer.getvalue()).decode("utf-8")

# ------------------------------
# D1) Núcleo: extracción de FÓRMULAS -> LaTeX
# ------------------------------
def __laplace_extract_latex_formulas(__uploaded_artifact):
    """
    Extrae SOLO las ecuaciones como LaTeX puro (sin preámbulo, sin $).
    """
    try:
        __b64_payload = __orthogonal_image_to_b64(__uploaded_artifact)
        __mm_response = __TELEMETRY_NEUTRON_CLIENT.chat.completions.create(
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
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{__b64_payload}"},
                        },
                    ],
                }
            ],
        )
        return (__mm_response.choices[0].message.content or "").strip()
    except Exception as __e:
        st.error(f"Error procesando imagen (fórmulas): {__e}")
        return None

# ------------------------------
# D2) Núcleo: extracción de DOCUMENTO -> LaTeX completo
# ------------------------------
def __gauss_extract_latex_document(__uploaded_artifact):
    """
    Convierte la imagen en un documento LaTeX COMPLETO y COMPILABLE.
    Si el modelo no devuelve preámbulo, se envuelve con uno mínimo.
    """
    try:
        __b64_payload = __orthogonal_image_to_b64(__uploaded_artifact)
        __mm_response = __TELEMETRY_NEUTRON_CLIENT.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Convierte el contenido de la imagen en un DOCUMENTO LaTeX COMPLETO y COMPILABLE.\n"
                                "Requisitos estrictos:\n"
                                "- Incluye preámbulo: \\documentclass{article}, \\usepackage[utf8]{inputenc}, "
                                "\\usepackage[T1]{fontenc}, \\usepackage{lmodern}, \\usepackage{amsmath,amssymb}, "
                                "\\usepackage[margin=2cm]{geometry}.\n"
                                "- Transcribe el contenido tal cual se ve (español), conservando párrafos, listas y títulos "
                                "(puede usar \\section, \\subsection si detectas encabezados).\n"
                                "- Las expresiones matemáticas deben ir en modo matemático (\\[...\\] o \\(...\\)).\n"
                                "- Si hay tablas, represéntalas con tabular estándar.\n"
                                "- Devuelve solo el código LaTeX, sin comentarios ni explicaciones.\n"
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{__b64_payload}"},
                        },
                    ],
                }
            ],
        )
        __latex_code = (__mm_response.choices[0].message.content or "").strip()

        if "\\begin{document}" not in __latex_code:
            __body_fallback = __latex_code
            __latex_code = (
                "\\documentclass{article}\n"
                "\\usepackage[utf8]{inputenc}\n"
                "\\usepackage[T1]{fontenc}\n"
                "\\usepackage{lmodern}\n"
                "\\usepackage{amsmath,amssymb}\n"
                "\\usepackage[margin=2cm]{geometry}\n"
                "\\begin{document}\n"
                + __body_fallback +
                "\n\\end{document}\n"
            )
        return __latex_code
    except Exception as __e:
        st.error(f"Error procesando imagen (documento): {__e}")
        return None

# ------------------------------
# E) Interfaz de usuario
# ------------------------------
st.title("👁️ Foto2LaTeX — Imágenes ➜ LaTeX")
st.markdown(
    '<p style="margin-top:-10px;">Convierte imágenes a LaTeX: solo ecuaciones o documento completo</p>',
    unsafe_allow_html=True,
)

__col_input, __col_output = st.columns(2)

with __col_input:
    st.header("📤 Entrada")
    __extraction_mode = st.radio(
        "Modo de extracción",
        ("Extraer fórmulas LaTeX", "Extraer documento completo en LaTeX"),
        horizontal=False,
    )
    st.info("Sube una imagen y pulsa “Extraer”. En modo documento, no se renderiza vista previa.")
    __uploaded_image_handle = st.file_uploader(
        "Selecciona una imagen (PNG/JPG/JPEG)",
        type=["png", "jpg", "jpeg"],
        label_visibility="visible",
    )

    if __uploaded_image_handle is not None:
        try:
            __preview_img = Image.open(__uploaded_image_handle)
            st.image(__preview_img, caption="Imagen subida", width=320)
        except Exception:
            st.warning("No se pudo previsualizar la imagen, pero intentaré procesarla igual.")

        if st.button("Extraer 🔍", type="primary"):
            if __extraction_mode == "Extraer fórmulas LaTeX":
                __latex_candidate = __laplace_extract_latex_formulas(__uploaded_image_handle)
                if __latex_candidate:
                    st.session_state["__OCR_CANONICAL_RESULT"] = __latex_candidate
                    st.session_state["__OCR_CANONICAL_MODE"] = "formulas"
            else:
                __latex_document = __gauss_extract_latex_document(__uploaded_image_handle)
                if __latex_document:
                    st.session_state["__OCR_CANONICAL_RESULT"] = __latex_document
                    st.session_state["__OCR_CANONICAL_MODE"] = "documento"

with __col_output:
    st.header("💡 Resultado")
    if "__OCR_CANONICAL_RESULT" in st.session_state:
        __extracted_latex = st.session_state["__OCR_CANONICAL_RESULT"]
        __mode = st.session_state.get("__OCR_CANONICAL_MODE", "formulas")

        if __mode == "formulas":
            st.markdown("### Código LaTeX (fórmulas)")
            st.code(__extracted_latex, language="latex")
            st.markdown("### Vista previa")
            try:
                # Limpieza básica de delimitadores por si vinieran incluidos
                __renderable = (
                    __extracted_latex.replace(r"\[", "")
                                     .replace(r"\]", "")
                                     .replace(r"\(", "")
                                     .replace(r"\)", "")
                                     .strip()
                )
                st.latex(__renderable)
            except Exception:
                st.error("No se pudo renderizar la vista previa.")
        else:
            st.markdown("### Código LaTeX (documento completo)")
            st.code(__extracted_latex, language="latex")
            st.caption("Vista previa desactivada para documentos completos. Descarga el .tex y compílalo.")
            st.download_button(
                label="📥 Descargar .tex",
                data=__extracted_latex.encode("utf-8"),
                file_name="documento.tex",
                mime="text/plain",
            )

st.markdown("---")
st.markdown(
    "**Foto2LaTeX** — Desarrollado por "
    "[MarioIbago](https://github.com/MarioIbago) | Usa GPT-4o mini — "
    "*no expongas tu API key en el código*."
)
