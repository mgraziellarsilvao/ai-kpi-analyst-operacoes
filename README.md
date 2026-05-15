# AI KPI Analyst — Operações, Processos e Dados

> Análise de OPEX/CAPEX · Desvios orçamentários · SLA operacional · Diagnóstico executivo automatizado

---

## O Problema

Em ambientes operacionais com múltiplos centros de custo, desvios de OPEX e CAPEX frequentemente
só são identificados no fechamento mensal — tarde demais para ação corretiva. SLA abaixo da meta
e estouro de volume são tratados separadamente, quando na prática estão diretamente relacionados.

Este projeto simula um painel analítico que consolida orçamento, realizado, SLA e volume operacional
em uma única visão, identificando desvios críticos e gerando diagnóstico executivo automatizado —
antes do fechamento contábil.

---

## O que o projeto entrega

| Funcionalidade | Descrição |
|---|---|
| **KPIs de topo** | Total orçado, realizado, desvio R$ e % e pontos de atenção |
| **Visão Executiva** | Diagnóstico textual gerado por regras analíticas + evolução mensal |
| **Desvios Críticos** | Cards de alerta para as 3 categorias com maior estouro + gráfico de desvio × volume |
| **SLA Operacional** | Comparativo meta × real por categoria, com destaque para gaps críticos |
| **Base Tratada** | Dados com colunas calculadas, filtro por status orçamentário e exportação visual |

---

## Valor de Negócio

Desvios de OPEX acumulam silenciosamente ao longo do mês. Este projeto demonstra como estruturar
dados operacionais para antecipar esse diagnóstico — transformando análise reativa em gestão
preventiva.

**Três impactos diretos para a operação:**

1. **Visibilidade antecipada:** desvios identificados por categoria e área, sem esperar o fechamento.
2. **Correlação SLA × custo:** quedas de SLA combinadas com estouro de volume indicam gargalo
   operacional — não apenas variação financeira. Essa leitura cruzada acelera a causa-raiz.
3. **Diagnóstico executivo pronto:** o painel gera uma narrativa estruturada de posição orçamentária,
   pontos críticos e recomendação — reduzindo o tempo de preparação de relatórios gerenciais.

O modelo de dados foi construído com variáveis reais de gestão operacional: centro de custo,
lead time, volume planejado × executado, SLA meta × real e categorias típicas de OPEX/CAPEX
em empresas de infraestrutura e serviços.

---

## Como o Claude Code foi usado neste projeto

O desenvolvimento deste projeto seguiu um fluxo de colaboração humano-IA documentado em
[`docs/prompt_claude_code.md`](docs/prompt_claude_code.md).

**O que o Claude Code fez:**

- Gerou a estrutura inicial do projeto (pastas, arquivos, separação de responsabilidades)
- Criou o esqueleto de `app.py` e `insights.py` a partir do prompt de negócio
- Sugeriu a separação entre lógica analítica (`insights.py`) e interface (`app.py`)
- Produziu o primeiro rascunho da base CSV com colunas operacionais

**O que foi definido e ajustado manualmente:**

- Critérios de SLA, faixas de desvio e lógica de categorização por tipo de gargalo
- Curadoria das categorias da base simulada (Manutenção Corretiva, Implantação de Ativos etc.)
- Narrativa executiva: estrutura do diagnóstico, tom e recomendações por cenário
- Refinamento visual das abas, cards de alerta e paleta de cores dos gráficos
- README, documentação e posicionamento do projeto

Essa iteração — IA gerando estrutura, analista refinando critério de negócio — é exatamente
como o uso profissional de IA assistida funciona na prática.

---

## Modelo de Dados

A base [`data/custos_operacionais.csv`](data/custos_operacionais.csv) simula 6 meses de
execução orçamentária com as seguintes variáveis:

| Coluna | Descrição |
|---|---|
| `mes` | Período de referência (YYYY-MM) |
| `area` | Área responsável (Operações, Facilities, Logística, Engenharia, Administrativo) |
| `tipo` | Classificação contábil: OPEX ou CAPEX |
| `categoria` | Tipo de gasto (Manutenção Corretiva, Energia Elétrica, Transporte etc.) |
| `centro_custo` | Centro de custo operacional |
| `orcado` / `realizado` | Valores planejados e executados em R$ |
| `sla_meta` / `sla_real` | Metas e resultado de nível de serviço (%) |
| `lead_time_dias` | Tempo médio de execução por categoria |
| `volume_planejado` / `volume_realizado` | Quantidade de itens ou chamados no período |

---

## Stack Técnico

| Tecnologia | Papel no projeto |
|---|---|
| **Python** | Linguagem principal |
| **Pandas** | Transformação, agregação e cálculo de KPIs |
| **Streamlit** | Interface analítica interativa |
| **Plotly** | Gráficos de linha, barras e scatter |
| **Claude Code** | Assistente de desenvolvimento (estrutura, código e documentação) |
| **VS Code** | Ambiente de desenvolvimento |
| **GitHub** | Versionamento e portfólio |

---

## Estrutura do Projeto

```text
ai-kpi-analyst-operacoes/
├── app.py                        # Interface Streamlit (4 abas analíticas)
├── insights.py                   # Lógica de negócio: KPIs, desvios e narrativa executiva
├── requirements.txt              # Dependências
├── README.md
├── .gitignore
├── data/
│   └── custos_operacionais.csv   # Base simulada com parâmetros de mercado
└── docs/
    ├── prompt_claude_code.md     # Prompt original usado no Claude Code
    └── linkedin_post.md          # Post de divulgação no LinkedIn
```

---

## Como Executar

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar a aplicação
streamlit run app.py
```

Acesse em `http://localhost:8501`

---

## Decisões de Design

**Por que separar `insights.py` de `app.py`?**
Separação de responsabilidades: a lógica analítica não deve depender da camada de apresentação.
Isso facilita testes, reuso e evolução independente de cada camada.

**Por que usar regras em vez de LLM para o diagnóstico?**
Reprodutibilidade e auditabilidade. Em contextos corporativos, um diagnóstico baseado em regras
explícitas é mais fácil de validar, documentar e manter do que um modelo generativo. A IA
(Claude Code) foi usada no desenvolvimento, não em tempo de execução.

**O que eu faria em produção?**
Conexão direta com banco de dados (PostgreSQL ou BigQuery), autenticação por área, atualização
incremental via pipeline de dados, e possivelmente uma camada de LLM para enriquecer o
diagnóstico com contexto histórico.

---

## Aprendizados

- A separação entre lógica analítica e interface tornou o código mais limpo e testável do que
  o esperado para um projeto de portfólio.
- Modelar a base com critérios reais (SLA, lead time, volume) foi mais trabalhoso que usar dados
  genéricos, mas é o que torna o projeto reconhecível para quem trabalha com operações.
- O uso do Claude Code acelerou a estrutura inicial em cerca de 70% do tempo estimado —
  o tempo restante foi de refinamento analítico e de negócio, que não tem atalho.

---

*Projeto de portfólio desenvolvido para demonstrar aplicação de Python e IA em análise operacional.*
