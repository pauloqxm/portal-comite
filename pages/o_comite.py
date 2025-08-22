import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import unicodedata
import plotly.express as px
from branca.element import CssLink

def render_o_comite():
    st.title("🙋🏽 O Comitê")
    st.markdown(
        """
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 12px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Listagem dos representantes com filtros e busca<br>
    • Mapa categorizado por <b>Segmento</b> + troca de mapa de fundo (cluster + heatmap)<br>
    • Distribuição por <b>Segmento</b> e <b>Município</b>
  </p>
</div>
""",
        unsafe_allow_html=True,
    )

    # ===== Compacta margens/espacamentos =====
    st.markdown(
        """
        <style>
          /* compacta headers e hr */
          div[data-testid="stMarkdownContainer"] h3 { margin: .25rem 0 .5rem 0 !important; }
          hr { margin: .5rem 0 !important; }
          /* reduz padding lateral em telas pequenas */
          @media (max-width: 900px){
            section.main > div.block-container { padding-left: .6rem; padding-right: .6rem; }
            div[data-testid="column"] { width: 100% !important; }
          }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ===== Fonte: Planilha =====
    SHEET_ID = "14Hb7N5yq4u-B3JN8Stpvpbdlt3sL0JxWUYpJK4fzLV8"
    GID = "1572572584"
    CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

    @st.cache_data(show_spinner=False)
    def load_data(url: str) -> pd.DataFrame:
        df = pd.read_csv(url, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        for c in df.columns:
            df[c] = df[c].astype(str).str.strip()

        # Datas (opcional)
        for c in ["Inicio do mandato", "Fim do mandato"]:
            if c in df.columns:
                df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)

        # Coordenadas → Latitude/Longitude
        if "Coordenadas" in df.columns:
            coords = (
                df["Coordenadas"]
                .astype(str).str.strip()
                .str.replace(";", ",", regex=False)
                .str.replace("[()\\[\\]]", "", regex=True)
            )
            parts = coords.str.split(",", n=1, expand=True)
            if parts.shape[1] == 2:
                df["Latitude"]  = pd.to_numeric(parts[0].str.replace(" ", ""), errors="coerce")
                df["Longitude"] = pd.to_numeric(parts[1].str.replace(" ", ""), errors="coerce")
            else:
                df["Latitude"] = pd.NA
                df["Longitude"] = pd.NA
        else:
            df["Latitude"] = pd.NA
            df["Longitude"] = pd.NA

        # Nome curto (dois primeiros)
        if "Nome do(a) representante" in df.columns:
            def dois_primeiros(nm: str) -> str:
                parts = [p for p in (nm or "").split() if p]
                return " ".join(parts[:2]) if parts else nm
            df["Nome (2)"] = df["Nome do(a) representante"].apply(dois_primeiros)

        return df

    df = load_data(CSV_URL)
    if df is None or df.empty:
        st.info("Planilha vazia ou inacessível.")
        return

    # ===== Filtros =====
    st.markdown("### 🔎 Filtros")
    fc1, fc2, fc3, fc4 = st.columns(4)

    def options(colname: str):
        if colname not in df.columns: return []
        col = df[colname].dropna().astype(str).str.strip()
        return sorted([x for x in col.unique() if x != ""])

    with fc1:
        seg_sel = st.multiselect("Segmento", options("Segmento"), default=options("Segmento"))
    with fc2:
        mun_sel = st.multiselect("Município", options("Município"), default=options("Município"))
    with fc3:
        man_sel = st.multiselect("Mandato", options("Mandato"), default=options("Mandato"))
    with fc4:
        fun_sel = st.multiselect("Função", options("Função"), default=options("Função"))

    # Busca por nome (ignora acentos)
    def normalize(s: str) -> str:
        return "".join(ch for ch in unicodedata.normalize("NFKD", (s or "").lower()) if not unicodedata.combining(ch))
    nome_query = st.text_input("Pesquisar por nome", placeholder="Digite parte do nome…").strip()

    dff = df.copy()
    if seg_sel and "Segmento" in dff:   dff = dff[dff["Segmento"].isin(seg_sel)]
    if mun_sel and "Município" in dff:  dff = dff[dff["Município"].isin(mun_sel)]
    if man_sel and "Mandato" in dff:    dff = dff[dff["Mandato"].isin(man_sel)]
    if fun_sel and "Função" in dff:     dff = dff[dff["Função"].isin(fun_sel)]
    if nome_query and "Nome do(a) representante" in dff.columns:
        nq = normalize(nome_query)
        dff = dff[dff["Nome do(a) representante"].apply(lambda x: nq in normalize(str(x)))]

    if dff.empty:
        st.warning("Sem registros para os filtros selecionados.")
        return

    # ===== Download dos filtrados =====
    dl_cols = st.columns([1,1,1,1])
    with dl_cols[-1]:
        csv_bytes = dff.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Baixar CSV (filtrados)", data=csv_bytes, file_name="comite_filtrado.csv", mime="text/csv", use_container_width=True)

    # ===== Tabela & Mapa (lado a lado — gap pequeno) =====
    col_tab, col_map = st.columns([0.48, 0.52], gap="small")

    with col_tab:
        st.subheader("📑 Representantes")
        cols_tabela = ["Nome (2)", "Sigla", "Função", "Segmento", "Diretoria"]
        cols_exist = [c for c in cols_tabela if c in dff.columns]
        if not cols_exist:
            st.info("As colunas esperadas não foram encontradas.")
        else:
            tab = dff[cols_exist].rename(columns={"Nome (2)": "Nome"}).sort_values(by="Nome")
            # altura pareada com o mapa para evitar “buraco” visual
            st.dataframe(tab, use_container_width=True, hide_index=True, height=720)

#====================== MAPA (sem cluster/heatmap) =============
    with col_map:
        st.subheader("🗺️ Mapa dos Representantes")

        # CSS do Font Awesome (para ícones)
        font_awesome_css = CssLink('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css')

        tile_option = st.selectbox(
            "Mapa de fundo",
            ["OpenStreetMap", "CartoDB positron", "Stamen Terrain", "CartoDB dark_matter", "Esri Satellite"],
            index=0
        )

        have_geo = {"Latitude", "Longitude"}.issubset(dff.columns)
        pontos = dff.dropna(subset=["Latitude", "Longitude"]) if have_geo else pd.DataFrame()

        if pontos.empty:
            st.info("Sem coordenadas válidas para exibir no mapa.")
        else:
            # Centro no Ceará
            center = [-5.5, -39.5]
            zoom_start = 7

            m = folium.Map(location=center, zoom_start=zoom_start, tiles=None)
            m.get_root().header.add_child(font_awesome_css)

            tile_config = {
                "CartoDB positron": (
                    "https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
                    '&copy; <a href="https://carto.com/attributions">CARTO</a>'
                ),
                "OpenStreetMap": ("OpenStreetMap", '&copy; <a href="https://openstreetmap.org">OSM</a>'),
                "Stamen Terrain": (
                    "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
                    'Map tiles by <a href="http://stamen.com">Stamen</a>'
                ),
                "CartoDB dark_matter": (
                    "https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
                    '&copy; <a href="https://carto.com/attributions">CARTO</a>'
                ),
                "Esri Satellite": (
                    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                    "Tiles &copy; Esri"
                ),
            }
            tiles, attr = tile_config[tile_option]
            folium.TileLayer(tiles=tiles, attr=attr, name=tile_option, control=True).add_to(m)

            # Paleta por Segmento
            seg_unicos = [s for s in pontos["Segmento"].dropna().unique()]
            palette = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
                      "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"]
            color_map = {seg: palette[i % len(palette)] for i, seg in enumerate(seg_unicos)}
            default_color = "#7f7f7f"

            # Camadas por segmento
            groups = {seg: folium.FeatureGroup(name=f"Segmento: {seg}", show=True) for seg in seg_unicos}
            groups["_sem_segmento"] = folium.FeatureGroup(name="Segmento: (vazio)", show=True)

            # Ícones (font-awesome) por segmento
            icon_config = {
                "agric": "tractor",
                "indús": "industry",
                "comér": "shopping-cart",
                "serv":  "cogs",
                "gover": "landmark",
                "educ":  "graduation-cap",
                "saúd":  "heart",
                "ambient": "leaf",
                "comun": "users",
            }
            def pick_icon(seg: str) -> str:
                s = (seg or "").lower()
                for k, v in icon_config.items():
                    if k in s:
                        return v
                return "user"

            # Marcadores simples (sem cluster/heatmap)
            for _, row in pontos.iterrows():
                try:
                    lat = float(row["Latitude"]); lon = float(row["Longitude"])
                except Exception:
                    continue

                segm = (row.get("Segmento", "") or "").strip() or "(vazio)"
                grp_key = segm if segm in groups else ("_sem_segmento" if segm == "(vazio)" else segm)
                if grp_key not in groups:
                    groups[grp_key] = folium.FeatureGroup(name=f"Segmento: {segm}", show=True)

                nome_full = row.get("Nome do(a) representante", "N/A")
                nome_2 = row.get("Nome (2)", nome_full)
                sigla = row.get("Sigla", row.get("Instituição", "N/A"))
                func  = row.get("Função", "N/A")
                mun   = row.get("Município", "N/A")
                mandato = row.get("Mandato", "N/A")
                diretoria = row.get("Diretoria", "N/A")
                telefone = row.get("Telefone", "N/A")
                email = row.get("E-mail", "N/A")

                color = color_map.get(segm, default_color)
                icon_name = pick_icon(segm)

                popup_html = f"""
                <div style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6;">
                    <div style="background-color: {color}; color: white; padding: 10px; margin: -10px -10px 10px -10px; border-radius: 5px 5px 0 0;">
                        <h3 style="margin:0; padding:0; font-size: 16px;">{nome_full}</h3>
                    </div>
                    <div style="padding: 5px 0;">
                        <p style="margin: 5px 0;"><strong>🏢 Sigla:</strong> {sigla}</p>
                        <p style="margin: 5px 0;"><strong>💼 Função:</strong> {func}</p>
                        <p style="margin: 5px 0;"><strong>📊 Segmento:</strong> <span style="color: {color}; font-weight: bold;">{segm}</span></p>
                        <p style="margin: 5px 0;"><strong>👥 Diretoria:</strong> {diretoria}</p>
                        <p style="margin: 5px 0;"><strong>🏙️ Município:</strong> {mun}</p>
                        <p style="margin: 5px 0;"><strong>📅 Mandato:</strong> {mandato}</p>
                        <p style="margin: 5px 0;"><strong>📞 Telefone:</strong> {telefone}</p>
                        <p style="margin: 5px 0;"><strong>📧 E-mail:</strong> {email}</p>
                    </div>
                </div>
                """

                icon = BeautifyIcon(
                    icon=icon_name,
                    icon_shape='marker',
                    background_color=color,
                    border_color=color,
                    text_color='white',
                    border_width=1,
                    inner_icon_style='font-size:10px;padding-top:2px;'
                )

                folium.Marker(
                    location=[lat, lon],
                    icon=icon,
                    tooltip=f"{nome_2} • {sigla} • {segm}",
                    popup=folium.Popup(popup_html, max_width=360)
                ).add_to(groups[grp_key])

            for g in groups.values():
                g.add_to(m)
            folium.LayerControl(collapsed=True).add_to(m)

            map_height = 720
            folium_static(m, width=920, height=map_height)


    # ===== Gráficos (em colunas, responsivos) =====
    st.markdown("""<hr/>""", unsafe_allow_html=True)
    st.subheader("📊 Distribuição dos Representantes")

    gcol1, gcol2 = st.columns(2, gap="small")

    with gcol1:
        if "Segmento" in dff.columns:
            seg_counts = (
                dff["Segmento"].fillna("(vazio)").replace("", "(vazio)")
                .value_counts()
                .reset_index(name="Contagem")
                .rename(columns={"index": "Segmento"})
            )
            if not seg_counts.empty:
                fig_pie = px.pie(seg_counts, names="Segmento", values="Contagem", hole=0.35, title="Por Segmento")
                fig_pie.update_traces(textposition="inside", textinfo="percent+label")
                st.plotly_chart(fig_pie, use_container_width=True, config={"displaylogo": False})
            else:
                st.info("Sem dados para o gráfico de Segmento.")

    with gcol2:
        if "Município" in dff.columns:
            mun_counts = (
                dff["Município"].fillna("(vazio)").replace("", "(vazio)")
                .value_counts()
                .reset_index(name="Contagem")
                .rename(columns={"index": "Município"})
                .sort_values("Contagem", ascending=True)
            )
            if not mun_counts.empty:
                fig_bar = px.bar(mun_counts, y="Município", x="Contagem", orientation="h", title="Por Município")
                fig_bar.update_layout(yaxis_title="Município", xaxis_title="Contagem", bargap=0.2)
                st.plotly_chart(fig_bar, use_container_width=True, config={"displaylogo": False})
            else:
                st.info("Sem dados para o gráfico de Município.")
