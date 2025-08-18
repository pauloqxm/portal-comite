
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
    pagina_inical.render_home()

with tab2:
    painel_vazoes.render_vazoes_dashboard()

with tab3:
    acudes_monitorados.render_acudes()

with tab4:
    sistuacao_sedes.render_dados()

with tab5:
    alocacao_negociada.render_docs()
    
with tab6:
    fale_conosco.render_fale_conosco() # Chamando a nova função

# ======================RODAPÉ (GLOBAL)
render_footer()





