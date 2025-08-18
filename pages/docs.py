
import streamlit as st
import pandas as pd
import plotly.graph_objects as go 
import plotly.express as px
from html import escape
from utils.common import load_docs_data

def render_docs():
    st.title("📜 Documentos para Download")
    st.markdown(
        """
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Atas e apresentações das reuniões da Bacia do Banabuiú<br>
    • Organizadas por operação, reservatório e parâmetros<br>
    • Dados de vazão média aprovados
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    df = load_docs_data()
    if df is None or df.empty:
        st.info("Não há documentos disponíveis no momento.")
        return

# ---------- Filtros (com cartão de cantos arredondados + multiselect) ----------
    st.markdown("""
    <style>
    .filter-card {
      border: 1px solid #e6e6e6;
      border-radius: 14px;
      padding: 14px;
      background: linear-gradient(180deg,#ffffff 0%, #fafafa 100%);
      box-shadow: 0 6px 16px rgba(0,0,0,.06);
      margin: 6px 0 16px 0;
    }
    .filter-title { font-weight:700; color:#006400; margin-bottom:8px; letter-spacing:.2px; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="filter-card">', unsafe_allow_html=True)
        st.markdown('<div class="filter-title">Filtrar documentos</div>', unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        # Opções únicas (como string) e ordenadas
        ops_opts = sorted(df["Operação"].dropna().astype(str).unique()) if "Operação" in df.columns else []
        datas_opts = sorted(df["Data da Reunião"].dropna().astype(str).unique()) if "Data da Reunião" in df.columns else []
        reserv_opts = sorted(df["Reservatório/Sistema"].dropna().astype(str).unique()) if "Reservatório/Sistema" in df.columns else []

        with col1:
            filtro_operacao = st.multiselect("Operação", ops_opts, default=ops_opts)

        with col2:
            filtro_data = st.selectbox("Data da Reunião", ["Todos"] + (sorted(df["Data da Reunião"].dropna().astype(str).unique()) if "Data da Reunião" in df.columns else []), index=None, placeholder="Selecione...")

        with col3:
            filtro_reservatorio = st.multiselect("Reservatório/Sistema", reserv_opts, default=reserv_opts)

        busca = st.text_input("Buscar em todos os campos", "")

        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Aplicação dos filtros ----------
    df_filtrado = df.copy()

    # Filtra por Operação
    if filtro_operacao and "Operação" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Operação"].astype(str).isin([str(x) for x in filtro_operacao])]

    # Filtra por Data
    if filtro_data and "Data da Reunião" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Data da Reunião"].astype(str).isin([str(x) for x in filtro_data])]

    # Filtra por Reservatório/Sistema
    if filtro_reservatorio and "Reservatório/Sistema" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Reservatório/Sistema"].astype(str).isin([str(x) for x in filtro_reservatorio])]

    # Busca textual em todas as colunas
    if busca:
        busca_lower = busca.lower().strip()
        df_filtrado = df_filtrado[
            df_filtrado.apply(lambda row: any(busca_lower in str(val).lower() for val in row.values), axis=1)
        ]

    st.markdown(f"**{len(df_filtrado)} registros encontrados**")

# ---------- Estilos (sem indentação no início!) ----------
    table_style = (
        "<style>"
        ".table-container{overflow:auto;margin:1rem 0;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);} "
        "table{width:100%;border-collapse:collapse;font-size:14px;} "
        "th,td{border:1px solid #ddd;padding:8px 12px;text-align:center;} "
        "th{background-color:#f8f9fa;position:sticky;top:0;z-index:1;} "
        ".download-btn{display:inline-block;padding:4px 10px;background:#28a745;color:#fff!important;border-radius:4px;text-decoration:none;font-size:13px;} "
        ".no-data{color:#6c757d;font-style:italic;padding:1rem;}"
        "</style>"
    )

    # ---------- Cabeçalho da tabela ----------
    parts = []
    parts.append(table_style)
    parts.append('<div class="table-container"><table>')
    parts.append(
        "<thead><tr>"
        "<th>Operação</th><th>Reservatório</th><th>Data</th><th>Local</th>"
        "<th>Parâmetros</th><th>Vazão</th><th>Apresentação</th><th>Ata</th>"
        "</tr></thead><tbody>"
    )

# ---------- Linhas ----------
    if not df_filtrado.empty:
        for _, row in df_filtrado.iterrows():
            op   = escape("" if pd.isna(row.get("Operação")) else str(row.get("Operação")))
            res  = escape("" if pd.isna(row.get("Reservatório/Sistema")) else str(row.get("Reservatório/Sistema")))
            data = escape("" if pd.isna(row.get("Data da Reunião")) else str(row.get("Data da Reunião")))
            loc  = escape("" if pd.isna(row.get("Local da Reunião")) else str(row.get("Local da Reunião")))
            par  = escape("" if pd.isna(row.get("Parâmetros aprovados")) else str(row.get("Parâmetros aprovados")))

            # 👉 Formatação da coluna Vazão média
            if pd.isna(row.get("Vazão média")) or str(row.get("Vazão média")).strip() in ("", "nan", "None", "null"):
                vaz = ""
            else:
                try:
                    vaz_num = float(row.get("Vazão média"))
                    vaz = f"{int(vaz_num):,}".replace(",", ".") + " l/s"
                except:
                    vaz = escape(str(row.get("Vazão média")))

            apr  = row.get("Apresentação", "")
            ata  = row.get("Ata da Reunião", "")

            def linkify(u):
                if pd.isna(u):
                    return "—"
                u = str(u).strip()
                if not u or u.lower() in ("nan", "none", "null", "-"):
                    return "—"
                return f'<a class="download-btn" href="{escape(u)}" target="_blank" rel="noopener">Baixar</a>'

            parts.append(
                "<tr>"
                f"<td>{op}</td><td>{res}</td><td>{data}</td><td>{loc}</td>"
                f"<td>{par}</td><td>{vaz}</td><td>{linkify(apr)}</td><td>{linkify(ata)}</td>"
                "</tr>"
            )
    else:
        parts.append('<tr><td colspan="8" class="no-data">Nenhum registro encontrado</td></tr>')


    # ---------- Fechamento ----------
    parts.append("</tbody></table></div>")
    table_html = "".join(parts)

    # Renderiza como HTML (sem virar bloco de código)
    st.markdown(table_html, unsafe_allow_html=True)

# --- GRÁFICO DE BARRAS VERTICAIS OTIMIZADO ---
    st.markdown("---")
    st.subheader("📊 Comparativo: Operação x Vazão média (Barras Verticais)")

    # Verificação se as colunas necessárias existem
    if all(col in df_filtrado.columns for col in ["Operação", "Vazão média", "Reservatório/Sistema"]) and not df_filtrado.empty:
        try:
            # Pré-processamento dos dados
            df_plot = df_filtrado[["Operação", "Vazão média", "Reservatório/Sistema"]].copy()
            
            # Converte a vazão para l/s
            df_plot["Vazão (l/s)"] = (
                df_plot["Vazão média"]
                .astype(str)
                .str.replace(",", ".")
                .str.extract(r"(\d+\.?\d*)")[0]
                .astype(float)
            )
            
            # Remove linhas com valores inválidos e agrupa por reservatório para a média
            df_grouped = df_plot.dropna(subset=["Vazão (l/s)"]).groupby(
                ["Operação", "Reservatório/Sistema"], as_index=False
            )["Vazão (l/s)"].mean()
            
            if not df_grouped.empty:
                # Ordena por vazão total para o eixo X
                df_grouped_total = df_grouped.groupby("Operação")["Vazão (l/s)"].sum().sort_values(ascending=False).index
                
                fig = go.Figure()

                # Configuração do gradiente de cores
                color_scale = [
                    [0.0, '#e5f5e0'],  # Verde muito claro
                    [0.2, '#a1d99b'],  # Verde claro
                    [0.5, '#74c476'],  # Verde médio
                    [0.8, '#31a354'],  # Verde escuro
                    [1.0, '#006d2c']   # Verde muito escuro
                ]
                
                # Adiciona um "trace" para cada reservatório
                reservatorios_ordenados = sorted(df_grouped["Reservatório/Sistema"].unique())
                
                for reservatorio in reservatorios_ordenados:
                    df_res = df_grouped[df_grouped["Reservatório/Sistema"] == reservatorio]
                    fig.add_trace(go.Bar(
                        x=df_res["Operação"],
                        y=df_res["Vazão (l/s)"],
                        name=reservatorio,
                        marker=dict(
                            color=df_res["Vazão (l/s)"],
                            colorscale=color_scale,
                            cmin=max(0, df_grouped["Vazão (l/s)"].min() * 0.8),
                            cmax=df_grouped["Vazão (l/s)"].max() * 1.1,
                            line=dict(width=1, color='#333333'),
                            showscale=False # Desativa a barra lateral de cor
                        ),
                        hovertemplate="<b>Operação: %{x}</b><br>Reservatório: "+reservatorio+"<br>Vazão: %{y:.1f} l/s<extra></extra>"
                    ))
                
                # Layout otimizado
                fig.update_layout(
                    barmode='stack', # Define o modo empilhado para todos os traces
                    template="plotly_white",
                    xaxis=dict(
                        title="Operação",
                        tickangle=-45,
                        tickfont=dict(size=12),
                        categoryorder="array",
                        categoryarray=df_grouped_total
                    ),
                    yaxis=dict(
                        title="Vazão Média Acumulada (l/s)",
                        gridcolor='#f0f0f0'
                    ),
                    margin=dict(l=50, r=50, t=80, b=150),
                    legend=dict(
                        title="Reservatório",
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="right",
                        x=1.1
                    ),
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Legenda explicativa
                st.markdown("""
                <style>
                    .legenda-box {
                        background-color: #f8f9fa;
                        border-radius: 5px;
                        padding: 12px;
                        margin-top: 10px;
                        border-left: 4px solid #228B22;
                        font-size: 14px;
                    }
                    .legenda-box b {
                        color: #228B22;
                    }
                </style>
                <div class="legenda-box">
                    <b>Interpretação:</b> Cada barra representa uma operação, e as seções coloridas dentro dela correspondem à vazão média de cada reservatório, empilhadas. A altura total da barra é a vazão média total daquela operação. A intensidade do verde corresponde ao valor da vazão de cada reservatório (tons mais escuros = maiores valores).
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.warning("Não foram encontrados valores numéricos válidos na coluna 'Vazão média'.")
                
        except Exception as e:
            st.error(f"Erro ao processar os dados: {str(e)}")
    else:
        st.info("Dados insuficientes. Verifique se as colunas 'Operação', 'Vazão média' e 'Reservatório/Sistema' existem no dataset.")
