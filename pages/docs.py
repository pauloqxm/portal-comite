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

# --- GRÁFICO DE BARRAS VERTICAIS COM INFORMAÇÕES COMPLETAS ---
    st.markdown("---")
    st.subheader("📊 Comparativo: Operação x Vazão média por Reservatório")

    if all(col in df_filtrado.columns for col in ["Operação", "Vazão média", "Reservatório"]) and not df_filtrado.empty:
        try:
            # Pré-processamento seguro
            df_plot = df_filtrado[["Operação", "Vazão média", "Reservatório"]].copy()
            
            # Converter vazão para numérico
            df_plot["Vazão (l/s)"] = (
                df_plot["Vazão média"]
                .astype(str)
                .str.replace(",", ".")
                .str.extract(r"(\d+\.?\d*)")[0]
                .astype(float)
            ).dropna()
            
            if not df_plot.empty:
                # Configurações de formatação adaptáveis
                formato = {
                    'tamanho_fonte': 10,          # Tamanho da fonte do texto
                    'max_caracteres': 18,         # Máximo de caracteres para o nome do reservatório
                    'altura_grafico': 700,        # Altura total do gráfico
                    'margem_inferior': 180        # Margem para caber textos
                }
                
                # Ordenar por vazão (maior para menor)
                df_plot = df_plot.sort_values("Vazão (l/s)", ascending=False)
                
                # Formatar texto das barras (vazão + reservatório abreviado)
                df_plot["Texto_Barras"] = df_plot.apply(
                    lambda row: (
                        f"{row['Vazão (l/s)']:.1f} l/s<br>"
                        f"({row['Reservatório'][:formato['max_caracteres']]}"
                        f"{'...' if len(row['Reservatório']) > formato['max_caracteres'] else ''})"
                    ), axis=1
                )
                
                # Paleta de cores otimizada
                color_scale = [
                    [0.0, '#e5f5e0'], [0.3, '#a1d99b'],
                    [0.6, '#31a354'], [1.0, '#006d2c']
                ]
                
                # Criar figura
                fig = go.Figure()
                
                # Adicionar barras com informações completas
                fig.add_trace(go.Bar(
                    x=df_plot["Operação"],
                    y=df_plot["Vazão (l/s)"],
                    marker=dict(
                        color=df_plot["Vazão (l/s)"],
                        colorscale=color_scale,
                        cmin=max(0, df_plot["Vazão (l/s)"].min() * 0.8),
                        cmax=df_plot["Vazão (l/s)"].max() * 1.1,
                        line=dict(width=1, color='#333333')
                    ),
                    text=df_plot["Texto_Barras"],
                    textposition="outside",
                    textfont=dict(
                        size=formato['tamanho_fonte'],
                        color='#333333'
                    ),
                    hovertemplate=(
                        "<b>Operação:</b> %{x}<br>"
                        "<b>Vazão:</b> %{y:.1f} l/s<br>"
                        "<b>Reservatório Completo:</b> %{customdata}<br>"
                        "<extra></extra>"
                    ),
                    customdata=df_plot["Reservatório"]
                ))
                
                # Layout profissional
                fig.update_layout(
                    template="plotly_white",
                    height=formato['altura_grafico'],
                    xaxis=dict(
                        title="Operação",
                        tickangle=-45,
                        type="category",
                        categoryorder="total descending",
                        tickfont=dict(size=12)
                    ),
                    yaxis=dict(
                        title="Vazão Média (l/s)",
                        gridcolor='#f0f0f0',
                        zeroline=False
                    ),
                    margin=dict(
                        l=50, 
                        r=50, 
                        t=80, 
                        b=formato['margem_inferior']
                    ),
                    hoverlabel=dict(
                        bgcolor="white",
                        font_size=12,
                        font_family="Arial"
                    ),
                    uniformtext=dict(
                        minsize=8,
                        mode='hide'
                    )
                )
                
                # Exibir gráfico
                st.plotly_chart(fig, use_container_width=True)
                
                # Legenda explicativa
                st.markdown("""
                <style>
                    .info-box {
                        background-color: #f8f9fa;
                        border-radius: 5px;
                        padding: 12px;
                        margin-top: 10px;
                        border-left: 4px solid #228B22;
                        font-size: 14px;
                        line-height: 1.5;
                    }
                    .info-box b {
                        color: #228B22;
                    }
                </style>
                <div class="info-box">
                    <b>Como interpretar:</b><br>
                    • Cada barra mostra a <b>vazão em litros/segundo (l/s)</b><br>
                    • Entre parênteses aparece o <b>reservatório associado</b> (nomes longos são abreviados)<br>
                    • Passe o mouse sobre as barras para ver o nome completo do reservatório
                </div>
                """, unsafe_allow_html=True)
                
            else:
                st.warning("Não foram encontrados valores numéricos válidos para exibição.")
                
        except Exception as e:
            st.error(f"Erro ao gerar visualização: {str(e)}")
    else:
        st.info("""
        Dados necessários não encontrados. Verifique se existem as colunas:
        - 'Operação'
        - 'Vazão média' 
        - 'Reservatório'
        """)
