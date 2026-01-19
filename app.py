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


# ---------------- BOTÃO GPTMAKER WIDGET (FLOAT) ----------------

def inject_gptmaker_widget():
    components.html(
        r"""
        <script>
        (function () {
          try {
            var doc = (window.parent && window.parent.document) ? window.parent.document : document;

            // Carrega o float.js uma única vez
            if (!doc.getElementById("gptmaker-float-loader")) {
              var s = doc.createElement("script");
              s.id = "gptmaker-float-loader";
              s.async = true;
              s.src = "https://app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/float.js";
              doc.head.appendChild(s);
            }

            function getIfr() {
              return doc.querySelector('iframe[src*="app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/iframe"]');
            }

            function isOpen(ifr){
              if (!ifr) return false;
              var r = ifr.getBoundingClientRect();
              return (r.width > 10 && r.height > 10);
            }

            function isClosed(ifr){
              if (!ifr) return false;
              var r = ifr.getBoundingClientRect();
              return (r.width === 0 && r.height === 0);
            }

            function boostZ(ifr){
              if (!ifr) return;
              try { ifr.style.zIndex = "2147483647"; } catch(e){}
            }

            function hardResetIframe(ifr){
              try {
                var src = (ifr.getAttribute("src") || "").split("#")[0];
                if (!src) return;

                // remove __ts antigo
                src = src.replace(/([?&])__ts=\d+/g, "");
                src = src.replace(/[?&]$/, "");

                // cria src novo
                var sep = src.indexOf("?") >= 0 ? "&" : "?";
                var newSrc = src + sep + "__ts=" + Date.now();

                // remove e recria (reset forte)
                var parent = ifr.parentElement;
                var next = ifr.nextSibling;
                ifr.remove();

                var n = doc.createElement("iframe");
                n.src = newSrc;
                n.allow = "clipboard-read; clipboard-write; microphone; camera; autoplay";
                n.style.border = "0";
                n.style.position = "fixed"; // se o widget reposicionar, não atrapalha
                n.style.width = "0px";
                n.style.height = "0px";
                n.style.opacity = "0";
                n.style.pointerEvents = "none";

                if (parent) {
                  if (next) parent.insertBefore(n, next);
                  else parent.appendChild(n);
                } else {
                  doc.body.appendChild(n);
                }
              } catch(e){}
            }

            var wasOpen = false;

            setInterval(function(){
              var ifr = getIfr();
              if (!ifr) return;

              boostZ(ifr);

              var openNow = isOpen(ifr);
              var closedNow = isClosed(ifr);

              // ABERTO -> FECHADO: reseta forte
              if (wasOpen && closedNow) {
                hardResetIframe(ifr);
              }

              wasOpen = openNow;
            }, 300);

          } catch (e) {
            console.log("GPTMaker hard-reset error:", e);
          }
        })();
        </script>
        """,
        height=0,
        width=0
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







