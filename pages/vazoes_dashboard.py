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
# 🏞️ Média da Vazão Operada por reservatório — CORRIGIDO
# =====================================================================
    st.subheader("🏞️ Média da Vazão Operada por Reservatório")

    if not df_filtrado.empty:
        dfm = df_filtrado.copy()
        dfm["Data"] = pd.to_datetime(dfm["Data"], errors="coerce")
        dfm = dfm.dropna(subset=["Data", "Reservatório Monitorado"])
        
        # Data máxima do dataset (mesma referência do gráfico de Evolução)
        data_maxima_dataset = dfm["Data"].max()

        # 1 leitura por dia por reservatório (última do dia), igual ao gráfico de Evolução
        df_diario = (
            dfm.sort_values("Data")
              .groupby(["Reservatório Monitorado", "Data"], as_index=False)
              .last()
        )

        # Mês e ano para não misturar períodos
        meses_map = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
                    7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}
        df_diario["Ano"] = df_diario["Data"].dt.year
        df_diario["Mês"] = df_diario["Data"].dt.month.map(meses_map)
        df_diario["MêsRef"] = df_diario["Mês"] + "/" + df_diario["Ano"].astype(str)

        # Função para calcular média ponderada mensal (MESMA metodologia do gráfico de Evolução)
        def calcular_media_ponderada_mensal(grupo):
            grupo = grupo.sort_values('Data')
            grupo = grupo.copy()
            grupo['dias_ativos'] = grupo['Data'].diff().dt.days.fillna(0)
            
            # CORREÇÃO: Usar a mesma lógica do gráfico de Evolução
            # Para o último registro, calcular dias até a data máxima do dataset
            if not grupo.empty:
                ultima_data = grupo['Data'].iloc[-1]
                
                # Se for o último mês do dataset, vai até data_maxima_dataset
                # Se for mês anterior, vai até o final do mês
                if ultima_data.month == data_maxima_dataset.month and ultima_data.year == data_maxima_dataset.year:
                    # Último mês: usa data máxima do dataset (igual gráfico Evolução)
                    dias_restantes = (data_maxima_dataset - ultima_data).days + 1
                else:
                    # Mês completo: vai até o final do mês
                    fim_mes = ultima_data + pd.offsets.MonthEnd(0)
                    dias_restantes = (fim_mes - ultima_data).days + 1
                
                grupo.loc[grupo.index[-1], 'dias_ativos'] = dias_restantes
            
            # Calcular média ponderada (mesma metodologia do gráfico de Evolução)
            vazao_total_ponderada = (grupo['Vazão Operada'] * grupo['dias_ativos']).sum()
            dias_totais = grupo['dias_ativos'].sum()
            
            return vazao_total_ponderada / dias_totais if dias_totais > 0 else 0

        # Calcular média mensal ponderada (igual à metodologia do gráfico de Evolução)
        media_mensal = (
            df_diario.groupby(["Reservatório Monitorado", "MêsRef"], dropna=True)
                    .apply(calcular_media_ponderada_mensal)
                    .reset_index(name='Vazão Operada')
        )

        # Mesma unidade do gráfico de evolução
        y_vals_media, unit_suffix_media = convert_vazao(media_mensal["Vazão Operada"], unidade_sel)
        media_mensal["Vazão (conv)"] = y_vals_media

        # Ordena reservatórios pelo total do período
        ordem_res = (
            media_mensal.groupby("Reservatório Monitorado")["Vazão (conv)"]
                        .sum().sort_values(ascending=True).index.tolist()
        )

        # Ordena MêsRef cronologicamente
        inv_meses = {v: k for k, v in meses_map.items()}
        media_mensal["ord"] = media_mensal["MêsRef"].apply(
            lambda s: int(s.split("/")[1]) * 100 + inv_meses[s.split("/")[0]]
        )
        media_mensal = media_mensal.sort_values("ord")
        ordem_mesref = media_mensal["MêsRef"].unique().tolist()

        # Rotulagem com pontos e unidade
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
            hover_data={
                "Vazão (conv)": False,
                "Valor Formatado": True
            }
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





