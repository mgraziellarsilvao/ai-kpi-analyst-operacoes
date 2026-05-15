import pandas as pd


# ─────────────────────────────────────────────
# Formatação
# ─────────────────────────────────────────────

def moeda(valor: float) -> str:
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def percentual(valor: float) -> str:
    return f"{valor:.1f}%".replace(".", ",")


# ─────────────────────────────────────────────
# Transformação de dados
# ─────────────────────────────────────────────

def preparar_dados(df: pd.DataFrame) -> pd.DataFrame:
    dados = df.copy()
    dados["desvio_rs"] = dados["realizado"] - dados["orcado"]
    dados["desvio_pct"] = (dados["desvio_rs"] / dados["orcado"]) * 100
    dados["gap_sla"] = dados["sla_real"] - dados["sla_meta"]
    dados["gap_volume"] = dados["volume_realizado"] - dados["volume_planejado"]
    dados["status_orcamento"] = dados["desvio_rs"].apply(
        lambda x: "⚠️ Acima do orçamento" if x > 0 else "✅ Dentro/abaixo do orçamento"
    )
    dados["status_sla"] = dados["gap_sla"].apply(
        lambda x: "✅ SLA atingido" if x >= 0 else "⚠️ SLA abaixo da meta"
    )
    return dados


# ─────────────────────────────────────────────
# Consolidação executiva
# ─────────────────────────────────────────────

def resumo_executivo(df: pd.DataFrame) -> dict:
    dados = preparar_dados(df)

    total_orcado = dados["orcado"].sum()
    total_realizado = dados["realizado"].sum()
    desvio_total = total_realizado - total_orcado
    desvio_pct_total = (desvio_total / total_orcado) * 100 if total_orcado else 0

    categorias = (
        dados.groupby(["categoria", "tipo", "area"], as_index=False)
        .agg(
            orcado=("orcado", "sum"),
            realizado=("realizado", "sum"),
            sla_real=("sla_real", "mean"),
            sla_meta=("sla_meta", "mean"),
            volume_planejado=("volume_planejado", "sum"),
            volume_realizado=("volume_realizado", "sum"),
            lead_time_dias=("lead_time_dias", "mean"),
        )
    )

    categorias["desvio_rs"] = categorias["realizado"] - categorias["orcado"]
    categorias["desvio_pct"] = (categorias["desvio_rs"] / categorias["orcado"]) * 100
    categorias["gap_sla"] = categorias["sla_real"] - categorias["sla_meta"]
    categorias["gap_volume"] = categorias["volume_realizado"] - categorias["volume_planejado"]

    criticos = categorias[categorias["desvio_rs"] > 0].sort_values("desvio_rs", ascending=False)
    sla_criticos = categorias[categorias["gap_sla"] < 0].sort_values("gap_sla")

    return {
        "total_orcado": total_orcado,
        "total_realizado": total_realizado,
        "desvio_total": desvio_total,
        "desvio_pct_total": desvio_pct_total,
        "categorias": categorias,
        "criticos": criticos,
        "sla_criticos": sla_criticos,
        "dados_tratados": dados,
    }


# ─────────────────────────────────────────────
# Narrativa executiva (baseada em regras analíticas)
# ─────────────────────────────────────────────

def gerar_insight_textual(df: pd.DataFrame) -> str:
    r = resumo_executivo(df)
    criticos = r["criticos"]
    sla_criticos = r["sla_criticos"]

    desvio = r["desvio_total"]
    desvio_pct = r["desvio_pct_total"]
    total_orcado = r["total_orcado"]
    total_realizado = r["total_realizado"]

    linhas = []

    # Abertura com posição orçamentária
    if desvio > 0:
        linhas.append(
            f"**Posição orçamentária:** O período encerrou com estouro de {moeda(desvio)} "
            f"({percentual(desvio_pct)} acima do orçado), totalizando {moeda(total_realizado)} "
            f"realizados contra {moeda(total_orcado)} planejados."
        )
        linhas.append(
            "Esse nível de desvio requer análise de causa-raiz por categoria antes do "
            "próximo ciclo de planejamento, com foco em contratos recorrentes e consumo variável."
        )
    else:
        linhas.append(
            f"**Posição orçamentária:** O período encerrou com economia de {moeda(abs(desvio))} "
            f"({percentual(abs(desvio_pct))} abaixo do orçado), totalizando {moeda(total_realizado)} "
            f"realizados contra {moeda(total_orcado)} planejados."
        )
        linhas.append(
            "O resultado indica aderência ao planejamento, com oportunidade de revisão "
            "de premissas para otimização do próximo ciclo."
        )

    # Desvios críticos
    if not criticos.empty:
        linhas.append("")
        linhas.append("**Desvios críticos por categoria:**")
        for _, row in criticos.head(3).iterrows():
            vol_gap = int(row["gap_volume"])
            vol_texto = (
                f" Volume executado superou o planejado em {abs(vol_gap)} unidades,"
                if vol_gap > 0
                else f" Volume executado {abs(vol_gap)} unidades abaixo do planejado,"
            )
            linhas.append(
                f"- **{row['categoria']} ({row['area']}):** desvio de {moeda(row['desvio_rs'])} "
                f"({percentual(row['desvio_pct'])}).{vol_texto} "
                f"lead time médio de {row['lead_time_dias']:.1f} dias."
            )

    # Leitura de SLA
    linhas.append("")
    if not sla_criticos.empty:
        linhas.append("**Atenção ao nível de serviço (SLA):**")
        for _, row in sla_criticos.head(2).iterrows():
            linhas.append(
                f"- **{row['categoria']}:** SLA realizado de {percentual(row['sla_real'])} "
                f"contra meta de {percentual(row['sla_meta'])} "
                f"(gap de {percentual(row['gap_sla'])})."
            )
        linhas.append(
            "Quedas de SLA associadas a estouro de volume indicam gargalo operacional, "
            "não apenas variação de custo. Recomenda-se análise de capacidade."
        )
    else:
        linhas.append(
            "**Nível de serviço (SLA):** Todas as categorias atingiram ou superaram as metas "
            "de SLA no período. Manter monitoramento preventivo nos próximos ciclos."
        )

    # Recomendação final
    linhas.append("")
    linhas.append("**Recomendação executiva:**")
    if desvio > 0 and not sla_criticos.empty:
        linhas.append(
            "O cenário combina estouro orçamentário e deterioração de SLA — padrão típico "
            "de pressão por demanda não planejada. Priorizar revisão de contratos variáveis, "
            "capacidade operacional e premissas de volume para o próximo período."
        )
    elif desvio > 0:
        linhas.append(
            "Estouro orçamentário sem impacto em SLA sugere variação de volume ou reajuste "
            "contratual. Ação recomendada: revisão de custo unitário e negociação com "
            "fornecedores prioritários."
        )
    else:
        linhas.append(
            "Resultado favorável. Recomenda-se documentar as práticas que sustentaram a "
            "aderência orçamentária e avaliar reinvestimento ou redução de orçamento nas "
            "categorias com desempenho consistente."
        )

    return "\n".join(linhas)
