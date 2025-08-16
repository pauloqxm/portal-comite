
import streamlit as st
import pandas as pd
import folium, base64
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MousePosition
from datetime import datetime
from utils.common import render_header

st.set_page_config(page_title="🗺️ Açudes Monitorados", layout="wide")
render_header()

st.title("🗺️ Açudes Monitorados")
st.markdown(
    """
    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
      <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
        <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
        • Visualização dos açudes monitorados na bacia do Banabuiú<br>
        • Filtros interativos para análise dos dados<br>
        • Tabela detalhada com informações técnicas
      </p>
    </div>
    """, unsafe_allow_html=True
)

@st.cache_data(ttl=3600)
def load_reservatorios_data():
    try:
        url = "https://docs.google.com/spreadsheets/d/1zZ0RCyYj-AzA_dhWzxRziDWjgforbaH7WIoSEd2EKdk/export?format=csv"
        df = pd.read_csv(url)
        if {"Latitude","Longitude"} <= set(df.columns):
            df["Latitude"] = pd.to_numeric(df["Latitude"].astype(str).str.replace(",", "."), errors="coerce")
            df["Longitude"] = pd.to_numeric(df["Longitude"].astype(str).str.replace(",", "."), errors="coerce")
            df = df.dropna(subset=["Latitude","Longitude"])
        else:
            st.error("Colunas 'Latitude' e 'Longitude' são necessárias")
            return pd.DataFrame()

        if "Data de Coleta" in df.columns:
            df["Data de Coleta"] = pd.to_datetime(df["Data de Coleta"], errors="coerce", dayfirst=True)
            df = df.dropna(subset=["Data de Coleta"])

        for col in ["Percentual","Volume","Cota Sangria","Nivel"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", ".").str.replace("%","").str.strip(), errors="coerce")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

df_full = load_reservatorios_data()
if df_full.empty:
    st.warning("Não foi possível carregar os dados dos reservatórios.")
    st.stop()

with st.expander("🔍 Filtros", expanded=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        min_date = df_full["Data de Coleta"].min().date()
        max_date = df_full["Data de Coleta"].max().date()
        date_range = st.date_input("Período:", value=(max_date, max_date), min_value=min_date, max_value=max_date)
        if len(date_range) == 2:
            start_date, end_date = date_range
        else:
            st.warning("Selecione um intervalo válido")
            st.stop()
    with col2:
        reservatorios = sorted(df_full["Reservatório"].dropna().astype(str).unique())
        reservatorio_filtro = st.multiselect("Reservatório(s):", options=reservatorios, default=reservatorios, placeholder="Selecione...")
    with col3:
        municipios = ["Todos"] + sorted(df_full["Município"].dropna().astype(str).unique().tolist())
        municipio_filtro = st.selectbox("Município:", options=municipios, index=0)

    perc_series = df_full["Percentual"].dropna()
    min_perc, max_perc = (float(perc_series.min()), float(perc_series.max())) if not perc_series.empty else (0.0,100.0)
    perc_range = st.slider("Percentual de Volume (%):", min_value=float(min_perc), max_value=float(max_perc), value=(float(min_perc), float(max_perc)), step=0.1)

if not reservatorio_filtro:
    reservatorio_filtro = reservatorios

mask = (
    (df_full["Data de Coleta"].dt.date >= start_date) &
    (df_full["Data de Coleta"].dt.date <= end_date) &
    (df_full["Reservatório"].astype(str).isin(reservatorio_filtro)) &
    (df_full["Percentual"].between(perc_range[0], perc_range[1], inclusive="both"))
)
df_filtrado = df_full.loc[mask].copy()

if municipio_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Município"].astype(str) == municipio_filtro].copy()

df_mapa = df_filtrado.sort_values("Data de Coleta", ascending=False).drop_duplicates(subset=["Reservatório"]).copy()

st.subheader("🌍 Mapa dos Açudes")
with st.expander("Configurações do Mapa", expanded=False):
    tile_option = st.selectbox("Estilo do Mapa:", ["OpenStreetMap","Stamen Terrain","Stamen Toner","CartoDB positron","CartoDB dark_matter","Esri Satellite"], index=0)

tile_config = {
    "OpenStreetMap": {"tiles": "OpenStreetMap","attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'},
    "Stamen Terrain": {"tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png","attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
    "CartoDB positron": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png","attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
    "CartoDB dark_matter": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png","attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
    "Esri Satellite": {"tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}","attr": "Tiles &copy; Esri — Source: Esri"},
    "Stamen Toner": {"tiles": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png","attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
}

def get_marker_color(percentual):
    import math
    if percentual is None or (isinstance(percentual, float) and math.isnan(percentual)) or 0 <= percentual <= 10: return "#808080"
    if 10.1 <= percentual <= 30: return "#FF0000"
    if 30.1 <= percentual <= 50: return "#FFFF00"
    if 50.1 <= percentual <= 70: return "#008000"
    if 70.1 <= percentual <= 100: return "#0000FF"
    return "#800080"

def create_svg_icon(color, size=15):
    svg = (f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" '
           f'xmlns="http://www.w3.org/2000/svg">'
           f'<polygon points="50,0 100,100 0,100" fill="{color}" '
           f'stroke="#000000" stroke-width="5"/></svg>')
    svg_b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f"data:image/svg+xml;base64,{svg_b64}"

if not df_filtrado.empty:
    mapa_center = [df_mapa["Latitude"].mean(), df_mapa["Longitude"].mean()]
    m = folium.Map(location=mapa_center, zoom_start=9, tiles=None)
    folium.TileLayer(tiles=tile_config[tile_option]["tiles"], attr=tile_config[tile_option]["attr"], name=tile_option).add_to(m)

    for _, row in df_mapa.iterrows():
        try:
            percentual_val = float(row["Percentual"]); percentual_str = f"{percentual_val:.2f}%"
        except (ValueError, TypeError):
            percentual_val, percentual_str = None, "N/A"
        try:
            volume_str = f"{float(row['Volume']):,.2f} hm³".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            volume_str = "N/A"
        try:
            cota_sangria_str = f"{float(row['Cota Sangria']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            cota_sangria_str = "N/A"

        ultima_data = df_filtrado[df_filtrado["Reservatório"] == row["Reservatório"]]["Data de Coleta"].max()
        data_formatada = ultima_data.strftime("%d/%m/%Y") if pd.notnull(ultima_data) else "N/A"
        icon_color = get_marker_color(percentual_val)

        popup_content = (
            '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">'
            f"<div style='font-family: "Segoe UI", sans-serif; width: 280px; background: linear-gradient(to bottom, #f9f9f9, #ffffff); "
            f"border-radius: 8px; border-left: 5px solid {icon_color}; padding: 12px; box-shadow: 0 3px 10px rgba(0,0,0,0.2);'>"
            f"<div style='color: #006400; font-size: 18px; font-weight: 700; margin-bottom: 10px; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px;'>"
            f"<i class='fas fa-water' style='margin-right: 8px;'></i>{row['Reservatório']}</div>"
            f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-calendar-alt' style='margin-right: 5px;'></i>Data:</span><span style='color: #333;'>{data_formatada}</span></div>"
            f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-city' style='margin-right: 5px;'></i>Município:</span><span style='color: #333;'>{row.get('Município', 'N/A')}</span></div>"
            f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-chart-bar' style='margin-right: 5px;'></i>Volume:</span><span style='color: #1a5276; font-weight: 500;'>{volume_str}</span></div>"
            f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-percentage' style='margin-right: 5px;'></i>Percentual:</span><span style='color: #27ae60; font-weight: 600;'>{percentual_str}</span></div>"
            f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-ruler' style='margin-right: 5px;'></i>Cota Sangria:</span><span style='color: #7d3c98; font-weight: 500;'>{cota_sangria_str} m</span></div>"
            "</div>"
        )

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup_content, max_width=300),
            icon=folium.CustomIcon(create_svg_icon(icon_color), icon_size=(15, 15), icon_anchor=(7, 7)),
            tooltip=f"{row['Reservatório']} - {data_formatada}",
        ).add_to(m)

    folium.LayerControl().add_to(m)
    Fullscreen(position="topleft").add_to(m)
    MousePosition(position="bottomleft").add_to(m)
    folium_static(m, width=1200)
else:
    st.warning("Não há reservatórios com os filtros aplicados.")

# ---- Tabela Interativa resumida ----
st.subheader("📊 Dados Detalhados Interativos")
if not df_filtrado.empty:
    faixas_percentual = [
        (0, 10, "#808080", "Muito Crítica"),
        (10.1, 30, "#FF0000", "Crítica"),
        (30.1, 50, "#FFFF00", "Alerta"),
        (50.1, 70, "#008000", "Confortável"),
        (70.1, 100, "#0000FF", "Muito Confortável"),
        (100.1, float("inf"), "#800080", "Vertendo")
    ]

    def get_status_color(percentual):
        import math
        if percentual is None or (isinstance(percentual,float) and math.isnan(percentual)):
            return "#FFFFFF", "N/A", "#000000"
        for min_val, max_val, color, status in faixas_percentual:
            if min_val <= percentual <= max_val:
                text_color = "#FFFFFF" if color in ["#808080","#FF0000","#0000FF","#800080"] else "#000000"
                return color, status, text_color
        return "#FFFFFF", "Não classificado", "#000000"

    df_filtrado[["Cor","Status","TextColor"]] = df_filtrado["Percentual"].apply(lambda x: pd.Series(get_status_color(x)))
    df_filtrado["Sangria"] = df_filtrado["Cota Sangria"] - df_filtrado["Nivel"]

    colunas_exibir = ["Data de Coleta","Reservatório","Município","Volume","Percentual","Status","Cota Sangria","Nivel","Sangria"]

    def colorize_row(row):
        idx = row.name
        bg = df_filtrado.loc[idx, "Cor"]
        tx = df_filtrado.loc[idx, "TextColor"]
        return [f"background-color: {bg}; color: {tx}; font-weight: bold;" for _ in row]

    styled_df = df_filtrado[colunas_exibir].copy().style.apply(colorize_row, axis=1)

    column_config = {
        "Percentual": st.column_config.ProgressColumn("Percentual", format="%.1f%%", min_value=0, max_value=100),
        "Volume": st.column_config.NumberColumn("Volume", format="%.2f hm³"),
        "Cota Sangria": st.column_config.NumberColumn("Cota Sangria", format="%.2f m"),
        "Nivel": st.column_config.NumberColumn("Nível", format="%.2f m"),
        "Sangria": st.column_config.NumberColumn("Margem de Sangria", format="%.2f m"),
        "Status": st.column_config.TextColumn("Status"),
        "Data de Coleta": st.column_config.DateColumn("Data de Coleta", format="DD/MM/YYYY")
    }

    st.dataframe(styled_df, column_config=column_config, use_container_width=True, hide_index=True, height=600, column_order=colunas_exibir)

    with st.expander("📥 Opções de Download", expanded=False):
        st.download_button(
            label="Baixar dados completos (CSV)",
            data=df_filtrado.drop(columns=["Cor","Status","TextColor"]).to_csv(index=False, encoding="utf-8-sig", sep=";"),
            file_name=f"reservatorios_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
else:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.", icon="⚠️")
