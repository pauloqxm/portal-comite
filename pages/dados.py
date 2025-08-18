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


# ===================== Mapa dos Açudes (com camadas e base segura) =====================

    st.subheader("🌍 Mapa dos Açudes")
    with st.expander("Configurações do Mapa", expanded=False):
        tile_option = st.selectbox(
            "Estilo do Mapa:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            index=0,
            key='map_style_select'
        )
    
    # Carrega os dados GeoJSON
    geojson_data = load_geojson_data()
    geojson_situa = geojson_data.get('geojson_situa', {})
    geojson_bacia = geojson_data.get('geojson_bacia', {})
    geojson_sedes = geojson_data.get('geojson_sedes', {})
        
    # Configurações dos tiles
    tile_config = {
        "OpenStreetMap": {"tiles": "OpenStreetMap", "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'},
        "Stamen Terrain": {"tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png", "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
        "CartoDB positron": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
        "CartoDB dark_matter": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
        "Esri Satellite": {"tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "attr": "Tiles &copy; Esri — Source: Esri"},
        "Stamen Toner": {"tiles": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png", "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
    }
    
    if 'Coordenadas' in dff.columns:
        center_lat = dff['Latitude'].mean()
        center_lon = dff['Longitude'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=9, tiles=None)
        
        # Adiciona o tile layer selecionado
        folium.TileLayer(
            tiles=tile_config[tile_option]["tiles"], 
            attr=tile_config[tile_option]["attr"], 
            name=tile_option
        ).add_to(m)
    
        # --- FUNÇÕES DE ESTILO ---
        def get_classification_color(props):
            classificacao_keys = ['Classificação', 'classificacao', 'CLASSIFICACAO', 'classificação', 'situacao', 'SITUACAO']
            classificacao = None
            
            for key in classificacao_keys:
                if key in props:
                    classificacao = str(props[key]).strip()
                    break
            
            if classificacao is None:
                return "#999999"
            
            color_map = {
                "Criticidade Alta": "#E24F42",
                "criticidade alta": "#E24F42",
                "Alta": "#E24F42",
                "Criticidade Média": "#ECC116",
                "criticidade média": "#ECC116",
                "Média": "#ECC116",
                "Criticidade Baixa": "#F4FA4A",
                "criticidade baixa": "#F4FA4A",
                "Baixa": "#F4FA4A",
                "Fora de Criticidade": "#8DCC90",
                "fora de criticidade": "#8DCC90",
                "Fora criticidade": "#8DCC90",
                "fora criticidade": "#8DCC90",
                "Normal": "#8DCC90",
                "Sem classificação": "#999999"
            }
            
            for key in color_map:
                if key.lower() == classificacao.lower():
                    return color_map[key]
            
            return "#999999"
    
        def style_function(feature):
            return {
                'fillColor': get_classification_color(feature.get('properties', {})),
                'color': '#555555',
                'weight': 1.5,
                'fillOpacity': 0.7,
                'opacity': 0.9
            }
    
        # --- CAMADA DA BACIA DO BANABUIÚ ---
        if geojson_bacia:
            folium.GeoJson(
                geojson_bacia,
                name="Bacia do Banabuiú",
                style_function=lambda x: {
                    "color": "blue",
                    "weight": 2,
                    "fillOpacity": 0.1
                },
                tooltip=folium.GeoJsonTooltip(
                    fields=["DESCRICA1"],
                    aliases=["Bacia:"]
                )
            ).add_to(m)
    
        # --- CAMADA DAS SEDES MUNICIPAIS ---
        if geojson_sedes:
            sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=False)
            for feature in geojson_sedes["features"]:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]
                nome = props.get("NOME_MUNIC", "Sem nome")
                folium.Marker(
                    [coords[1], coords[0]],
                    icon=folium.CustomIcon(
                        "https://cdn-icons-png.flaticon.com/512/854/854878.png",
                        icon_size=(25, 25)
                    ),
                    tooltip=nome
                ).add_to(sedes_layer)
            sedes_layer.add_to(m)
    
        # --- CAMADA PRINCIPAL (SITUAÇÃO DA BACIA) ---
        if geojson_situa and geojson_situa.get('type') == 'FeatureCollection':
            try:
                situa_group = folium.FeatureGroup(name="Situação da Bacia", show=True)
                
                # Verificação das classificações presentes
                classificacoes_presentes = set()
                for feature in geojson_situa.get('features', []):
                    props = feature.get('properties', {})
                    for key in ['Classificação', 'classificacao', 'CLASSIFICACAO']:
                        if key in props:
                            classificacoes_presentes.add(props[key])
                
                if classificacoes_presentes:
                    st.session_state.classificacoes_presentes = classificacoes_presentes
                
                folium.GeoJson(
                    geojson_situa,
                    style_function=style_function,
                    tooltip=folium.GeoJsonTooltip(
                        fields=['Classificação'],
                        aliases=['Classificação:'],
                        sticky=True,
                        style=("font-weight: bold;")
                    )
                ).add_to(situa_group)
                
                situa_group.add_to(m)
                
            except Exception as e:
                st.error(f"Erro ao processar GeoJSON: {str(e)}")
                if 'classificacoes_presentes' in st.session_state:
                    st.write("Classificações encontradas:", st.session_state.classificacoes_presentes)
    
            
    
        # --- MARCADORES DOS AÇUDES ---
        for _, row in dff.iterrows():
            classificacao = row.get('Classificação', 'Sem classificação')
            color_marker = get_classification_color({'Classificação': classificacao})
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 14px;">
                <h4 style="margin:0; padding:0; color: #2c3e50;">{row.get('Açude', 'N/A')}</h4>
                <p><b>Município:</b> {row.get('Município', 'N/A')}</p>
                <p><b>Cota Simulada:</b> {row.get('Cota Simulada (m)', 'N/A')} m</p>
                <p><b>Cota Realizada:</b> {row.get('Cota Realizada (m)', 'N/A')} m</p>
                <p><b>Volume:</b> {row.get('Volume(m³)', 'N/A')} m³</p>
                <p><b>Classificação:</b> <span style="color: {color_marker}; font-weight: bold;">{classificacao}</span></p>
            </div>
            """
            
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=6,
                color=color_marker,
                fill=True,
                fill_color=color_marker,
                fill_opacity=0.9,
                tooltip=row.get('Açude', 'N/A'),
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)
    
        # --- LEGENDA ---
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 50px; left: 50px; width: 180px; 
                    border:2px solid grey; z-index:9999; 
                    font-size:14px; background:white;
                    padding: 10px; font-family: Arial, sans-serif;">
            <p style="margin:0 0 10px 0; padding:0; font-weight:bold; border-bottom:1px solid #eee; color: #2c3e50;">Legenda:</p>
            <div style="display: flex; align-items: center; margin: 5px 0;">
                <div style="width:20px; height:20px; background:#E24F42; margin-right:5px; border:1px solid #555;"></div>
                <span>Criticidade Alta</span>
            </div>
            <div style="display: flex; align-items: center; margin: 5px 0;">
                <div style="width:20px; height:20px; background:#ECC116; margin-right:5px; border:1px solid #555;"></div>
                <span>Criticidade Média</span>
            </div>
            <div style="display: flex; align-items: center; margin: 5px 0;">
                <div style="width:20px; height:20px; background:#F4FA4A; margin-right:5px; border:1px solid #555;"></div>
                <span>Criticidade Baixa</span>
            </div>
            <div style="display: flex; align-items: center; margin: 5px 0;">
                <div style="width:20px; height:20px; background:#8DCC90; margin-right:5px; border:1px solid #555;"></div>
                <span>Fora de Criticidade</span>
            </div>
            <div style="display: flex; align-items: center; margin: 5px 0;">
                <div style="width:20px; height:20px; background:#999999; margin-right:5px; border:1px solid #555;"></div>
                <span>Sem classificação</span>
            </div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))
    
        # --- PLUGINS ADICIONAIS ---
        Fullscreen().add_to(m)
        MousePosition(position="bottomleft", separator=" | ", num_digits=4).add_to(m)
        folium.LayerControl().add_to(m)
        
        # --- EXIBIÇÃO DO MAPA ---
        folium_static(m, width=1000, height=600)
    else:
        st.info("Mapa não disponível devido à falta da coluna 'Coordenadas'.")
    
        
# --- FIM DO BLOCO DO MAPA ---
    
    # --- INDICADORES DE DESEMPENHO (KPIs) ---
    st.markdown("---")
    st.subheader("📊 Indicadores de Desempenho (KPIs)")
    
    st.markdown("""
    <style>
    .kpi-card {
        background-color: #f0f4f8;
        border: 1px solid #d9e2eb;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    .kpi-label {
        font-size: 16px;
        color: #5a7d9a;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: bold;
        color: #2c3e50;
    }
    </style>
    """, unsafe_allow_html=True)
    
    kpi_cols = st.columns(4)
    
    if 'Liberação (m³/s)' in dff.columns:
        with kpi_cols[0]:
            try:
                dff["Liberação (m³/s)"] = pd.to_numeric(
                    dff["Liberação (m³/s)"].astype(str).str.replace(',', '.'),
                    errors='coerce'
                )
                
                ultima_data = dff['Data'].max()
                
                df_ultima_data = dff[dff['Data'] == ultima_data]
                
                total_liberacao_m3h = df_ultima_data["Liberação (m³/s)"].sum() * 3600
                
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Liberação Total Diária (m³/h)</div>
                    <div class="kpi-value">{total_liberacao_m3h:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.warning(f"Não foi possível calcular a liberação total. Erro: {str(e)}")
    else:
        with kpi_cols[0]:
            st.warning("Coluna 'Liberação (m³/s)' não encontrada. KPI não disponível.")
    
    with kpi_cols[1]:
        if not dff.empty:
            primeira_data = dff["Data"].min().strftime('%d/%m/%Y')
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Data Inicial</div>
                <div class="kpi-value">{primeira_data}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-label">Data Inicial</div>
                <div class="kpi-value">N/A</div>
            </div>
            """, unsafe_allow_html=True)
    
    with kpi_cols[2]:
        if not dff.empty and 'Data' in dff.columns:
            ultima_data = dff['Data'].max().strftime('%d/%m/%Y')
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Última Atualização</div>
                <div class="kpi-value">{ultima_data}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-label">Última Atualização</div>
                <div class="kpi-value">N/A</div>
            </div>
            """, unsafe_allow_html=True)
    
    with kpi_cols[3]:
        if periodo:
            dias = (dff["Data"].max() - dff["Data"].min()).days
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Dias do Período</div>
                <div class="kpi-value">{dias}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-label">Dias do Período</div>
                <div class="kpi-value">N/A</div>
            </div>
            """, unsafe_allow_html=True)
    
    # --- GRÁFICO DE COTAS ---
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
            yaxis=dict(title="Cota (m)", tickformat=".2f"),
            height=480
        )
        st.plotly_chart(fig_cotas, use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Gráfico de Cotas não disponível. Colunas 'Cota Simulada (m)' ou 'Cota Realizada (m)' não encontradas.")
    
    # --- GRÁFICO DE VOLUME ---
    st.subheader("📈 Volume (hm³)")
    if 'Volume(m³)' in dff.columns and 'Volume (%)' in dff.columns and 'Volume Observado (m³)' in dff.columns:
        dff["Volume(m³)"] = pd.to_numeric(dff["Volume(m³)"].astype(str).str.replace(',', '.'), errors='coerce')
        dff["Volume (%)"] = pd.to_numeric(dff["Volume (%)"].astype(str).str.replace(',', '.'), errors='coerce')
        dff["Volume Observado (m³)"] = pd.to_numeric(dff["Volume Observado (m³)"].astype(str).str.replace(',', '.'), errors='coerce')
        
        dff['Volume (hm³)'] = dff['Volume(m³)'] / 1_000_000
        dff['Volume Observado (hm³)'] = dff['Volume Observado (m³)'] / 1_000_000
        
        fig_vol = go.Figure()
        for acude in sorted(dff["Açude"].dropna().unique()):
            base = dff[dff["Açude"] == acude].sort_values("Data")
            
            fig_vol.add_trace(go.Scatter(
                x=base["Data"], 
                y=base["Volume (hm³)"], 
                mode="lines+markers", 
                name=f"{acude} - Vol. Simulado (hm³)", 
                hovertemplate="""
                    <b>%{x|%d/%m/%Y}</b><br>
                    <b>Vol. Simulado:</b> %{y:,.2f} hm³<br>
                    <b>Vol. Percentual:</b> %{customdata:,.2f}%<br>
                    <extra></extra>
                """,
                customdata=base["Volume (%)"]
            ))
            
            fig_vol.add_trace(go.Scatter(
                x=base["Data"], 
                y=base["Volume Observado (hm³)"], 
                mode="lines+markers", 
                name=f"{acude} - Vol. Observado (hm³)", 
                hovertemplate="""
                    <b>%{x|%d/%m/%Y}</b><br>
                    <b>Vol. Observado:</b> %{y:,.2f} hm³<br>
                    <extra></extra>
                """
            ))
        
        fig_vol.update_layout(
            template="plotly_white", 
            margin=dict(l=10, r=10, t=10, b=10), 
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), 
            xaxis_title="Data", 
            yaxis_title="Volume (hm³)", 
            height=420
        )
        st.plotly_chart(fig_vol, use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Gráfico de Volume não disponível. Verifique se as colunas 'Volume(m³)', 'Volume (%)' e 'Volume Observado (m³)' existem na planilha.")

    # --- TABELA DE DADOS ---
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
            'Volume Observado (m³)',
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
                "Volume Observado (m³)": st.column_config.NumberColumn(format="%.2f"),
                "Volume (%)": st.column_config.NumberColumn(format="%.2f"),
                "Liberação (m³/s)": st.column_config.NumberColumn(format="%.2f"),
                "Liberação (m³)": st.column_config.NumberColumn(format="%.2f")
            }
        )
