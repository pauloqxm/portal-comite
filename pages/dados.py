import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.common import load_simulacoes_data

def render_dados():
    st.title("📈 Simulações")
    st.markdown("""
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
    <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
        <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
        • Linha comparativa de <b>Cota Inicial (m)</b> e <b>Cota Dia (m)</b><br>
        • Filtros por <b>Data</b> e <b>Açude</b><br>
        • Linha de <b>Volume (m³)</b> ao longo do tempo
    </p>
</div>
""", unsafe_allow_html=True)

    df = load_simulacoes_data()
    if df.empty:
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

    with st.container():
        st.markdown('<div class="expander-rounded">', unsafe_allow_html=True)
        with st.expander("☰ Filtros (clique para expandir)", expanded=True):
            st.markdown('<div class="filter-card"><div class="filter-title">Filtros de Visualização</div>', unsafe_allow_html=True)
            c1, c2 = st.columns([2, 3])
            with c1:
                opcoes_acudes = sorted(df["Açude"].dropna().unique().tolist())
                acudes_sel = st.multiselect("Açude", options=opcoes_acudes, default=opcoes_acudes)
            with c2:
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

    dff = df.copy()
    if acudes_sel:
        dff = dff[dff["Açude"].isin(acudes_sel)]
    if periodo:
        if len(periodo) == 1:
            ini = fim = pd.to_datetime(periodo[0])
        else:
            ini, fim = [pd.to_datetime(d) for d in periodo]
        dff = dff[(dff["Data"] >= ini) & (dff["Data"] <= fim)]

    if dff.empty:
        st.info("Não há dados para os filtros selecionados.")
        return

    dff = dff.sort_values(["Açude", "Data"])

    st.subheader("📈 Cotas (Cota Inicial x Cota Dia)")
    fig_cotas = go.Figure()
    for acude in sorted(dff["Açude"].dropna().unique()):
        base = dff[dff["Açude"] == acude].sort_values("Data")
        fig_cotas.add_trace(go.Scatter(x=base["Data"], y=base["Cota Simulada (m)"], mode="lines+markers", name=f"{acude} - Cota Simulada (m)", hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"))
        fig_cotas.add_trace(go.Scatter(x=base["Data"], y=base["Cota Realizada (m)"], mode="lines+markers", name=f"{acude} - Cota Realizada (m)", hovertemplate="%{x|%d/%m/%Y} • %{y:.3f} m<extra></extra>"))
    fig_cotas.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), xaxis_title="Data", yaxis_title="Cota (m)", height=480)
    st.plotly_chart(fig_cotas, use_container_width=True, config={"displaylogo": False})

    st.subheader("📈 Volume (m³)")
    fig_vol = go.Figure()
    for acude in sorted(dff["Açude"].dropna().unique()):
        base = dff[dff["Açude"] == acude].sort_values("Data")
        fig_vol.add_trace(go.Scatter(x=base["Data"], y=base["Volume (m³)"], mode="lines+markers", name=f"{acude} - Volume (m³)", hovertemplate="%{x|%d/%m/%Y} • %{y:.2f} m³<extra></extra>"))
    fig_vol.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5), xaxis_title="Data", yaxis_title="Volume (m³)", height=420)
    st.plotly_chart(fig_vol, use_container_width=True, config={"displaylogo": False})

    # --- NOVO CÓDIGO ---
    st.subheader("📋 Tabela de Dados")
    with st.expander("Ver dados filtrados"):
        # Define as colunas a serem exibidas na ordem desejada
        colunas_tabela = [
            'Data',
            'Açude',
            'Município',
            'Região Hidrográfica',
            'Cota Simulada (m)',
            'Cota Realizada (m)',
            'Volume(m³)',
            'Volume (%)',
            'Evapor. Parcial(mm)',
            'Cota Interm. (m)',
            'Liberação (m³/s)',
            'Liberação (m³)',
            'Classificação',
            'Coordenadas'
        ]
        
        # Cria um novo DataFrame com apenas as colunas selecionadas
        dff_tabela = dff[colunas_tabela]
        
        # Exibe o DataFrame filtrado e com as colunas na ordem correta
        st.dataframe(dff_tabela.sort_values(["Açude", "Data"], ascending=[True, False]), use_container_width=True)
