import streamlit as st
import pandas as pd
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

    # Carrega dados
    df = load_docs_data()
    if df is None or df.empty:
        st.info("Não há documentos disponíveis no momento.")
        return

    # Garante as colunas esperadas (evita KeyError)
    expected_cols = [
        "Operação",
        "Reservatório/Sistema",
        "Data da Reunião",
        "Local da Reunião",
        "Parâmetros aprovados",
        "Vazão média",
        "Apresentação",
        "Ata da Reunião",
    ]
    for c in expected_cols:
        if c not in df.columns:
            df[c] = pd.NA

    # Normaliza/parse de data + coluna formatada para exibição e filtro
    # Mantém strings originais se não parsear
    df["_Data_dt"] = pd.to_datetime(df["Data da Reunião"], errors="coerce", dayfirst=True)
    df["_Data_fmt"] = df["_Data_dt"].dt.strftime("%d/%m/%Y")
    # quando não parseou, use o valor original (como string)
    mask_na = df["_Data_dt"].isna()
    df.loc[mask_na, "_Data_fmt"] = df.loc[mask_na, "Data da Reunião"].astype(str)

    # ========== Filtros ==========
    with st.container():
        st.markdown("**Filtrar documentos**")
        col1, col2 = st.columns(2)
        with col1:
            if df["Operação"].notna().any():
                ops_unicas = sorted([x for x in df["Operação"].dropna().astype(str).unique().tolist()])
            else:
                ops_unicas = []
            ops = ["Todos"] + ops_unicas
            filtro_operacao = st.selectbox("Operação", ops, index=0)

        with col2:
            # únicas datas formatadas (sem NaN), ordenadas por valor datetime quando possível
            # criamos pares (dt, fmt) para ordenar por dt e exibir fmt
            date_pairs = df[["_Data_dt", "_Data_fmt"]].drop_duplicates()
            # primeiro as que têm datetime, ordenadas; depois as sem datetime, ordenadas alfab.
            com_dt = date_pairs[date_pairs["_Data_dt"].notna()].sort_values("_Data_dt")
            sem_dt = date_pairs[date_pairs["_Data_dt"].isna()].sort_values("_Data_fmt")
            datas_fmt_ordenadas = com_dt["_Data_fmt"].tolist() + sem_dt["_Data_fmt"].tolist()
            datas = ["Todos"] + datas_fmt_ordenadas
            filtro_data = st.selectbox("Data da Reunião", datas, index=0)

        busca = st.text_input("Buscar em todos os campos", "")

    # ========== Aplicação dos filtros ==========
    df_filtrado = df.copy()

    if filtro_operacao != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Operação"].astype(str) == str(filtro_operacao)]

    if filtro_data != "Todos":
        # compara com a coluna formatada (textual) para robustez
        df_filtrado = df_filtrado[df_filtrado["_Data_fmt"].astype(str) == str(filtro_data)]

    if busca:
        busca_lower = busca.lower().strip()
        # busca em todas as colunas relevantes (inclui a data formatada)
        cols_busca = [
            "Operação", "Reservatório/Sistema", "Data da Reunião", "Local da Reunião",
            "Parâmetros aprovados", "Vazão média", "Apresentação", "Ata da Reunião", "_Data_fmt"
        ]
        cols_busca = [c for c in cols_busca if c in df_filtrado.columns]
        mask = df_filtrado[cols_busca].apply(
            lambda s: s.astype(str).str.lower().str.contains(busca_lower, na=False)
        ).any(axis=1)
        df_filtrado = df_filtrado[mask]

    st.markdown(f"**{len(df_filtrado)} registros encontrados**")

    # ========== Tabela HTML ==========
    table_style = """
    <style>
    .table-container { overflow: auto; margin: 1rem 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: center; }
    th { background-color: #f8f9fa; position: sticky; top: 0; z-index: 1; }
    .download-btn { display: inline-block; padding: 4px 10px; background: #28a745; color: white !important; border-radius: 4px; text-decoration: none; font-size: 13px; }
    .no-data { color: #6c757d; font-style: italic; padding: 1rem; }
    </style>
    """
    table_html = f"""{table_style}
    <div class="table-container"><table>
    <thead><tr>
        <th>Operação</th><th>Reservatório</th><th>Data</th><th>Local</th>
        <th>Parâmetros</th><th>Vazão</th><th>Apresentação</th><th>Ata</th>
    </tr></thead><tbody>"""

    if not df_filtrado.empty:
        for _, row in df_filtrado.iterrows():
            # Valores brutos
            op  = row.get("Operação", "")
            res = row.get("Reservatório/Sistema", "")
            # usa a data formatada (já robusta)
            data_fmt = row.get("_Data_fmt", "")  
            loc = row.get("Local da Reunião", "")
            par = row.get("Parâmetros aprovados", "")
            vaz = row.get("Vazão média", "")
            url_apres = row.get("Apresentação", "")
            url_ata   = row.get("Ata da Reunião", "")

            # Escape para evitar quebrar o HTML
            op_e  = html.escape("" if pd.isna(op) else str(op))
            res_e = html.escape("" if pd.isna(res) else str(res))
            data_e= html.escape("" if pd.isna(data_fmt) else str(data_fmt))
            loc_e = html.escape("" if pd.isna(loc) else str(loc))
            par_e = html.escape("" if pd.isna(par) else str(par))
            # Vazão: formata se for número; caso contrário, mostra como string
            try:
                vaz_num = pd.to_numeric(vaz, errors="coerce")
                vaz_e = f"{vaz_num:,.3f}".replace(",", "X").replace(".", ",").replace("X", ".") if pd.notna(vaz_num) else html.escape("" if pd.isna(vaz) else str(vaz))
            except Exception:
                vaz_e = html.escape("" if pd.isna(vaz) else str(vaz))

            # Botões de download (só se houver URL não vazia)
            def _btn(url):
                if pd.isna(url):
                    return "—"
                u = str(url).strip()
                if not u or u.lower() in ("nan", "none", "null", "-"):
                    return "—"
                return f'<a class="download-btn" href="{html.escape(u)}" target="_blank" rel="noopener">Baixar</a>'

            btn_apres = _btn(url_apres)
            btn_ata   = _btn(url_ata)

            table_html += (
                "<tr>"
                f"<td>{op_e}</td>"
                f"<td>{res_e}</td>"
                f"<td>{data_e}</td>"
                f"<td>{loc_e}</td>"
                f"<td>{par_e}</td>"
                f"<td>{vaz_e}</td>"
                f"<td>{btn_apres}</td>"
                f"<td>{btn_ata}</td>"
                "</tr>"
            )
    else:
        table_html += '<tr><td colspan="8" class="no-data">Nenhum registro encontrado</td></tr>'

    table_html += "</tbody></table></div>"
    st.markdown(table_html, unsafe_allow_html=True)
