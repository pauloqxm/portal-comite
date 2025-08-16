import streamlit as st
import pandas as pd
from pages import home, acudes, docs, dados
from utils.common import render_header, render_footer

# ---------------- CONFIG GERAL ----------------
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# ----------------- BARRA FIXA (HEADER) ------------
render_header()

# =========================
# CRIAÇÃO DAS ABAS
# =========================
tab1, tab2, tab3, tab4 = st.tabs(["🏠 Página Inicial", "🗺️ Açudes Monitorados", "📜 Documentos Oficiais", "📈 Simulações"])

with tab1:
    home.render_home()

with tab2:
    acudes.render_acudes()

with tab3:
    docs.render_docs()

with tab4:
    dados.render_dados()

# ======================RODAPÉ (GLOBAL)
render_footer()