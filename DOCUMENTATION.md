# Documento de Projeto — Rede Turmalina Café

## 1. Usuária, momento de uso e premissas

**Usuária**: Marina Salles, diretora de operações. Lê números com facilidade, não programa, não constrói consultas.

**Momento de uso**: início da manhã de segunda-feira, antes da reunião semanal com os 5 gerentes regionais, que define as prioridades da semana.

**Restrição central do projeto**: a estrutura atual sustenta ação efetiva em, no máximo, **2 lojas por semana**. Essa é a premissa que mais influenciou o desenho — o sistema não precisa ranquear "tudo", precisa apontar rápido para onde a atenção escassa deve ir.

**Premissas assumidas** (nenhuma delas está no material fornecido, e nenhuma extrapola para dado não fornecido):

- A "semana" operacional é segunda a domingo (`W-SUN` na agregação), e a reunião de segunda-feira olha para a **última semana já fechada** (a anterior à corrente), não para a semana em andamento.
- Meta semanal = meta mensal ÷ 4,345 (média de semanas por mês). Não há meta semanal nativa nos dados.
- O status cadastral "1" (LJ08, LJ11, LJ13) não tem definição documentada. Não presumido como "Ativa" — tratado como operacionalmente ativo (porque as três lojas geram vendas normalmente), mas sinalizado na tela como cadastro a confirmar. Essa é uma premissa operacional, não uma limpeza silenciosa do dado.
- O sistema assume que todas as lojas com linhas em `vendas_diarias` estavam operando nos dias com faturamento > 0, mesmo quando `status` é desconhecido.

## 2. Perguntas que o sistema responde — e o recorte

**Pergunta central**: *"Quais lojas precisam de atenção essa semana, e por quê?"*

Desdobrada em:
1. **Triagem** — qual loja está com desempenho fora do esperado essa semana (abre a Tela 1).
2. **Diagnóstico de margem** — a loja sinalizada está perdendo dinheiro por desconto, desperdício ou custo de insumo?
3. **Diagnóstico de cliente** — a loja sinalizada tem problema de experiência (nota, tempo de espera)?
4. **Diagnóstico de equipe** — a loja está sub ou sobredimensionada frente ao movimento?

**Fora do escopo, por decisão**: **Expansão** (manter/desacelerar/suspender aberturas). Dois motivos: (a) não é uma decisão de cadência semanal — é estratégica, mais próxima de uma revisão trimestral; (b) as lojas mais novas (LJ10–LJ14) têm entre 10 e 26 semanas de histórico, insuficiente para uma leitura de maturação de loja nova que sustente uma recomendação de expansão. Incluir essa pergunta com o dado disponível seria responder algo que os dados não sustentam.

O tema **Equipe** entrou parcialmente: o case menciona "cobertura de horário de pico", mas os dados de venda são diários — não há granularidade de hora em nenhum dos 4 arquivos. O sistema responde produtividade agregada (tickets/hora trabalhada no dia), não cobertura de pico.

## 3. Mapa dos dados

| Indicador | Arquivo(s) fonte | Coluna(s) | Tratamento aplicado |
|---|---|---|---|
| Atingimento de meta | `turmalina_vendas_diarias.csv`, `turmalina_lojas.csv` | `faturamento_bruto`, `meta_faturamento_mensal` | Soma semanal ÷ (meta mensal ÷ 4,345); meta parseada de string moeda BR |
| Tendência recente | `turmalina_vendas_diarias.csv` | `faturamento_bruto`, `data` | Variação % entre média das 2 semanas mais recentes e as 2 anteriores |
| Margem sobre insumos | `turmalina_vendas_diarias.csv` | `faturamento_bruto`, `custo_insumos` | Soma de 4 semanas fechadas; `(fat − custo) / fat` |
| % desconto | `turmalina_vendas_diarias.csv` | `descontos`, `faturamento_bruto` | Soma de 4 semanas fechadas |
| % desperdício | `turmalina_vendas_diarias.csv` | `valor_desperdicio`, `custo_insumos` | Soma de 4 semanas fechadas |
| Nota média / tempo de espera | `turmalina_avaliacoes.csv` | `nota`, `tempo_espera_min` | Nota normalizada (extenso/estrelas/vírgula → 1–5); sentinela `999` em tempo de espera tratado como ausente; janela de 90 dias (ver seção 4); mínimo de 5 avaliações para exibir |
| Produtividade de equipe | `turmalina_vendas_diarias.csv`, `turmalina_lojas.csv` | `num_tickets`, `horas_trabalhadas_equipe`, `formato` | Soma de 4 semanas; linhas com horas = 0 e faturamento > 0 tratadas como erro de captura (NaN), não como zero real; comparação contra média do mesmo formato de loja |

`turmalina_itens.csv` foi tratado (categorias normalizadas, preço parseado) mas **não alimenta nenhum indicador da v1** — ver seção 6 (alternativas descartadas).

## 4. Dicionário de indicadores

| # | Nome | Fórmula | Unidade | Período | Pergunta atendida | Limitação |
|---|---|---|---|---|---|---|
| 1 | Atingimento de meta | faturamento da semana ÷ meta semanal × 100 | % | 1 semana | Triagem | Meta semanal é uma proporção da meta mensal, não uma meta semanal real (não existe no dado) |
| 2 | Tendência recente | (média 2 sem. recentes − média 2 sem. anteriores) ÷ média 2 sem. anteriores × 100 | % | 4 semanas | Triagem | Lojas com < 4 semanas de histórico (abertas há pouco tempo) não têm esse indicador — aparecem como "dado insuficiente", nunca como 0% |
| 3 | Margem sobre insumos | (faturamento − custo insumos) ÷ faturamento × 100 | % | 4 semanas fechadas | Margem | Não inclui aluguel, folha ou outros custos fixos — não fornecidos, não presumidos |
| 4 | % desconto concedido | descontos ÷ faturamento × 100 | % | 4 semanas fechadas | Margem | Não distingue desconto promocional de desconto por erro operacional |
| 5 | % desperdício sobre insumos | desperdício ÷ custo insumos × 100 | % | 4 semanas fechadas | Margem | — |
| 6 | Nota média | média das notas normalizadas | pontos (1–5) | 90 dias | Cliente | Amostra pequena mesmo em 90 dias para lojas novas; abaixo de 5 avaliações o sistema não exibe número |
| 7 | Tempo médio de espera | média de `tempo_espera_min`, excluindo sentinela 999 | minutos | 90 dias | Cliente | Mesmo problema de amostra do indicador 6; falha do totem em si não é quantificada (só removida) |
| 8 | Produtividade de equipe | tickets ÷ horas trabalhadas | tickets/hora | 4 semanas fechadas | Equipe | Não mede cobertura por horário de pico (dado é diário); horas zeradas tratadas como ausentes, não como fechamento |

## 5. Wireframe

```
┌─────────────────────────────────────────────────────────┐
│  TELA 1 · Visão da Semana                               │
│  Semana de referência: [seletor]                        │
├─────────────────────────────────────────────────────────┤
│  [Prioridade: N]  [Atenção: N]  [Estável: N]  [Insuf: N]│
├─────────────────────────────────────────────────────────┤
│                                                         │
│   tendência          Quadrante de priorização           │
│      ▲                (atingimento × tendência,         │
│      │  •  •           cor = classificação,             │
│  ────┼────────▶        cada ponto = 1 loja)            │
│      │  •                                               │
│      │                                                  │
├─────────────────────────────────────────────────────────┤
│  Ranking completo (tabela ordenada por prioridade)      │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  TELA 2 · Diagnóstico da Loja        [seletor de loja]  │
├─────────────────────────────────────────────────────────┤
│  Nome · formato · modelo · status                       │
│  Atingimento: X%      Tendência: Y%                     │
├────────────────┬────────────────┬───────────────────────┤
│  💰 Margem     │  😊 Cliente   │  👥 Equipe            │
│  margem %      │  nota média    │  tickets/hora         │
│  desconto %    │  espera média  │  vs. média do formato │
│  desperdício % │  (ou "insuf.") │                       │
├────────────────┴────────────────┴───────────────────────┤
│  Histórico de faturamento — 12 semanas (linha + meta)   │
└─────────────────────────────────────────────────────────┘
```

Divergência entre wireframe e protótipo final: o wireframe previa 3 blocos de diagnóstico lado a lado sem gráfico de histórico; o histórico de 12 semanas foi adicionado durante a implementação porque, sem ele, "tendência" na Tela 1 fica um número solto — o gráfico dá o contexto visual de por que a loja está classificada como está.

## 6. Alternativas descartadas

- **Indicador de ticket médio** (faturamento ÷ tickets): descartado como indicador de triagem porque varia estruturalmente por formato de loja (quiosque vende itens mais baratos por natureza) e por si só não aponta ação — dado interessante, mas não decisório na cadência semanal proposta.
- **Mix de produtos (`turmalina_itens.csv`) como indicador de diagnóstico**: descartado da v1. A granularidade é mensal, não semanal — incompatível com o ritmo do sistema — e 85 linhas sem `custo_unitario` (5% do arquivo) tornariam qualquer indicador de margem por categoria parcialmente furado. Fica registrado como extensão natural para uma v2 com cadência mensal complementar.
- **Score único de priorização** (um número que resume tudo): descartado em favor do quadrante (atingimento × tendência). Um score esconde a causa; o quadrante já separa "problema crônico" (abaixo da meta, estável) de "problema em formação" (dentro da meta, mas caindo) — informação que se perderia num número só.
- **Tela única com os 4 diagnósticos de todas as 14 lojas**: descartada por transformar o sistema em planilha navegável em vez de ferramenta de decisão — contraria a própria premissa de capacidade (2 lojas/semana).
- **Gráfico de barras comparando faturamento absoluto entre lojas**: descartado porque compara lojas de porte e tempo de operação muito diferentes sem normalizar — um gráfico honesto sobre um eixo desonesto para a decisão em questão.
