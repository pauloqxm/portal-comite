import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
import json
import unicodedata
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MousePosition
from utils.common import load_geojson_data

# Use cache para carregar dados externos uma única vez
@st.cache_data(show_spinner="Carregando dados da planilha...")
def load_data():
    google_sheet_url = "https://docs.google.com/spreadsheets/d/1C40uaNmLUeu-k_FGEPZOgF8FwpSU00C9PtQu8Co4AUI/gviz/tq?tqx=out:csv&sheet=simulacoes_data"
    try:
        df = pd.read_csv(google_sheet_url)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        if 'Coordendas' in df.columns:
            df.rename(columns={'Coordendas': 'Coordenadas'}, inplace=True)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar os dados da planilha. Verifique se o link está correto e se a planilha está pública. Detalhes do erro: {e}")
        return pd.DataFrame()

@st.cache_data(show_spinner="Carregando arquivos GeoJSON...")
def load_map_data():
    return load_geojson_data()

# Definição das funções de padronização
def padronizar_classificacao(valor):
    """Padroniza os valores de classificação para comparação"""
    if pd.isna(valor):
        return "sem classificação"
    valor = str(valor).strip().lower()
    if "fora" in valor and "criticidade" in valor:
        return "fora de criticidade"
    # Você pode adicionar mais padronizações aqui, se necessário
    return valor

def _get_classificacao_from_props(props: dict) -> str:
    """Extrai e padroniza a classificação de um dicionário de propriedades de GeoJSON."""
    for k in ['Classificação', 'classificacao', 'CLASSIFICACAO', 'classificação', 'situacao', 'SITUACAO']:
        if k in props and pd.notna(props[k]):
            return padronizar_classificacao(props[k])
    return "sem classificação"

def render_dados():
    st.title("📈 Situação das Sedes Municipais")
    st.markdown("""
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
    <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Situação do abastecimento <b>das Sede Municipais</b><br>
    • Linha comparativa de <b>Cota Simulada (m)</b> e <b>Cota Realizada (m)</b><br>
    • Filtros por <b>Data</b>, <b>Açude</b>, <b>Município</b> e <b>Classificação</b><br>
    • Mapa interativo com camadas<br>
    • Indicadores de <b>KPIs</b> e tabela de dados
    </p>
</div>
""", unsafe_allow_html=True)

    df = load_data()
    if df.empty:
        st.info("A planilha de simulações está vazia. Por favor, verifique os dados.")
        return

    # GeoJSONs adicionais
    geojson_data = load_map_data()
    geojson_situa = geojson_data.get('geojson_situa', {})
    geojson_bacia = geojson_data.get('geojson_bacia', {})
    geojson_sedes = geojson_data.get('geojson_sedes', {})

    def _get_geo_classes(gj: dict) -> set:
        classes = set()
        if isinstance(gj, dict) and gj.get('type') == 'FeatureCollection':
            for f in gj.get('features', []):
                props = (f.get('properties') or {})
                for k in ['Classificação', 'classificacao', 'CLASSIFICACAO', 'classificação', 'situacao', 'SITUACAO']:
                    if k in props and pd.notna(props[k]):
                        classes.add(padronizar_classificacao(props[k]))
                        break
        return classes

    geo_classes = _get_geo_classes(geojson_situa)
    opcoes_classificacao_df = set(df["Classificação"].dropna().apply(padronizar_classificacao).tolist())
    opcoes_classificacao_unificadas = sorted(list(opcoes_classificacao_df.union(geo_classes)))
    
    # Mapeamento para exibir nomes mais bonitos nos filtros
    mapa_exibicao = {
        'fora de criticidade': 'Fora de Criticidade',
        'criticidade alta': 'Criticidade Alta',
        'criticidade média': 'Criticidade Média',
        'criticidade baixa': 'Criticidade Baixa',
        'sem classificação': 'Sem classificação'
    }
    
    opcoes_exibicao = [mapa_exibicao.get(o, o) for o in opcoes_classificacao_unificadas]
    
    # ---------- Estilos dos filtros ----------
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

    # ---------- Filtros ----------
    with st.container():
        st.markdown('<div class="expander-rounded">', unsafe_allow_html=True)
        with st.expander("☰ Filtros (clique para expandir)", expanded=True):
            st.markdown('<div class="filter-card"><div class="filter-title">Filtros de Visualização</div>', unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                opcoes_acudes = sorted(df["Açude"].dropna().unique().tolist())
                acudes_sel = st.multiselect("Açude", options=opcoes_acudes, default=[])
            with col2:
                opcoes_municipios = sorted(df["Município"].dropna().unique().tolist())
                municipios_sel = st.multiselect("Município", options=opcoes_municipios, default=[])
            with col3:
                classificacao_sel_exibicao = st.multiselect("Classificação", options=opcoes_exibicao, default=opcoes_exibicao)
                classificacao_sel = [k for k, v in mapa_exibicao.items() if v in classificacao_sel_exibicao]
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

    # ---------- Aplicação dos filtros ----------
    dff = df.copy()

    # Filtro de Açudes
    if acudes_sel:
        dff = dff[dff["Açude"].isin(acudes_sel)]

    # Filtro de Municípios
    if municipios_sel:
        dff = dff[dff["Município"].isin(municipios_sel)]

    # Filtro de Classificação (com tratamento especial para "Fora de Criticidade")
    if classificacao_sel:
        classificacoes_filtradas = [padronizar_classificacao(c) for c in classificacao_sel]
        dff = dff[dff["Classificação"].apply(padronizar_classificacao).isin(classificacoes_filtradas)]

    # Filtro de Período
    if periodo:
        if len(periodo) == 1:
            ini = fim = pd.to_datetime(periodo[0])
        else:
            ini, fim = [pd.to_datetime(d) for d in periodo]
        dff = dff[(dff["Data"] >= ini) & (dff["Data"] <= fim)]

    if dff.empty:
        st.info("Não há dados para os filtros selecionados.")
        return

    # Latitude/Longitude a partir de "Coordenadas"
    if 'Coordenadas' in dff.columns:
        try:
            dff[['Latitude', 'Longitude']] = dff['Coordenadas'].astype(str).str.split(',', expand=True).astype(float)
        except Exception:
            latlon = dff['Coordenadas'].astype(str).str.split(',', n=1, expand=True)
            dff['Latitude'] = pd.to_numeric(latlon[0], errors='coerce')
            dff['Longitude'] = pd.to_numeric(latlon[1], errors='coerce')
    else:
        st.warning("A coluna 'Coordenadas' não foi encontrada. O mapa não será exibido.")

    dff = dff.sort_values(["Açude", "Data"])

    # ===================== Mapa dos Açudes =====================
    st.subheader("🌍 Mapa dos Açudes")
    
    with st.expander("Mapas de Fundo", expanded=False):
        tile_option = st.selectbox(
            "Estilo do Mapa:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            index=0,
            key='map_style_select'
        )

    # Configurações dos tiles
    tile_config = {
        "OpenStreetMap": {"tiles": "OpenStreetMap", "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'},
        "Stamen Terrain": {"tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png", "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
        "CartoDB positron": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
        "CartoDB dark_matter": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
        "Esri Satellite": {"tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "attr": "Tiles &copy; Esri — Source: Esri"},
        "Stamen Toner": {"tiles": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png", "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
    }
    
    # Configuração inicial do mapa
    if not dff.empty and {'Latitude', 'Longitude'}.issubset(dff.columns):
        start_center = [float(dff['Latitude'].mean()), float(dff['Longitude'].mean())]
    else:
        start_center = [-5.2, -39.5]  # Coordenadas padrão

    m = folium.Map(location=start_center, zoom_start=9, tiles=None)
    folium.TileLayer(
        tiles=tile_config[tile_option]["tiles"],
        attr=tile_config[tile_option]["attr"],
        name=tile_option
    ).add_to(m)

    # Cores por classificação
    def get_classification_color(classificacao):
        """Retorna a cor baseada na classificação padronizada"""
        classificacao = padronizar_classificacao(classificacao)
        color_map = {
            "fora de criticidade": "#8DCC90",
            "criticidade alta": "#E24F42",
            "criticidade média": "#ECC116",
            "criticidade baixa": "#F4FA4A",
            "sem classificação": "#999999"
        }
        return color_map.get(classificacao, "#999999")

    # Adiciona camadas do GeoJSON
    if geojson_bacia:
        gj_bacia = folium.GeoJson(
            geojson_bacia,
            name="Bacia do Banabuiú",
            style_function=lambda x: {"color": "blue", "weight": 2, "fillOpacity": 0.1},
            tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"])
        ).add_to(m)

    # Sedes Municipais
    if geojson_sedes and isinstance(geojson_sedes, dict) and "features" in geojson_sedes:
        sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=True)
        for feature in geojson_sedes["features"]:
            props = feature.get("properties", {})
            geom = feature.get("geometry", {})
            coords = geom.get("coordinates", [])
            if geom.get("type") == "Point" and isinstance(coords, (list, tuple)) and len(coords) >= 2:
                nome = props.get("NOME_MUNIC", "Sem nome")
                try:
                    lat, lon = float(coords[1]), float(coords[0])
                    folium.Marker(
                        [lat, lon],
                        icon=folium.CustomIcon(
                            "https://cdn-icons-png.flaticon.com/512/854/854878.png",
                            icon_size=(25, 25)
                        ),
                        tooltip=nome
                    ).add_to(sedes_layer)
                except Exception:
                    continue
        sedes_layer.add_to(m)

    # Filtra GeoJSON pela classificação selecionada
    def filtrar_geojson_por_classificacao(geojson_fc, classes_sel):
        if not geojson_fc or geojson_fc.get('type') != 'FeatureCollection':
            return {}
        sel_canon = {padronizar_classificacao(c) for c in (classes_sel or [])}
        feats = []
        for f in geojson_fc.get('features', []):
            cls_canon = _get_classificacao_from_props(f.get('properties', {}))
            if cls_canon in sel_canon:
                f.setdefault("properties", {})["Classificacao"] = mapa_exibicao.get(cls_canon, cls_canon)
                feats.append(f)
        return {'type': 'FeatureCollection', 'features': feats} if feats else {}

    geojson_situa_filtrado = filtrar_geojson_por_classificacao(geojson_situa, classificacao_sel_exibicao)
    if geojson_situa_filtrado:
        situa_group = folium.FeatureGroup(name="Situação da Bacia", show=True)
        folium.GeoJson(
            geojson_situa_filtrado,
            style_function=lambda feature: {
                'fillColor': get_classification_color(feature.get('properties', {}).get('Classificacao')),
                'color': '#555555',
                'weight': 1.5,
                'fillOpacity': 0.7,
                'opacity': 0.9
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['Classificacao'],
                aliases=['Classificação:'],
                sticky=True
            )
        ).add_to(situa_group)
        situa_group.add_to(m)

    # Adiciona marcadores dos açudes
    if not dff.empty and {'Latitude', 'Longitude'}.issubset(dff.columns):
        for _, row in dff.iterrows():
            try:
                lat = float(row['Latitude'])
                lon = float(row['Longitude'])
                if pd.isna(lat) or pd.isna(lon): # Adiciona esta verificação
                    continue
            except Exception:
                continue
            
            classificacao = row.get('Classificação', 'Sem classificação')
            color_marker = get_classification_color(classificacao)
            
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
                location=[lat, lon],
                radius=6,
                color=color_marker,
                fill=True,
                fill_color=color_marker,
                fill_opacity=0.9,
                tooltip=row.get('Açude', 'N/A'),
                popup=folium.Popup(popup_html, max_width=300)
            ).add_to(m)

    # Adiciona controles ao mapa
    Fullscreen().add_to(m)
    MousePosition(position="bottomleft", separator=" | ", num_digits=4).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    # Exibe o mapa com legenda
    folium_static(m, width=1000, height=600)

    # Legenda
    st.markdown("""
    <style>
    .map-legend-container {
        position: relative;
        margin-top: -40px;
        margin-bottom: 20px;
        z-index: 1000;
    }
    .map-legend {
        background: white;
        padding: 10px 15px;
        border-radius: 5px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        border: 1px solid #eee;
        display: inline-block;
        margin: 0 auto;
    }
    .legend-items {
        display: flex;
        flex-wrap: wrap;
        gap: 15px;
        justify-content: center;
    }
    .legend-item {
        display: flex;
        align-items: center;
    }
    .legend-color {
        width: 18px;
        height: 18px;
        margin-right: 8px;
        border: 1px solid #555;
        border-radius: 3px;
    }
    .legend-label {
        font-size: 13px;
        font-family: Arial, sans-serif;
        color: #333;
    }
    </style>
    
    <div class="map-legend-container">
        <div class="map-legend">
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #E24F42;"></div>
                    <span class="legend-label">Criticidade Alta</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #ECC116;"></div>
                    <span class="legend-label">Criticidade Média</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #F4FA4A;"></div>
                    <span class="legend-label">Criticidade Baixa</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #8DCC90;"></div>
                    <span class="legend-label">Fora de Criticidade</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #999999;"></div>
                    <span class="legend-label">Sem classificação</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ===================== KPIs =====================
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
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-label { font-size: 16px; color: #5a7d9a; font-weight: bold; margin-bottom: 5px; }
    .kpi-value { font-size: 28px; font-weight: bold; color: #2c3e50; }
    </style>
    """, unsafe_allow_html=True)

    kpi_cols = st.columns(4)
    
    # KPI: Vazão Simulada (m³/h)
    if 'Liberação (m³/s)' in dff.columns:
        with kpi_cols[0]:
            try:
                dff["Liberação (m³/s)"] = pd.to_numeric(
                    dff["Liberação (m³/s)"].astype(str).str.replace(',', '.'),
                    errors='coerce'
                )
                
                data_mais_antiga = dff['Data'].min()
                df_dia_antigo = dff[dff['Data'] == data_mais_antiga]
                primeira_liberacao_m3s = df_dia_antigo["Liberação (m³/s)"].iloc[0]
                liberacao_m3h = primeira_liberacao_m3s * 3600
                
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Vazão Simulada (m³/h)</div>
                    <div class="kpi-value">{liberacao_m3h:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.warning(f"Não foi possível calcular a liberação. Erro: {str(e)}")
    else:
        with kpi_cols[0]:
            st.warning("Coluna 'Liberação (m³/s)' não encontrada. KPI não disponível.")

    # KPI: Data Inicial
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

    # KPI: Data Final
    with kpi_cols[2]:
        if not dff.empty and 'Data' in dff.columns:
            ultima_data = dff['Data'].max().strftime('%d/%m/%Y')
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Data Final</div>
                <div class="kpi-value">{ultima_data}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="kpi-card">
                <div class="kpi-label">Data Final</div>
                <div class="kpi-value">N/A</div>
            </div>
            """, unsafe_allow_html=True)

    # KPI: Dias do Período
    with kpi_cols[3]:
        if 'Data' in dff.columns and not dff['Data'].isna().all():
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

    # ===================== Gráfico de Cotas =====================
    st.markdown("---")
    st.subheader("📈 Cotas (Cota Simulada x Cota Realizada)")
    if 'Cota Simulada (m)' in dff.columns and 'Cota Realizada (m)' in dff.columns:
        dff["Cota Simulada (m)"] = pd.to_numeric(dff["Cota Simulada (m)"].astype(str).str.replace(',', '.'), errors='coerce')
        dff["Cota Realizada (m)"] = pd.to_numeric(dff["Cota Realizada (m)"].astype(str).str.replace(',', '.'), errors='coerce')
        fig_cotas = go.Figure()
        for acude in sorted(dff["Açude"].dropna().unique()):
            base = dff[dff["Açude"] == acude].sort_values("Data")
            fig_cotas.add_trace(go.Scatter(
                x=base["Data"], y=base["Cota Simulada (m)"],
                mode="lines+markers", name=f"{acude} - Cota Simulada (m)",
                hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"
            ))
            fig_cotas.add_trace(go.Scatter(
                x=base["Data"], y=base["Cota Realizada (m)"],
                mode="lines+markers", name=f"{acude} - Cota Realizada (m)",
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

    # ===================== Gráfico de Volume =====================
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
                x=base["Data"], y=base["Volume (hm³)"],
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
                x=base["Data"], y=base["Volume Observado (hm³)"],
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

    # ===================== Tabela =====================
    st.markdown("---")
    st.subheader("📋 Tabela de Dados")
    with st.expander("Ver dados filtrados"):
        colunas_tabela = [
            'Data','Açude','Município','Região Hidrográfica',
            'Cota Simulada (m)','Cota Realizada (m)','Volume(m³)','Volume Observado (m³)',
            'Volume (%)','Evapor. Parcial(mm)','Cota Interm. (m)',
            'Liberação (m³/s)','Liberação (m³)','Classificação','Coordenadas'
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

# Executa o aplicativo
if __name__ == "__main__":
    render_dados()
