
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.common import render_header

st.set_page_config(page_title="📈 Simulações", layout="wide")
render_header()

st.title("📈 Simulações")

st.markdown("""
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Linha comparativa de <b>Cota Inicial (m)</b> e <b>Cota Dia (m)</b><br>
    • Filtros por <b>Data</b> e <b>Açude</b><br>
    • Linha de <b>Volume (m³)</b> ao longo do tempo
  </p>
</div>
""", unsafe_allow_html=True)

sheet_url = "https://docs.google.com/spreadsheets/d/1C40uaNmLUeu-k_FGEPZOgF8FwpSU00C9PtQu8Co4AUI/export?format=csv"
try:
    df = pd.read_csv(sheet_url, sep=',', decimal=',')
except Exception as e:
    st.error(f"Não foi possível ler a planilha: {e}")
    st.stop()

colunas = ["Data", "Açude", "Município", "Região Hidrográfica", "Cota Inicial (m)", "Cota Dia (m)", "Volume (m³)",
           "Volume (%)", "Evapor. Parcial (mm)", "Cota Interm. (m)", "Volume Interm. (m³)",
           "Liberação (m³/s)", "Liberação (m³)", "Volume Final (m³)", "Cota Final (m)", "Coordendas"]
faltantes = [c for c in colunas if c not in df.columns]
if faltantes:
    st.error(f"As seguintes colunas não foram encontradas na planilha: {', '.join(faltantes)}")
    st.stop()

df = df[colunas].copy()
df["Data"] = pd.to_datetime(df["Data"].astype(str).str.strip(), dayfirst=True, errors="coerce")
df = df.dropna(subset=["Data"])

colunas_numericas = ["Cota Inicial (m)", "Cota Dia (m)", "Volume (m³)", "Volume (%)", "Evapor. Parcial (mm)"]
for col in colunas_numericas:
    df[col] = pd.to_numeric(df[col], errors='coerce')

def formatar_volume(volume):
    if volume >= 1_000_000:
        return f"{volume / 1_000_000:.2f} milhões/m³"
    elif volume > 0:
        return f"{volume / 1_000:.2f} mil/m³"
    else:
        return "0 m³"

df['Volume_formatado'] = df['Volume (m³)'].apply(formatar_volume)

with st.container():
    with st.expander("☰ Filtros (clique para expandir)", expanded=True):
        c1, c2 = st.columns([2, 3])
        with c1:
            opcoes_acudes = sorted(df["Açude"].dropna().unique().tolist())
            acudes_sel = st.multiselect("Açude", options=opcoes_acudes, default=opcoes_acudes)
        with c2:
            datas_validas = df["Data"]
            if not datas_validas.empty:
                data_min = datas_validas.min().date()
                data_max = datas_validas.max().date()
                periodo = st.date_input("Período", value=(data_min, data_max), min_value=data_min, max_value=data_max, format="DD/MM/YYYY")
            else:
                periodo = None

dff = df.copy()
if acudes_sel:
    dff = dff[dff["Açude"].isin(acudes_sel)]
if periodo:
    if len(periodo) == 1:
        ini = fim = pd.to_datetime(periodo[0])
    else:
        ini, fim = [pd.to_datetime(d) for d in periodo]
    dff = dff[(dff["Data"] >= ini) & (dff["Data"] <= fim)]

if dff.empty:
    st.info("Não há dados para os filtros selecionados.")
    st.stop()

dff = dff.sort_values(["Açude", "Data"])

st.subheader("📈 Cotas (Cota Inicial x Cota Dia)")
fig_cotas = go.Figure()
for acude in sorted(dff["Açude"].dropna().unique()):
    base = dff[dff["Açude"] == acude].sort_values("Data")
    fig_cotas.add_trace(go.Scatter(x=base["Data"], y=base["Cota Inicial (m)"], mode="lines+markers", name=f"{acude} - Cota Inicial (m)", hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"))
    fig_cotas.add_trace(go.Scatter(x=base["Data"], y=base["Cota Dia (m)"], mode="lines+markers", name=f"{acude} - Cota Dia (m)", hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"))
fig_cotas.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), xaxis_title="Data", yaxis_title="Cota (m)", height=480)
st.plotly_chart(fig_cotas, use_container_width=True, config={"displaylogo": False})

st.subheader("📈 Volume (m³)")
fig_vol = go.Figure()
for acude in sorted(dff["Açude"].dropna().unique()):
    base = dff[dff["Açude"] == acude].sort_values("Data")
    fig_vol.add_trace(go.Scatter(x=base["Data"], y=base["Volume (m³)"], mode="lines+markers", name=f"{acude} - Volume (m³)", hovertemplate="%{x|%d/%m/%Y} • %{y:,.0f} m³<extra></extra>"))
fig_vol.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), xaxis_title="Data", yaxis_title="Volume (m³)", height=420)
st.plotly_chart(fig_vol, use_container_width=True, config={"displaylogo": False})

with st.expander("📋 Ver dados filtrados"):
    st.dataframe(dff.sort_values(["Açude", "Data"], ascending=[True, False]), use_container_width=True)
