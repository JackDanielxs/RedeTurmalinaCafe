# Registro de Uso de IA

**Ferramentas utilizada:** Claude (chat) e Claude Code (via terminal).

O chat foi utilizado para discussão e definição das decisões do projeto, enquanto o Claude Code foi empregado para executar código, validar hipóteses e analisar os dados reais ao longo do desenvolvimento.

---

## Registro de momentos

| # | O que foi pedido | O que foi devolvido | O que foi mantido / alterado / descartado |
|:--:|---------------------------|------------------------------|-------------------------------------------|
| **1** | Exploração inicial dos quatro arquivos CSV, solicitando um diagnóstico completo da qualidade dos dados. | Identificação das principais inconsistências em cada arquivo, incluindo formatos de data diferentes, categorias livres, uso do valor sentinela `999`, IDs em letras minúsculas/com hífen e notas representadas como texto, número e estrelas. | **Mantido.** Todas as inconsistências foram confirmadas por meio da execução de código sobre os arquivos reais (não se tratava de uma lista genérica) e cada uma delas foi transformada em uma regra explícita no `data_pipeline.py`. |
| **2** | "Vamos fechar o recorte do problema primeiro." | Proposta de definição do escopo do projeto utilizando **"prioridade da semana"** como pergunta principal, deixando margem, cliente e equipe como análises de apoio, além da justificativa para excluir temas que os dados não sustentavam. | **Mantido.** Após revisão, o recorte foi adotado e registrado em `DOCUMENTACAO_DECISOES.md`. |
| **3** | Solicitação de indicadores concretos (fórmula, unidade e base de comparação) para responder às quatro perguntas definidas no escopo. | Tabela contendo oito indicadores com fórmula, unidade, período e base de comparação, incluindo a sugestão de utilizar uma janela de **90 dias** para análise dos clientes. | **Mantido parcialmente.** A maior parte dos indicadores foi utilizada. Entretanto, a janela de 90 dias somente foi adotada após validação experimental, comparando a suficiência amostral em janelas de 28, 60, 90 e 180 dias. Portanto, essa decisão foi baseada em testes realizados sobre os dados reais, e não apenas na sugestão da IA. |

---

## Desacordo

Durante a revisão do protótipo, foi reavaliado o critério de utilização da janela de **90 dias** para análise dos clientes.

Embora essa configuração tenha sido sugerida inicialmente pela IA, a decisão final não foi aceita automaticamente. Foram executados testes comparando diferentes janelas (**28, 60, 90 e 180 dias**), avaliando a quantidade de dados disponíveis e a estabilidade dos indicadores.

A escolha final pela janela de **90 dias** foi baseada nos resultados observados durante esses testes, e não apenas na recomendação da IA. Dessa forma, a decisão foi fundamentada em evidências obtidas a partir dos dados do projeto.

---

## Recusa

Foi solicitada à IA uma sugestão de indicadores adicionais para complementar o dashboard.

Entre as sugestões apresentadas estava a criação de um **ranking de clientes por volume de pedidos**.

Essa proposta não foi incorporada ao projeto porque não contribuía diretamente para responder à pergunta central definida no escopo (**"qual deve ser a prioridade da semana?"**). Além disso, incluir essa visualização aumentaria a complexidade do dashboard sem agregar informações relevantes para a tomada de decisão proposta pelo trabalho.
