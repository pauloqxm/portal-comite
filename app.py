
import streamlit as st
import pandas as pd
from pages import home, acudes, docs, dados, vazoes_dashboard, fale_conosco # Importe a nova página
from utils.common import render_header, render_footer

# ---------------- CONFIG GERAL ----------------
st.set_page_config(
    page_title="📊 Comitê Transparente",
    page_icon="💧",
    layout="wide"
)

# ----------------- BARRA FIXA (HEADER) ------------
render_header()

# =========================
# CRIAÇÃO DAS ABAS
# =========================
# Adicionando uma nova aba para "Fale Conosco"
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 Página Inicial", "💧 Painel de Vazões", "🗺️ Açudes Monitorados", "📈 Situação das Sedes", "🗪 Alocação Negociada", "✉️ Fale Conosco"])

with tab1:
    🏠 Página Inicial.render_home()

with tab2:
    💧 Painel de Vazões.render_vazoes_dashboard()

with tab3:
    🗺️ Açudes Monitorados.render_acudes()

with tab4:
    📈 Situação das Sedes.render_dados()

with tab5:
    🗪 Alocação Negociada.render_docs()
    
with tab6:
    ✉️ Fale Conosco.render_fale_conosco() # Chamando a nova função

# ======================RODAPÉ (GLOBAL)
render_footer()



