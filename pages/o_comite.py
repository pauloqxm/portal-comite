import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
from utils.common import load_o_comite_data

st.set_page_config(layout="wide")

def render_o_comite():
    st.title("🙋🏽 O Comitê")
    st.markdown(
        """
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Atas e apresentações das reuniões da Bacia do Banabuiú<br>
    • Organizadas por operação, reservatório e parâmetros<br>
    • Dados de vazão média aprovados
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    df = load_o_comite_data()
    if df is None or df.empty:
        st.info("Não há documentos disponíveis no momento.")
        return

SHEET_ID = "14Hb7N5yq4u-B3JN8Stpvpbdlt3sL0JxWUYpJK4fzLV8"
GID = "1572572584"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

st.title("📋 Conselho — Representantes e Localização")

@st.cache_data(show_spinner=False)
def load_data(url: str) -> pd.DataFrame:
    df = pd.read_csv(url, dtype=str)
    # limpa nomes de colunas (espaços extras)
    df.columns = [c.strip() for c in df.columns]
    # normaliza strings
    for c in df.columns:
        df[c] = df[c].astype(str).str.strip()
    # datas (se existirem)
    for c in ["Inicio do mandato", "Fim do mandato"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    # Coordenadas → Latitude/Longitude
    if "Coordenadas" in df.columns:
        coords = (
            df["Coordenadas"]
            .astype(str).str.strip()
            .str.replace(";", ",", regex=False)
            .str.replace("[()\\[\\]]", "", regex=True)
        )
        parts = coords.str.split(",", n=1, expand=True)
        if parts.shape[1] == 2:
            df["Latitude"]  = pd.to_numeric(parts[0].str.replace(" ", ""), errors="coerce")
            df["Longitude"] = pd.to_numeric(parts[1].str.replace(" ", ""), errors="coerce")
        else:
            df["Latitude"] = pd.NA
            df["Longitude"] = pd.NA
    return df

df = load_data(CSV_URL)
if df.empty:
    st.info("Planilha vazia ou inacessível.")
    st.stop()

# ======== FILTROS ========
st.markdown("### 🔎 Filtros")
fc1, fc2, fc3, fc4 = st.columns(4)

def options(colname):
    return sorted([x for x in df.get(colname, pd.Series(dtype=str)).dropna().unique() if str(x).strip() != ""])

with fc1:
    seg_sel = st.multiselect("Segmento", options("Segmento"), default=options("Segmento"))
with fc2:
    mun_sel = st.multiselect("Município", options("Município"), default=options("Município"))
with fc3:
    man_sel = st.multiselect("Mandato", options("Mandato"), default=options("Mandato"))
with fc4:
    fun_sel = st.multiselect("Função", options("Função"), default=options("Função"))

dff = df.copy()
if seg_sel: dff = dff[dff["Segmento"].isin(seg_sel)]
if mun_sel: dff = dff[dff["Município"].isin(mun_sel)]
if man_sel and "Mandato" in dff.columns: dff = dff[dff["Mandato"].isin(man_sel)]
if fun_sel and "Função" in dff.columns: dff = dff[dff["Função"].isin(fun_sel)]

if dff.empty:
    st.warning("Sem registros para os filtros selecionados.")
    st.stop()

# ======== LAYOUT 2 COLUNAS ========
col_tab, col_map = st.columns([0.48, 0.52])

# --- TABELA (coluna esquerda) ---
with col_tab:
    st.subheader("📑 Representantes")
    cols_tabela = ["Nome do(a) representante", "Instituição", "Função", "Segmento", "Diretoria"]
    # garante colunas existentes
    cols_exist = [c for c in cols_tabela if c in dff.columns]
    tab = dff[cols_exist].sort_values(by=cols_exist[0] if cols_exist else dff.columns[0])
    st.dataframe(
        tab,
        use_container_width=True,
        hide_index=True
    )

# --- MAPA (coluna direita) ---
with col_map:
    st.subheader("🗺️ Mapa dos Representantes")
    have_geo = {"Latitude", "Longitude"}.issubset(dff.columns)
    pontos = dff.dropna(subset=["Latitude", "Longitude"]) if have_geo else pd.DataFrame()

    if pontos.empty:
        st.info("Sem coordenadas válidas para exibir no mapa.")
    else:
        try:
            center = [pontos["Latitude"].astype(float).mean(), pontos["Longitude"].astype(float).mean()]
        except Exception:
            center = [-5.2, -39.5]

        m = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

        for _, row in pontos.iterrows():
            try:
                lat = float(row["Latitude"])
                lon = float(row["Longitude"])
            except Exception:
                continue

            nome = row.get("Nome do(a) representante", "N/A")
            inst = row.get("Instituição", "N/A")
            func = row.get("Função", "N/A")
            segm = row.get("Segmento", "N/A")
            mun  = row.get("Município", "N/A")

            popup = folium.Popup(
                f"""
                <div style="font-family:Arial; font-size:13px;">
                    <b>{nome}</b><br>
                    <b>Instituição:</b> {inst}<br>
                    <b>Função:</b> {func}<br>
                    <b>Segmento:</b> {segm}<br>
                    <b>Município:</b> {mun}
                </div>
                """,
                max_width=280
            )

            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color="#005BBB",
                fill=True,
                fill_color="#1f78b4",
                fill_opacity=0.9,
                tooltip=f"{nome} • {inst}",
                popup=popup
            ).add_to(m)

        folium_static(m, width=900, height=540)
