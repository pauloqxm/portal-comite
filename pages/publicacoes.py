import streamlit as st
import pandas as pd
from html import escape
import re

# ====================== CONFIG ======================
GOOGLESHEET_URL = "https://docs.google.com/spreadsheets/d/1A9Ibbij0aDUbFzVdqyl1FmGAbulFnylOHeU_qFdpjgs/edit?gid=0#gid=0"

# Tamanhos das imagens do Drive
THUMB_SIZE = "w150"   # miniatura na grade
FULL_SIZE  = "w2000"  # ao clicar, abre maior

def _gsheet_to_csv_url(url: str) -> str:
    try:
        sheet_id = url.split("/d/")[1].split("/")[0]
        gid = "0"
        if "gid=" in url:
            gid = url.split("gid=")[-1].split("&")[0].split("#")[0]
        return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    except Exception:
        return url

# -------- conversores Google Drive --------
def _extract_gdrive_id(url: str) -> str:
    if not url or not isinstance(url, str):
        return ""
    url = url.strip()
    m = re.search(r"/file/d/([^/]+)/", url)
    if m: return m.group(1)
    m = re.search(r"[?&]id=([^&]+)", url)
    if m: return m.group(1)
    m = re.search(r"/uc\?[^#]*[?&]id=([^&]+)", url)
    if m: return m.group(1)
    return ""

def gdrive_image_url(url: str, size: str = "w800") -> str:
    """Preferência: endpoint thumbnail do Drive com controle de tamanho."""
    fid = _extract_gdrive_id(url)
    if not fid:
        return (url or "").strip()
    return f"https://drive.google.com/thumbnail?id={fid}&sz={size}"

def gdrive_image_fallback(url: str) -> str:
    """Fallback simples (embed view)."""
    fid = _extract_gdrive_id(url)
    return f"https://drive.google.com/uc?export=view&id={fid}" if fid else (url or "").strip()

# -------- carregamento da planilha --------
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

def _clickable_cover(thumb_url: str, full_url: str, alt: str = "capa"):
    """Renderiza <a><img/></a> com largura responsiva."""
    if not thumb_url:
        return '<div class="img-wrap">sem capa</div>'
    return (
        f'<a href="{escape(full_url, quote=True)}" target="_blank" rel="noopener">'
        f'  <img src="{escape(thumb_url, quote=True)}" alt="{escape(alt)}" '
        f'       style="width:100%;height:auto;display:block;" />'
        f'</a>'
    )

def render_publicacoes():
    st.title("📚 Publicações/Acervo")
    st.markdown(
        """
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Publicações organizadas em grade com capa e detalhes<br>
    • Acesso rápido ao arquivo de cada item
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

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
            # Miniatura e versão grande
            thumb_url = gdrive_image_url(capa_raw, size=THUMB_SIZE) if capa_raw else ""
            full_url  = gdrive_image_url(capa_raw, size=FULL_SIZE)  if capa_raw else ""

            titulo = item["Título"].strip()
            ano = item["Ano da Publicação"].strip()
            cat = item["Categoria"].strip()
            resumo = item["Resumo"].strip()
            link = item["Link"].strip()

            max_chars = 220
            resumo_show = (resumo[:max_chars].rstrip() + "…") if len(resumo) > max_chars else resumo

            with col:
                st.markdown('<div class="card">', unsafe_allow_html=True)

                # Capa clicável (abre maior)
                st.markdown(_clickable_cover(thumb_url, full_url, alt=titulo or "capa"), unsafe_allow_html=True)

                # Corpo
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
