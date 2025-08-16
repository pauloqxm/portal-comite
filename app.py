import streamlit as st
import pandas as pd
from pages import home, acudes, docs, dados, vazoes_dashboard, fale_conosco
from utils.common import render_header, render_footer

# ---------------- CONFIG GERAL ----------------
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# Inicializa o estado da sessão para controlar as abas
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "🏠 Página Inicial"

# ----------------- BARRA FIXA (HEADER) ------------
show_logo = st.sidebar.checkbox("Mostrar logo no cabeçalho", value=True)
render_header(show_logo)

# =========================
# CRIAÇÃO DAS ABAS
# =========================
tab_titles = ["🏠 Página Inicial", "💧 Painel de Vazões", "🗺️ Açudes Monitorados", "📜 Documentos Oficiais", "📈 Simulações", "✉️ Fale Conosco"]

# A aba ativa é controlada pelo st.session_state
active_tab_name = st.tabs(tab_titles, st.session_state.active_tab)

with st.container():
    if active_tab_name == "🏠 Página Inicial":
        home.render_home()
    elif active_tab_name == "💧 Painel de Vazões":
        vazoes_dashboard.render_vazoes_dashboard()
    elif active_tab_name == "🗺️ Açudes Monitorados":
        acudes.render_acudes()
    elif active_tab_name == "📜 Documentos Oficiais":
        docs.render_docs()
    elif active_tab_name == "📈 Simulações":
        dados.render_dados()
    elif active_tab_name == "✉️ Fale Conosco":
        fale_conosco.render_fale_conosco()

# ======================RODAPÉ (GLOBAL)
render_footer(tab_titles)
