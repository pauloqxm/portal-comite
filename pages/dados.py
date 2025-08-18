
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
import json
import unicodedata
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MousePosition
from utils.common import load_geojson_data

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

# ========= HELPERS DE NORMALIZAÇÃO/CANONIZAÇÃO =========
  def _normalize_txt(s: str) -> str:
      if s is None:
          return ""
      s = str(s).strip()
      s = unicodedata.normalize("NFKD", s)
      s = "".join(ch for ch in s if not unicodedata.combining(ch))  # remove acentos
      s = " ".join(s.split())  # colapsa espaços múltiplos
      return s.lower()

  ALIAS_TO_CANON = {
      # Alta
      "criticidade alta": "Criticidade Alta",
      "alta": "Criticidade Alta",
      # Média
      "criticidade media": "Criticidade Média",
      "media": "Criticidade Média",
      # Baixa
      "criticidade baixa": "Criticidade Baixa",
      "baixa": "Criticidade Baixa",
      # Fora de Criticidade (inclui 'Normal')
      "fora de criticidade": "Fora de Criticidade",
      "fora criticidade": "Fora de Criticidade",
      "fora da criticidade": "Fora de Criticidade",
      "normal": "Fora de Criticidade",
      # Sem classificação / nulos
      "sem classificacao": "Sem classificação",
      "sem classificacao.": "Sem classificação",
      "sem class": "Sem classificação",
      "na": "Sem classificação",
      "": "Sem classificação",
  }

  def canon_classificacao(value: str) -> str:
      key = _normalize_txt(value)
      # tolera ponto final etc.
      return ALIAS_TO_CANON.get(key) or ALIAS_TO_CANON.get(key.replace(".", ""), None) or "Sem classificação"

  # ========= APLIQUE A CANONIZAÇÃO NO DF (uma vez) =========
  if "Classificação (canon)" not in df.columns:
      df["Classificação (canon)"] = df["Classificação"].apply(canon_classificacao)

  # ========= UI: FILTROS =========
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
              # opções canônicas fixas
              opcoes_classificacao = [
                  "Criticidade Alta",
                  "Criticidade Média",
                  "Criticidade Baixa",
                  "Fora de Criticidade",
                  "Sem classificação",
              ]
              classificacao_sel = st.multiselect(
                  "Classificação",
                  options=opcoes_classificacao,
                  default=opcoes_classificacao,
              )
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
                      format="DD/MM/YYYY",
                  )
              else:
                  periodo = None
          st.markdown("</div>", unsafe_allow_html=True)
      st.markdown("</div>", unsafe_allow_html=True)

  # ========= APLICAÇÃO DOS FILTROS (vistas df_filtrado e dff) =========
  if municipios_sel:
      df_filtrado = df[df["Município"].isin(municipios_sel)]
  else:
      df_filtrado = df.copy()

  if acudes_sel:
      df_filtrado = df_filtrado[df_filtrado["Açude"].isin(acudes_sel)]

  if classificacao_sel:
      df_filtrado = df_filtrado[df_filtrado["Classificação (canon)"].isin(classificacao_sel)]

  if periodo and len(periodo) == 2:
      data_inicio, data_fim = periodo
      df_filtrado = df_filtrado[
          (df_filtrado["Data"].dt.date >= data_inicio) &
          (df_filtrado["Data"].dt.date <= data_fim)
      ]

  dff = df.copy()
  if acudes_sel:
      dff = dff[dff["Açude"].isin(acudes_sel)]
  if municipios_sel:
      dff = dff[dff["Município"].isin(municipios_sel)]
  if classificacao_sel:
      dff = dff[dff["Classificação (canon)"].isin(classificacao_sel)]
  if periodo:
      if len(periodo) == 1:
          ini = fim = pd.to_datetime(periodo[0])
      else:
          ini, fim = [pd.to_datetime(d) for d in periodo]
      dff = dff[(dff["Data"] >= ini) & (dff["Data"] <= fim)]

  if dff.empty:
      st.info("Não há dados para os filtros selecionados.")
      st.stop()

  # ========= LAT/LON A PARTIR DE 'Coordenadas' (fallback robusto) =========
  def _ensure_latlon(df_in: pd.DataFrame) -> pd.DataFrame:
      df_out = df_in.copy()
      if "Coordenadas" in df_out.columns and not {"Latitude", "Longitude"}.issubset(df_out.columns):
          try:
              latlon = df_out["Coordenadas"].astype(str).str.split(",", n=1, expand=True)
              df_out["Latitude"]  = pd.to_numeric(latlon[0], errors="coerce")
              df_out["Longitude"] = pd.to_numeric(latlon[1], errors="coerce")
          except Exception:
              pass
      return df_out

  dff = _ensure_latlon(dff)
  df_filtrado = _ensure_latlon(df_filtrado)

  dff = dff.sort_values(["Açude", "Data"])

  # ========= MAPA =========
  st.subheader("🌍 Mapa dos Açudes")

  with st.expander("Mapas de Fundo", expanded=False):
      tile_option = st.selectbox(
          "Estilo do Mapa:",
          [
              "OpenStreetMap",
              "Stamen Terrain",
              "Stamen Toner",
              "CartoDB positron",
              "CartoDB dark_matter",
              "Esri Satellite",
          ],
          index=0,
          key="map_style_select",
      )

  # GeoJSONs adicionais já carregados
  geojson_bacia = geojson_data.get("geojson_bacia", {})
  geojson_sedes = geojson_data.get("geojson_sedes", {})
  geojson_situa = geojson_data.get("geojson_situa", {})  # importante: precisa existir

  tile_config = {
      "OpenStreetMap": {
          "tiles": "OpenStreetMap",
          "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      },
      "Stamen Terrain": {
          "tiles": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
          "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
      },
      "CartoDB positron": {
          "tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
          "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
      },
      "CartoDB dark_matter": {
          "tiles": "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
          "attr": '&copy; <a href="https://carto.com/attributions">CARTO</a>',
      },
      "Esri Satellite": {
          "tiles": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
          "attr": "Tiles &copy; Esri — Source: Esri",
      },
      "Stamen Toner": {
          "tiles": "https://stamen-tiles-a.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
          "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>',
      },
  }

  # Centro inicial
  df_base = df_filtrado.copy()
  if not df_base.empty and {"Latitude", "Longitude"}.issubset(df_base.columns):
      start_center = [float(df_base["Latitude"].mean()), float(df_base["Longitude"].mean())]
  else:
      start_center = [-5.2, -39.5]

  m = folium.Map(location=start_center, zoom_start=9, tiles=None)
  folium.TileLayer(
      tiles=tile_config[tile_option]["tiles"],
      attr=tile_config[tile_option]["attr"],
      name=tile_option,
  ).add_to(m)

  # ========= COR POR CLASSIFICAÇÃO (usa canônico) =========
  def get_classification_color(props: dict) -> str:
      classificacao = props.get("Classificação") or props.get("classificacao") or ""
      classificacao = canon_classificacao(classificacao)
      color_map = {
          "Criticidade Alta":   "#E24F42",
          "Criticidade Média":  "#ECC116",
          "Criticidade Baixa":  "#F4FA4A",
          "Fora de Criticidade":"#8DCC90",
          "Sem classificação":  "#999999",
      }
      return color_map.get(classificacao, "#999999")

  def style_function(feature):
      props = feature.get("properties", {})
      return {
          "fillColor": get_classification_color(props),
          "color": "#555555",
          "weight": 1.5,
          "fillOpacity": 0.7,
          "opacity": 0.9,
      }

  # ========= FIT BOUNDS PELA BACIA =========
  if geojson_bacia:
      gj_bacia = folium.GeoJson(
          geojson_bacia,
          name="Bacia do Banabuiú",
          style_function=lambda x: {"color": "blue", "weight": 2, "fillOpacity": 0.1},
          tooltip=folium.GeoJsonTooltip(fields=["DESCRICA1"], aliases=["Bacia:"]),
      ).add_to(m)
      try:
          coords_all = []
          feats = geojson_bacia.get("features", [])
          for feature in feats:
              geom = feature.get("geometry", {})
              gtype = geom.get("type")
              gcoords = geom.get("coordinates", [])
              if gtype == "Polygon":
                  for ring in gcoords:
                      coords_all.extend(ring)
              elif gtype == "MultiPolygon":
                  for poly in gcoords:
                      for ring in poly:
                          coords_all.extend(ring)
              elif gtype == "Point":
                  coords_all.append(gcoords)
              elif gtype in ("MultiPoint", "LineString", "MultiLineString"):
                  for c in gcoords:
                      if isinstance(c, (list, tuple)) and len(c) >= 2:
                          coords_all.append(c)
          if coords_all:
              lons, lats = zip(*coords_all)
              m.fit_bounds([[min(lats), min(lons)], [max(lats), max(lons)]])
      except Exception as e:
          st.warning(f"Não foi possível centralizar pela bacia: {e}")

  # ========= SEDES MUNICIPAIS =========
  if geojson_sedes and isinstance(geojson_sedes, dict) and "features" in geojson_sedes:
      sedes_layer = folium.FeatureGroup(name="Sedes Municipais", show=True)
      for feature in geojson_sedes["features"]:
          props  = feature.get("properties", {})
          geom   = feature.get("geometry", {})
          coords = geom.get("coordinates", [])
          if geom.get("type") == "Point" and isinstance(coords, (list, tuple)) and len(coords) >= 2:
              nome = props.get("NOME_MUNIC", "Sem nome")
              try:
                  lat, lon = float(coords[1]), float(coords[0])
                  folium.Marker(
                      [lat, lon],
                      icon=folium.CustomIcon(
                          "https://cdn-icons-png.flaticon.com/512/854/854878.png",
                          icon_size=(25, 25),
                      ),
                      tooltip=nome,
                  ).add_to(sedes_layer)
              except Exception:
                  continue
      sedes_layer.add_to(m)

  # ========= FILTRAR GEOJSON DE SITUAÇÃO POR CLASSIFICAÇÃO CANÔNICA =========
  def _get_classificacao_from_props(props: dict) -> str:
      for k in ["Classificação", "classificacao", "CLASSIFICACAO", "classificação", "situacao", "SITUACAO"]:
          if k in (props or {}) and pd.notna(props[k]):
              return canon_classificacao(props[k])
      return "Sem classificação"

  def filtrar_geojson_por_classificacao(geojson_fc: dict, classes_sel):
      if not geojson_fc or geojson_fc.get("type") != "FeatureCollection":
          return {}
      sel_canon = {canon_classificacao(c) for c in (classes_sel or [])}
      feats = []
      for f in geojson_fc.get("features", []):
          cls_canon = _get_classificacao_from_props(f.get("properties", {}))
          if cls_canon in sel_canon:
              # grava canônico para tooltip/estilo consistentes
              f.setdefault("properties", {})["Classificação"] = cls_canon
              feats.append(f)
      return {"type": "FeatureCollection", "features": feats} if feats else {}

  geojson_situa_filtrado = filtrar_geojson_por_classificacao(geojson_situa, classificacao_sel)

  if geojson_situa_filtrado:
      try:
          situa_group = folium.FeatureGroup(name="Situação da Bacia", show=True)
          folium.GeoJson(
              geojson_situa_filtrado,
              style_function=style_function,
              tooltip=folium.GeoJsonTooltip(
                  fields=["Classificação"],
                  aliases=["Classificação:"],
                  sticky=True,
                  style="font-weight: bold;",
              ),
          ).add_to(situa_group)
          situa_group.add_to(m)
      except Exception as e:
          st.error(f"Erro ao processar a camada de Situação: {e}")
  else:
      st.info("Nenhuma área da camada 'Situação da Bacia' corresponde à Classificação selecionada.")

  # ========= MARCADORES DOS AÇUDES =========
  if not df_base.empty and {"Latitude", "Longitude"}.issubset(df_base.columns):
      for _, row in df_base.iterrows():
          try:
              lat = float(row["Latitude"]); lon = float(row["Longitude"])
          except Exception:
              continue
          classificacao_canon = row.get("Classificação (canon)", "Sem classificação")
          color_marker = get_classification_color({"Classificação": classificacao_canon})

          # Mostra canônico e original (opcional)
          classificacao_original = row.get("Classificação", "Sem classificação")
          popup_html = f"""
          <div style="font-family: Arial, sans-serif; font-size: 14px;">
              <h4 style="margin:0; padding:0; color: #2c3e50;">{row.get('Açude', 'N/A')}</h4>
              <p><b>Município:</b> {row.get('Município', 'N/A')}</p>
              <p><b>Cota Simulada:</b> {row.get('Cota Simulada (m)', 'N/A')} m</p>
              <p><b>Cota Realizada:</b> {row.get('Cota Realizada (m)', 'N/A')} m</p>
              <p><b>Volume:</b> {row.get('Volume(m³)', 'N/A')} m³</p>
              <p><b>Classificação:</b> <span style="color:{color_marker}; font-weight:bold;">{classificacao_canon}</span>
                <br><small style="color:#666;">Origem: {classificacao_original}</small></p>
          </div>
          """
          folium.CircleMarker(
              location=[lat, lon],
              radius=6,
              color=color_marker,
              fill=True,
              fill_color=color_marker,
              fill_opacity=0.9,
              tooltip=row.get("Açude", "N/A"),
              popup=folium.Popup(popup_html, max_width=300),
          ).add_to(m)

  # ========= PLUGINS / CONTROLES =========
  Fullscreen().add_to(m)
  MousePosition(position="bottomleft", separator=" | ", num_digits=4).add_to(m)
  folium.LayerControl(collapsed=False).add_to(m)

  # ========= RENDER E LEGENDA =========
  map_container = st.container()
  with map_container:
      folium_static(m, width=1000, height=600)

      st.markdown("""
      <style>
      .map-legend-container { position: relative; margin-top: -40px; margin-bottom: 20px; z-index: 1000; }
      .map-legend { background: white; padding: 10px 15px; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.15); border: 1px solid #eee; display: inline-block; margin: 0 auto; }
      .legend-items { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; }
      .legend-item { display: flex; align-items: center; }
      .legend-color { width: 18px; height: 18px; margin-right: 8px; border: 1px solid #555; border-radius: 3px; }
      .legend-label { font-size: 13px; font-family: Arial, sans-serif; color: #333; }
      </style>
      <div class="map-legend-container">
          <div class="map-legend">
              <div class="legend-items">
                  <div class="legend-item"><div class="legend-color" style="background-color:#E24F42;"></div><span class="legend-label">Criticidade Alta</span></div>
                  <div class="legend-item"><div class="legend-color" style="background-color:#ECC116;"></div><span class="legend-label">Criticidade Média</span></div>
                  <div class="legend-item"><div class="legend-color" style="background-color:#F4FA4A;"></div><span class="legend-label">Criticidade Baixa</span></div>
                  <div class="legend-item"><div class="legend-color" style="background-color:#8DCC90;"></div><span class="legend-label">Fora de Criticidade</span></div>
                  <div class="legend-item"><div class="legend-color" style="background-color:#999999;"></div><span class="legend-label">Sem classificação</span></div>
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
    
# ===================== Liberação (m³/s)' =====================
 
    if 'Liberação (m³/s)' in dff.columns:
        with kpi_cols[0]:
            try:
                # Converte valores para numérico (tratando vírgulas como decimais)
                dff["Liberação (m³/s)"] = pd.to_numeric(
                    dff["Liberação (m³/s)"].astype(str).str.replace(',', '.'),
                    errors='coerce'
                )
                
                # Encontra o dia MAIS ANTIGO
                data_mais_antiga = dff['Data'].min()
                
                # Filtra os dados apenas para o dia mais antigo
                df_dia_antigo = dff[dff['Data'] == data_mais_antiga]
                
                # Calcula a liberação para UMA HORA (m³/s → m³/h)
                primeira_liberacao_m3s = df_dia_antigo["Liberação (m³/s)"].iloc[0]  # Pega o primeiro valor
                liberacao_m3h = primeira_liberacao_m3s * 3600  # Conversão para m³/h
                
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Vazão Simulada (m³/h)</div>  <!-- Título alterado -->
                    <div class="kpi-value">{liberacao_m3h:,.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
            except Exception as e:
                st.warning(f"Não foi possível calcular a liberação. Erro: {str(e)}")
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
