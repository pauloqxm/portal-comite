
import streamlit as st
import pandas as pd
from utils.common import render_header

st.set_page_config(page_title="📜 Documentos Oficiais", layout="wide")
render_header()

st.title("📜 Documentos para Download")

SHEET_ID = "1-Tn_ZDHH-mNgJAY1WtjWd_Pyd2f5kv_ZU8dhL0caGDI"
GID = "0"
URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

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
    """, unsafe_allow_html=True,
)

@st.cache_data(ttl=3600)
def load_data():
    try:
        df = pd.read_csv(URL, encoding="utf-8-sig").dropna(how="all")
        for col in ["Operação","Data da Reunião","Reservatório/Sistema","Local da Reunião","Parâmetros aprovados","Vazão média"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return pd.DataFrame()

df = load_data()

with st.container():
    st.markdown("**Filtrar documentos**")
    col1, col2 = st.columns(2)
    with col1:
        ops = ["Todos"] + sorted(df["Operação"].unique()) if "Operação" in df.columns else ["Todos"]
        filtro_operacao = st.selectbox("Operação", ops, index=0)
    with col2:
        datas = ["Todos"] + sorted(df["Data da Reunião"].unique()) if "Data da Reunião" in df.columns else ["Todos"]
        filtro_data = st.selectbox("Data da Reunião", datas, index=0)
    busca = st.text_input("Buscar em todos os campos", "")

df_filtrado = df.copy()
if filtro_operacao != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Operação"] == filtro_operacao]
if filtro_data != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Data da Reunião"] == filtro_data]
if busca:
    busca_lower = busca.lower().strip()
    mask = df_filtrado.apply(lambda row: any(busca_lower in str(val).lower() for val in row.values), axis=1)
    df_filtrado = df_filtrado[mask]

st.markdown(f"**{len(df_filtrado)} registros encontrados**")

table_style = """
<style>
.table-container { overflow: auto; margin: 1rem 0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: center; }
th { background-color: #f8f9fa; position: sticky; top: 0; }
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
        cells = [
            row.get("Operação", ""),
            row.get("Reservatório/Sistema", ""),
            row.get("Data da Reunião", ""),
            row.get("Local da Reunião", ""),
            row.get("Parâmetros aprovados", ""),
            row.get("Vazão média", ""),
            row.get("Apresentação", ""),
            row.get("Ata da Reunião", "")
        ]
        for i in [6, 7]:
            if not cells[i] or str(cells[i]).lower() in ["nan", "none", ""]:
                cells[i] = "—"
            else:
                cells[i] = f'<a class="download-btn" href="{cells[i]}" target="_blank">Baixar</a>'
        table_html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in cells) + "</tr>"
else:
    table_html += '<tr><td colspan="8" class="no-data">Nenhum registro encontrado</td></tr>'

table_html += "</tbody></table></div>"
st.markdown(table_html, unsafe_allow_html=True)
