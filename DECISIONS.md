# Documentação das Decisões

Um parágrafo por decisão relevante: a decisão, as alternativas consideradas, o critério que sustentou a escolha e a condição que a invalidaria.

---

**Recorte do problema: "prioridade da semana" como pergunta central, Expansão fora do escopo.**
Alternativas consideradas: cobrir os 5 temas do briefing (seção 03 do case) com o mesmo peso; ou focar só em margem, que é o tema com dado mais robusto. O critério foi a cadência de uso: a usuária age semanalmente e só em 2 lojas — qualquer pergunta que não termine em "para qual loja eu olho essa semana" não cabe no momento de uso descrito. Essa decisão seria invalidada se a empresa tivesse um segundo ritual de decisão (por exemplo, uma reunião trimestral de expansão) com acesso ao mesmo sistema — nesse caso, Expansão voltaria ao escopo com indicadores próprios de maturação de loja nova.

**Status "1" no cadastro de lojas tratado como "status desconhecido", não como "Ativa".**
Alternativa considerada: assumir "1" = "Ativa", já que as 3 lojas (LJ08, LJ11, LJ13) geram vendas normalmente nos dados. O critério que pesou contra foi o requisito explícito do case de não presumir dado não fornecido — "1" não aparece em nenhuma nota de exportação como sinônimo de "Ativa", e presumir isso silenciosamente é o tipo de decisão que o case pede para documentar, não descartar. A decisão seria invalidada por uma confirmação da equipe de que "1" é de fato um código legado para "Ativa" (nesse caso o mapeamento entraria direto no pipeline).

**Linhas com `horas_trabalhadas_equipe = 0` e faturamento positivo tratadas como dado ausente, não como zero real.**
Alternativa considerada: manter o valor 0 e deixar a produtividade (tickets/hora) como infinita ou indefinida na tela. O critério foi a própria nota de exportação do arquivo ("loja que não abriu não gera linha") — uma loja com faturamento positivo obrigatoriamente teve equipe trabalhando; 0h é erro de captura, não fechamento. A decisão seria invalidada se a Turmalina confirmasse que existe operação sem equipe própria registrada (por exemplo, terceirização não capturada no campo).

**Janela de 90 dias para os indicadores de cliente, diferente da janela de 4 semanas usada em margem e equipe.**
Alternativa considerada: manter a mesma janela de 4 semanas para todos os diagnósticos, por consistência. O critério que decidiu contra foi checagem empírica: em 4 semanas, só 1 das 14 lojas atinge o mínimo de 5 avaliações para uma leitura confiável; em 90 dias, todas as 14 atingem. Manter 4 semanas geraria uma tela quase sempre "sem dados" no bloco de cliente, o que não ajuda a diretora a decidir. A decisão seria invalidada se o volume de avaliações coletadas crescesse (por exemplo, 3–4× o atual), tornando a janela de 4 semanas estatisticamente viável.

**Sentinela `999` em `tempo_espera_min` tratado como valor ausente.**
Alternativa considerada: manter o valor e deixá-lo entrar na média (o que levaria o tempo médio de espera a números absurdos, como visto no teste inicial dos dados). O critério foi a nota de exportação do próprio case, que atribui esse valor a falhas do totem, não a espera real. A decisão seria invalidada se a Turmalina confirmasse que 999 é um valor de espera genuíno registrado manualmente em algum cenário.

**Mínimo de 5 avaliações no período para exibir nota e tempo de espera; abaixo disso, "dado insuficiente".**
Alternativa considerada: exibir a média mesmo com poucas avaliações (por exemplo, calcular sobre 2 registros). O critério foi evitar que o sistema pareça confiável quando não é — uma média de 2 avaliações pode virar de 2 para 5 estrelas com um único cliente insatisfeito, e apresentar isso como "a nota da loja" sustentaria decisão errada. O limite de 5 é arbitrário e está registrado como tal; poderia ser recalibrado com mais contexto sobre a variância real das notas.

**Comparação de produtividade de equipe por formato de loja (rua/shopping/quiosque), não pela rede inteira.**
Alternativa considerada: comparar todas as 14 lojas contra uma única média de rede. O critério foi que quiosque, loja de rua e loja de shopping têm operações estruturalmente diferentes (área, equipe, fluxo) — uma média única penalizaria sistematicamente um formato inteiro. A decisão seria invalidada se a rede padronizasse operação a ponto de os formatos deixarem de ser estruturalmente distintos.

**`turmalina_itens.csv` foi limpo mas não virou indicador na v1.**
Alternativa considerada: incluir margem por categoria de produto como quinto bloco de diagnóstico. O critério contra foi granularidade (mensal, incompatível com a cadência semanal do resto do sistema) somada à lacuna de 5% em `custo_unitario`, que tornaria a margem por categoria parcialmente estimada sem sinalização clara disso na tela. A decisão seria invalidada se o sistema evoluísse para uma segunda cadência de revisão mensal, onde esse descompasso de granularidade deixaria de ser um problema.
