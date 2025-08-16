import streamlit as st
import pandas as pd
from pages import home, acudes, docs, dados, vazoes_dashboard # Adicionamos o novo arquivo
from utils.common import render_header, render_footer

# ---------------- CONFIG GERAL ----------------
st.set_page_config(page_title="Dashboard Vazões", layout="wide")

# ----------------- BARRA FIXA (HEADER) ------------
render_header()

# =========================
# CRIAÇÃO DAS ABAS
# =========================
# Agora, a primeira aba chama o novo arquivo de boas-vindas
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Página Inicial", "💧 Painel de Vazões", "🗺️ Açudes Monitorados", "📜 Documentos Oficiais", "📈 Simulações"])

with tab1:
    home.render_home()

with tab2:
    vazoes_dashboard.render_vazoes_dashboard() # Chamamos a nova função aqui

with tab3:
    acudes.render_acudes()

with tab4:
    docs.render_docs()

with tab5:
    dados.render_dados()

# ======================RODAPÉ (GLOBAL)
render_footer()
