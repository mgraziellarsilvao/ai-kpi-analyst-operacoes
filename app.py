import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from insights import preparar_dados, resumo_executivo, gerar_insight_textual, moeda, percentual

# ─────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="AI KPI Analyst | Operações e Processos",
    page_icon="📊",
    layout="wide",
)

st.title("📊 AI KPI Analyst")
st.caption(
    "Análise de OPEX/CAPEX · Desvios orçamentários · SLA operacional · Tomada de decisão"
)

# ─────────────────────────────────────────────
# Carga de dados
# ─────────────────────────────────────────────

@st.cache_data
def carregar_dados():
    return pd.read_csv("data/custos_operacionais.csv")

df_raw = carregar_dados()
df = preparar_dados(df_raw)

# ─────────────────────────────────────────────
# Sidebar — filtros
# ─────────────────────────────────────────────

with st.sidebar:
    st.header("🔎 Filtros")
    meses = st.multiselect(
        "Mês", sorted(df["mes"].unique()), default=sorted(df["mes"].unique())
    )
    tipos = st.multiselect(
        "Tipo (OPEX / CAPEX)", sorted(df["tipo"].unique()), default=sorted(df["tipo"].unique())
    )
    areas = st.multiselect(
        "Área", sorted(df["area"].unique()), default=sorted(df["area"].unique())
    )
    st.divider()
    st.caption("Projeto de portfólio · Python · Streamlit · Pandas")

filtrado = df[
    (df["mes"].isin(meses)) &
    (df["tipo"].isin(tipos)) &
    (df["area"].isin(areas))
]

r = resumo_executivo(filtrado)

# ─────────────────────────────────────────────
# KPIs de topo
# ─────────────────────────────────────────────

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Orçado", moeda(r["total_orcado"]))
col2.metric("Total Realizado", moeda(r["total_realizado"]))

desvio_delta = f"{percentual(r['desvio_pct_total'])} vs orçado"
col3.metric(
    "Desvio R$",
    moeda(r["desvio_total"]),
    delta=desvio_delta,
    delta_color="inverse",
)

n_criticos = len(r["criticos"])
n_sla = len(r["sla_criticos"])
col4.metric(
    "Pontos de Atenção",
    f"{n_criticos} categorias",
    delta=f"{n_sla} com SLA abaixo da meta",
    delta_color="inverse" if n_sla > 0 else "normal",
)

st.divider()

# ─────────────────────────────────────────────
# Abas
# ─────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Visão Executiva",
    "🚨 Desvios Críticos",
    "📐 SLA Operacional",
    "🗂️ Base Tratada",
])

# ── Tab 1: Visão Executiva ──────────────────

with tab1:
    st.subheader("Diagnóstico do período")

    insight = gerar_insight_textual(filtrado)
    st.markdown(insight)

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        mensal = (
            filtrado.groupby("mes", as_index=False)
            .agg(orcado=("orcado", "sum"), realizado=("realizado", "sum"))
        )
        fig_linha = px.line(
            mensal,
            x="mes",
            y=["orcado", "realizado"],
            markers=True,
            labels={"mes": "Mês", "value": "R$", "variable": ""},
            title="Evolução mensal: Orçado × Realizado",
            color_discrete_map={"orcado": "#636EFA", "realizado": "#EF553B"},
        )
        fig_linha.update_layout(legend_title_text="")
        st.plotly_chart(fig_linha, use_container_width=True)

    with col_b:
        por_tipo = (
            filtrado.groupby("tipo", as_index=False)
            .agg(orcado=("orcado", "sum"), realizado=("realizado", "sum"))
        )
        por_tipo["desvio"] = por_tipo["realizado"] - por_tipo["orcado"]
        fig_tipo = px.bar(
            por_tipo,
            x="tipo",
            y=["orcado", "realizado"],
            barmode="group",
            labels={"tipo": "Tipo", "value": "R$", "variable": ""},
            title="OPEX × CAPEX: Orçado vs Realizado",
            color_discrete_map={"orcado": "#636EFA", "realizado": "#EF553B"},
        )
        fig_tipo.update_layout(legend_title_text="")
        st.plotly_chart(fig_tipo, use_container_width=True)

# ── Tab 2: Desvios Críticos ─────────────────

with tab2:
    st.subheader("Categorias com maior desvio orçamentário")

    categorias = r["categorias"].sort_values("desvio_rs", ascending=False)

    criticos = r["criticos"]
    if criticos.empty:
        st.success("Nenhuma categoria encerrou acima do orçamento no período selecionado.")
    else:
        # Cards de alerta para os top 3
        cols = st.columns(min(3, len(criticos)))
        for i, (_, row) in enumerate(criticos.head(3).iterrows()):
            with cols[i]:
                st.error(
                    f"**{row['categoria']}**\n\n"
                    f"Desvio: {moeda(row['desvio_rs'])}\n\n"
                    f"{percentual(row['desvio_pct'])} acima do orçado\n\n"
                    f"Área: {row['area']}"
                )

        st.divider()

        fig_desvio = px.bar(
            categorias,
            x="categoria",
            y="desvio_rs",
            color="tipo",
            text=categorias["desvio_pct"].apply(lambda x: f"{x:.1f}%"),
            labels={"categoria": "Categoria", "desvio_rs": "Desvio R$", "tipo": "Tipo"},
            title="Desvio financeiro por categoria (R$)",
            color_discrete_map={"OPEX": "#EF553B", "CAPEX": "#636EFA"},
        )
        fig_desvio.update_traces(textposition="outside")
        fig_desvio.add_hline(y=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_desvio, use_container_width=True)

        st.subheader("Desvio × Volume operacional")
        fig_scatter = px.scatter(
            categorias,
            x="desvio_pct",
            y="volume_realizado",
            size=categorias["desvio_rs"].abs(),
            color="tipo",
            hover_name="categoria",
            labels={
                "desvio_pct": "Desvio %",
                "volume_realizado": "Volume Realizado",
                "tipo": "Tipo",
            },
            title="Relação entre desvio % e volume executado",
        )
        fig_scatter.add_vline(x=0, line_dash="dash", line_color="gray")
        st.plotly_chart(fig_scatter, use_container_width=True)

# ── Tab 3: SLA Operacional ──────────────────

with tab3:
    st.subheader("Performance de SLA por categoria")

    categorias = r["categorias"].copy()
    sla_criticos = r["sla_criticos"]

    if sla_criticos.empty:
        st.success("Todas as categorias atingiram ou superaram a meta de SLA no período.")
    else:
        st.warning(
            f"{len(sla_criticos)} categoria(s) com SLA abaixo da meta. "
            "Quedas de SLA combinadas com estouro de volume indicam gargalo operacional."
        )

    # Gráfico de barras SLA meta vs real
    fig_sla = go.Figure()
    fig_sla.add_trace(go.Bar(
        name="SLA Meta",
        x=categorias["categoria"],
        y=categorias["sla_meta"],
        marker_color="#636EFA",
        opacity=0.6,
    ))
    fig_sla.add_trace(go.Bar(
        name="SLA Real",
        x=categorias["categoria"],
        y=categorias["sla_real"],
        marker_color=categorias["gap_sla"].apply(
            lambda x: "#00CC96" if x >= 0 else "#EF553B"
        ),
    ))
    fig_sla.update_layout(
        barmode="group",
        title="SLA Meta × SLA Real por categoria (%)",
        xaxis_title="Categoria",
        yaxis_title="SLA (%)",
        legend_title_text="",
    )
    st.plotly_chart(fig_sla, use_container_width=True)

    # Tabela de SLA
    sla_tabela = categorias[[
        "categoria", "area", "tipo", "sla_meta", "sla_real", "gap_sla",
        "lead_time_dias", "volume_planejado", "volume_realizado", "gap_volume"
    ]].sort_values("gap_sla")

    st.dataframe(
        sla_tabela.style.applymap(
            lambda v: "color: red; font-weight: bold" if isinstance(v, float) and v < 0 else "",
            subset=["gap_sla", "gap_volume"]
        ),
        use_container_width=True,
    )

# ── Tab 4: Base Tratada ─────────────────────

with tab4:
    st.subheader("Base de dados tratada")
    st.caption(
        "Base simulada com parâmetros de mercado: OPEX/CAPEX, SLA, volume operacional "
        "e lead time por categoria e centro de custo."
    )

    col_x, col_y = st.columns([3, 1])
    with col_y:
        status_filter = st.selectbox(
            "Filtrar por status orçamentário",
            ["Todos", "⚠️ Acima do orçamento", "✅ Dentro/abaixo do orçamento"],
        )

    base = filtrado.copy()
    if status_filter != "Todos":
        base = base[base["status_orcamento"] == status_filter]

    st.dataframe(
        base[[
            "mes", "area", "tipo", "categoria", "centro_custo",
            "orcado", "realizado", "desvio_rs", "desvio_pct",
            "status_orcamento", "sla_meta", "sla_real", "status_sla",
            "volume_planejado", "volume_realizado", "gap_volume", "lead_time_dias"
        ]],
        use_container_width=True,
    )

    total_linhas = len(base)
    acima = len(base[base["desvio_rs"] > 0])
    st.caption(f"{total_linhas} registros exibidos · {acima} acima do orçamento")
