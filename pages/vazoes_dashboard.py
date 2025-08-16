import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MiniMap, MousePosition, MeasureControl, MarkerCluster
import altair as alt
from utils.common import carregar_dados_vazoes, convert_vazao, load_geojson_data

def render_vazoes_dashboard(): # Certifique-se de que o nome da função é este
    geojson_data = load_geojson_data()
    geojson_trechos = geojson_data.get('geojson_trechos', {})
    geojson_acudes = geojson_data.get('geojson_acudes', {})
    geojson_sedes = geojson_data.get('geojson_sedes', {})
    geojson_c_gestoras = geojson_data.get('geojson_c_gestoras', {})
    geojson_poligno = geojson_data.get('geojson_poligno', {})
    geojson_bacia = geojson_data.get('geojson_bacia', {})
    geojson_pontos = geojson_data.get('geojson_pontos', {})

    df = carregar_dados_vazoes()
    
    # === CONTEÚDO DA ABA 1 (🏠 Painel de Vazões) ===
    cA1, cA2, cA3 = st.columns([1, 1, 1])
    with cA1:
        if st.button("🔄 Atualizar agora"):
            carregar_dados_vazoes.clear()
            df = carregar_dados_vazoes()
            st.success("Atualizado.")

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

    # ------------- Filtros -------------
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

    # ------------- Filtragem -------------
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

    # ------------- KPIs -------------
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
    registros_count = len(df_filtrado)
    ultima_data = df_filtrado["Data"].max().strftime("%d/%m/%Y") if not df_filtrado.empty and pd.notna(df_filtrado["Data"].max()) else "—"
    unidade_show = "m³/s" if unidade_sel == "m³/s" else "L/s"
    st.markdown(
        f"""
        <div class="kpi-container">
            <div class="kpi-card"><div class="kpi-label">Reservatórios</div><div class="kpi-value">{reservatorios_count}</div></div>
            <div class="kpi-card"><div class="kpi-label">Registros</div><div class="kpi-value">{registros_count}</div></div>
            <div class="kpi-card"><div class="kpi-label">Última Data</div><div class="kpi-value">{ultima_data}</div></div>
            <div class="kpi-card"><div class="kpi-label">Unidade</div><div class="kpi-value">{unidade_show}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ======================GRÁFICO SÉRIE TEMPORAL
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    fig = go.Figure()
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#17becf", "#e377c2"]
    reservatorios = df_filtrado["Reservatório Monitorado"].dropna().unique()

    for i, r in enumerate(reservatorios):
        dfr = df_filtrado[df_filtrado["Reservatório Monitorado"] == r].sort_values("Data").groupby("Data", as_index=False).last()
        y_vals, unit_suffix = convert_vazao(dfr["Vazão Operada"], unidade_sel)
        fig.add_trace(go.Scatter(x=dfr["Data"], y=y_vals, mode="lines+markers", name=r, line=dict(shape="hv", width=2, color=cores[i % len(cores)]), marker=dict(size=5), hovertemplate=f"<b>{r}</b><br>Data: %{{x|%d/%m/%Y}}<br>Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"))
        if len(reservatorios) == 1 and len(dfr) > 1:
            dfr["dias_ativos"] = dfr["Data"].diff().dt.days.fillna(0)
            if not dfr.empty:
              dfr.loc[dfr.index[-1], "dias_ativos"] = (df_filtrado["Data"].max() - dfr["Data"].iloc[-1]).days + 1
              media_pond = (dfr["Vazão Operada"] * dfr["dias_ativos"]).sum() / dfr["dias_ativos"].sum()
              media_pond_conv, _ = convert_vazao(pd.Series([media_pond]), unidade_sel)
              fig.add_hline(y=media_pond_conv.iloc[0], line_dash="dash", line_width=2, line_color="red", annotation_text=f"Média Ponderada: {media_pond_conv.iloc[0]:.2f} {unit_suffix}", annotation_position="top right")

    # Configurações de layout atualizadas
    fig.update_layout(xaxis_title="Data", yaxis_title=f"Vazão Operada ({'m³/s' if unidade_sel=='m³/s' else 'L/s'})", legend_title="Reservatório", template="plotly_white", margin=dict(l=40, r=20, t=10, b=40), height=600, legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5), xaxis=dict(rangeslider=dict(visible=True, thickness=0.1, bgcolor="#f5f5f5", bordercolor="#cccccc", borderwidth=1)))
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})

    # ------------- Abas de gráficos agregados -------------
    gtab1, gtab2 = st.tabs(["📊 Média mensal", "📦 Distribuição (boxplot)"])
    with gtab1:
        if not df_filtrado.empty:
            dmm = df_filtrado.assign(mes_num=df_filtrado["Data"].dt.to_period("M").astype(str)).groupby(["Reservatório Monitorado", "mes_num"], as_index=False)["Vazão Operada"].mean()
            yconv, sufx = convert_vazao(dmm["Vazão Operada"], unidade_sel)
            dmm["Vazão (conv)"] = yconv
            figm = px.bar(dmm, x="mes_num", y="Vazão (conv)", color="Reservatório Monitorado", labels={"mes_num": "Mês", "Vazão (conv)": f"Média ({sufx})"}, barmode="group")
            st.plotly_chart(figm, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sem dados para média mensal.")

    # ======================GRÁFICO DE VOLUME
    with gtab2:
      if not df_filtrado.empty and df_filtrado["Reservatório Monitorado"].nunique() > 0:
        df_box = df_filtrado.copy()
        volumes = []
        for reservatorio in df_box["Reservatório Monitorado"].unique():
            df_res = df_box[df_box["Reservatório Monitorado"] == reservatorio].sort_values("Data").copy()
            df_res["dias_entre_medicoes"] = df_res["Data"].diff().dt.days.fillna(0)
            ultima_data_res = df_res["Data"].iloc[-1]
            fim_periodo = df_box["Data"].max() if pd.notna(df_box["Data"].max()) else ultima_data_res
            df_res.loc[df_res.index[-1], "dias_entre_medicoes"] = (fim_periodo - ultima_data_res).days + 1
            vazao_m3s = df_res["Vazão Operada"] / 1000.0
            segundos_por_dia = 86400
            df_res["volume_periodo_m3"] = vazao_m3s * segundos_por_dia * df_res["dias_entre_medicoes"]
            volume_total_m3 = df_res["volume_periodo_m3"].sum()
            volumes.append({"Reservatório Monitorado": reservatorio, "Volume Acumulado (m³)": volume_total_m3})
        df_volumes = pd.DataFrame(volumes)

        def fmt_m3(x):
            if pd.isna(x): return "—"
            if x >= 1_000_000: return f"{x/1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " milhões m³"
            elif x >= 1_000: return f"{x/1e3:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mil m³"
            else: return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m³"
        df_volumes["Volume Formatado"] = df_volumes["Volume Acumulado (m³)"].apply(fmt_m3)
        df_volumes["Volume Eixo Y"] = df_volumes["Volume Acumulado (m³)"] / 1e6
        y_max = float(df_volumes["Volume Eixo Y"].max()) if not df_volumes.empty else 0.0
        y_max = y_max * 1.1 if y_max > 0 else 1.0
        y_title = "Volume Acumulado (milhões m³)"
        chart = alt.Chart(df_volumes).mark_text(align="center", baseline="bottom", dy=10).encode(x=alt.X("Reservatório Monitorado:N", title="Reservatório"), y=alt.Y("Volume Eixo Y:Q", title=y_title, scale=alt.Scale(domain=[0, y_max])), text=alt.value("💧"), size=alt.Size("Volume Eixo Y:Q", scale=alt.Scale(range=[10, 300]), legend=None), color=alt.value("steelblue"), tooltip=[alt.Tooltip("Reservatório Monitorado:N", title="Reservatório"), alt.Tooltip("Volume Formatado:N", title="Volume Total")]).properties(title="Volume Acumulado por Reservatório", height=600).interactive()
        st.altair_chart(chart, use_container_width=True)
      else:
          st.info("Sem dados suficientes para o gráfico de volume.")

    # ------------- Mapa com camadas -------------
    st.subheader("🗺️ Mapa dos Reservatórios com Camadas")
    df_mapa = df_filtrado.copy()
    coord_col = "Coordenadas" if "Coordenadas" in df_mapa.columns else ("Coordendas" if "Coordendas" in df_mapa.columns else None)
    if coord_col:
        try:
            df_mapa[["lat", "lon"]] = df_mapa[coord_col].str.split(",", expand=True).astype(float)
        except Exception:
            df_mapa[["lat", "lon"]] = df_mapa[coord_col].str.replace(" ", "").str.split(",", expand=True).astype(float)
    df_mapa = df_mapa.dropna(subset=["lat", "lon"]).drop_duplicates(subset=["Reservatório Monitorado"])

    with st.expander("☰ Estilo do Mapa", expanded=False):
        mapa_tipo = st.selectbox("Selecione o estilo:", ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"], index=0, key="map_style_selector", label_visibility="collapsed")

    tile_urls = {"OpenStreetMap": None, "Stamen Terrain": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png", "Stamen Toner": "https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png", "CartoDB positron": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", "CartoDB dark_matter": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", "Esri Satellite": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"}
    tile_attr = {"OpenStreetMap": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>', "Stamen Terrain": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under CC BY 3.0. Data by OpenStreetMap, under ODbL.', "Stamen Toner": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under CC BY 3.0. Data by OpenStreetMap, under ODbL.', "CartoDB positron": '&copy; <a href="https://carto.com/attributions">CARTO</a>', "CartoDB dark_matter": '&copy; <a href="https://carto.com/attributions">CARTO</a>', "Esri Satellite": "Tiles &copy; Esri — Sources: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, GIS User Community"}

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

        folium.GeoJson(geojson_bacia, name="Bacia do Banabuiu", tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]), style_function=lambda x: {"color": "darkblue", "weight": 2}).add_to(m)

        trechos_layer = folium.FeatureGroup(name="Trechos Perenizados", show=False)
        folium.GeoJson(geojson_trechos, tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Name:"]), style_function=lambda x: {"color": "darkblue", "weight": 1}).add_to(trechos_layer)
        trechos_layer.add_to(m)

        pontos_layer = folium.FeatureGroup(name="Pontos de Controle", show=False)
        for feature in geojson_pontos["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            nome_municipio = props.get("Name", "Sem nome")
            folium.Marker([coords[1], coords[0]], icon=folium.CustomIcon("https://i.ibb.co/HfCcFWjb/marker.png", icon_size=(22, 22)), tooltip=nome_municipio).add_to(pontos_layer)
        pontos_layer.add_to(m)

        acudes_layer = folium.FeatureGroup(name="Açudes Monitorados", show=False)
        folium.GeoJson(geojson_acudes, tooltip=folium.GeoJsonTooltip(fields=["Name"], aliases=["Açude:"]), style_function=lambda x: {"color": "darkgreen", "weight": 2}).add_to(acudes_layer)
        acudes_layer.add_to(m)

        sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=False)
        for feature in geojson_sedes["features"]:
            props = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            nome = props.get("NOME_MUNIC", "Sem nome")
            folium.Marker([coords[1], coords[0]], icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/854/854878.png", icon_size=(22, 22)), tooltip=nome).add_to(sedes_layer)
        sedes_layer.add_to(m)

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
            folium.Marker([coords[1], coords[0]], icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30, 30)), tooltip=nome_g, popup=folium.Popup(popup_info, max_width=300)).add_to(gestoras_layer)
        gestoras_layer.add_to(m)

        municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
        folium.GeoJson(geojson_poligno, tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]), style_function=lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1}).add_to(municipios_layer)
        municipios_layer.add_to(m)

        cluster = MarkerCluster(name="Reservatórios (pinos)").add_to(m)
        for _, row in df_mapa.iterrows():
            try:
                val = float(row.get("Vazao_Aloc", float("nan")))
            except Exception:
                val = float("nan")
            val_conv, unit_suf = convert_vazao(pd.Series([val]), unidade_sel)
            val_num = val_conv.iloc[0] if not pd.isna(val_conv.iloc[0]) else None
            val_txt = f"{val_num:.3f} {unit_suf}" if val_num is not None else "—"
            data_txt = row["Data"].date() if pd.notna(row["Data"]) else "—"
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
            folium.Marker([row["lat"], row["lon"]], popup=folium.Popup(popup_info, max_width=300), icon=folium.CustomIcon("https://i.ibb.co/kvvL870/hydro-dam.png", icon_size=(30, 30)), tooltip=row["Reservatório Monitorado"]).add_to(cluster)

        folium.LayerControl(collapsed=True, position="topright").add_to(m)
        folium_static(m, width=1200)
    else:
        st.info("Nenhum ponto com coordenadas disponíveis para plotar no mapa.")

    # ------------- Média por reservatório -------------
    st.subheader("🏞️ Média da Vazão Operada por Reservatório")
    if not df_filtrado.empty:
        media_vazao = df_filtrado.groupby("Reservatório Monitorado")["Vazão Operada"].mean().reset_index()
        media_conv, unit_bar = convert_vazao(media_vazao["Vazão Operada"], unidade_sel)
        media_vazao["Vazão (conv)"] = media_conv
        st.plotly_chart(px.bar(media_vazao, x="Reservatório Monitorado", y="Vazão (conv)", text_auto=".2s", labels={"Vazão (conv)": f"Média ({unit_bar})"}), use_container_width=True, config={"displaylogo": False})
    else:
        st.info("Sem dados para a média.")

    # ------------- Tabela -------------
    st.subheader("📋 Tabela Detalhada")

    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True)
