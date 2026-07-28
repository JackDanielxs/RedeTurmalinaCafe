# Rede Turmalina Café — Protótipo

Sistema de apoio à decisão semanal para a diretora de operações, a partir dos 4 CSVs originais (sem edição manual).

## Como executar

1. Coloque os 4 arquivos CSV originais na mesma pasta deste projeto (`turmalina_lojas.csv`, `turmalina_vendas_diarias.csv`, `turmalina_itens.csv`, `turmalina_avaliacoes.csv`). Já estão aqui.

2. Instale as dependências (Python 3.10+):
   ```
   pip install streamlit pandas plotly numpy
   ```

3. Rode:
   ```
   streamlit run app.py
   ```

4. Abra o link que aparece no terminal (geralmente `http://localhost:8501`).

## Estrutura dos arquivos

- `data_pipeline.py` — leitura e normalização dos 4 CSVs (datas, moeda, categorias, ids, sentinelas)
- `indicadores.py` — cálculo dos indicadores de triagem, margem, cliente e equipe
- `app.py` — interface Streamlit (Tela 1: Visão da Semana · Tela 2: Diagnóstico da Loja)
- `DOCUMENTATION.md` — usuária, perguntas, mapa de dados, dicionário de indicadores, wireframe, alternativas descartadas
- `DECISIONS.md` — um parágrafo por decisão relevante
- `AI_USAGE_LOGS.md` — registro de uso de IA conforme seção 06 do case

## Stack e justificativa

Python + Streamlit + Plotly. Justificativa em duas linhas: o volume e a variedade de tratamento de dados (parsing de datas em 3 formatos, moeda em string, categorias livres) pedem uma linguagem de propósito geral com pandas; Streamlit entrega uma interface interativa sem exigir front-end separado, mantendo o protótipo em um único ambiente reproduzível.
