import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from pages import (
    home,
    acudes,
    docs,
    dados,
    vazoes_dashboard,
    fale_conosco,
    o_comite,
    publicacoes,
    acompanhamento_diario,
)
from utils.common import render_header, render_footer


# ---------------- CONFIG GERAL ----------------
st.set_page_config(
    page_title="Comitê Transparente",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------- GPTMAKER WIDGET (FLOAT) ----------------
def inject_gptmaker_widget():
    components.html(
        r"""
        <script>
        (function () {
          try {
            // tenta acessar o DOM principal (fora do iframe do Streamlit)
            var doc = (window.parent && window.parent.document)
              ? window.parent.document
              : document;

            // evita duplicar em reruns do Streamlit
            if (doc.getElementById("gptmaker-float-loader")) return;

            var s = doc.createElement("script");
            s.id = "gptmaker-float-loader";
            s.async = true;
            s.src = "https://app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/float.js";
            doc.head.appendChild(s);

            // força z-index alto para não ficar atrás do header fixo
            var tries = 0;
            var t = setInterval(function () {
              tries++;

              var els = doc.querySelectorAll(
                '[id*="gptmaker"], [class*="gptmaker"], iframe[src*="gptmaker"], div[style*="position: fixed"]'
              );

              els.forEach(function (el) {
                try {
                  el.style.zIndex = "2147483647";
                } catch (e) {}
              });

              if (tries > 60) clearInterval(t);
            }, 200);

          } catch (e) {
            console.log("GPTMaker inject error:", e);
          }
        })();
        </script>
        """,
        height=0,
        width=0,
    )


# injeta o widget ANTES do header
inject_gptmaker_widget()


# ----------------- BARRA FIXA (HEADER) ----------------
render_header()


# =========================
# CRIAÇÃO DAS ABAS
# =========================
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(
    [
        "🏠 Inicial",
        "💧 Painel da Operação",
        "🗺️ Açudes Monitorados",
        "📈 Situação das Sedes",
        "💬 Alocação Negociada",
        "🙋🏽 O Comitê",
        "📚 Publicações/Acervo",
        "📝 Acompanhamento Diário",
        "✉️ Fale Conosco",
    ]
)

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
    o_comite.render_o_comite()

with tab7:
    publicacoes.render_publicacoes()

with tab8:
    acompanhamento_diario.render_acompanhamento_diario()

with tab9:
    fale_conosco.render_fale_conosco()


# ----------------- RODAPÉ (GLOBAL) ----------------
render_footer()
