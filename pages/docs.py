import streamlit as st
import pandas as pd
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

    # ---------- Filtros ----------
    with st.container():
        st.markdown("**Filtrar documentos**")
        col1, col2 = st.columns(2)
        with col1:
            ops = ["Todos"] + (sorted(df["Operação"].dropna().astype(str).unique()) if "Operação" in df.columns else [])
            filtro_operacao = st.selectbox("Operação", ops, index=0)
        with col2:
            datas = ["Todos"] + (sorted(df["Data da Reunião"].dropna().astype(str).unique()) if "Data da Reunião" in df.columns else [])
            filtro_data = st.selectbox("Data da Reunião", datas, index=0)
        busca = st.text_input("Buscar em todos os campos", "")

    # ---------- Aplicação dos filtros ----------
    df_filtrado = df.copy()
    if filtro_operacao != "Todos" and "Operação" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Operação"].astype(str) == str(filtro_operacao)]
    if filtro_data != "Todos" and "Data da Reunião" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["Data da Reunião"].astype(str) == str(filtro_data)]
    if busca:
        busca_lower = busca.lower().strip()
        mask = df_filtrado.apply(lambda row: any(busca_lower in str(val).lower() for val in row.values), axis=1)
        df_filtrado = df_filtrado[mask]

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

# --- Gráfico comparativo por Operação (Vazão média x Nº de Reservatórios) ---
    st.markdown("---")
    st.subheader("Comparativo por Operação: Vazão média e Nº de Reservatórios")

    cols_ok = {"Operação", "Vazão média", "Reservatório/Sistema"}.issubset(df_filtrado.columns)
    if cols_ok and not df_filtrado.empty:
        # extrai parte numérica da 'Vazão média' (aceita vírgula e sufixos como 'l/s')
        vazao_num = (
            df_filtrado["Vazão média"]
            .astype(str)
            .str.replace(",", ".", regex=False)            # vírgula -> ponto
            .str.extract(r"([-+]?\d*\.?\d+)")[0]           # pega só o número
        )
        df_plot = df_filtrado.copy()
        df_plot["Vazão média (num)"] = pd.to_numeric(vazao_num, errors="coerce")

        grp = (
            df_plot.groupby("Operação", dropna=False).agg(
                vazao_media=("Vazão média (num)", "mean"),
                n_reservatorios=("Reservatório/Sistema", lambda s: s.astype(str).nunique())
            )
            .reset_index()
            .sort_values("vazao_media", ascending=False)
        )

        if not grp.empty:
            fig = go.Figure()
            # Barra: Vazão média (l/s)
            fig.add_trace(go.Bar(
                x=grp["Operação"],
                y=grp["vazao_media"],
                name="Vazão média (l/s)"
            ))
            # Linha: Nº de reservatórios (eixo secundário)
            fig.add_trace(go.Scatter(
                x=grp["Operação"],
                y=grp["n_reservatorios"],
                name="Nº de reservatórios",
                mode="lines+markers",
                yaxis="y2"
            ))

            fig.update_layout(
                template="plotly_white",
                margin=dict(l=10, r=10, t=10, b=10),
                height=420,
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                xaxis_title="Operação",
                yaxis=dict(title="Vazão média (l/s)"),
                yaxis2=dict(title="Nº de reservatórios", overlaying="y", side="right", showgrid=False),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False})
        else:
            st.info("Sem dados suficientes para montar o gráfico.")
    else:
        st.info("Não foi possível montar o gráfico. Verifique se as colunas 'Operação', 'Vazão média' e 'Reservatório/Sistema' existem.")



