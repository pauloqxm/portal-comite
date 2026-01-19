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

def inject_gptmaker_widget_debug():
    components.html(
        r"""
        <script>
        (function () {
          var doc = (window.parent && window.parent.document) ? window.parent.document : document;

          // overlay de debug (canto inferior esquerdo)
          function ensureDebugBox(){
            var box = doc.getElementById("__gpt_debug_box");
            if (box) return box;

            box = doc.createElement("div");
            box.id = "__gpt_debug_box";
            box.style.position = "fixed";
            box.style.left = "12px";
            box.style.bottom = "12px";
            box.style.zIndex = "2147483647";
            box.style.background = "rgba(0,0,0,0.75)";
            box.style.color = "#fff";
            box.style.padding = "8px 10px";
            box.style.borderRadius = "8px";
            box.style.fontFamily = "monospace";
            box.style.fontSize = "12px";
            box.style.maxWidth = "320px";
            box.style.whiteSpace = "pre-line";
            doc.body.appendChild(box);
            return box;
          }

          var box = ensureDebugBox();

          function log(msg){
            box.textContent = msg;
          }

          function clearGPTMakerStorage() {
            var removed = [];
            try {
              Object.keys(localStorage || {}).forEach(function(k){
                var kk = (k || "").toLowerCase();
                if (kk.includes("gptmaker") || kk.includes("gpt") || kk.includes("chat")) {
                  removed.push("LS:" + k);
                  localStorage.removeItem(k);
                }
              });
              Object.keys(sessionStorage || {}).forEach(function(k){
                var kk = (k || "").toLowerCase();
                if (kk.includes("gptmaker") || kk.includes("gpt") || kk.includes("chat")) {
                  removed.push("SS:" + k);
                  sessionStorage.removeItem(k);
                }
              });
            } catch(e){}
            return removed;
          }

          function getIfr() {
            return doc.querySelector('iframe[src*="app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/iframe"]');
          }

          // carrega o widget se não existir
          if (!doc.getElementById("gptmaker-float-loader")) {
            var s = doc.createElement("script");
            s.id = "gptmaker-float-loader";
            s.async = true;
            s.src = "https://app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/float.js";
            doc.head.appendChild(s);
          }

          var wasOpen = false;
          var lastEvent = "init";

          setInterval(function(){
            var ifr = getIfr();

            if (!ifr) {
              log("GPT Debug\niframe: NAO ENCONTRADO\nultimo: " + lastEvent);
              return;
            }

            // z-index alto
            try { ifr.style.zIndex = "2147483647"; } catch(e){}

            var r = ifr.getBoundingClientRect();
            var openNow = (r.width > 10 && r.height > 10);
            var closedNow = (r.width === 0 && r.height === 0);

            if (wasOpen && closedNow) {
              var removed = clearGPTMakerStorage();
              lastEvent = "FECHOU -> limpou (" + removed.length + ")";
            }

            if (!wasOpen && openNow) {
              lastEvent = "ABRIU";
            }

            wasOpen = openNow;

            log(
              "GPT Debug\n" +
              "iframe src: " + (ifr.getAttribute("src") || "").slice(0, 60) + "...\n" +
              "w,h: " + r.width.toFixed(0) + " x " + r.height.toFixed(0) + "\n" +
              "openNow: " + openNow + " | closedNow: " + closedNow + "\n" +
              "ultimo: " + lastEvent
            );
          }, 300);

        })();
        </script>
        """,
        height=0,
        width=0
    )

# injeta o widget ANTES do header
inject_gptmaker_widget_debug()


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






