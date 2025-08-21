

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import folium
from streamlit_folium import folium_static
from folium.plugins import Fullscreen, MiniMap, MousePosition, MeasureControl, MarkerCluster
import altair as alt
from utils.common import carregar_dados_vazoes, convert_vazao, load_geojson_data

st.set_page_config(layout="wide")

def render_vazoes_dashboard():
    """Renderiza a página completa do painel de vazões."""
    
    # === Carregamento de Dados e GeoJSON (Cachê) ===
    geojson_data = load_geojson_data()
    df = carregar_dados_vazoes()
    
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

    # === Botão de Atualização ===
    cA1, cA2, cA3 = st.columns([1, 1, 1])
    with cA1:
        if st.button("🔄 Atualizar agora", key="btn_vazoes_atualizar"):
            carregar_dados_vazoes.clear()
            df = carregar_dados_vazoes()
            st.success("Atualizado.")

    # === Filtros da Página ===
    with st.expander("☰ Filtros", expanded=True):
        st.markdown('<div class="filter-card"><div class="filter-title">Opções de Filtro</div>', unsafe_allow_html=True)
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

    # === Exibe KPIs ===
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

# === Gráficos de Vazão e Volume ===
    st.subheader("📈 Evolução da Vazão Operada por Reservatório")
    fig = go.Figure()
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#17becf", "#e377c2"]
    reservatorios = df_filtrado["Reservatório Monitorado"].dropna().unique()

    for i, r in enumerate(reservatorios):
        dfr = df_filtrado[df_filtrado["Reservatório Monitorado"] == r] \
                .sort_values("Data").groupby("Data", as_index=False).last()

        # Linha principal (Vazão Operada)
        y_vals, unit_suffix = convert_vazao(dfr["Vazão Operada"], unidade_sel)
        fig.add_trace(go.Scatter(
            x=dfr["Data"], y=y_vals, mode="lines+markers", name=r,
            line=dict(shape="hv", width=2, color=cores[i % len(cores)]),
            marker=dict(size=5),
            hovertemplate=f"<b>{r}</b><br>Data: %{{x|%d/%m/%Y}}<br>"
                          f"Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
        ))

        # Caso tenha apenas um reservatório selecionado → adicionar linhas extras
        if len(reservatorios) == 1 and len(dfr) > 1:
            # --- Média ponderada ---
            dfr["dias_ativos"] = dfr["Data"].diff().dt.days.fillna(0)
            if not dfr.empty:
                dfr.loc[dfr.index[-1], "dias_ativos"] = \
                    (df_filtrado["Data"].max() - dfr["Data"].iloc[-1]).days + 1

                media_pond = (dfr["Vazão Operada"] * dfr["dias_ativos"]).sum() / dfr["dias_ativos"].sum()
                media_pond_conv, _ = convert_vazao(pd.Series([media_pond]), unidade_sel)

                fig.add_hline(
                    y=media_pond_conv.iloc[0], line_dash="dash", line_width=2, line_color="red",
                    annotation_text=f"Média Ponderada: {media_pond_conv.iloc[0]:.2f} {unit_suffix}",
                    annotation_position="top right"
                )

            # --- Linha Azul (Vazao_Aloc) ---
            if "Vazao_Aloc" in dfr.columns:
                y_aloc, _ = convert_vazao(dfr["Vazao_Aloc"], unidade_sel)
                fig.add_trace(go.Scatter(
                    x=dfr["Data"], y=y_aloc, mode="lines",
                    name="Vazão Alocada", line=dict(color="blue", width=2, dash="dot"),
                    hovertemplate=f"<b>Vazão Alocada</b><br>Data: %{{x|%d/%m/%Y}}<br>"
                                  f"Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
                ))

    # Configuração para colocar a legenda na parte inferior
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5
        )
    )

    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key="plotly_vazao_evolucao")



#==================VOLUME LIBERADO===========
    st.subheader("📊 Volume acumulado por reservatório")

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
                return "—"
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
            y_title = "Volume acumulado em milhões de m³"

            base = alt.Chart(df_volumes).encode(
                x=alt.X("Reservatório Monitorado:N", title="Reservatório", sort="-y")
            ).properties(
                title="Volume acumulado por reservatório",
                height=400
            ).interactive()

            bars = base.mark_bar(color="steelblue").encode(
                y=alt.Y("Volume Eixo Y:Q", title=y_title, scale=alt.Scale(domain=[0, y_max])),
                tooltip=[
                    alt.Tooltip("Reservatório Monitorado:N", title="Reservatório"),
                    alt.Tooltip("Volume Formatado:N", title="Volume total")
                ]
            )

            # Texto com o valor formatado em cima de cada barra
            text = base.mark_text(
                align="center",
                baseline="bottom",
                dy=-5,
                fontSize=12
            ).encode(
                y=alt.Y("Volume Eixo Y:Q", stack=None),
                text="Volume Formatado:N"
            )

            chart = alt.layer(bars, text).resolve_scale(y="independent")
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Sem dados suficientes para montar o gráfico.")
    else:
        st.info("Sem dados suficientes para o gráfico de volume.") 

# ------------- Média por reservatório -------------
    st.subheader("🏞️ Média da Vazão Operada por Reservatório — barras empilhadas (horizontal por mês)")

    if not df_filtrado.empty:
        df = df_filtrado.copy()
        # Tipagem segura
        df["Vazão Operada"] = pd.to_numeric(df.get("Vazão Operada", 0), errors="coerce").fillna(0)

        if "Data" in df.columns:
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
            df["Mês"] = df["Data"].dt.month
            # Nome dos meses (em português)
            meses_map = {
                1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun",
                7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"
            }
            df["Mês"] = df["Mês"].map(meses_map)
        else:
            df["Mês"] = "Total"

        # Média por reservatório e mês
        media_vazao = (
            df.groupby(["Reservatório Monitorado", "Mês"], dropna=True)["Vazão Operada"]
              .mean()
              .reset_index()
        )

        # Conversão de unidade
        media_conv, unit_bar = convert_vazao(media_vazao["Vazão Operada"], unidade_sel)
        media_vazao["Vazão (conv)"] = media_conv

        # Ordena reservatórios pelo total anual
        ordem = (
            media_vazao.groupby("Reservatório Monitorado")["Vazão (conv)"]
            .sum()
            .sort_values(ascending=True)
            .index.tolist()
        )

        # Gráfico horizontal empilhado
        fig = px.bar(
            media_vazao,
            y="Reservatório Monitorado",
            x="Vazão (conv)",
            color="Mês",
            orientation="h",
            text_auto=".2s",
            category_orders={"Reservatório Monitorado": ordem,
                            "Mês": ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]},
            labels={
                "Reservatório Monitorado": "Reservatório",
                "Vazão (conv)": f"Média ({unit_bar})",
                "Mês": "Mês"
            },
            barmode="stack"
        )

        fig.update_layout(
            bargap=0.2,
            legend_title_text="Mês",
            xaxis_title=f"Média ({unit_bar})",
            yaxis_title="Reservatório"
        )

        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key="plotly_vazao_media_res_mes")
    else:
        st.info("Sem dados para a média.")

    # ------------- Tabela -------------
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True, key="dataframe_vazao")







