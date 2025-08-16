
import streamlit as st
from utils.common import render_header

st.set_page_config(page_title="Dashboard Vazões - Banabuiú", layout="wide")
render_header()

st.title("🌊 Painel Banabuiú")
st.markdown(
    """
    Bem-vindo! Use o menu lateral para navegar:
    - 🏠 Página Inicial
    - 🗺️ Açudes Monitorados
    - 📜 Documentos Oficiais
    - 📈 Simulações
    """
)
st.info("Dica: você pode colapsar/expandir filtros e escolher estilos de mapa nas páginas.")
