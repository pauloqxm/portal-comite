import streamlit as st
import pandas as pd
import folium
import json
import base64
from datetime import datetime
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MousePosition
from utils.common import load_reservatorios_data, load_geojson_data

def render_acudes():
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
    """,
        unsafe_allow_html=True,
    )

    df_full = load_reservatorios_data()
    if df_full.empty:
        st.warning("Não foi possível carregar os dados dos reservatórios.")
        return

    # --- Filtros ---
    with st.expander("🔍 Filtros", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            min_date = df_full["Data de Coleta"].min().date()
            max_date = df_full["Data de Coleta"].max().date()
            date_range = st.date_input(
                "Período:", value=(max_date, max_date),
                min_value=min_date, max_value=max_date
            )
        with col2:
            reservatorios = sorted(df_full["Reservatório"].dropna().astype(str).unique())
            reservatorio_filtro = st.multiselect(
                "Reservatório(s):", options=reservatorios,
                default=reservatorios, placeholder="Selecione..."
            )
        with col3:
            municipios = ["Todos"] + sorted(df_full["Município"].dropna().astype(str).unique().tolist())
            municipio_filtro = st.selectbox("Município:", options=municipios, index=0)

        perc_series = df_full["Percentual"].dropna()
        min_perc = float(perc_series.min()) if not perc_series.empty else 0.0
        max_perc = float(perc_series.max()) if not perc_series.empty else 100.0
        perc_range = st.slider(
            "Percentual de Volume (%):",
            min_value=float(min_perc), max_value=float(max_perc),
            value=(float(min_perc), float(max_perc)), step=0.1,
        )

    # Verifica se os filtros são válidos antes de continuar
    if len(date_range) != 2:
        st.warning("Selecione um intervalo de datas válido para prosseguir.")
        return # Para a execução da função se o filtro for inválido

    start_date, end_date = date_range

    # --- Aplicar filtros ---
    if not reservatorio_filtro: reservatorio_filtro = reservatorios
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

    # ===================== Mapa Interativo =====================
    st.subheader("🌍 Mapa dos Açudes")
    with st.expander("Configurações do Mapa", expanded=False):
        tile_option = st.selectbox(
            "Estilo do Mapa:",
            ["OpenStreetMap", "Stamen Terrain", "Stamen Toner", "CartoDB positron", "CartoDB dark_matter", "Esri Satellite"],
            index=0
        )
    geojson_data = load_geojson_data()
    geojson_bacia = geojson_data.get('geojson_bacia', {})
    geojson_c_gestoras = geojson_data.get('geojson_c_gestoras', {})
    geojson_poligno = geojson_data.get('geojson_poligno', {})

    tile_config = {
        "OpenStreetMap": {"tiles": "OpenStreetMap", "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'},
        "Stamen Terrain": {"tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png", "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
        "CartoDB positron": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png", "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
        "CartoDB dark_matter": {"tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png", "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>'},
        "Esri Satellite": {"tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", "attr": "Tiles &copy; Esri — Source: Esri"},
        "Stamen Toner": {"tiles": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png", "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>'},
    }

    def get_marker_color(percentual):
        if pd.isna(percentual) or 0 <= percentual <= 10: return "#808080"
        if 10.1 <= percentual <= 30: return "#FF0000"
        if 30.1 <= percentual <= 50: return "#FFFF00"
        if 50.1 <= percentual <= 70: return "#008000"
        if 70.1 <= percentual <= 100: return "#0000FF"
        return "#800080"

    def create_svg_icon(color, size=15):
        svg = (
            f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" '
            f'xmlns="http://www.w3.org/2000/svg">'
            f'<polygon points="50,0 100,100 0,100" fill="{color}" '
            f'stroke="#000000" stroke-width="5"/></svg>'
        )
        svg_b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
        return f"data:image/svg+xml;base64,{svg_b64}"

    if not df_filtrado.empty:
        mapa_center = [df_mapa["Latitude"].mean(), df_mapa["Longitude"].mean()]
        m = folium.Map(location=mapa_center, zoom_start=9, tiles=None)
        folium.TileLayer(tiles=tile_config[tile_option]["tiles"], attr=tile_config[tile_option]["attr"], name=tile_option).add_to(m)
        if geojson_bacia:
            folium.GeoJson(geojson_bacia, name="Bacia do Banabuiú", style_function=lambda x: {"color": "blue", "weight": 2, "fillOpacity": 0.1}, tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"])).add_to(m)
        
        gestoras_layer = folium.FeatureGroup(name="Comissões Gestoras", show=False)
        if geojson_c_gestoras:
            for feature in geojson_c_gestoras["features"]:
                props = feature["properties"]
                lon, lat = feature["geometry"]["coordinates"]
                nome_g = props.get("SISTEMAH3", "Sem nome")
                popup_info = (f"<div style='font-family: \"Segoe UI\", Arial, sans-serif; padding: 12px; "f"background: white; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); "f"border-top: 4px solid #228B22; min-width: 200px;'>"f"<div style='font-size: 16px; font-weight: 600; color: #2c3e50; margin-bottom: 8px;'>{nome_g}</div>"f"<div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Ano de Formação</div>"f"<div style='color: #2c3e50;'>{props.get('ANOFORMA1','N/A')}</div></div>"f"<div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Sistema</div>"f"<div style='color: #2c3e50;'>{props.get('SISTEMAH3','N/A')}</div></div>"f"<div style='margin: 6px 0;'><div style='font-weight: 500; color: #7f8c8d;'>Município</div>"f"<div style='color: #228B22; font-weight: 500;'>{props.get('MUNICIPI6','N/A')}</div></div>"f"</div>")
                folium.Marker([lat, lon], icon=folium.CustomIcon("https://cdn-icons-png.flaticon.com/512/4144/4144517.png", icon_size=(30, 30)), tooltip=nome_g, popup=folium.Popup(popup_info, max_width=300)).add_to(gestoras_layer)
            gestoras_layer.add_to(m)

        municipios_layer = folium.FeatureGroup(name="Polígonos Municipais", show=False)
        if geojson_poligno:
            folium.GeoJson(geojson_poligno, tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Município:"]), style_function=lambda x: {"fillOpacity": 0, "color": "blue", "weight": 1}).add_to(municipios_layer)
            municipios_layer.add_to(m)

        for _, row in df_mapa.iterrows():
            percentual_val = float(row.get("Percentual", "nan"))
            percentual_str = f"{percentual_val:.2f}%" if not pd.isna(percentual_val) else "N/A"
            volume_str = f"{float(row.get('Volume', 'nan')):,.2f} hm³".replace(",", "X").replace(".", ",").replace("X", ".") if not pd.isna(row.get('Volume', None)) else "N/A"
            cota_sangria_str = f"{float(row.get('Cota Sangria', 'nan')):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if not pd.isna(row.get('Cota Sangria', None)) else "N/A"
            ultima_data = df_filtrado[df_filtrado["Reservatório"] == row["Reservatório"]]["Data de Coleta"].max()
            data_formatada = ultima_data.strftime("%d/%m/%Y") if pd.notnull(ultima_data) else "N/A"
            icon_color = get_marker_color(percentual_val)
            popup_content = (
                '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">'
                f"<div style='font-family: \"Segoe UI\", sans-serif; width: 280px; background: linear-gradient(to bottom, #f9f9f9, #ffffff); border-radius: 8px; border-left: 5px solid {icon_color}; padding: 12px; box-shadow: 0 3px 10px rgba(0,0,0,0.2);'>"
                f"<div style='color: #006400; font-size: 18px; font-weight: 700; margin-bottom: 10px; border-bottom: 1px solid #e0e0e0; padding-bottom: 8px;'>"
                f"<i class='fas fa-water' style='margin-right: 8px;'></i>{row['Reservatório']}</div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-calendar-alt' style='margin-right: 5px;'></i>Data:</span>"
                f"<span style='color: #333;'>{data_formatada}</span></div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-city' style='margin-right: 5px;'></i>Município:</span>"
                f"<span style='color: #333;'>{row.get('Município', 'N/A')}</span></div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-chart-bar' style='margin-right: 5px;'></i>Volume:</span>"
                f"<span style='color: #1a5276; font-weight: 500;'>{volume_str}</span></div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-percentage' style='margin-right: 5px;'></i>Percentual:</span>"
                f"<span style='color: #27ae60; font-weight: 600;'>{percentual_str}</span></div>"
                f"<div style='margin-bottom: 8px;'><span style='display: inline-block; width: 100px; font-weight: 600; color: #555;'><i class='fas fa-ruler' style='margin-right: 5px;'></i>Cota Sangria:</span>"
                f"<span style='color: #7d3c98; font-weight: 500;'>{cota_sangria_str} m</span></div>"
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

    # ===================== Tabela Interativa =====================
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.write("")
    st.markdown("---")    
    st.subheader("📊 Dados Detalhados Interativos")
    if not df_filtrado.empty:
        faixas_percentual = [(0, 10, "#808080", "Muito Crítica"), (10.1, 30, "#FF0000", "Crítica"), (30.1, 50, "#FFFF00", "Alerta"), (50.1, 70, "#008000", "Confortável"), (70.1, 100, "#0000FF", "Muito Confortável"), (100.1, float("inf"), "#800080", "Vertendo")]
        def get_status_color(percentual):
            if pd.isna(percentual): return "#FFFFFF", "N/A", "#000000"
            for min_val, max_val, color, status in faixas_percentual:
                if min_val <= percentual <= max_val:
                    text_color = "#FFFFFF" if color in ["#808080", "#FF0000", "#0000FF", "#800080"] else "#000000"
                    return color, status, text_color
            return "#FFFFFF", "Não classificado", "#000000"

        df_filtrado[["Cor", "Status", "TextColor"]] = df_filtrado["Percentual"].apply(lambda x: pd.Series(get_status_color(x)))
        df_filtrado["Sangria"] = df_filtrado["Cota Sangria"] - df_filtrado["Nivel"]
        colunas_exibir = ["Data de Coleta", "Reservatório", "Município", "Volume", "Percentual", "Status", "Cota Sangria", "Nivel", "Sangria"]
        def colorize_row(row):
            idx = row.name
            bg_color = df_filtrado.loc[idx, "Cor"]
            text_color = df_filtrado.loc[idx, "TextColor"]
            return [f"background-color: {bg_color}; color: {text_color}; font-weight: bold;" for _ in row]

        styled_df = df_filtrado[colunas_exibir].copy().style.apply(colorize_row, axis=1)

        column_config = {"Percentual": st.column_config.ProgressColumn("Percentual", format="%.1f%%", min_value=0, max_value=100), "Volume": st.column_config.NumberColumn("Volume", format="%.2f hm³"), "Cota Sangria": st.column_config.NumberColumn("Cota Sangria", format="%.2f m"), "Nivel": st.column_config.NumberColumn("Nível", format="%.2f m"), "Sangria": st.column_config.NumberColumn("Margem de Sangria", format="%.2f m"), "Status": st.column_config.TextColumn("Status"), "Data de Coleta": st.column_config.DateColumn("Data de Coleta", format="DD/MM/YYYY")}
        st.dataframe(styled_df, column_config=column_config, use_container_width=True, hide_index=True, height=600, column_order=colunas_exibir)

        st.markdown(
            """
        <div style="margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; border: 1px solid #ddd;">
            <h4 style="margin-bottom: 12px; color: #333; font-size: 16px;">Legenda de Status:</h4>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
        """
            + "\n".join([f"""<div style="display: flex; align-items: center; padding: 4px;">
            <div style="width: 24px; height: 24px; background: {color}; margin-right: 10px; border: 1px solid #ccc; border-radius: 4px;"></div>
            <span style="font-size: 14px;">{status} ({'≥' if min_val == 100.1 else ''}{min_val}-{'' if max_val == float('inf') else max_val}%)</span>
        </div>""" for min_val, max_val, color, status in faixas_percentual])
            + "</div></div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.subheader("📈 Volume dos Reservatórios ao Longo do Tempo")
        df_reservatorio = df_filtrado[df_filtrado["Reservatório"].isin(reservatorio_filtro)].sort_values("Data de Coleta")
        if not df_reservatorio.empty:
            df_reservatorio["Data de Coleta"] = df_reservatorio["Data de Coleta"].dt.date
            df_plot = df_reservatorio.pivot_table(index="Data de Coleta", columns="Reservatório", values="Volume", aggfunc="mean")
            st.line_chart(df_plot)
        else:
            st.warning("Não há dados de volume para o(s) reservatório(s) selecionado(s) no período.")
        st.markdown("---")
        with st.expander("📥 Opções de Download", expanded=False):
            st.download_button(label="Baixar dados completos (CSV)", data=df_filtrado.drop(columns=["Cor", "Status", "TextColor"]).to_csv(index=False, encoding="utf-8-sig", sep=";"), file_name=f"reservatorios_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
    else:
        st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.", icon="⚠️")



