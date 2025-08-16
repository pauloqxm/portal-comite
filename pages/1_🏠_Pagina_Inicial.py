import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
import json
import base64
import unicodedata2  # pode ser removido se não usar
import altair as alt  # pode ser removido se não usar
from datetime import datetime, timedelta, timezone
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MiniMap, MousePosition, MeasureControl, MarkerCluster
from utils.common import render_header, load_geojsons

st.set_page_config(page_title="🏠 Página Inicial", layout="wide")
render_header()

@st.cache_data(ttl=300)
def carregar_dados():
    url = "https://docs.google.com/spreadsheets/d/1pbNcZ9hS8DhotdkYuPc8kIOy5dgyoYQb384-jgqLDfA/export?format=csv"
    df = pd.read_csv(url)
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
    df["Mês"] = df["Data"].dt.to_period("M").astype(str)
    return df

def convert_vazao(series, unidade):
    if unidade == "m³/s":
        return series / 1000.0, "m³/s"
    return series, "L/s"

df = carregar_dados()

cA1, cA2, cA3 = st.columns([1, 1, 1])
with cA1:
    if st.button("🔄 Atualizar agora"):
        carregar_dados.clear()
        df = carregar_dados()
        st.success("Atualizado.")

st.markdown(
    """
    <style>
    .custom-title { font-family: 'Segoe UI', Roboto, sans-serif !important; font-size: 20px !important;
    font-weight: 700 !important; color: #006400 !important; text-align: center !important; margin: 8px 0 10px 0 !important;
    padding: 12px 22px !important; position: relative !important; display: flex !important; align-items: center !important;
    justify-content: center !important; gap: 8px !important; background: rgba(144, 238, 144, 0.15) !important; border-radius: 8px !important;
    box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important; }
    .custom-title::before, .custom-title::after { content: ""; flex: 1; height: 2px; background: linear-gradient(90deg, transparent, #228B22); border-radius: 2px; }
    .custom-title::after { background: linear-gradient(90deg, #228B22, transparent); }
    .custom-title span { display: inline-flex; align-items: center; justify-content: center; font-size: 18px; }
    @media (max-width: 600px) { .custom-title { flex-direction: column; gap: 4px; padding: 6px 12px; }
    .custom-title::before, .custom-title::after { width: 70%; height: 1.5px; } }
    </style>
    <h1 class="custom-title"><span>💧</span> Painel de Vazões </span></h1>
    """, unsafe_allow_html=True
)

with st.expander("☰ Filtros", expanded=False):
    st.markdown('<div class="filter-card"><div class="filter-title">Opções de Filtro</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        estacoes = st.multiselect("🏞️ Reservatório", df["Reservatório Monitorado"].dropna().unique())
        operacao = st.multiselect("🔧 Operação", df["Operação"].dropna().unique())
    with col2:
        meses = st.multiselect("📆 Mês", df["Mês"].dropna().unique())
    col3, col4 = st.columns(2)
    with col3:
        datas_disponiveis = df["Data"].dropna().sort_values()
        data_min = datas_disponiveis.min()
        data_max = datas_disponiveis.max()
        intervalo_data = st.date_input("📅 Intervalo", (data_min, data_max), format="DD/MM/YYYY")
    with col4:
        unidade_sel = st.selectbox("🧪 Unidade", ["L/s", "m³/s"], index=0)
    st.markdown("</div>", unsafe_allow_html=True)

df_filtrado = df.copy()
if estacoes:
    df_filtrado = df_filtrado[df_filtrado["Reservatório Monitorado"].isin(estacoes)]
if operacao:
    df_filtrado = df_filtrado[df_filtrado["Operação"].isin(operacao)]
if meses:
    df_filtrado = df_filtrado[df_filtrado["Mês"].isin(meses)]
if isinstance(intervalo_data, tuple) and len(intervalo_data) == 2:
    inicio, fim = intervalo_data
    df_filtrado = df_filtrado[(df_filtrado["Data"] >= pd.to_datetime(inicio)) & (df_filtrado["Data"] <= pd.to_datetime(fim))]

st.subheader("📈 Evolução da Vazão Operada por Reservatório")
fig = go.Figure()
cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#17becf", "#e377c2"]
reservatorios = df_filtrado["Reservatório Monitorado"].dropna().unique()

for i, r in enumerate(reservatorios):
    dfr = df_filtrado[df_filtrado["Reservatório Monitorado"] == r].sort_values("Data").groupby("Data", as_index=False).last()
    y_vals, unit_suffix = convert_vazao(dfr["Vazão Operada"], unidade_sel)
    fig.add_trace(go.Scatter(x=dfr["Data"], y=y_vals, mode="lines+markers", name=r,
                             line=dict(shape="hv", width=2, color=cores[i % len(cores)]), marker=dict(size=5),
                             hovertemplate=f"<b>{r}</b><br>Data: %{{x|%d/%m/%Y}}<br>Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"))

fig.update_layout(
    xaxis_title="Data",
    yaxis_title=f"Vazão Operada ({'m³/s' if unidade_sel=='m³/s' else 'L/s'})",
    legend_title="Reservatório",
    template="plotly_white",
    margin=dict(l=40, r=20, t=10, b=40),
    height=600,
    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
    xaxis=dict(rangeslider=dict(visible=True, thickness=0.1, bgcolor="#f5f5f5", bordercolor="#cccccc", borderwidth=1))
)
st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

# Mapa com camadas (necessita geojsons no diretório raiz)
st.subheader("🗺️ Mapa dos Reservatórios com Camadas")
gj = load_geojsons()
df_mapa = df_filtrado.copy()
coord_col = "Coordenadas" if "Coordenadas" in df_mapa.columns else ("Coordendas" if "Coordendas" in df_mapa.columns else None)
if coord_col:
    try:
        df_mapa[["lat", "lon"]] = df_mapa[coord_col].str.split(",", expand=True).astype(float)
    except Exception:
        df_mapa[["lat", "lon"]] = df_mapa[coord_col].str.replace(" ", "").str.split(",", expand=True).astype(float)
df_mapa = df_mapa.dropna(subset=["lat", "lon"]).drop_duplicates(subset=["Reservatório Monitorado"])

mapa_tipo = st.selectbox("Estilo do Mapa:", ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"], index=0, key="map_style_selector_home")
tile_urls = {
    "OpenStreetMap": None,
    "Stamen Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
    "Stamen Toner": "https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
    "CartoDB positron": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
    "CartoDB dark_matter": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
    "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
}
tile_attr = {
    "OpenStreetMap": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    "Stamen Terrain": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
    "Stamen Toner": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
    "CartoDB positron": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
    "CartoDB dark_matter": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
    "Esri Satellite": "Tiles &copy; Esri"
}

if not df_mapa.empty:
    center = [df_mapa["lat"].mean(), df_mapa["lon"].mean()]
    m = folium.Map(location=center, zoom_start=8, tiles=None)
    if mapa_tipo == "OpenStreetMap":
        folium.TileLayer(tiles="OpenStreetMap").add_to(m)
    else:
        folium.TileLayer(tiles=tile_urls[mapa_tipo], attr=tile_attr[mapa_tipo], name=mapa_tipo).add_to(m)

    Fullscreen(position="topleft").add_to(m)
    MiniMap(toggle_display=True, minimized=True).add_to(m)
    MousePosition(position="bottomleft", separator=" | ", prefix="Coords").add_to(m)
    MeasureControl(primary_length_unit="meters").add_to(m)

    if gj.get("bacia"):
        folium.GeoJson(gj["bacia"], name="Bacia do Banabuiu",
                       tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]),
                       style_function=lambda x: {"color": "darkblue", "weight": 2}).add_to(m)

    folium.LayerControl(collapsed=True, position="topright").add_to(m)
    folium_static(m, width=1200)
else:
    st.info("Nenhum ponto com coordenadas disponíveis para plotar no mapa.")

# KPIs e tabela simples
st.subheader("📋 Tabela Detalhada")
st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)
