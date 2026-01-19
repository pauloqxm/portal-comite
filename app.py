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

            // --- 1) Carrega o widget uma vez ---
            if (!doc.getElementById("gptmaker-float-loader")) {
              var s = doc.createElement("script");
              s.id = "gptmaker-float-loader";
              s.async = true;
              s.src = "https://app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/float.js";
              doc.head.appendChild(s);
            }

            // --- 2) Limpa storage do GPTMaker ---
            function clearGPTMakerStorage() {
              try {
                var keys = Object.keys(localStorage || {});
                keys.forEach(function(k){
                  var kk = (k || "").toLowerCase();
                  if (kk.includes("gptmaker") || kk.includes("gpt") || kk.includes("chat")) {
                    localStorage.removeItem(k);
                  }
                });

                var skeys = Object.keys(sessionStorage || {});
                skeys.forEach(function(k){
                  var kk = (k || "").toLowerCase();
                  if (kk.includes("gptmaker") || kk.includes("gpt") || kk.includes("chat")) {
                    sessionStorage.removeItem(k);
                  }
                });
              } catch(e){}
            }

            // --- 3) Acha o iframe do GPTMaker (o teu src é esse) ---
            function getGptIframe() {
              return doc.querySelector('iframe[src*="app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/iframe?floating=true"]')
                  || doc.querySelector('iframe[src*="app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/iframe"]')
                  || doc.querySelector('iframe[src*="app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A"]');
            }

            // --- 4) Detecta aberto/fechado por tamanho do iframe ---
            // Ajuste fino: aberto quando >= 260x260 (igual ao teu 458x386)
            var OPEN_W = 260, OPEN_H = 260;
            var wasOpen = false;

            function isOpenBySize(ifr) {
              if (!ifr) return false;
              var r = ifr.getBoundingClientRect();
              return (r.width >= OPEN_W && r.height >= OPEN_H);
            }

            // --- 5) Z-index alto pra não ficar atrás do header ---
            function boostZIndex(ifr) {
              if (!ifr) return;
              try { ifr.style.zIndex = "2147483647"; } catch(e){}
            }

            // --- 6) Loop: se estava aberto e fechou => limpa histórico ---
            setInterval(function () {
              var ifr = getGptIframe();
              if (!ifr) return;

              boostZIndex(ifr);

              var open = isOpenBySize(ifr);

              // Transição: ABERTO -> FECHADO
              if (wasOpen && !open) {
                clearGPTMakerStorage();

                // Extra (forte): “reinicia” o iframe pra garantir conversa zerada
                // sem depender só do storage
                try {
                  var src = ifr.getAttribute("src") || "";
                  if (src) {
                    var sep = src.indexOf("?") >= 0 ? "&" : "?";
                    ifr.setAttribute("src", src.split("#")[0].replace(/([?&])__ts=\d+/,"$1").replace(/&$/,"") + sep + "__ts=" + Date.now());
                  }
                } catch(e){}
              }

              wasOpen = open;
            }, 500);

          } catch (e) {
            console.log("GPTMaker close-reset error:", e);
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




