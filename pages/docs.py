import streamlit as st
import pandas as pd
import plotly.graph_objects as go 
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
            filtro_data = st.multiselect("Data da Reunião", datas_opts, default=datas_opts)

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
            vaz  = escape("" if pd.isna(row.get("Vazão média")) else str(row.get("Vazão média")))
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

# --- Gráfico comparativo Operação x Vazão média (sem agrupar) ---
    st.markdown("---")
    st.subheader("Comparativo: Operação x Vazão média")

    if "Operação" in df_filtrado.columns and "Vazão média" in df_filtrado.columns and not df_filtrado.empty:
        # limpar valores da coluna Vazão média (tirar textos como 'l/s')
        vazao_num = (
            df_filtrado["Vazão média"]
            .astype(str)
            .str.replace(",", ".", regex=False)            # vírgula -> ponto
            .str.extract(r"([-+]?\d*\.?\d+)")[0]           # captura apenas o número
        )
        df_plot = df_filtrado.copy()
        df_plot["Vazão média (num)"] = pd.to_numeric(vazao_num, errors="coerce")

        # remover linhas sem valor numérico
        df_plot = df_plot.dropna(subset=["Vazão média (num)"])

        if not df_plot.empty:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=df_plot["Operação"],
                y=df_plot["Vazão média (num)"],
                text=df_plot["Vazão média (num)"].round(1),
                textposition="outside",
                marker_color="#228B22",
                name="Vazão média"
            ))
            fig.update_layout(
                template="plotly_white",
                height=420,
                margin=dict(l=10, r=10, t=30, b=10),
                xaxis_title="Operação",
                yaxis_title="Vazão média (l/s)",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Não há valores válidos de Vazão média para montar o gráfico.")
    else:
        st.info("Colunas 'Operação' e 'Vazão média' não encontradas na base de dados.")


