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

            function clearGPTMakerStorage() {
              try {
                Object.keys(localStorage || {}).forEach(function(k){
                  var kk = (k || "").toLowerCase();
                  if (kk.includes("gptmaker") || kk.includes("gpt") || kk.includes("chat")) localStorage.removeItem(k);
                });
                Object.keys(sessionStorage || {}).forEach(function(k){
                  var kk = (k || "").toLowerCase();
                  if (kk.includes("gptmaker") || kk.includes("gpt") || kk.includes("chat")) sessionStorage.removeItem(k);
                });
              } catch(e){}
            }

            function loadWidget() {
              if (doc.getElementById("gptmaker-float-loader")) return;
              var s = doc.createElement("script");
              s.id = "gptmaker-float-loader";
              s.async = true;
              s.src = "https://app.gptmaker.ai/widget/3ED61474B48BE397410802603320372A/float.js";
              doc.head.appendChild(s);
            }

            // Detecta se o chat está aberto (heurística bem mais assertiva)
            function isChatOpen() {
              // 1) iframe do gptmaker
              var ifr = doc.querySelector('iframe[src*="gptmaker"], iframe[src*="app.gptmaker.ai"]');
              if (ifr) {
                var r = ifr.getBoundingClientRect();
                if (r.width > 10 && r.height > 10) return true;
              }

              // 2) qualquer container do widget visível (classes/ids variam)
              var nodes = doc.querySelectorAll('[id*="gptmaker"], [class*="gptmaker"], [class*="chat"], [id*="chat"]');
              for (var i=0; i<nodes.length; i++){
                var el = nodes[i];
                if (!el || !el.getBoundingClientRect) continue;
                var rr = el.getBoundingClientRect();
                if (rr.width > 120 && rr.height > 120) {
                  var st = window.getComputedStyle(el);
                  if (st && st.display !== "none" && st.visibility !== "hidden" && st.opacity !== "0") return true;
                }
              }

              return false;
            }

            // Mantém estado anterior para detectar transição aberto -> fechado
            var wasOpen = false;

            function checkCloseAndClear() {
              var open = isChatOpen();
              if (wasOpen && !open) {
                clearGPTMakerStorage();
              }
              wasOpen = open;
            }

            // 1) Carrega widget
            loadWidget();

            // 2) Observa mudanças no DOM (abrir/fechar costuma mexer no DOM)
            var obs = new MutationObserver(function(){
              checkCloseAndClear();
              boostZIndex();
            });
            obs.observe(doc.documentElement, { childList: true, subtree: true, attributes: true });

            // 3) Fallback por intervalo (se fechar só via CSS, sem mutação relevante)
            setInterval(function(){
              checkCloseAndClear();
              boostZIndex();
            }, 500);

            // 4) Clique em qualquer coisa do widget. Após o clique, re-checa e se fechou, limpa.
            doc.addEventListener("click", function(e){
              try {
                var t = e.target;
                if (!t) return;

                // Se o clique foi dentro de algo que parece ser do widget
                var hit = false;
                var p = t;
                for (var i=0; i<8 && p; i++){
                  var idc = ((p.id||"") + " " + (p.className||"")).toLowerCase();
                  if (idc.includes("gptmaker") || idc.includes("chat")) { hit = true; break; }
                  p = p.parentElement;
                }
                if (!hit) return;

                // dá tempo do widget abrir/fechar e depois verifica
                setTimeout(function(){
                  checkCloseAndClear();
                  boostZIndex();
                }, 300);
              } catch(err){}
            }, true);

            // z-index alto pra não sumir atrás do header
            function boostZIndex() {
              try {
                var els = doc.querySelectorAll(
                  '[id*="gptmaker"], [class*="gptmaker"], iframe[src*="gptmaker"], iframe[src*="app.gptmaker.ai"]'
                );
                els.forEach(function(el){
                  try { el.style.zIndex = "2147483647"; } catch(e){}
                });
              } catch(e){}
            }
            boostZIndex();

            // Estado inicial
            wasOpen = isChatOpen();

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



