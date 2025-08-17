import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MousePosition
from utils.common import load_geojson_data

def render_dados():
    st.title("📈 Simulações")
    st.markdown("""
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
    <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
        <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
        • Linha comparativa de <b>Cota Simulada (m)</b> e <b>Cota Realizada (m)</b><br>
        • Filtros por <b>Data</b>, <b>Açude</b>, <b>Município</b> e <b>Classificação</b><br>
        • Mapa interativo com camadas<br>
        • Indicadores de <b>KPIs</b> e tabela de dados
    </p>
</div>
""", unsafe_allow_html=True)

    google_sheet_url = "https://docs.google.com/spreadsheets/d/1C40uaNmLUeu-k_FGEPZOgF8FwpSU00C9PtQu8Co4AUI/gviz/tq?tqx=out:csv&sheet=simulacoes_data"
    
    try:
        df = pd.read_csv(google_sheet_url)

        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')

        if 'Coordendas' in df.columns:
            df.rename(columns={'Coordendas': 'Coordenadas'}, inplace=True)
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados da planilha. Verifique se o link está correto e se a planilha está pública. Detalhes do erro: {e}")
        return

    if df.empty:
        st.info("A planilha de simulações está vazia. Por favor, verifique os dados.")
        return

    st.markdown("""
    <style>
      .filter-card { border:1px solid #e6e6e6; border-radius:14px; padding:14px;
                    background:linear-gradient(180deg,#ffffff 0%, #fafafa 100%);
                    box-shadow:0 6px 16px rgba(0,0,0,.06); margin:6px 0 16px 0; }
      .filter-title { font-weight:700; color:#006400; margin-bottom:8px; letter-spacing:.2px; }
      .expander-rounded > details { border:1px solid #e6e6e6 !important; border-radius:14px !important;
                                     background:#fff !important; box-shadow:0 4px 14px rgba(0,0,0,.06) !important;
                                     padding:6px 6px 0 6px !important; }
      .expander-rounded summary { font-weight:600 !important; color:#006400 !important; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="expander-rounded">', unsafe_allow_html=True)
        with st.expander("☰ Filtros (clique para expandir)", expanded=True):
            st.markdown('<div class="filter-card"><div class="filter-title">Filtros de Visualização</div>', unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                opcoes_acudes = sorted(df["Açude"].dropna().unique().tolist())
                acudes_sel = st.multiselect("Açude", options=opcoes_acudes, default=opcoes_acudes)
            with col2:
                opcoes_municipios = sorted(df["Município"].dropna().unique().tolist())
                municipios_sel = st.multiselect("Município", options=opcoes_municipios, default=opcoes_municipios)
            with col3:
                opcoes_classificacao = sorted(df["Classificação"].dropna().unique().tolist())
                classificacao_sel = st.multiselect("Classificação", options=opcoes_classificacao, default=opcoes_classificacao)
            with col4:
                datas_validas = df["Data"]
                if not datas_validas.empty:
                    data_min = datas_validas.min().date()
                    data_max = datas_validas.max().date()
                    periodo = st.date_input(
                        "Período",
                        value=(data_min, data_max),
                        min_value=data_min,
                        max_value=data_max,
                        format="DD/MM/YYYY"
                    )
                else:
                    periodo = None
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    dff = df.copy()
    if acudes_sel:
        dff = dff[dff["Açude"].isin(acudes_sel)]
    if municipios_sel:
        dff = dff[dff["Município"].isin(municipios_sel)]
    if classificacao_sel:
        dff = dff[dff["Classificação"].isin(classificacao_sel)]
    if periodo:
        if len(periodo) == 1:
            ini = fim = pd.to_datetime(periodo[0])
        else:
            ini, fim = [pd.to_datetime(d) for d in periodo]
        dff = dff[(dff["Data"] >= ini) & (dff["Data"] <= fim)]

    if dff.empty:
        st.info("Não há dados para os filtros selecionados.")
        return

    if 'Coordenadas' in dff.columns:
        dff[['Latitude', 'Longitude']] = dff['Coordenadas'].str.split(',', expand=True).astype(float)
    else:
        st.warning("A coluna 'Coordenadas' não foi encontrada. O mapa não será exibido.")
        
    dff = dff.sort_values(["Açude", "Data"])

    st.markdown("---")
    st.subheader("📊 Indicadores de Desempenho (KPIs)")
    kpi1, kpi2, kpi3 = st.columns(3)

    if 'Liberação (m³/s)' in dff.columns:
        with kpi1:
            try:
                dff["Liberação (m³/s)"] = pd.to_numeric(
                    dff["Liberação (m³/s)"].astype(str).str.replace(',', '.'), 
                    errors='coerce'
                )
                total_liberacao = dff["Liberação (m³/s)"].sum()
                st.metric(label="Total de Liberação (m³/s)", value=f"{total_liberacao:.2f}")
            except Exception as e:
                st.warning(f"Não foi possível calcular a liberação total. Erro: {str(e)}")
    else:
        with kpi1:
            st.warning("Coluna 'Liberação (m³/s)' não encontrada. KPI não disponível.")

    with kpi2:
        total_acudes = dff["Açude"].nunique()
        st.metric(label="Açudes Monitorados", value=total_acudes)

    with kpi3:
        if periodo:
            dias = (dff["Data"].max() - dff["Data"].min()).days
            st.metric(label="Dias do Período", value=dias)
        else:
            st.metric(label="Dias do Período", value="N/A")

    st.markdown("---")
        # ---------------------- MAPA (corrigido) ----------------------
    st.markdown("---")
    st.subheader("🌍 Mapa dos Açudes")

    # Função robusta para extrair latitude/longitude mesmo com vírgula decimal
    def parse_latlon(series_coordenadas: pd.Series):
        lat, lon = [], []
        for v in series_coordenadas.fillna(""):
            if not isinstance(v, str):
                v = str(v)
            parts = [p.strip() for p in v.split(",")]
            if len(parts) == 2:
                # troca vírgula decimal por ponto
                lat_str = parts[0].replace(",", ".")
                lon_str = parts[1].replace(",", ".")
                try:
                    lat.append(float(lat_str))
                    lon.append(float(lon_str))
                except ValueError:
                    lat.append(None); lon.append(None)
            else:
                lat.append(None); lon.append(None)
        return pd.Series(lat), pd.Series(lon)

    # Garante Latitude/Longitude
    if "Coordenadas" in dff.columns:
        if not {"Latitude", "Longitude"}.issubset(dff.columns):
            dff["Latitude"], dff["Longitude"] = parse_latlon(dff["Coordenadas"])
    else:
        st.info("Mapa não disponível devido à falta da coluna 'Coordenadas'.")
        dff["Latitude"] = None
        dff["Longitude"] = None

    # Filtra apenas coordenadas válidas
    mapa_df = dff.dropna(subset=["Latitude", "Longitude"])
    if mapa_df.empty:
        st.info("Não há coordenadas válidas para exibir no mapa com os filtros atuais.")
    else:
        with st.expander("Configurações do Mapa", expanded=False):
            tile_option = st.selectbox(
                "Estilo do Mapa:",
                ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
                index=0,
                key='map_style_select'
            )

        # Carrega GeoJSONs
        geojson_data = load_geojson_data()
        geojson_bacia = geojson_data.get('geojson_bacia', {})
        geojson_c_gestoras = geojson_data.get('geojson_c_gestoras', {})
        geojson_poligno = geojson_data.get('geojson_poligno', {})

        # Configura tiles como TileLayer (para LayerControl funcionar)
        tile_config = {
            "OpenStreetMap": {
                "tiles": "OpenStreetMap",
                "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            },
            "Stamen Terrain": {
                "tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
                "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'
            },
            "Stamen Toner": {
                "tiles": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
                "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'
            },
            "CartoDB positron": {
                "tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
                "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'
            },
            "CartoDB dark_matter": {
                "tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
                "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'
            },
            "Esri Satellite": {
                "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                "attr": "Tiles &copy; Esri — Source: Esri"
            },
        }

        # Centro do mapa
        center_lat = float(mapa_df["Latitude"].mean())
        center_lon = float(mapa_df["Longitude"].mean())

        # Inicie SEM tiles para poder adicionar múltiplas bases
        m = folium.Map(location=[center_lat, center_lon], zoom_start=8, tiles=None)

        # Adiciona todas as bases como TileLayer (a selecionada virá marcada)
        for name, cfg in tile_config.items():
            folium.TileLayer(
                tiles=cfg["tiles"], attr=cfg["attr"], name=name,
                control=True, show=(name == tile_option)
            ).add_to(m)

        # Overlays GeoJSON com nomes
        if geojson_bacia:
            folium.GeoJson(geojson_bacia, name="Bacia Hidrográfica", show=False).add_to(m)
        if geojson_c_gestoras:
            folium.GeoJson(geojson_c_gestoras, name="Células Gestoras", show=False).add_to(m)
        if geojson_poligno:
            folium.GeoJson(geojson_poligno, name="Polígonos", show=False).add_to(m)

        # Marcadores em um FeatureGroup nomeado (vira camada com toggle)
        fg_pontos = folium.FeatureGroup(name="Açudes (pontos)", show=True)
        for _, row in mapa_df.iterrows():
            acude = row.get('Açude', 'N/A')
            municipio = row.get('Município', 'N/A')
            cota_sim = row.get('Cota Simulada (m)', None)
            cota_real = row.get('Cota Realizada (m)', None)
            volume = row.get('Volume(m³)', None)
            classificacao = row.get('Classificação', 'N/A')

            def fmt(x, casas=3):
                try:
                    return f"{float(str(x).replace(',','.')):.{casas}f}"
                except:
                    return "N/A"

            popup_html = f"""
            <b>Açude:</b> {acude}<br>
            <b>Município:</b> {municipio}<br>
            <b>Cota Simulada:</b> {fmt(cota_sim, 3)} m<br>
            <b>Cota Realizada:</b> {fmt(cota_real, 3)} m<br>
            <b>Volume:</b> {fmt(volume, 2)} m³<br>
            <b>Classificação:</b> {classificacao}
            """

            folium.Marker(
                location=[row["Latitude"], row["Longitude"]],
                tooltip=str(acude),
                popup=folium.Popup(popup_html, max_width=320),
                icon=folium.Icon(color="green", icon="tint", prefix="fa")
            ).add_to(fg_pontos)

        fg_pontos.add_to(m)

        # Controles extras e controle de camadas
        Fullscreen().add_to(m)
        MousePosition(position="bottomleft", separator=" | ", num_digits=5).add_to(m)
        folium.LayerControl(collapsed=False).add_to(m)

        # Render
        folium_static(m, width=1200, height=600)


    st.markdown("---")
    st.subheader("📈 Cotas (Cota Simulada x Cota Realizada)")
    
    if 'Cota Simulada (m)' in dff.columns and 'Cota Realizada (m)' in dff.columns:
        dff["Cota Simulada (m)"] = pd.to_numeric(dff["Cota Simulada (m)"].astype(str).str.replace(',', '.'), errors='coerce')
        dff["Cota Realizada (m)"] = pd.to_numeric(dff["Cota Realizada (m)"].astype(str).str.replace(',', '.'), errors='coerce')
        
        fig_cotas = go.Figure()
        for acude in sorted(dff["Açude"].dropna().unique()):
            base = dff[dff["Açude"] == acude].sort_values("Data")
            fig_cotas.add_trace(go.Scatter(
                x=base["Data"], 
                y=base["Cota Simulada (m)"], 
                mode="lines+markers", 
                name=f"{acude} - Cota Simulada (m)", 
                hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"
            ))
            fig_cotas.add_trace(go.Scatter(
                x=base["Data"], 
                y=base["Cota Realizada (m)"], 
                mode="lines+markers", 
                name=f"{acude} - Cota Realizada (m)", 
                hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"
            ))
        fig_cotas.update_layout(
            template="plotly_white", 
            margin=dict(l=10, r=10, t=10, b=10), 
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), 
            xaxis_title="Data", 
            yaxis_title="Cota (m)", 
            height=480
        )
        st.plotly_chart(fig_cotas, use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Gráfico de Cotas não disponível. Colunas 'Cota Simulada (m)' ou 'Cota Realizada (m)' não encontradas.")

    st.subheader("📈 Volume (m³)")
    if 'Volume(m³)' in dff.columns:
        dff["Volume(m³)"] = pd.to_numeric(dff["Volume(m³)"].astype(str).str.replace(',', '.'), errors='coerce')
        
        fig_vol = go.Figure()
        for acude in sorted(dff["Açude"].dropna().unique()):
            base = dff[dff["Açude"] == acude].sort_values("Data")
            fig_vol.add_trace(go.Scatter(
                x=base["Data"], 
                y=base["Volume(m³)"], 
                mode="lines+markers", 
                name=f"{acude} - Volume (m³)", 
                hovertemplate="%{x|%d/%m/%Y} • %{y:.2f} m³<extra></extra>"
            ))
        fig_vol.update_layout(
            template="plotly_white", 
            margin=dict(l=10, r=10, t=10, b=10), 
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), 
            xaxis_title="Data", 
            yaxis_title="Volume (m³)", 
            height=420
        )
        st.plotly_chart(fig_vol, use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Gráfico de Volume não disponível. Coluna 'Volume(m³)' não encontrada.")

    st.markdown("---")
    st.subheader("📋 Tabela de Dados")
    with st.expander("Ver dados filtrados"):
        colunas_tabela = [
            'Data',
            'Açude',
            'Município',
            'Região Hidrográfica',
            'Cota Simulada (m)',
            'Cota Realizada (m)',
            'Volume(m³)',
            'Volume (%)',
            'Evapor. Parcial(mm)',
            'Cota Interm. (m)',
            'Liberação (m³/s)',
            'Liberação (m³)',
            'Classificação',
            'Coordenadas'
        ]
        
        colunas_existentes = [col for col in colunas_tabela if col in dff.columns]
        dff_tabela = dff[colunas_existentes]
        
        st.dataframe(
            dff_tabela.sort_values(["Açude", "Data"], ascending=[True, False]), 
            use_container_width=True,
            column_config={
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Cota Simulada (m)": st.column_config.NumberColumn(format="%.3f"),
                "Cota Realizada (m)": st.column_config.NumberColumn(format="%.3f"),
                "Volume(m³)": st.column_config.NumberColumn(format="%.2f"),
                "Volume (%)": st.column_config.NumberColumn(format="%.2f"),
                "Liberação (m³/s)": st.column_config.NumberColumn(format="%.2f"),
                "Liberação (m³)": st.column_config.NumberColumn(format="%.2f")
            }
        )

