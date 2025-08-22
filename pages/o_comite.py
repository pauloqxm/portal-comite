import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import unicodedata
import plotly.express as px

def render_o_comite():
    st.title("🙋🏽 O Comitê")
    st.markdown(
        """
<div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); border-radius: 12px; padding: 20px; border-left: 4px solid #228B22; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 20px;">
  <p style="font-family: 'Segoe UI', Roboto, sans-serif; color: #2c3e50; font-size: 16px; line-height: 1.6; margin: 0;">
    <span style="font-weight: 600; color: #006400;">📌 Nesta página você encontra:</span><br>
    • Listagem dos representantes com filtros e busca<br>
    • Mapa categorizado por <b>Segmento</b> + troca de mapa de fundo<br>
    • Distribuição por <b>Segmento</b> e <b>Município</b>
  </p>
</div>
""",
        unsafe_allow_html=True,
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

    # ===== Tabela & Mapa (lado a lado, responsivo) =====
    col_tab, col_map = st.columns([0.48, 0.52], gap="large")

    with col_tab:
        st.subheader("📑 Representantes")
        cols_tabela = ["Nome (2)", "Sigla", "Função", "Segmento", "Diretoria"]
        cols_exist = [c for c in cols_tabela if c in dff.columns]
        if not cols_exist:
            st.info("As colunas esperadas não foram encontradas.")
        else:
            tab = dff[cols_exist].rename(columns={"Nome (2)": "Nome"}).sort_values(by="Nome")
            st.dataframe(tab, use_container_width=True, hide_index=True)

    with col_map:
        st.subheader("🗺️ Mapa dos Representantes")
        tile_option = st.selectbox(
            "Mapa de fundo",
            ["CartoDB positron", "OpenStreetMap", "Stamen Terrain", "CartoDB dark_matter", "Esri Satellite"],
            index=0
        )

        have_geo = {"Latitude", "Longitude"}.issubset(dff.columns)
        pontos = dff.dropna(subset=["Latitude", "Longitude"]) if have_geo else pd.DataFrame()

        if pontos.empty:
            st.info("Sem coordenadas válidas para exibir no mapa.")
        else:
            try:
                center = [pontos["Latitude"].astype(float).mean(), pontos["Longitude"].astype(float).mean()]
            except Exception:
                center = [-5.2, -39.5]

            seg_unicos = [s for s in pontos["Segmento"].dropna().unique()]
            palette = ["#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
                       "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf"]
            color_map = {seg: palette[i % len(palette)] for i, seg in enumerate(seg_unicos)}
            default_color = "#7f7f7f"

            m = folium.Map(location=center, zoom_start=7, tiles=None)
            tile_config = {
                "CartoDB positron": ("https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png",
                                     '&copy; <a href="https://carto.com/attributions">CARTO</a>'),
                "OpenStreetMap": ("OpenStreetMap", '&copy; <a href="https://openstreetmap.org">OSM</a>'),
                "Stamen Terrain": ("https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
                                   'Map tiles by <a href="http://stamen.com">Stamen</a>'),
                "CartoDB dark_matter": ("https://cartodb-basemaps-a.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png",
                                        '&copy; <a href="https://carto.com/attributions">CARTO</a>'),
                "Esri Satellite": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                                   "Tiles &copy; Esri"),
            }
            tiles, attr = tile_config[tile_option]
            folium.TileLayer(tiles=tiles, attr=attr, name=tile_option, control=True).add_to(m)

            groups = {seg: folium.FeatureGroup(name=f"Segmento: {seg}", show=True) for seg in seg_unicos}
            groups["_sem_segmento"] = folium.FeatureGroup(name="Segmento: (vazio)", show=True)

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

                color = color_map.get(segm, default_color)
                popup = folium.Popup(
                    f"""
                    <div style="font-family:Arial; font-size:13px; line-height:1.4;">
                        <div style="font-weight:700; font-size:14px; color:#2c3e50;">{nome_full}</div>
                        <div><b>Sigla:</b> {sigla}</div>
                        <div><b>Função:</b> {func}</div>
                        <div><b>Segmento:</b> {segm}</div>
                        <div><b>Diretoria:</b> {diretoria}</div>
                        <div><b>Município:</b> {mun}</div>
                        <div><b>Mandato:</b> {mandato}</div>
                    </div>
                    """,
                    max_width=320
                )

                folium.CircleMarker(
                    location=[lat, lon],
                    radius=6,
                    color=color,
                    fill=True,
                    fill_color=color,
                    fill_opacity=0.9,
                    tooltip=f"{nome_2} • {sigla}",
                    popup=popup
                ).add_to(groups[grp_key])

            for g in groups.values():
                g.add_to(m)

            folium.LayerControl(collapsed=False).add_to(m)
            folium_static(m, width=920, height=560)

    # ===== Gráficos (em colunas, responsivos) =====
    st.markdown("---")
    st.subheader("📊 Distribuição dos Representantes")

    gcol1, gcol2 = st.columns(2, gap="large")

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
        else:
            st.info("Coluna 'Segmento' não encontrada.")

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
        else:
            st.info("Coluna 'Município' não encontrada.")

    # ===== Pequeno ajuste de responsividade de padding =====
    st.markdown(
        """
        <style>
          @media (max-width: 900px){
            section.main > div.block-container { padding-left: .6rem; padding-right: .6rem; }
          }
        </style>
        """,
        unsafe_allow_html=True
    )
