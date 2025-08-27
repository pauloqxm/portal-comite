import streamlit as st
import pandas as pd
from html import escape
import re
import base64

GOOGLESHEET_URL = "https://docs.google.com/spreadsheets/d/1A9Ibbij0aDUbFzVdqyl1FmGAbulFnylOHeU_qFdpjgs/edit?gid=0#gid=0"

THUMB_SIZE = "w150"   # miniatura
FULL_SIZE  = "w2000"  # ao clicar

def _gsheet_to_csv_url(url: str) -> str:
    try:
        sheet_id = url.split("/d/")[1].split("/")[0]
        gid = "0"
        if "gid=" in url:
            gid = url.split("gid=")[-1].split("&")[0].split("#")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    except Exception:
        return url

# ---------------- Google Drive helpers ----------------
def _extract_gdrive_id(url: str) -> str:
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    m = re.search(r"/file/d/([^/]+)/", url)  # /file/d/<ID>/view
    if m: return m.group(1)
    m = re.search(r"[?&]id=([^&]+)", url)    # ?id=<ID>
    if m: return m.group(1)
    m = re.search(r"/uc\?[^#]*[?&]id=([^&]+)", url)  # /uc?...&id=<ID>
    if m: return m.group(1)
    return ""

def gdrive_urls(url: str, thumb_size=THUMB_SIZE, full_size=FULL_SIZE):
    """
    Retorna (thumb, full, fallback) para imagens do Drive.
    Se não for Drive, retorna (url, url, "").
    """
    if not url:
        return "", "", ""
    fid = _extract_gdrive_id(url)
    if not fid:
        # não é Drive (ou formato não reconhecido)
        clean = url.strip()
        return clean, clean, ""
    thumb = f"https://drive.google.com/thumbnail?id={fid}&sz={thumb_size}"
    full  = f"https://drive.google.com/thumbnail?id={fid}&sz={full_size}"
    fb    = f"https://drive.google.com/uc?export=view&id={fid}"
    return thumb, full, fb

# Placeholder cinza (SVG inline) se tudo falhar
_PLACEHOLDER_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 200'>
  <rect width='320' height='200' fill='#f2f4f7'/>
  <text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle'
        fill='#9aa0a6' font-family='Segoe UI, Roboto, sans-serif' font-size='14'>
    capa indisponível
  </text>
</svg>"""
_PLACEHOLDER_DATAURI = "data:image/svg+xml;base64," + base64.b64encode(_PLACEHOLDER_SVG.encode()).decode()

def _img_clickable_with_fallback(thumb: str, full: str, fallback: str, alt: str):
    """
    Gera <a><img/></a>. Se a miniatura der erro, troca para fallback via onerror.
    """
    img_src = escape(thumb or fallback or _PLACEHOLDER_DATAURI, quote=True)
    img_fb  = escape(fallback or _PLACEHOLDER_DATAURI, quote=True)
    href    = escape(full or fallback or "#", quote=True)
    alt_txt = escape(alt or "capa")

    return (
        f'<a href="{href}" target="_blank" rel="noopener">'
        f'  <img src="{img_src}" alt="{alt_txt}" '
        f'       style="width:100%;height:auto;display:block;" '
        f'       onerror="this.onerror=null;this.src=\'{img_fb}\';" />'
        f'</a>'
    )

@st.cache_data(ttl=600)
def load_publicacoes_from_gsheet(url: str) -> pd.DataFrame:
    csv_url = _gsheet_to_csv_url(url)
    df = pd.read_csv(csv_url, dtype="string").fillna("")
    expected = ["Capa_link","Título","Ano da Publicação","Categoria","Resumo","Link"]
    df.columns = [str(c).strip() for c in df.columns]
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    return df[expected]

def _card_button(href: str, label: str = "Visualizar"):
    href = (href or "").strip()
    if not href:
        return '<span class="btn disabled">Indisponível</span>'
    safe = escape(href, quote=True)
    return f'<a class="btn" href="{safe}" target="_blank" rel="noopener">🔗 {escape(label)}</a>'

def render_publicacoes():
    st.title("📚 Publicações/Acervo")

    st.markdown(
        """
<style>
.card{ border:1px solid #e6e6e6; border-radius:14px; overflow:hidden;
       background:linear-gradient(180deg,#ffffff 0%, #fafafa 100%);
       box-shadow:0 6px 16px rgba(0,0,0,.06); }
.card-body{ padding:10px 12px 14px; }
.card-title{ font-weight:700; color:#1f2d3d; font-size:15px; margin:6px 0 4px; }
.card-meta{ color:#3a5f3a; font-size:12px; margin-bottom:6px; }
.card-resumo{ color:#2c3e50; font-size:13px; line-height:1.45; min-height:44px; }
.img-wrap{ width:100%; aspect-ratio:3/2; background:#f2f4f7; display:flex; align-items:center; justify-content:center; }
.btn{ display:inline-block; padding:6px 10px; margin-top:8px;
      background:#228B22; color:#fff !important; text-decoration:none; border-radius:8px; font-size:13px;
      transition: filter .2s ease; }
.btn:hover{ filter:brightness(0.95); }
.btn.disabled{ background:#9aa0a6; pointer-events:none; }
</style>
""",
        unsafe_allow_html=True,
    )

    try:
        df = load_publicacoes_from_gsheet(GOOGLESHEET_URL)
    except Exception as e:
        st.error(f"Erro ao carregar a planilha: {e}")
        return

    if df.empty:
        st.info("Não há publicações no momento.")
        return

    st.markdown(f"**{len(df)} publicações encontradas**")

    for c in df.columns:
        df[c] = df[c].astype(str).fillna("")

    n_cols = 4
    rows = (len(df) + n_cols - 1) // n_cols

    idx = 0
    for _ in range(rows):
        cols = st.columns(n_cols, gap="small")
        for col in cols:
            if idx >= len(df):
                break
            item = df.iloc[idx]; idx += 1

            capa_raw = item["Capa_link"].strip()
            thumb_url, full_url, fb_url = gdrive_urls(capa_raw, THUMB_SIZE, FULL_SIZE)

            titulo = item["Título"].strip()
            ano    = item["Ano da Publicação"].strip()
            cat    = item["Categoria"].strip()
            resumo = item["Resumo"].strip()
            link   = item["Link"].strip()

            max_chars = 220
            resumo_show = (resumo[:max_chars].rstrip() + "…") if len(resumo) > max_chars else resumo

            with col:
                st.markdown('<div class="card">', unsafe_allow_html=True)

                # Capa clicável com fallback (thumbnail -> uc?export=view -> placeholder)
                cover_html = _img_clickable_with_fallback(thumb_url, full_url, fb_url, alt=titulo or "capa")
                st.markdown(cover_html, unsafe_allow_html=True)

                body = []
                body.append('<div class="card-body">')
                body.append(f'<div class="card-title">{escape(titulo) if titulo else "Sem título"}</div>')
                meta = " • ".join([m for m in [ano, cat] if m])
                if meta:
                    body.append(f'<div class="card-meta">{escape(meta)}</div>')
                if resumo_show:
                    body.append(f'<div class="card-resumo">{escape(resumo_show)}</div>')
                body.append(_card_button(link, "Visualizar"))
                body.append('</div>')

                st.markdown("".join(body), unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
