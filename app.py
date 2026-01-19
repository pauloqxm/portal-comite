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

WIDGET_ID = "3ED61474B48BE397410802603320372A"


def inject_gptmaker_widget():
    """
    Injeta o float.js do GPTMaker no DOM do Streamlit (Railway ok).
    Ao fechar o chat, troca o contextId e recarrega o iframe,
    para a próxima abertura começar uma conversa nova.
    """
    html = f"""
    <script>
    (function() {{
      const WIDGET_ID = "{WIDGET_ID}";
      const FLOAT_JS = "https://app.gptmaker.ai/widget/" + WIDGET_ID + "/float.js";
      const IFRAME_BASE = "https://app.gptmaker.ai/widget/" + WIDGET_ID + "/iframe?floating=true";
      const LS_KEY = "gptmaker_context_id_" + WIDGET_ID;

      function newContextId() {{
        return "ctx_" + Date.now() + "_" + Math.random().toString(16).slice(2);
      }}

      function getOrCreateContextId() {{
        try {{
          let v = parent.localStorage.getItem(LS_KEY);
          if (!v) {{
            v = newContextId();
            parent.localStorage.setItem(LS_KEY, v);
          }}
          return v;
        }} catch (e) {{
          return newContextId();
        }}
      }}

      function setContextId(v) {{
        try {{ parent.localStorage.setItem(LS_KEY, v); }} catch (e) {{}}
      }}

      function loadFloatOnce() {{
        const doc = parent.document;
        if (!doc) return;

        if (doc.querySelector('script[data-gptmaker-float="1"][data-widget-id="' + WIDGET_ID + '"]')) {{
          return;
        }}

        const s = doc.createElement("script");
        s.async = true;
        s.src = FLOAT_JS;
        s.setAttribute("data-gptmaker-float", "1");
        s.setAttribute("data-widget-id", WIDGET_ID);
        doc.head.appendChild(s);
      }}

      function findWidgetIframe() {{
        const doc = parent.document;
        if (!doc) return null;
        const iframes = Array.from(doc.querySelectorAll("iframe"));
        return iframes.find(i => (i.src || "").includes("app.gptmaker.ai/widget/" + WIDGET_ID + "/iframe"));
      }}

      function forceIframeUrl(iframe, contextId) {{
        try {{
          const url = new URL(iframe.src || IFRAME_BASE);
          url.searchParams.set("floating", "true");
          url.searchParams.set("contextId", contextId);
          url.searchParams.set("__ts", String(Date.now()));
          iframe.src = url.toString();
        }} catch (e) {{
          iframe.src = IFRAME_BASE + "&contextId=" + encodeURIComponent(contextId) + "&__ts=" + Date.now();
        }}
      }}

      loadFloatOnce();

      let lastOpen = null;

      const timer = setInterval(() => {{
        const iframe = findWidgetIframe();
        if (!iframe) return;

        // Garante que existe contextId no iframe, senão ele reaproveita conversa
        const ctx = getOrCreateContextId();
        if (!(iframe.src || "").includes("contextId=")) {{
          forceIframeUrl(iframe, ctx);
        }}

        // Detecta aberto/fechado por tamanho real
        const rect = iframe.getBoundingClientRect();
        const openNow = rect.width > 10 && rect.height > 10;

        if (lastOpen === null) {{
          lastOpen = openNow;
          return;
        }}

        const closedNow = !openNow;

        // Transição ABERTO -> FECHADO
        if (lastOpen && closedNow) {{
          const fresh = newContextId();
          setContextId(fresh);

          // Recarrega o iframe "por baixo" já com contexto novo,
          // pra quando abrir de novo, vir zerado e sem tela branca.
          forceIframeUrl(iframe, fresh);
        }}

        lastOpen = openNow;
      }}, 700);

      // Segurança: se o Streamlit recriar o DOM, não deixa acumular interval duplicado
      window.addEventListener("beforeunload", () => {{
        try {{ clearInterval(timer); }} catch (e) {{}}
      }});
    }})();
    </script>
    """
    components.html(html, height=0, width=0)


inject_gptmaker_widget()

# ----------------- BARRA FIXA (HEADER) ------------
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

# ====================== RODAPÉ (GLOBAL)
render_footer()
