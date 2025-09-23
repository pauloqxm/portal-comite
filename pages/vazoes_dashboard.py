import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
# from streamlit_folium import st_folium  # não usamos mais
from folium.plugins import Fullscreen, MiniMap, MousePosition, MeasureControl, MarkerCluster
import altair as alt
from streamlit.components.v1 import html as st_html
from utils.common import carregar_dados_vazoes, convert_vazao, load_geojson_data

st.set_page_config(layout="wide")

# ----------------- caches leves -----------------
@st.cache_data(ttl=1800)
def _load_geojson_cached():
    return load_geojson_data()

@st.cache_data(ttl=600)
def _load_vazoes_cached():
    return carregar_dados_vazoes()

def render_vazoes_dashboard():
    """Renderiza a página completa do painel de vazões."""

    # === Carregamento de Dados e GeoJSON (cache) ===
    geojson_data = _load_geojson_cached()
    df = _load_vazoes_cached()

    st.markdown(
        """
        <style>
        .custom-title {
            font-family: 'Segoe UI', Roboto, sans-serif !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            color: #006400 !important;
            text-align: center !important;
            margin: 8px 0 10px 0 !important;
            padding: 12px 22px !important;
            position: relative !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 8px !important;
            background: rgba(144, 238, 144, 0.15) !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 6px rgba(0,0,0,0.06) !important;
        }
        .custom-title::before, .custom-title::after { content: ""; flex: 1; height: 2px; background: linear-gradient(90deg, transparent, #228B22); border-radius: 2px; }
        .custom-title::after { background: linear-gradient(90deg, #228B22, transparent); }
        .custom-title span { display: inline-flex; align-items: center; justify-content: center; font-size: 18px; }
        @media (max-width: 600px) {
            .custom-title { flex-direction: column; gap: 4px; padding: 6px 12px; }
            .custom-title::before, .custom-title::after { width: 70%; height: 1.5px; }
        }
        </style>
        <h1 class="custom-title"><span>💧</span> Painel de Vazões </span></h1>
        """,
        unsafe_allow_html=True,
    )

    # === Botão de Atualização de dados (opcional) ===
    cA1, _, _ = st.columns([1, 1, 1])
    with cA1:
        if st.button("🔄 Atualizar agora", key="btn_vazoes_atualizar"):
            # limpa ambos os caches
            _load_vazoes_cached.clear()
            _load_geojson_cached.clear()
            df = _load_vazoes_cached()
            st.success("Atualizado.")

    # === Filtros da Página ===
    with st.expander("☰ Filtros", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            estacoes = st.multiselect("🏞️ Reservatório", df["Reservatório Monitorado"].dropna().unique(), key="estacoes_vazao")
            operacao = st.multiselect("🔧 Operação", df["Operação"].dropna().unique(), key="operacao_vazao")
        with col2:
            meses = st.multiselect("📆 Mês", df["Mês"].dropna().unique(), key="meses_vazao")
        col3, col4 = st.columns(2)
        with col3:
            datas_disponiveis = df["Data"].dropna().sort_values()
            data_min = datas_disponiveis.min()
            data_max = datas_disponiveis.max()
            intervalo_data = st.date_input("📅 Intervalo", (data_min, data_max), format="DD/MM/YYYY", key="intervalo_vazao")
        with col4:
            unidade_sel = st.selectbox("🧪 Unidade", ["L/s", "m³/s"], index=0, key="unidade_vazao")
        st.markdown("</div>", unsafe_allow_html=True)

    # === Aplica os Filtros ===
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

# === KPIs ===
    st.markdown(
        """
        <style>
        .kpi-container { display: flex; gap: 16px; margin: -15px 0; flex-wrap: wrap; justify-content: space-between; }
        .kpi-card { flex: 1; min-width: 180px; background: linear-gradient(135deg, #e0f5ec, #b2dfdb); border-radius: 12px; padding: 16px; box-shadow: 0 3px 8px rgba(0,0,0,0.08); text-align: center; transition: transform .2s, box-shadow .2s; }
        .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.15); }
        .kpi-label { font-size: 14px; font-weight: 600; color: #004d40; margin-bottom: 6px; text-transform: uppercase; letter-spacing: .5px; }
        .kpi-value { font-size: 24px; font-weight: 700; color: #00695c; }
        @media (max-width: 768px) { .kpi-container { flex-direction: column; } }
        </style>
        """,
        unsafe_allow_html=True,
    )

    reservatorios_count = df_filtrado["Reservatório Monitorado"].nunique()

    # Novo cálculo: quantidade de dias distintos no intervalo
    if not df_filtrado.empty and pd.notna(df_filtrado["Data"].min()) and pd.notna(df_filtrado["Data"].max()):
        dias_count = (df_filtrado["Data"].max() - df_filtrado["Data"].min()).days + 1
    else:
        dias_count = "—"

    ultima_data = df_filtrado["Data"].max().strftime("%d/%m/%Y") if not df_filtrado.empty and pd.notna(df_filtrado["Data"].max()) else "—"
    unidade_show = "m³/s" if unidade_sel == "m³/s" else "L/s"

    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-card"><div class="kpi-label">Reservatórios</div><div class="kpi-value">{reservatorios_count}</div></div>
            <div class="kpi-card"><div class="kpi-label">Dias</div><div class="kpi-value">{dias_count}</div></div>
            <div class="kpi-card"><div class="kpi-label">Última Data</div><div class="kpi-value">{ultima_data}</div></div>
            <div class="kpi-card"><div class="kpi-label">Unidade</div><div class="kpi-value">{unidade_show}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


    # =====================================================================
    # 📈 Evolução da Vazão Operada por Reservatório
    # =====================================================================
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    if not df_filtrado.empty and "Reservatório Monitorado" in df_filtrado.columns:
        fig = go.Figure()
        cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#17becf", "#e377c2"]
        reservatorios = df_filtrado["Reservatório Monitorado"].dropna().unique()
        if len(reservatorios) > 0:
            for i, r in enumerate(reservatorios):
                dfr = (
                    df_filtrado[df_filtrado["Reservatório Monitorado"] == r]
                    .sort_values("Data")
                    .groupby("Data", as_index=False)
                    .last()
                )
                if not dfr.empty:
                    y_vals, unit_suffix = convert_vazao(dfr["Vazão Operada"], unidade_sel)
                    fig.add_trace(go.Scatter(
                        x=dfr["Data"], y=y_vals, mode="lines+markers", name=r,
                        line=dict(shape="hv", width=2, color=cores[i % len(cores)]),
                        marker=dict(size=5),
                        hovertemplate=f"<b>{r}</b><br>Data: %{{x|%d/%m/%Y}}<br>Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
                    ))
                    if len(reservatorios) == 1 and len(dfr) > 1:
                        dfr = dfr.copy()
                        dfr["dias_ativos"] = dfr["Data"].diff().dt.days.fillna(0)
                        if not dfr.empty:
                            dmax = df_filtrado["Data"].max()
                            dfr.loc[dfr.index[-1], "dias_ativos"] = (dmax - dfr["Data"].iloc[-1]).days + 1
                            media_pond = (dfr["Vazão Operada"] * dfr["dias_ativos"]).sum() / dfr["dias_ativos"].sum()
                            media_pond_conv, _ = convert_vazao(pd.Series([media_pond]), unidade_sel)
                            fig.add_hline(
                                y=float(media_pond_conv.iloc[0]), line_dash="dash", line_width=2, line_color="red",
                                annotation_text=f"Média da Operação {media_pond_conv.iloc[0]:.2f} {unit_suffix}",
                                annotation_position="top right"
                            )
                        if "Vazao_Aloc" in dfr.columns:
                            y_aloc, _ = convert_vazao(dfr["Vazao_Aloc"], unidade_sel)
                            fig.add_trace(go.Scatter(
                                x=dfr["Data"], y=y_aloc, mode="lines",
                                name="Vazão Alocada", line=dict(color="blue", width=2, dash="dot"),
                                hovertemplate=f"<b>Vazão Alocada</b><br>Data: %{{x|%d/%m/%Y}}<br>Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
                            ))
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                              height=500, title="Curva da operação por reservatório")
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key="plotly_vazao_evolucao")
        else:
            st.info("Nenhum reservatório encontrado para exibir o gráfico.")
    else:
        st.info("Dados insuficientes para exibir o gráfico de evolução.")

    # =====================================================================
    # 🗺️ Mapa com camadas — render rápido com HTML cacheado
    # =====================================================================
    st.subheader("🗺️ Mapa dos Reservatórios com Camadas")

    df_mapa = df_filtrado.copy()
    coord_col = "Coordenadas" if "Coordenadas" in df_mapa.columns else ("Coordendas" if "Coordendas" in df_mapa.columns else None)
    if coord_col:
        latlon = df_mapa[coord_col].astype(str).str.replace(" ", "")
        parts = latlon.str.split(",", n=1, expand=True)
        df_mapa["lat"] = pd.to_numeric(parts[0], errors="coerce")
        df_mapa["lon"] = pd.to_numeric(parts[1], errors="coerce")
    df_mapa = df_mapa.dropna(subset=["lat", "lon"])
    if "Reservatório Monitorado" in df_mapa.columns:
        df_mapa = df_mapa.drop_duplicates(subset=["Reservatório Monitorado"])

    with st.expander("☰ Estilo do Mapa", expanded=False):
        mapa_tipo = st.selectbox(
            "Selecione o estilo:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            index=0, key="map_style_selector_vazao", label_visibility="collapsed"
        )

    tile_urls = {
        "OpenStreetMap": None,
        "Stamen Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        "Stamen Toner": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
        "CartoDB positron": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
        "CartoDB dark_matter": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
        "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    }
    tile_attr = {
        "OpenStreetMap": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        "Stamen Terrain": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under CC BY 3.0. Data by OpenStreetMap, under ODbL.',
        "Stamen Toner": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under CC BY 3.0. Data by OpenStreetMap, under ODbL.',
        "CartoDB positron": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        "CartoDB dark_matter": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
        "Esri Satellite": "Tiles &copy; Esri — Sources: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, GIS User Community"
    }

    # ---------- assinatura p/ cache do mapa ----------
    def _map_signature(dfm: pd.DataFrame, tile: str, unidade: str) -> int:
        if dfm.empty:
            return hash((tile, unidade, "empty"))
        cols = [c for c in ["lat", "lon", "Reservatório Monitorado", "Data", "Vazao_Aloc"] if c in dfm.columns]
        sig_df = dfm[cols].copy()
        sig_df["lat"] = sig_df["lat"].round(6)
        sig_df["lon"] = sig_df["lon"].round(6)
        if "Data" in sig_df:
            sig_df["Data"] = pd.to_datetime(sig_df["Data"], errors="coerce").dt.date.astype(str)
        # força numérico para não depender de formatação
        if "Vazao_Aloc" in sig_df:
            sig_df["Vazao_Aloc"] = pd.to_numeric(sig_df["Vazao_Aloc"], errors="coerce").fillna(0)
        try:
            sig_num = int(pd.util.hash_pandas_object(sig_df, index=False).sum())
        except Exception:
            sig_num = len(sig_df)
        return hash((sig_num, tile, unidade))

    map_sig = _map_signature(df_mapa, mapa_tipo, unidade_sel)

    if st.session_state.get("vazoes_map_sig") == map_sig and st.session_state.get("vazoes_map_html"):
        # reutiliza HTML já pronto (super rápido)
        st_html(st.session_state["vazoes_map_html"], height=700, scrolling=False)
    else:
        # monta o mapa somente quando necessário
        geojson_trechos = geojson_data.get('geojson_trechos', {})
        geojson_acudes = geojson_data.get('geojson_acudes', {})
        geojson_sedes = geojson_data.get('geojson_sedes', {})
        geojson_c_gestoras = geojson_data.get('geojson_c_gestoras', {})
        geojson_poligno = geojson_data.get('geojson_poligno', {})
        geojson_bacia = geojson_data.get('geojson_bacia', {})
        geojson_pontos = geojson_data.get('geojson_pontos', {})

        if not df_mapa.empty:
            center = [df_mapa["lat"].mean(), df_mapa["lon"].mean()]
        else:
            center = [-5.2, -39.5]

        m = folium.Map(location=center, zoom_start=9, tiles=None)
        if mapa_tipo == "OpenStreetMap":
            folium.TileLayer(tiles="OpenStreetMap").add_to(m)
        else:
            folium.TileLayer(tiles=tile_urls[mapa_tipo], attr=tile_attr[mapa_tipo], name=mapa_tipo).add_to(m)

        Fullscreen(position="topleft").add_to(m)
        MiniMap(toggle_display=True, minimized=True).add_to(m)
        MousePosition(position="bottomleft", separator=" | ", prefix="Coords").add_to(m)
        MeasureControl(primary_length_unit="meters").add_to(m)

        if geojson_bacia:
            folium.GeoJson(
                geojson_bacia,
                name="Bacia do Banabuiu",
                tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]),
                style_function=lambda x: {"color": "darkblue", "weight": 2}
            ).add_to(m)
        if geojson_trechos:
            trechos_layer = folium.FeatureGroup(name="Trechos Perenizados", show=False)
            folium.GeoJson(
                geojson_trechos,
                tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Name:"]),
                style_function=lambda x: {"color": "darkblue", "weight": 1}
            ).add_to(trechos_layer)
            trechos_layer.add_to(m)
        if geojson_pontos:
            pontos_layer = folium.FeatureGroup(name="Pontos de Controle", show=False)
            for feature in geojson_pontos["features"]:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]
                nome_municipio = props.get("Name", "Sem nome")
                folium.Marker(
                    [coords[1], coords[0]],
                    icon=folium.CustomIcon("https://i.ibb.co/HfCcFWjb/marker.png", icon_size=(22, 22)),
                    tooltip=nome_municipio
                ).add_to(pontos_layer)
            pontos_layer.add_to(m)
        if geojson_acudes:
            acudes_layer = folium.FeatureGroup(name="Açudes Monitorados", show=False)
            folium.GeoJson(
                geojson_acudes,
                tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"]),
                style_function=lambda x: {"color": "darkgreen", "weight": 2}
            ).add_to(acudes_layer)
            acudes_layer.add_to(m)
        if geojson_sedes:
            sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=False)
            for feature in geojson_sedes["features"]:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]
                nome = props.get("NOME_MUNIC", "Sem nome")
                folium.Marker(
                    [coords[1], coords[0]],
                    icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png", icon_size=(22, 22)),
                    tooltip=nome
                ).add_to(sedes_layer)
            sedes_layer.add_to(m)
        if geojson_c_gestoras:
            gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
            for feature in geojson_c_gestoras["features"]:
                props = feature["properties"]
                coords = feature["geometry"]["coordinates"]
                nome_g = props.get("SISTEMAH3", "Sem nome")
                popup_info = f"""
            <div style='font-family: "Segoe UI", Arial, sans-serif; padding: 12px; background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); border-top: 4px solid #228B22; min-width: 200px;'>
                <div style='font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;'>{nome_g}</div>
                <div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Ano de Formação</div><div style='color: #2c3e50;'>{props.get("ANOFORMA1","N/A")}</div></div>
                <div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Sistema</div><div style='color: #2c3e50;'>{props.get("SISTEMAH3","N/A")}</div></div>
                <div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Município</div><div style='color: #228B22; font-weight: 500;'>{props.get("MUNICIPI6","N/A")}</div></div>
            </div>
            """
                folium.Marker(
                    [coords[1], coords[0]],
                    icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30, 30)),
                    tooltip=nome_g,
                    popup=folium.Popup(popup_info, max_width=300)
                ).add_to(gestoras_layer)
            gestoras_layer.add_to(m)
        if geojson_poligno:
            municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
            folium.GeoJson(
                geojson_poligno,
                tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]),
                style_function=lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1}
            ).add_to(municipios_layer)
            municipios_layer.add_to(m)

        cluster = MarkerCluster(name="Reservatórios (pinos)").add_to(m)
        for _, row in df_mapa.iterrows():
            val = pd.to_numeric(row.get("Vazao_Aloc", None), errors="coerce")
            val_conv, unit_suf = convert_vazao(pd.Series([val]), unidade_sel)
            val_num = val_conv.iloc[0] if not pd.isna(val_conv.iloc[0]) else None
            val_txt = f"{val_num:.3f} {unit_suf}" if val_num is not None else "—"
            data_txt = row["Data"].date() if pd.notna(row.get("Data", pd.NaT)) else "—"
            popup_info = f"""
        <div style='font-family: "Segoe UI", Arial, sans-serif; padding: 12px; background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border-left: 4px solid #228B22; min-width: 220px;'>
            <div style='font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 8px; border-bottom: 1px solid #dfe6e9; padding-bottom: 6px;'>
                {row['Reservatório Monitorado']}
            </div>
            <div style='margin-bottom: 4px;'><span style='display:inline-block;width:100px;font-weight:500;color:#7f8c8d;'>Data:</span><span style='color:#2c3e50;'>{data_txt}</span></div>
            <div style='margin-bottom: 4px;'><span style='display:inline-block;width:100px;font-weight:500;color:#7f8c8d;'>Vazão:</span><span style='color:#228B22;font-weight:600;'>{val_txt}</span></div>
            <div style='margin-top: 8px; font-size: 12px; color: #7f8c8d; text-align: right;'>Sistema de Monitoramento</div>
        </div>
        """
            folium.Marker(
                [row["lat"], row["lon"]],
                popup=folium.Popup(popup_info, max_width=300),
                icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30)),
                tooltip=row["Reservatório Monitorado"]
            ).add_to(cluster)

        folium.LayerControl(collapsed=True, position="topright").add_to(m)

        # renderiza e guarda HTML no estado da sessão
        html_map = m.get_root().render()
        st_html(html_map, height=700, scrolling=False)
        st.session_state["vazoes_map_sig"] = map_sig
        st.session_state["vazoes_map_html"] = html_map

    # 🔻 separador enxuto
    st.markdown("---", unsafe_allow_html=True)

    # =====================================================================
    # 📊 Volume Liberado por reservatório
    # =====================================================================
    st.subheader("📊 Volume liberado por reservatório")

    cols_necessarias = {"Reservatório Monitorado", "Data", "Vazão Operada"}
    tem_cols = cols_necessarias.issubset(set(df_filtrado.columns))
    tem_res = not df_filtrado.empty and df_filtrado["Reservatório Monitorado"].nunique() > 0

    if tem_cols and tem_res:
        df_box = df_filtrado.copy()
        df_box["Data"] = pd.to_datetime(df_box["Data"], errors="coerce")
        df_box["Vazão Operada"] = pd.to_numeric(df_box["Vazão Operada"], errors="coerce").fillna(0)

        volumes = []
        fim_periodo_global = df_box["Data"].max()

        for reservatorio in df_box["Reservatório Monitorado"].dropna().unique():
            df_res = (
                df_box[df_box["Reservatório Monitorado"] == reservatorio]
                .dropna(subset=["Data"])
                .sort_values("Data")
                .copy()
            )
            if df_res.empty:
                continue

            df_res["dias_entre_medicoes"] = df_res["Data"].diff().dt.days.fillna(0)
            ultima_data_res = df_res["Data"].iloc[-1]
            fim_periodo = fim_periodo_global if pd.notna(fim_periodo_global) else ultima_data_res
            df_res.loc[df_res.index[-1], "dias_entre_medicoes"] = max((fim_periodo - ultima_data_res).days + 1, 0)

            segundos_por_dia = 86400
            vazao_m3s = df_res["Vazão Operada"] / 1000.0
            df_res["volume_periodo_m3"] = vazao_m3s * segundos_por_dia * df_res["dias_entre_medicoes"]

            volume_total_m3 = float(df_res["volume_periodo_m3"].sum())
            volumes.append({"Reservatório Monitorado": reservatorio, "Volume Acumulado (m³)": volume_total_m3})

        df_volumes = pd.DataFrame(volumes)

        def fmt_m3(x):
            if pd.isna(x):
                return "-"
            if x >= 1_000_000:
                return f"{x/1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mi m³"
            elif x >= 1_000:
                return f"{x/1e3:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mil m³"
            else:
                return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m³"

        if not df_volumes.empty:
            df_volumes["Volume Formatado"] = df_volumes["Volume Acumulado (m³)"].apply(fmt_m3)
            df_volumes["Volume Eixo Y"] = df_volumes["Volume Acumulado (m³)"] / 1e6
            df_volumes = df_volumes.sort_values("Volume Eixo Y", ascending=False)

            y_max = float(df_volumes["Volume Eixo Y"].max()) if not df_volumes.empty else 1.0
            y_max = y_max * 1.2 if y_max > 0 else 1.0
            y_title = "Volume liberado em milhões de m³"

            base = alt.Chart(df_volumes).encode(
                x=alt.X("Reservatório Monitorado:N", title="Reservatório", sort="-y")
            ).properties(title="Volume total liberado na Operação", height=400).interactive()

            bars = base.mark_bar(color="steelblue").encode(
                y=alt.Y("Volume Eixo Y:Q", title=y_title, scale=alt.Scale(domain=[0, y_max])),
                tooltip=[alt.Tooltip("Reservatório Monitorado:N", title="Reservatório"),
                         alt.Tooltip("Volume Formatado:N", title="Volume total")]
            )
            text = base.mark_text(align="center", baseline="bottom", dy=-5, fontSize=12).encode(
                y=alt.Y("Volume Eixo Y:Q", stack=None), text="Volume Formatado:N"
            )
            chart = alt.layer(bars, text).resolve_scale(y="independent")
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Sem dados suficientes para montar o gráfico.")
    else:
        st.info("Sem dados suficientes para o gráfico de volume.")

    # =====================================================================
    # 🏞️ Média da Vazão Operada por reservatório — CORRIGIDO
    # =====================================================================
    st.subheader("🏞️ Média da Vazão Operada por Reservatório")

    if not df_filtrado.empty and "Reservatório Monitorado" in df_filtrado.columns:
        dfm = df_filtrado.copy()
        dfm["Data"] = pd.to_datetime(dfm["Data"], errors="coerce")
        dfm = dfm.dropna(subset=["Data", "Reservatório Monitorado"])

        data_maxima_dataset = dfm["Data"].max()

        df_diario = (
            dfm.sort_values("Data")
               .groupby(["Reservatório Monitorado", "Data"], as_index=False)
               .last()
        )

        meses_map = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
                     7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}
        df_diario["Ano"] = df_diario["Data"].dt.year
        df_diario["Mês"] = df_diario["Data"].dt.month.map(meses_map)
        df_diario["MêsRef"] = df_diario["Mês"] + "/" + df_diario["Ano"].astype(str)

        def calcular_media_ponderada_mensal(grupo):
            grupo = grupo.sort_values('Data').copy()
            grupo['dias_ativos'] = grupo['Data'].diff().dt.days.fillna(0)
            if not grupo.empty:
                ultima_data = grupo['Data'].iloc[-1]
                if ultima_data.month == data_maxima_dataset.month and ultima_data.year == data_maxima_dataset.year:
                    dias_restantes = (data_maxima_dataset - ultima_data).days + 1
                else:
                    fim_mes = ultima_data + pd.offsets.MonthEnd(0)
                    dias_restantes = (fim_mes - ultima_data).days + 1
                grupo.loc[grupo.index[-1], 'dias_ativos'] = dias_restantes
            vazao_total_ponderada = (grupo['Vazão Operada'] * grupo['dias_ativos']).sum()
            dias_totais = grupo['dias_ativos'].sum()
            return vazao_total_ponderada / dias_totais if dias_totais > 0 else 0

        try:
            media_mensal = (
                df_diario.groupby(["Reservatório Monitorado", "MêsRef"], dropna=True)
                         .apply(calcular_media_ponderada_mensal)
                         .reset_index(name='Vazão Operada')
            )
            if not media_mensal.empty:
                y_vals_media, unit_suffix_media = convert_vazao(media_mensal["Vazão Operada"], unidade_sel)
                media_mensal["Vazão (conv)"] = y_vals_media

                ordem_res = (
                    media_mensal.groupby("Reservatório Monitorado")["Vazão (conv)"]
                                .sum().sort_values(ascending=True).index.tolist()
                )
                inv_meses = {v: k for k, v in meses_map.items()}
                media_mensal["ord"] = media_mensal["MêsRef"].apply(
                    lambda s: int(s.split("/")[1]) * 100 + inv_meses[s.split("/")[0]]
                )
                media_mensal = media_mensal.sort_values("ord")
                ordem_mesref = media_mensal["MêsRef"].unique().tolist()

                def format_val_dot(v: float, unit: str) -> str:
                    if pd.isna(v): return "- " + unit
                    if abs(v) < 1000: s = f"{v:.3f}"
                    else: s = f"{v:,.2f}".replace(",", ".")
                    return f"{s} {unit}"

                media_mensal["Valor Formatado"] = media_mensal["Vazão (conv)"].apply(lambda v: format_val_dot(v, unit_suffix_media))

                fig_media = px.bar(
                    media_mensal,
                    y="Reservatório Monitorado",
                    x="Vazão (conv)",
                    color="MêsRef",
                    orientation="h",
                    text="Valor Formatado",
                    category_orders={"Reservatório Monitorado": ordem_res, "MêsRef": ordem_mesref},
                    labels={"Reservatório Monitorado": "Reservatório", "Vazão (conv)": f"Média ({unit_suffix_media})", "MêsRef": "Mês/Ano"},
                    barmode="stack",
                    hover_data={"Vazão (conv)": False, "Valor Formatado": True}
                )
                fig_media.update_traces(textposition="inside", insidetextanchor="middle", cliponaxis=False)
                fig_media.update_layout(bargap=0.2, legend_title_text="Mês/Ano",
                                        xaxis_title=f"Média ({unit_suffix_media})", yaxis_title="Reservatório",
                                        height=500)
                st.plotly_chart(fig_media, use_container_width=True, config={"displaylogo": False}, key="plotly_vazao_media_res_mes_alinhado")
            else:
                st.info("Sem dados para calcular a média.")
        except Exception as e:
            st.error(f"Erro ao calcular média: {str(e)}")
    else:
        st.info("Sem dados para a média.")

    # ------------- Tabela -------------
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True, key="dataframe_vazao")



