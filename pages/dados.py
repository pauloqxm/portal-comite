import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
    
    # Função para normalizar números (suporta pt-BR e variações)
    def _to_num(series: pd.Series) -> pd.Series:
        # Converte tudo para string, remove espaços, normaliza -, remove milhar, troca vírgula por ponto
        s = series.astype(str).str.strip()
        # Trata nulos: se vier "nan" ou vazio
        s = s.replace({"": None, "nan": None, "None": None})
        # Remove separador de milhar ponto quando a string tem vírgula como decimal
        # e também remove pontos isolados de milhar
        s = s.str.replace(r"\.", "", regex=True)  # remove todos . (assumindo que . é milhar)
        s = s.str.replace(",", ".", regex=False)  # vírgula vira decimal
        return pd.to_numeric(s, errors="coerce")

    try:
        df = pd.read_csv(google_sheet_url)
        # Datas
        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y", errors="coerce")
        else:
            st.error("A coluna 'Data' não foi encontrada na planilha.")
            return
    except Exception as e:
        st.error(f"Erro ao carregar os dados da planilha. Verifique o link e a permissão pública. Detalhes: {e}")
        return

    if df.empty:
        st.info("A planilha de simulações está vazia.")
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

    # 1) Filtros
    with st.container():
        st.markdown('<div class="expander-rounded">', unsafe_allow_html=True)
        with st.expander("☰ Filtros (clique para expandir)", expanded=True):
            st.markdown('<div class="filter-card"><div class="filter-title">Filtros de Visualização</div>', unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                opcoes_acudes = sorted(df.get("Açude", pd.Series(dtype=str)).dropna().unique().tolist())
                acudes_sel = st.multiselect("Açude", options=opcoes_acudes, default=opcoes_acudes)
            with col2:
                opcoes_municipios = sorted(df.get("Município", pd.Series(dtype=str)).dropna().unique().tolist())
                municipios_sel = st.multiselect("Município", options=opcoes_municipios, default=opcoes_municipios)
            with col3:
                opcoes_classificacao = sorted(df.get("Classificação", pd.Series(dtype=str)).dropna().unique().tolist())
                classificacao_sel = st.multiselect("Classificação", options=opcoes_classificacao, default=opcoes_classificacao)
            with col4:
                datas_validas = df["Data"].dropna()
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
        dff = dff[dff.get("Açude").isin(acudes_sel)]
    if municipios_sel:
        dff = dff[dff.get("Município").isin(municipios_sel)]
    if classificacao_sel:
        dff = dff[dff.get("Classificação").isin(classificacao_sel)]

    if periodo:
        if isinstance(periodo, tuple) and len(periodo) == 2:
            ini, fim = [pd.to_datetime(d) for d in periodo]
        else:
            ini = fim = pd.to_datetime(periodo)
        dff = dff[(dff["Data"] >= ini) & (dff["Data"] <= fim)]

    if dff.empty:
        st.info("Não há dados para os filtros selecionados.")
        return

    # 2) Conversão numérica padronizada (tratar . e ,)
    numeric_cols = [
        'Cota Simulada (m)',
        'Cota Realizada (m)',
        'Volume(m³)',
        'Volume (%)',
        'Evapor. Parcial(mm)',
        'Cota Interm. (m)',
        'Liberação (m³/s)',
        'Liberação (m³)'
    ]
    for col in numeric_cols:
        if col in dff.columns:
            dff[col] = _to_num(dff[col])

    # 3) Coordenadas (Latitude, Longitude) a partir de 'Coordenadas' ("lat, lon")
    if "Coordenadas" in dff.columns:
        coords = dff["Coordenadas"].astype(str).str.split(",", n=1, expand=True)
        if coords.shape[1] == 2:
            dff["Latitude"] = _to_num(coords[0].str.strip().str.replace(",", ".", regex=False))
            dff["Longitude"] = _to_num(coords[1].str.strip().str.replace(",", ".", regex=False))
        else:
            st.warning("Formato inesperado na coluna 'Coordenadas'. Mapa pode não ser exibido.")
    else:
        st.warning("A coluna 'Coordenadas' não foi encontrada. O mapa não será exibido.")

    dff = dff.sort_values(["Açude", "Data"])

    # 4) KPIs
    st.markdown("---")
    st.subheader("📊 Indicadores de Desempenho (KPIs)")
    kpi1, kpi2, kpi3 = st.columns(3)

    with kpi1:
        if 'Liberação (m³/s)' in dff.columns:
            total_liberacao = dff['Liberação (m³/s)'].sum(skipna=True)
            st.metric(label="Total de Liberação (m³/s)", value=f"{(total_liberacao or 0):.2f}")
        else:
            st.warning("Coluna 'Liberação (m³/s)' não encontrada.")

    with kpi2:
        total_acudes = dff.get("Açude", pd.Series(dtype=str)).nunique()
        st.metric(label="Açudes Monitorados", value=int(total_acudes))

    with kpi3:
        if not dff["Data"].dropna().empty:
            dias = int((dff["Data"].max() - dff["Data"].min()).days)
            st.metric(label="Dias do Período", value=dias)
        else:
            st.metric(label="Dias do Período", value="N/A")

    # 5) Mapa
    st.markdown("---")
    st.subheader("🗺️ Mapa dos Açudes e Cotas")

    if {"Latitude", "Longitude"}.issubset(dff.columns):
        # Remove linhas sem coordenadas válidas
        mapa_df = dff.dropna(subset=["Latitude", "Longitude"])
        if not mapa_df.empty:
            fig_mapa = px.scatter_mapbox(
                mapa_df,
                lat="Latitude",
                lon="Longitude",
                color="Classificação" if "Classificação" in mapa_df.columns else None,
                hover_name="Açude" if "Açude" in mapa_df.columns else None,
                hover_data={
                    "Cota Simulada (m)": True,
                    "Cota Realizada (m)": True,
                    "Município": True if "Município" in mapa_df.columns else False,
                    "Liberação (m³/s)": True if "Liberação (m³/s)" in mapa_df.columns else False,
                    "Latitude": False,
                    "Longitude": False,
                    "Data": True
                },
                zoom=7,
                mapbox_style="carto-positron",
                title="Localização e Status dos Açudes"
            )
            fig_mapa.update_layout(
                margin={"r":0,"t":40,"l":0,"b":0},
                legend_title_text="Classificação"
            )
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.info("Mapa não disponível: não há coordenadas válidas após os filtros.")
    else:
        st.info("Mapa não disponível devido à ausência de 'Latitude' e 'Longitude'.")

    # 6) Gráfico de Cotas
    st.markdown("---")
    st.subheader("📈 Cotas (Cota Simulada x Cota Realizada)")
    if {'Cota Simulada (m)', 'Cota Realizada (m)', 'Açude'}.issubset(dff.columns):
        fig_cotas = go.Figure()
        for acude in sorted(dff["Açude"].dropna().unique()):
            base = dff[dff["Açude"] == acude].sort_values("Data")
            if not base.empty:
                fig_cotas.add_trace(go.Scatter(
                    x=base["Data"], y=base["Cota Simulada (m)"],
                    mode="lines+markers",
                    name=f"{acude} - Cota Simulada (m)",
                    hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"
                ))
                fig_cotas.add_trace(go.Scatter(
                    x=base["Data"], y=base["Cota Realizada (m)"],
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
        st.info("Gráfico de Cotas não disponível. Verifique as colunas necessárias.")

    # 7) Gráfico de Volume
    st.subheader("📈 Volume (m³)")
    if {'Volume(m³)', 'Açude'}.issubset(dff.columns):
        fig_vol = go.Figure()
        for acude in sorted(dff["Açude"].dropna().unique()):
            base = dff[dff["Açude"] == acude].sort_values("Data")
            if not base.empty:
                fig_vol.add_trace(go.Scatter(
                    x=base["Data"], y=base["Volume(m³)"],
                    mode="lines+markers",
                    name=f"{acude} - Volume (m³)",
                    hovertemplate="%{x|%d/%m/%Y} • %{y:.2f} m³<extra></extra>"
                ))
        fig_vol.update_layout(
            template="plotly_white",
            margin=dict(l=10, r=10, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanch
