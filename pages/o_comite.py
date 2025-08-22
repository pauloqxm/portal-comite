# =====================================================================
# 📈 Evolução da Vazão Operada por Reservatório
# =====================================================================
st.subheader("📈 Evolução da Vazão Operada por Reservatório")

# Verificar se há dados para mostrar
if not df_filtrado.empty and "Reservatório Monitorado" in df_filtrado.columns:
    fig = go.Figure()
    cores = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#17becf", "#e377c2"]
    reservatorios = df_filtrado["Reservatório Monitorado"].dropna().unique()

    if len(reservatorios) > 0:
        for i, r in enumerate(reservatorios):
            dfr = (
                df_filtrado[df_filtrado["Reservatório Monitorado"] == r]
                .sort_values("Data")
                .groupby("Data", as_index=False)
                .last()
            )

            if not dfr.empty:
                # Linha principal (Vazão Operada)
                y_vals, unit_suffix = convert_vazao(dfr["Vazão Operada"], unidade_sel)
                fig.add_trace(go.Scatter(
                    x=dfr["Data"], y=y_vals, mode="lines+markers", name=r,
                    line=dict(shape="hv", width=2, color=cores[i % len(cores)]),
                    marker=dict(size=5),
                    hovertemplate=f"<b>{r}</b><br>Data: %{{x|%d/%m/%Y}}<br>"
                                  f"Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
                ))

                # Caso tenha apenas um reservatório selecionado → linhas extras
                if len(reservatorios) == 1 and len(dfr) > 1:
                    # Média ponderada no período com base em dias "ativos"
                    dfr = dfr.copy()
                    dfr["dias_ativos"] = dfr["Data"].diff().dt.days.fillna(0)
                    if not dfr.empty:
                        dmax = df_filtrado["Data"].max()
                        dfr.loc[dfr.index[-1], "dias_ativos"] = (dmax - dfr["Data"].iloc[-1]).days + 1

                        media_pond = (dfr["Vazão Operada"] * dfr["dias_ativos"]).sum() / dfr["dias_ativos"].sum()
                        media_pond_conv, _ = convert_vazao(pd.Series([media_pond]), unidade_sel)

                        fig.add_hline(
                            y=float(media_pond_conv.iloc[0]), line_dash="dash", line_width=2, line_color="red",
                            annotation_text=f"Média Ponderada {media_pond_conv.iloc[0]:.2f} {unit_suffix}",
                            annotation_position="top right"
                        )

                    # Linha Azul Vazao_Aloc se existir
                    if "Vazao_Aloc" in dfr.columns:
                        y_aloc, _ = convert_vazao(dfr["Vazao_Aloc"], unidade_sel)
                        fig.add_trace(go.Scatter(
                            x=dfr["Data"], y=y_aloc, mode="lines",
                            name="Vazão Alocada", line=dict(color="blue", width=2, dash="dot"),
                            hovertemplate=f"<b>Vazão Alocada</b><br>Data: %{{x|%d/%m/%Y}}<br>"
                                          f"Vazão: %{{y:.3f}} {unit_suffix}<extra></extra>"
                        ))

        # Legenda na parte inferior
        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            height=500,
            title="Evolução da Vazão Operada por Reservatório"
        )

        st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False}, key="plotly_vazao_evolucao")
    else:
        st.info("Nenhum reservatório encontrado para exibir o gráfico.")
else:
    st.info("Dados insuficientes para exibir o gráfico de evolução.")

# =====================================================================
# 📊 Volume acumulado por reservatório
# =====================================================================
st.subheader("📊 Volume acumulado por reservatório")

cols_necessarias = {"Reservatório Monitorado", "Data", "Vazão Operada"}
tem_cols = cols_necessarias.issubset(set(df_filtrado.columns))
tem_res = not df_filtrado.empty and df_filtrado["Reservatório Monitorado"].nunique() > 0

if tem_cols and tem_res:
    df_box = df_filtrado.copy()
    df_box["Data"] = pd.to_datetime(df_box["Data"], errors="coerce")
    df_box["Vazão Operada"] = pd.to_numeric(df_box["Vazão Operada"], errors="coerce").fillna(0)

    volumes = []
    fim_periodo_global = df_box["Data"].max()

    for reservatorio in df_box["Reservatório Monitorado"].dropna().unique():
        df_res = (
            df_box[df_box["Reservatório Monitorado"] == reservatorio]
            .dropna(subset=["Data"])
            .sort_values("Data")
            .copy()
        )
        if df_res.empty:
            continue

        # Dias entre medições (fecha último intervalo até o fim do período global)
        df_res["dias_entre_medicoes"] = df_res["Data"].diff().dt.days.fillna(0)
        ultima_data_res = df_res["Data"].iloc[-1]
        fim_periodo = fim_periodo_global if pd.notna(fim_periodo_global) else ultima_data_res
        df_res.loc[df_res.index[-1], "dias_entre_medicoes"] = max((fim_periodo - ultima_data_res).days + 1, 0)

        # Se Vazão Operada está em l/s, converter para m³/s dividindo por 1000
        segundos_por_dia = 86400
        vazao_m3s = df_res["Vazão Operada"] / 1000.0
        df_res["volume_periodo_m3"] = vazao_m3s * segundos_por_dia * df_res["dias_entre_medicoes"]

        volume_total_m3 = float(df_res["volume_periodo_m3"].sum())
        volumes.append({"Reservatório Monitorado": reservatorio, "Volume Acumulado (m³)": volume_total_m3})

    df_volumes = pd.DataFrame(volumes)

    def fmt_m3(x):
        if pd.isna(x):
            return "-"
        if x >= 1_000_000:
            return f"{x/1e6:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mi m³"
        elif x >= 1_000:
            return f"{x/1e3:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " mil m³"
        else:
            return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " m³"

    if not df_volumes.empty:
        df_volumes["Volume Formatado"] = df_volumes["Volume Acumulado (m³)"].apply(fmt_m3)
        df_volumes["Volume Eixo Y"] = df_volumes["Volume Acumulado (m³)"] / 1e6
        df_volumes = df_volumes.sort_values("Volume Eixo Y", ascending=False)

        y_max = float(df_volumes["Volume Eixo Y"].max()) if not df_volumes.empty else 1.0
        y_max = y_max * 1.2 if y_max > 0 else 1.0
        y_title = "Volume acumulado em milhões de m³"

        base = alt.Chart(df_volumes).encode(
            x=alt.X("Reservatório Monitorado:N", title="Reservatório", sort="-y")
        ).properties(
            title="Volume acumulado por reservatório",
            height=400
        ).interactive()

        bars = base.mark_bar(color="steelblue").encode(
            y=alt.Y("Volume Eixo Y:Q", title=y_title, scale=alt.Scale(domain=[0, y_max])),
            tooltip=[
                alt.Tooltip("Reservatório Monitorado:N", title="Reservatório"),
                alt.Tooltip("Volume Formatado:N", title="Volume total")
            ]
        )

        # Texto com o valor formatado em cima de cada barra
        text = base.mark_text(
            align="center",
            baseline="bottom",
            dy=-5,
            fontSize=12
        ).encode(
            y=alt.Y("Volume Eixo Y:Q", stack=None),
            text="Volume Formatado:N"
        )

        chart = alt.layer(bars, text).resolve_scale(y="independent")
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Sem dados suficientes para montar o gráfico.")
else:
    st.info("Sem dados suficientes para o gráfico de volume.")

# =====================================================================
# 🏞️ Média da Vazão Operada por reservatório — CORRIGIDO
# =====================================================================
st.subheader("🏞️ Média da Vazão Operada por Reservatório")

if not df_filtrado.empty and "Reservatório Monitorado" in df_filtrado.columns:
    dfm = df_filtrado.copy()
    dfm["Data"] = pd.to_datetime(dfm["Data"], errors="coerce")
    dfm = dfm.dropna(subset=["Data", "Reservatório Monitorado"])
    
    # Data máxima do dataset (mesma referência do gráfico de Evolução)
    data_maxima_dataset = dfm["Data"].max()

    # 1 leitura por dia por reservatório (última do dia), igual ao gráfico de Evolução
    df_diario = (
        dfm.sort_values("Data")
          .groupby(["Reservatório Monitorado", "Data"], as_index=False)
          .last()
    )

    # Mês e ano para não misturar períodos
    meses_map = {1:"Jan", 2:"Fev", 3:"Mar", 4:"Abr", 5:"Mai", 6:"Jun",
                7:"Jul", 8:"Ago", 9:"Set", 10:"Out", 11:"Nov", 12:"Dez"}
    df_diario["Ano"] = df_diario["Data"].dt.year
    df_diario["Mês"] = df_diario["Data"].dt.month.map(meses_map)
    df_diario["MêsRef"] = df_diario["Mês"] + "/" + df_diario["Ano"].astype(str)

    # Função para calcular média ponderada mensal (MESMA metodologia do gráfico de Evolução)
    def calcular_media_ponderada_mensal(grupo):
        grupo = grupo.sort_values('Data')
        grupo = grupo.copy()
        grupo['dias_ativos'] = grupo['Data'].diff().dt.days.fillna(0)
        
        # CORREÇÃO: Usar a mesma lógica do gráfico de Evolução
        # Para o último registro, calcular dias até a data máxima do dataset
        if not grupo.empty:
            ultima_data = grupo['Data'].iloc[-1]
            
            # Se for o último mês do dataset, vai até data_maxima_dataset
            # Se for mês anterior, vai até o final do mês
            if ultima_data.month == data_maxima_dataset.month and ultima_data.year == data_maxima_dataset.year:
                # Último mês: usa data máxima do dataset (igual gráfico Evolução)
                dias_restantes = (data_maxima_dataset - ultima_data).days + 1
            else:
                # Mês completo: vai até o final do mês
                fim_mes = ultima_data + pd.offsets.MonthEnd(0)
                dias_restantes = (fim_mes - ultima_data).days + 1
            
            grupo.loc[grupo.index[-1], 'dias_ativos'] = dias_restantes
        
        # Calcular média ponderada (mesma metodologia do gráfico de Evolução)
        vazao_total_ponderada = (grupo['Vazão Operada'] * grupo['dias_ativos']).sum()
        dias_totais = grupo['dias_ativos'].sum()
        
        return vazao_total_ponderada / dias_totais if dias_totais > 0 else 0

    # Calcular média mensal ponderada (igual à metodologia do gráfico de Evolução)
    try:
        media_mensal = (
            df_diario.groupby(["Reservatório Monitorado", "MêsRef"], dropna=True)
                     .apply(calcular_media_ponderada_mensal)
                     .reset_index(name='Vazão Operada')
        )

        if not media_mensal.empty:
            # Mesma unidade do gráfico de evolução
            y_vals_media, unit_suffix_media = convert_vazao(media_mensal["Vazão Operada"], unidade_sel)
            media_mensal["Vazão (conv)"] = y_vals_media

            # Ordena reservatórios pelo total do período
            ordem_res = (
                media_mensal.groupby("Reservatório Monitorado")["Vazão (conv)"]
                            .sum().sort_values(ascending=True).index.tolist()
            )

            # Ordena MêsRef cronologicamente
            inv_meses = {v: k for k, v in meses_map.items()}
            media_mensal["ord"] = media_mensal["MêsRef"].apply(
                lambda s: int(s.split("/")[1]) * 100 + inv_meses[s.split("/")[0]]
            )
            media_mensal = media_mensal.sort_values("ord")
            ordem_mesref = media_mensal["MêsRef"].unique().tolist()

            # Rotulagem com pontos e unidade
            def format_val_dot(v: float, unit: str) -> str:
                if pd.isna(v):
                    return "- " + unit
                if abs(v) < 1000:
                    s = f"{v:.3f}"
                else:
                    s = f"{v:,.2f}".replace(",", ".")
                return f"{s} {unit}"

            media_mensal["Valor Formatado"] = media_mensal["Vazão (conv)"].apply(lambda v: format_val_dot(v, unit_suffix_media))

            # Gráfico horizontal empilhado por Mês/Ano
            fig_media = px.bar(
                media_mensal,
                y="Reservatório Monitorado",
                x="Vazão (conv)",
                color="MêsRef",
                orientation="h",
                text="Valor Formatado",
                category_orders={"Reservatório Monitorado": ordem_res, "MêsRef": ordem_mesref},
                labels={
                    "Reservatório Monitorado": "Reservatório",
                    "Vazão (conv)": f"Média ({unit_suffix_media})",
                    "MêsRef": "Mês/Ano"
                },
                barmode="stack",
                hover_data={
                    "Vazão (conv)": False,
                    "Valor Formatado": True
                }
            )

            fig_media.update_traces(textposition="inside", insidetextanchor="middle", cliponaxis=False)
            fig_media.update_layout(
                bargap=0.2,
                legend_title_text="Mês/Ano",
                xaxis_title=f"Média ({unit_suffix_media})",
                yaxis_title="Reservatório",
                height=500
            )

            st.plotly_chart(fig_media, use_container_width=True, config={"displaylogo": False}, key="plotly_vazao_media_res_mes_alinhado")
        else:
            st.info("Sem dados para calcular a média.")
    except Exception as e:
        st.error(f"Erro ao calcular média: {str(e)}")
else:
    st.info("Sem dados para a média.")
