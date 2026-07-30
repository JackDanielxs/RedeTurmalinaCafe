"""
Cálculo de indicadores — Rede Turmalina Café
==============================================
Recebe os DataFrames tratados (ver data_pipeline.py) e devolve as tabelas
que alimentam as duas telas do protótipo.
"""

import pandas as pd
import numpy as np

MIN_AVALIACOES_CONFIAVEL = 5  # abaixo disso, nota/espera vira "dado insuficiente"


def semana_do(data: pd.Series) -> pd.Series:
    """Segunda-feira da semana de cada data (chave de agregação semanal)."""
    return data.dt.to_period("W-SUN").apply(lambda p: p.start_time)


def tabela_semanal_vendas(vendas: pd.DataFrame) -> pd.DataFrame:
    v = vendas.copy()
    v["semana"] = semana_do(v["data"])
    agg = v.groupby(["id_loja", "semana"], as_index=False).agg(
        faturamento_bruto=("faturamento_bruto", "sum"),
        descontos=("descontos", "sum"),
        custo_insumos=("custo_insumos", "sum"),
        valor_desperdicio=("valor_desperdicio", "sum"),
        num_tickets=("num_tickets", "sum"),
        horas_trabalhadas=("horas_trabalhadas_equipe", "sum"),
    )
    return agg


def indicadores_triagem(vendas: pd.DataFrame, lojas: pd.DataFrame, semana_ref: pd.Timestamp) -> pd.DataFrame:
    """Atingimento de meta e tendência recente, para a semana de referência."""
    sem = tabela_semanal_vendas(vendas)

    meta_semanal = lojas.set_index("id_loja")["meta_faturamento_mensal_norm"] / 4.345

    atual = sem[sem["semana"] == semana_ref].set_index("id_loja")
    janela_recente = sem[(sem["semana"] < semana_ref) & (sem["semana"] >= semana_ref - pd.Timedelta(weeks=2))]
    janela_anterior = sem[(sem["semana"] < semana_ref - pd.Timedelta(weeks=2)) & (sem["semana"] >= semana_ref - pd.Timedelta(weeks=4))]

    media_recente = janela_recente.groupby("id_loja")["faturamento_bruto"].mean()
    media_anterior = janela_anterior.groupby("id_loja")["faturamento_bruto"].mean()

    out = pd.DataFrame(index=lojas["id_loja"])
    out["faturamento_semana"] = atual["faturamento_bruto"]
    out["meta_semanal"] = meta_semanal
    out["atingimento_pct"] = 100 * out["faturamento_semana"] / out["meta_semanal"]
    out["tendencia_pct"] = 100 * (media_recente - media_anterior) / media_anterior
    out = out.reset_index()

    def quadrante(row):
        if pd.isna(row["atingimento_pct"]) or pd.isna(row["tendencia_pct"]):
            return "Dado insuficiente"
        abaixo = row["atingimento_pct"] < 100
        caindo = row["tendencia_pct"] < 0
        if abaixo and caindo:
            return "Prioridade"
        if abaixo or caindo:
            return "Atenção"
        return "Estável"

    out["classificacao"] = out.apply(quadrante, axis=1)
    return out.merge(lojas[["id_loja", "nome_loja", "formato_norm", "modelo_norm"]], on="id_loja")


def indicadores_margem(vendas: pd.DataFrame, periodo_ini: pd.Timestamp, periodo_fim: pd.Timestamp) -> pd.DataFrame:
    v = vendas[(vendas["data"] >= periodo_ini) & (vendas["data"] <= periodo_fim)]
    agg = v.groupby("id_loja", as_index=False).agg(
        faturamento_bruto=("faturamento_bruto", "sum"),
        descontos=("descontos", "sum"),
        custo_insumos=("custo_insumos", "sum"),
        valor_desperdicio=("valor_desperdicio", "sum"),
    )
    agg["margem_pct"] = 100 * (agg["faturamento_bruto"] - agg["custo_insumos"]) / agg["faturamento_bruto"]
    agg["desconto_pct"] = 100 * agg["descontos"] / agg["faturamento_bruto"]
    agg["desperdicio_pct"] = 100 * agg["valor_desperdicio"] / agg["custo_insumos"]

    rede = {
        "margem_pct": agg["margem_pct"].mean(),
        "desconto_pct": agg["desconto_pct"].mean(),
        "desperdicio_pct": agg["desperdicio_pct"].mean(),
    }
    return agg, rede


def indicadores_cliente(avaliacoes: pd.DataFrame, periodo_ini: pd.Timestamp, periodo_fim: pd.Timestamp) -> pd.DataFrame:
    a = avaliacoes[(avaliacoes["data_norm"] >= periodo_ini) & (avaliacoes["data_norm"] <= periodo_fim)]
    agg = a.groupby("id_loja", as_index=False).agg(
        nota_media=("nota_norm", "mean"),
        tempo_espera_medio=("tempo_espera_norm", "mean"),
        n_avaliacoes=("id_avaliacao", "count"),
    )
    agg["dado_suficiente"] = agg["n_avaliacoes"] >= MIN_AVALIACOES_CONFIAVEL
    agg.loc[~agg["dado_suficiente"], ["nota_media", "tempo_espera_medio"]] = np.nan
    return agg


def indicadores_equipe(vendas: pd.DataFrame, lojas: pd.DataFrame, periodo_ini: pd.Timestamp, periodo_fim: pd.Timestamp) -> pd.DataFrame:
    v = vendas[(vendas["data"] >= periodo_ini) & (vendas["data"] <= periodo_fim)]
    agg = v.groupby("id_loja", as_index=False).agg(
        num_tickets=("num_tickets", "sum"),
        horas_trabalhadas=("horas_trabalhadas_equipe", "sum"),
    )
    agg["tickets_por_hora"] = agg["num_tickets"] / agg["horas_trabalhadas"]
    agg = agg.merge(lojas[["id_loja", "formato_norm"]], on="id_loja")
    media_formato = agg.groupby("formato_norm")["tickets_por_hora"].transform("mean")
    agg["tickets_por_hora_media_formato"] = media_formato
    agg["desvio_pct_formato"] = 100 * (agg["tickets_por_hora"] - media_formato) / media_formato
    return agg
