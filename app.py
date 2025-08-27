import streamlit as st
import pandas as pd
from pages import home, acudes, docs, dados, vazoes_dashboard, fale_conosco, o_comite, publicacoes
from utils.common import render_header, render_footer

# ---------------- CONFIG GERAL ----------------
st.set_page_config(
    page_title="Comitê Transparente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"  # Adicione esta linha
)
# ----------------- BARRA FIXA (HEADER) ------------
render_header()

# =========================
# CRIAÇÃO DAS ABAS
# =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["🏠 Inicial", "💧 Painel da Operação", "🗺️ Açudes Monitorados", "📈 Situação das Sedes", "💬 Alocação Negociada", "✉️ Fale Conosco", "🙋🏽 O Comitê", "📚 Publicações/Acervo"])

with tab1:
    home.render_home()

with tab2:
    vazoes_dashboard.render_vazoes_dashboard()

with tab3:
    acudes.render_acudes()

with tab4:
    dados.render_dados()

with tab5:
    docs.render_docs()
    
with tab6:
    fale_conosco.render_fale_conosco()

with tab7:
    o_comite.render_o_comite()

with tab8:
    publicacoes.render_publicacoes()

# ======================RODAPÉ (GLOBAL)
render_footer()







