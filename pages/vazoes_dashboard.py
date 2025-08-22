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

# =====================================================================
# 📈 Evolução da Vazão Operada por Reservatório
# =====================================================================
st.subheader("📈 Evolução da Vazão Operada por Reservatório")

fig = go.Figure()
cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#17becf", "#e377c2"]
reservatorios = df_filtrado["Reservatório Monitorado"].dropna().unique()

# Normaliza Data no dataframe base
df_evo = df_filtrado.copy()
df_evo["Data"] = pd.to_datetime(df_evo["Data"], errors="coerce").dt.floor("D")
data_fim_global = df_evo["Data"].max()

for i, r in enumerate(reservatorios):
    dfr = (
        df_evo[df_evo["Reservatório Monitorado"] == r]
        .sort_values("Data")
        .groupby("Data", as_index=False)
        .last()
    )

    # Linha principal (Vazão Operada) na unidade selecionada
    y_vals, unit_suffix = convert_vazao(dfr["Vazão Operada"], unidade_sel)
    fig.add_trace(go.Scatter(
        x=dfr["Data"], y=y_vals, mode="lines+markers", name=r,
        line=dict(shape="hv", width=2, color=cores[i % len(cores)]),
        marker=dict(size=5),
        hovertemplate=f"<b>{r}</b><br>Data: %{{x|%d/%m/%Y}}<br>"
                      f"Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
    ))

    # Caso tenha apenas um reservatório selecionado → linhas extras
    if len(reservatorios) == 1 and len(dfr) > 1:
        dfr = dfr.copy()
        dfr["dias_ativos"] = dfr["Data"].diff().dt.days.fillna(0)
        if pd.notna(data_fim_global):
            dfr.loc[dfr.index[-1], "dias_ativos"] = (data_fim_global - dfr["Data"].iloc[-1]).days + 1

        if dfr["dias_ativos"].sum() > 0:
            media_pond = (dfr["Vazão Operada"] * dfr["dias_ativos"]).sum() / dfr["dias_ativos"].sum()
            media_pond_conv, _ = convert_vazao(pd.Series([media_pond]), unidade_sel)
            fig.add_hline(
                y=float(media_pond_conv.iloc[0]), line_dash="dash", line_width=2, line_color="red",
                annotation_text=f"Média ponderada {media_pond_conv.iloc[0]:.2f} {unit_suffix}",
                annotation_position="top right"
            )

        # Linha Azul Vazao_Aloc se existir
        if "Vazao_Aloc" in dfr.columns:
            y_aloc, _ = convert_vazao(dfr["Vazao_Aloc"], unidade_sel)
            fig.add_trace(go.Scatter(
                x=dfr["Data"], y=y_aloc, mode="lines",
                name="Vazão Alocada", line=dict(color="blue", width=2, dash="dot"),
                hovertemplate=f"<b>Vazão Alocada</b><br>Data: %{{x|%d/%m/%Y}}<br>"
                              f"Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
            ))

# Legenda na parte inferior
fig.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
)

st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key="plotly_vazao_evolucao")


# =====================================================================
# 📊 Volume acumulado por reservatório
# =====================================================================
st.subheader("📊 Volume acumulado por reservatório")

cols_necessarias = {"Reservatório Monitorado", "Data", "Vazão Operada"}
tem_cols = cols_necessarias.issubset(set(df_filtrado.columns))
tem_res = not df_filtrado.empty and df_filtrado["Reservatório Monitorado"].nunique() > 0

if tem_cols and tem_res:
    df_box = df_filtrado.copy()
    df_box["Data"] = pd.to_datetime(df_box["Data"], errors="coerce").dt.floor("D")
    df_box["Vazão Operada"] = pd.to_numeric(df_box["Vazão Operada"], errors="coerce").fillna(0)

    volumes = []
    fim_periodo_global = df_box["Data"].max()

    for reservatorio in df_box["Reservatório Monitorado"].dropna().unique():
        df_res = (
            df_box[df_box["Reservatório Monitorado"] == reservatorio]
            .dropna(subset=["Data"])
            .sort_values("Data")
            .groupby("Data", as_index=False)
            .last()
            .copy()
        )
        if df_res.empty:
            continue

        # Dias entre medições (fecha último intervalo até o fim do período global)
        df_res["dias_entre_medicoes"] = df_res["Data"].diff().dt.days.fillna(0)
        ultima_data_res = df_res["Data"].iloc[-1]
        fim_periodo = fim_periodo_global if pd.notna(fim_periodo_global) else ultima_data_res
        df_res.loc[df_res.index[-1], "dias_entre_medicoes"] = max((fim_periodo - ultima_data_res).days + 1, 0)

        # l/s -> m³/s
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


# =====================================================================
# 🏞️ Média da Vazão Operada por reservatório — barras empilhadas horizontal (100% coerente com Evolução)
# =====================================================================
st.subheader("🏞️ Média da Vazão Operada por Reservatório")

def medias_mensais_ponderadas_por_intervalo(df_base: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula média mensal ponderada por dias, respeitando os degraus
    entre medições (valor constante até a próxima medição).
    """
    meses_map = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
                 7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}

    out_rows = []
    data_fim = df_base["Data"].max()

    for r in df_base["Reservatório Monitorado"].dropna().unique():
        dfr = (
            df_base[df_base["Reservatório Monitorado"] == r]
            .sort_values("Data")
            .groupby("Data", as_index=False)
            .last()
        )
        if dfr.empty:
            continue

        # Lista de intervalos [ini, fim] com valor constante
        datas = dfr["Data"].tolist()
        vals  = dfr["Vazão Operada"].tolist()

        for j in range(len(datas)):
            ini = datas[j]
            if j < len(datas) - 1:
                fim = datas[j+1] - pd.Timedelta(days=1)  # até véspera da próxima medição
            else:
                fim = data_fim  # até o fim do período filtrado

            if pd.isna(ini) or pd.isna(fim) or fim < ini:
                continue

            # Percorre meses que intersectam o intervalo
            cursor = pd.Timestamp(ini.year, ini.month, 1)
            last_month_start = pd.Timestamp(fim.year, fim.month, 1)
            while cursor <= last_month_start:
                month_start = cursor
                month_end   = (cursor + MonthEnd(1)).floor("D")

                # Interseção [max(ini, month_start), min(fim, month_end)]
                o_ini = max(ini, month_start)
                o_fim = min(fim, month_end)
                if o_ini <= o_fim:
                    dias = (o_fim - o_ini).days + 1
                    out_rows.append({
                        "Reservatório Monitorado": r,
                        "Ano": month_start.year,
                        "MesNum": month_start.month,
                        "dias": dias,
                        "soma_pond": vals[j] * dias
                    })

                # Próximo mês
                cursor = (cursor + MonthEnd(1)) + pd.offsets.Day(1)

    if not out_rows:
        return pd.DataFrame(columns=["Reservatório Monitorado","MêsRef","Vazão Operada"])

    tmp = pd.DataFrame(out_rows)
    agg = tmp.groupby(["Reservatório Monitorado","Ano","MesNum"], as_index=False).sum()
    agg["Vazão Operada"] = agg["soma_pond"] / agg["dias"]
    agg["MêsRef"] = agg["MesNum"].map(meses_map) + "/" + agg["Ano"].astype(str)
    return agg[["Reservatório Monitorado","Ano","MesNum","MêsRef","Vazão Operada"]]

if not df_filtrado.empty:
    base = df_filtrado.copy()
    base["Data"] = pd.to_datetime(base["Data"], errors="coerce").dt.floor("D")
    base = base.dropna(subset=["Data", "Reservatório Monitorado"])

    # Média mensal ponderada por dias dos INTERVALOS (coerente com a escadinha)
    media_mensal = medias_mensais_ponderadas_por_intervalo(base)

    # Mesma unidade do gráfico de evolução
    y_vals_media, unit_suffix_media = convert_vazao(media_mensal["Vazão Operada"], unidade_sel)
    media_mensal["Vazão (conv)"] = y_vals_media

    # Ordenações
    ordem_res = (
        media_mensal.groupby("Reservatório Monitorado")["Vazão (conv)"]
                    .sum().sort_values(ascending=True).index.tolist()
    )
    media_mensal["ord_mes"] = media_mensal["Ano"]*100 + media_mensal["MesNum"]
    media_mensal = media_mensal.sort_values("ord_mes")
    ordem_mesref = media_mensal["MêsRef"].unique().tolist()

    # Rotulagem (3 casas < 1000; 2 casas + milhar com ponto >= 1000)
    def format_val_dot(v: float, unit: str) -> str:
        if pd.isna(v):
            return "- " + unit
        if abs(v) < 1000:
            s = f"{v:.3f}"
        else:
            s = f"{v:,.2f}".replace(",", ".")
        return f"{s} {unit}"

    media_mensal["Valor Formatado"] = media_mensal["Vazão (conv)"].apply(lambda v: format_val_dot(v, unit_suffix_media))

    # Gráfico horizontal empilhado por Mês/Ano
    fig_media = px.bar(
        media_mensal,
        y="Reservatório Monitorado",
        x="Vazão (conv)",
        color="MêsRef",
        orientation="h",
        text="Valor Formatado",
        category_orders={"Reservatório Monitorado": ordem_res, "MêsRef": ordem_mesref},
        labels={
            "Reservatório Monitorado": "Reservatório",
            "Vazão (conv)": f"Média ({unit_suffix_media})",
            "MêsRef": "Mês/Ano"
        },
        barmode="stack",
        hover_data={"Vazão (conv)": False, "Valor Formatado": True}
    )

    fig_media.update_traces(textposition="inside", insidetextanchor="middle", cliponaxis=False)
    fig_media.update_layout(
        bargap=0.2,
        legend_title_text="Mês/Ano",
        xaxis_title=f"Média ({unit_suffix_media})",
        yaxis_title="Reservatório"
    )

    st.plotly_chart(fig_media, use_container_width=True, config={"displaylogo": False}, key="plotly_vazao_media_res_mes_alinhado")

else:
    st.info("Sem dados para a média.")
    
    # ------------- Tabela -------------
    st.subheader("📋 Tabela Detalhada")
    st.dataframe(df_filtrado.sort_values(by="Data", ascending=False), use_container_width=True, key="dataframe_vazao")



