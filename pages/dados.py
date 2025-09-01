import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
import json
# from streamlit_folium import st_folium   # ⛔ não usado mais
from folium.plugins import Fullscreen, MousePosition
from streamlit.components.v1 import html as st_html  # ✅ para exibir HTML cacheado
from utils.common import load_geojson_data

st.set_page_config(layout="wide")

# ----------------- Caches de dados -----------------
@st.cache_data(ttl=600)
def load_sheet_cached(url: str) -> pd.DataFrame:
    return pd.read_csv(url)

@st.cache_data(ttl=3600)
def load_geojson_cached() -> dict:
    return load_geojson_data()

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

    google_sheet_url = "https://docs.google.com/spreadsheets/d/1C40uaNmLUeu-k_FGEPZOgF8FwpSU00C9PtQu8Co4AUI/gviz/tq?tqx=out:csv&sheet=simulacoes_data"
    try:
        df = load_sheet_cached(google_sheet_url)   # ✅ cache
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        if 'Coordendas' in df.columns:
            df.rename(columns={'Coordendas': 'Coordenadas'}, inplace=True)
    except Exception as e:
        st.error(f"Erro ao carregar os dados da planilha. Verifique o link/permits. Detalhes: {e}")
        return
    if df.empty:
        st.info("A planilha de simulações está vazia.")
        return

    # ---------- GeoJSON (cache) ----------
    geojson_data = load_geojson_cached()
    geojson_situa = geojson_data.get('geojson_situa', {})

    def _get_geo_classes(gj: dict) -> set:
        classes = set()
        if isinstance(gj, dict) and gj.get('type') == 'FeatureCollection':
            for f in gj.get('features', []):
                props = (f.get('properties') or {})
                for k in ['Classificação','classificacao','CLASSIFICACAO','classificação','situacao','SITUACAO']:
                    if k in props and pd.notna(props[k]):
                        classes.add(str(props[k]).strip()); break
        return classes

    geo_classes = _get_geo_classes(geojson_situa)
    opcoes_classificacao_df = set(df["Classificação"].dropna().astype(str).str.strip().tolist())
    opcoes_classificacao = sorted(opcoes_classificacao_df.union(geo_classes))

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
                classificacao_sel = st.multiselect("Classificação", options=opcoes_classificacao, default=opcoes_classificacao)
            with col4:
                datas_validas = df["Data"]
                if not datas_validas.empty:
                    data_min, data_max = datas_validas.min().date(), datas_validas.max().date()
                    periodo = st.date_input("Período", value=(data_min, data_max),
                                            min_value=data_min, max_value=data_max, format="DD/MM/YYYY")
                else:
                    periodo = None
            st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ---------- Aplicação dos filtros ----------
    def padronizar_classificacao(valor):
        if pd.isna(valor): return "sem classificação"
        valor = str(valor).strip().lower()
        if "fora" in valor and "criticidade" in valor: return "fora de criticidade"
        return valor

    dff = df.copy()
    if acudes_sel:
        dff = dff[dff["Açude"].isin(acudes_sel)]
    if municipios_sel:
        dff = dff[dff["Município"].isin(municipios_sel)]
    if classificacao_sel:
        classificacoes_filtradas = [padronizar_classificacao(c) for c in classificacao_sel]
        dff = dff[dff["Classificação"].apply(padronizar_classificacao).isin(classificacoes_filtradas)]
    if periodo:
        ini, fim = (pd.to_datetime(periodo[0]), pd.to_datetime(periodo[-1]))
        dff = dff[(dff["Data"] >= ini) & (dff["Data"] <= fim)]
    if dff.empty:
        st.info("Não há dados para os filtros selecionados.")
        return

    # Latitude/Longitude – extrai e normaliza
    if 'Coordenadas' in dff.columns and not {'Latitude','Longitude'} <= set(dff.columns):
        try:
            dff[['Latitude','Longitude']] = dff['Coordenadas'].astype(str).str.split(',', n=1, expand=True)
        except Exception:
            pass

    for col in ['Latitude','Longitude']:
        if col in dff.columns:
            dff[col] = pd.to_numeric(dff[col].astype(str).str.replace(',', '.'), errors='coerce')

    # df_map = somente coordenadas válidas (sem NaN e dentro da faixa)
    df_map = dff.copy()
    if {'Latitude','Longitude'} <= set(df_map.columns):
        df_map = df_map[
            df_map['Latitude'].between(-90, 90) &
            df_map['Longitude'].between(-180, 180)
        ].dropna(subset=['Latitude', 'Longitude'])
    else:
        df_map = pd.DataFrame(columns=dff.columns)

    dff = dff.sort_values(["Açude", "Data"])

    # ===================== 🌍 Mapa dos Açudes =====================
    st.subheader("🌍 Mapa dos Açudes")

    with st.expander("Mapas de Fundo", expanded=False):
        tile_option = st.selectbox(
            "Estilo do Mapa:",
            ["OpenStreetMap","Stamen Terrain","Stamen Toner","CartoDB positron","CartoDB dark_matter","Esri Satellite"],
            index=0, key='map_style_select'
        )

    # Assinatura do mapa (para decidir quando recalcular)
    def build_map_signature(dfm: pd.DataFrame, tile: str, classes) -> int:
        cols = [c for c in ['Latitude','Longitude','Classificação','Açude','Município'] if c in dfm.columns]
        if not cols:
            return hash((tile, 'no_points'))
        dfh = dfm[cols].copy()
        if 'Latitude' in dfh:  dfh['Latitude']  = dfh['Latitude'].round(6)
        if 'Longitude' in dfh: dfh['Longitude'] = dfh['Longitude'].round(6)
        try:
            sig_df = int(pd.util.hash_pandas_object(dfh, index=False).sum())
        except Exception:
            sig_df = len(dfh)
        return hash((sig_df, tile, tuple(sorted(map(str, classes or [])))))

    map_sig = build_map_signature(df_map, tile_option, classificacao_sel)

    # Se possível, reutiliza HTML cacheado (super rápido)
    if st.session_state.get('map_sig') == map_sig and st.session_state.get('map_html'):
        st_html(st.session_state['map_html'], height=700, scrolling=False)  # ✅ reutiliza
    else:
        # ---- montar mapa apenas quando precisa ----
        tile_config = {
            "OpenStreetMap": {"tiles": "OpenStreetMap", "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'},
            "Stamen Terrain": {"tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png", "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
            "CartoDB positron": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
            "CartoDB dark_matter": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
            "Esri Satellite": {"tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "attr": "Tiles &copy; Esri — Source: Esri"},
            "Stamen Toner": {"tiles": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png", "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
        }

        geojson_bacia = geojson_data.get('geojson_bacia', {})
        geojson_sedes = geojson_data.get('geojson_sedes', {})

        # Centro inicial baseado em df_map (limpo)
        if not df_map.empty:
            start_center = [float(df_map['Latitude'].mean()), float(df_map['Longitude'].mean())]
        else:
            start_center = [-5.2, -39.5]

        m = folium.Map(location=start_center, zoom_start=9, tiles=None)
        folium.TileLayer(tiles=tile_config[tile_option]["tiles"],
                         attr=tile_config[tile_option]["attr"], name=tile_option).add_to(m)

        # helpers
        def padronizar_classificacao_map(classificacao):
            c = str(classificacao or "").strip().lower()
            c = (c.replace("á","a").replace("ã","a").replace("â","a")
                   .replace("é","e").replace("ê","e")
                   .replace("í","i").replace("î","i")
                   .replace("ó","o").replace("ô","o")
                   .replace("ú","u").replace("û","u")
                   .replace("ç","c"))
            if c == "normal" or ("fora" in c and "criticidade" in c): return "fora de criticidade"
            if "alta" in c:  return "criticidade alta"
            if "media" in c: return "criticidade média"
            if "baixa" in c: return "criticidade baixa"
            if "sem" in c and "class" in c: return "sem classificação"
            return c or "sem classificação"

        def get_classification_color(classificacao):
            c = padronizar_classificacao_map(classificacao)
            return {
                "fora de criticidade": "#8DCC90",
                "criticidade alta":    "#E24F42",
                "criticidade média":   "#ECC116",
                "criticidade baixa":   "#F4FA4A",
                "sem classificação":   "#999999"
            }.get(c, "#999999")

        def _compute_bounds_from_geojson(gj: dict):
            try:
                if not isinstance(gj, dict) or gj.get("type") != "FeatureCollection":
                    return None
                lats, lons = [], []
                for feat in gj.get("features", []):
                    geom = (feat or {}).get("geometry", {}) or {}
                    gtype = geom.get("type"); coords = geom.get("coordinates", [])
                    if gtype == "Polygon":
                        for ring in coords:
                            for lon, lat in ring: lats.append(lat); lons.append(lon)
                    elif gtype == "MultiPolygon":
                        for poly in coords:
                            for ring in poly:
                                for lon, lat in ring: lats.append(lat); lons.append(lon)
                    elif gtype == "LineString":
                        for lon, lat in coords: lats.append(lat); lons.append(lon)
                    elif gtype == "MultiLineString":
                        for line in coords:
                            for lon, lat in line: lats.append(lat); lons.append(lon)
                    elif gtype == "Point" and len(coords) >= 2:
                        lons.append(coords[0]); lats.append(coords[1])
                    elif gtype == "MultiPoint":
                        for lon, lat in coords: lats.append(lat); lons.append(lon)
                if lats and lons:
                    return [[min(lats), min(lons)], [max(lats), max(lons)]]
            except Exception:
                return None
            return None

        # Bacia + fit_bounds
        if geojson_bacia:
            gj_bacia = folium.GeoJson(
                geojson_bacia, name="Bacia do Banabuiú",
                style_function=lambda x: {"color":"blue","weight":2,"fillOpacity":0.1},
                tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"])
            ).add_to(m)
            try:
                bounds = gj_bacia.get_bounds()
            except Exception:
                bounds = _compute_bounds_from_geojson(geojson_bacia)
            if bounds: m.fit_bounds(bounds)

        # Sedes Municipais
        if geojson_sedes and isinstance(geojson_sedes, dict) and "features" in geojson_sedes:
            sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=True)
            for feature in geojson_sedes["features"]:
                props = feature.get("properties", {})
                geom  = feature.get("geometry", {})
                coords = geom.get("coordinates", [])
                if geom.get("type") == "Point" and isinstance(coords, (list, tuple)) and len(coords) >= 2:
                    nome = props.get("NOME_MUNIC", "Sem nome")
                    try:
                        lat, lon = float(coords[1]), float(coords[0])
                        folium.Marker(
                            [lat, lon],
                            icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png", icon_size=(25, 25)),
                            tooltip=nome
                        ).add_to(sedes_layer)
                    except Exception:
                        continue
            sedes_layer.add_to(m)

        # Situação (GeoJSON filtrado)
        def _get_classificacao_from_props_map(props: dict):
            if not isinstance(props, dict): return None
            for k in ['Classificação','classificacao','CLASSIFICACAO','classificação','situacao','SITUACAO']:
                if k in props and pd.notna(props[k]): return padronizar_classificacao_map(props[k])
            return None

        def filtrar_geojson_por_classificacao(geojson_fc, classes_sel):
            if not geojson_fc or geojson_fc.get('type') != 'FeatureCollection': return {}
            sel_lower = {str(c).lower() for c in (classes_sel or [])}
            feats = []
            for f in geojson_fc.get('features', []):
                cls = _get_classificacao_from_props_map(f.get('properties', {}))
                if cls is None:
                    if {'sem classificação','sem classificacao'} & sel_lower: feats.append(f)
                else:
                    if cls.lower() in sel_lower: feats.append(f)
            return {'type': 'FeatureCollection', 'features': feats} if feats else {}

        geojson_situa_filtrado = filtrar_geojson_por_classificacao(geojson_situa, classificacao_sel)
        if geojson_situa_filtrado:
            situa_group = folium.FeatureGroup(name="Situação da Bacia", show=True)
            folium.GeoJson(
                geojson_situa_filtrado,
                style_function=lambda feature: {
                    'fillColor': get_classification_color(feature.get('properties', {}).get('Classificação')),
                    'color': '#555555','weight': 1.5,'fillOpacity': 0.7,'opacity': 0.9
                },
                tooltip=folium.GeoJsonTooltip(fields=['Classificação'], aliases=['Classificação:'], sticky=True)
            ).add_to(situa_group)
            situa_group.add_to(m)

        # Marcadores
        if not df_map.empty:
            for _, row in df_map.iterrows():
                try:
                    lat, lon = float(row['Latitude']), float(row['Longitude'])
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
                    location=[lat, lon], radius=6, color=color_marker, fill=True, fill_color=color_marker,
                    fill_opacity=0.9, tooltip=row.get('Açude', 'N/A'), popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)
        else:
            st.info("Nenhum ponto válido para plotar no mapa (coordenadas ausentes/fora da faixa).")

        Fullscreen().add_to(m)
        MousePosition(position="bottomleft", separator=" | ", num_digits=4).add_to(m)
        folium.LayerControl(collapsed=False).add_to(m)

        # ✅ renderiza e guarda HTML no estado da sessão (sem botões/alternadores)
        html = m.get_root().render()
        st_html(html, height=700, scrolling=False)
        st.session_state['map_sig'] = map_sig
        st.session_state['map_html'] = html

    # --------- Legenda ---------
    st.markdown("""
    <style>
    .map-legend-container { position: relative; margin-top: -20px; margin-bottom: 12px; z-index: 1000; }
    .map-legend { background: white; padding: 10px 15px; border-radius: 5px;
                  box-shadow: 0 2px 8px rgba(0,0,0,0.15); border: 1px solid #eee; display: inline-block; }
    .legend-items { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; }
    .legend-item { display: flex; align-items: center; }
    .legend-color { width: 18px; height: 18px; margin-right: 8px; border: 1px solid #555; border-radius: 3px; }
    .legend-label { font-size: 13px; font-family: Arial, sans-serif; color: #333; }
    </style>
    <div class="map-legend-container">
        <div class="map-legend">
            <div class="legend-items">
                <div class="legend-item"><div class="legend-color" style="background-color:#E24F42;"></div><span class="legend-label">Criticidade Alta (até 12/2025)</span></div>
                <div class="legend-item"><div class="legend-color" style="background-color:#ECC116;"></div><span class="legend-label">Criticidade Média (até 06/2026)</span></div>
                <div class="legend-item"><div class="legend-color" style="background-color:#F4FA4A;"></div><span class="legend-label">Criticidade Baixa (até 12/2026)</span></div>
                <div class="legend-item"><div class="legend-color" style="background-color:#8DCC90;"></div><span class="legend-label">Fora de Criticidade (após 12/2026)</span></div>
                <div class="legend-item"><div class="legend-color" style="background-color:#999999;"></div><span class="legend-label">Sem classificação</span></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ===================== KPIs =====================
    st.subheader("📊 Indicadores de Desempenho (KPIs)")
    st.markdown("""
    <style>
    .kpi-card { background-color:#f0f4f8; border:1px solid #d9e2eb; border-radius:10px;
                padding:20px; text-align:center; box-shadow:0 4px 8px rgba(0,0,0,0.1);
                transition:transform .2s; height:100%; display:flex; flex-direction:column; justify-content:center; }
    .kpi-card:hover { transform: translateY(-5px); }
    .kpi-label { font-size:16px; color:#5a7d9a; font-weight:bold; margin-bottom:5px; }
    .kpi-value { font-size:28px; font-weight:bold; color:#2c3e50; }
    </style>
    """, unsafe_allow_html=True)

    kpi_cols = st.columns(4)

    if 'Liberação (m³/s)' in dff.columns:
        with kpi_cols[0]:
            try:
                dff["Liberação (m³/s)"] = pd.to_numeric(dff["Liberação (m³/s)"].astype(str).str.replace(',', '.'), errors='coerce')
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
            st.warning("Coluna 'Liberação (m³/s)' não encontrada.")

    with kpi_cols[1]:
        st.markdown(f"""
        <div class="kpi-card"><div class="kpi-label">Data Inicial</div>
        <div class="kpi-value">{(dff["Data"].min().strftime('%d/%m/%Y') if not dff.empty else 'N/A')}</div></div>
        """, unsafe_allow_html=True)
    with kpi_cols[2]:
        st.markdown(f"""
        <div class="kpi-card"><div class="kpi-label">Data Final</div>
        <div class="kpi-value">{(dff['Data'].max().strftime('%d/%m/%Y') if ('Data' in dff.columns and not dff.empty) else 'N/A')}</div></div>
        """, unsafe_allow_html=True)
    with kpi_cols[3]:
        if 'Data' in dff.columns and not dff['Data'].isna().all():
            dias = (dff["Data"].max() - dff["Data"].min()).days
        else:
            dias = "N/A"
        st.markdown(f"""
        <div class="kpi-card"><div class="kpi-label">Dias do Período</div>
        <div class="kpi-value">{dias}</div></div>
        """, unsafe_allow_html=True)

# ===================== Gráficos =====================
    st.markdown("---")
    st.subheader("📈 Cotas (Cota Simulada x Cota Realizada)")
    if 'Cota Simulada (m)' in dff.columns and 'Cota Realizada (m)' in dff.columns:
        dff["Cota Simulada (m)"] = pd.to_numeric(dff["Cota Simulada (m)"].astype(str).str.replace(',', '.'), errors='coerce')
        dff["Cota Realizada (m)"] = pd.to_numeric(dff["Cota Realizada (m)"].astype(str).str.replace(',', '.'), errors='coerce')
        fig_cotas = go.Figure()
        for acude in sorted(dff["Açude"].dropna().unique()):
            base = dff[dff["Açude"] == acude].sort_values("Data")
            fig_cotas.add_trace(go.Scatter(x=base["Data"], y=base["Cota Simulada (m)"],
                                           mode="lines+markers", name=f"{acude} - Cota Simulada (m)",
                                           hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"))
            fig_cotas.add_trace(go.Scatter(x=base["Data"], y=base["Cota Realizada (m)"],
                                           mode="lines+markers", name=f"{acude} - Cota Realizada (m)",
                                           hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"))
        fig_cotas.update_layout(template="plotly_white", margin=dict(l=10,r=10,t=10,b=10),
                                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                                xaxis_title="Data", yaxis=dict(title="Cota (m)", tickformat=".2f"), height=480)
        st.plotly_chart(fig_cotas, use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Gráfico de Cotas não disponível. Colunas ausentes.")

#=====================📈 Volume (m³)
    st.subheader("📈 Volume (m³)")
    if {'Volume(m³)','Volume (%)','Volume Observado (m³)'} <= set(dff.columns):
        # Conversão dos dados
        dff["Volume(m³)"] = pd.to_numeric(dff["Volume(m³)"].astype(str).str.replace(',', '.'), errors='coerce')
        dff["Volume (%)"] = pd.to_numeric(dff["Volume (%)"].astype(str).str.replace(',', '.'), errors='coerce')
        dff["Volume Observado (m³)"] = pd.to_numeric(dff["Volume Observado (m³)"].astype(str).str.replace(',', '.'), errors='coerce')
        
        fig_vol = go.Figure()
        
        for acude in sorted(dff["Açude"].dropna().unique()):
            base = dff[dff["Açude"] == acude].sort_values("Data")
            
            # Volume Simulado
            fig_vol.add_trace(go.Scatter(
                x=base["Data"], 
                y=base["Volume(m³)"],
                mode="lines+markers", 
                name=f"{acude} - Vol. Simulado",
                hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Vol. Simulado: %{y:,.0f} m³<br>Vol. Percentual: %{customdata:,.2f}%<extra></extra>",
                customdata=base["Volume (%)"]
            ))
            
            # Volume Observado - apenas se houver dados
            if base["Volume Observado (m³)"].notna().any():
                fig_vol.add_trace(go.Scatter(
                    x=base["Data"], 
                    y=base["Volume Observado (m³)"],
                    mode="lines+markers", 
                    name=f"{acude} - Vol. Observado",
                    line=dict(dash='dash'),  # Linha tracejada para diferenciar
                    hovertemplate="<b>%{x|%d/%m/%Y}</b><br>Vol. Observado: %{y:,.0f} m³<extra></extra>"
                ))
        
        fig_vol.update_layout(
            template="plotly_white", 
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            xaxis_title="Data", 
            yaxis_title="Volume (m³)", 
            height=450
        )
        st.plotly_chart(fig_vol, use_container_width=True, config={"displaylogo": False})
    else:
        st.error(f"Colunas faltantes: { {'Volume(m³)','Volume (%)','Volume Observado (m³)'} - set(dff.columns) }")
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
        colunas_existentes = [c for c in colunas_tabela if c in dff.columns]
        dff_tabela = dff[colunas_existentes]
        st.dataframe(
            dff_tabela.sort_values(["Açude","Data"], ascending=[True, False]),
            use_container_width=True,
            column_config={
                "Data": st.column_config.DateColumn("Data", format="DD/MM/YYYY"),
                "Cota Simulada (m)": st.column_config.NumberColumn(format="%.3f"),
                "Cota Realizada (m)": st.column_config.NumberColumn(format="%.3f"),
                "Volume(m³)": st.column_config.NumberColumn(format="%.2f"),
                "Volume Observado (m³)": st.column_config.NumberColumn(format="%.2f"),
                "Volume (%)": st.column_config.NumberColumn(format="%.2f"),
                "Liberação (m³/s)": st.column_config.NumberColumn(format="%.2f"),
                "Liberação (m³)": st.column_config.NumberColumn(format="%.2f"),
            }
        )


