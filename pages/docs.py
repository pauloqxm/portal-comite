import streamlit as st
import pandas as pd
import plotly.graph_objects as go 
import altair as alt
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

# --- Gráfico comparativo Operação x Vazão média (com Altair) ---
    st.markdown("---")
    st.subheader("📊 Comparativo: Operação x Vazão média")

    if "Operação" in df_filtrado.columns and "Vazão média" in df_filtrado.columns and not df_filtrado.empty:
        # Pré-processamento dos dados
        vazao_num = (
            df_filtrado["Vazão média"]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.extract(r"([-+]?\d*\.?\d+)")[0]
        )
        df_plot = df_filtrado.copy()
        df_plot["Vazão média (l/s)"] = pd.to_numeric(vazao_num, errors="coerce")
        df_plot = df_plot.dropna(subset=["Vazão média (l/s)"]).sort_values("Vazão média (l/s)", ascending=False)
        
        if not df_plot.empty:
            import altair as alt
            
            # Gráfico de barras interativo com Altair
            bars = alt.Chart(df_plot).mark_bar(
                cornerRadiusTop=5,
                size=20  # Largura das barras
            ).encode(
                x=alt.X('Operação:N', 
                      title='Operação',
                      sort='-y',  # Ordena pela vazão
                      axis=alt.Axis(labelAngle=0)),  # Rótulos horizontais
                y=alt.Y('Vazão média (l/s):Q', 
                      title='Vazão média (l/s)'),
                color=alt.Color('Vazão média (l/s):Q',
                              scale=alt.Scale(scheme='greens'),
                tooltip=['Operação', 'Vazão média (l/s)']
            ).properties(
                height=400,
                width=alt.Step(40)  # Controla o espaçamento entre barras
            )
            
            # Adiciona texto em cima das barras
            text = bars.mark_text(
                align='center',
                baseline='bottom',
                dy=-5,  # Ajusta posição vertical do texto
                fontSize=12,
                fontWeight='bold',
                color='#333'
            ).encode(
                text=alt.Text('Vazão média (l/s):Q', format='.1f')
            )
            
            # Combina os elementos
            chart = (bars + text).configure_view(
                strokeWidth=0  # Remove borda
            ).configure_axis(
                grid=False,
                domain=False
            ).configure_scale(
                bandPaddingInner=0.2  # Espaçamento entre barras
            )
            
            st.altair_chart(chart, use_container_width=True)
            
            # Legenda explicativa
            st.caption("""
            <style>
                .legenda-box {
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    padding: 10px;
                    margin-top: 10px;
                    border-left: 4px solid #228B22;
                }
            </style>
            <div class="legenda-box">
                <b>Análise:</b> Este gráfico compara a vazão média associada a cada operação. 
                As cores mais intensas indicam maiores valores de vazão.
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.info("Não há valores válidos de Vazão média para montar o gráfico.")
    else:
        st.info("Colunas 'Operação' e 'Vazão média' não encontradas na base de dados.")






