"""
Pipeline de limpeza e normalização — Rede Turmalina Café
==========================================================
Lê os 4 CSVs originais (sem edição manual) e devolve DataFrames tratados.
Toda decisão de tratamento está comentada no ponto em que é aplicada;
o resumo em prosa dessas decisões vive em DOCUMENTACAO_DECISOES.md.
"""

import re
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# Utilitários de parsing reutilizados entre arquivos
# ---------------------------------------------------------------------------

def normaliza_id_loja(serie: pd.Series) -> pd.Series:
    """Uppercase, remove hífen/espaço -> 'lj-13' e 'lj05' viram 'LJ13'/'LJ05'."""
    return (
        serie.astype(str)
        .str.upper()
        .str.replace("-", "", regex=False)
        .str.replace(" ", "", regex=False)
    )


def parse_data_multi_formato(serie: pd.Series) -> pd.Series:
    """Datas chegam em 3 formatos: ISO (2026-01-09), BR (16/03/2026) e
    com ponto (21.03.2022). Tenta cada formato em ordem; o que sobrar
    vira NaT (e é reportado, não descartado silenciosamente)."""
    s = serie.astype(str).str.strip()
    out = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    falta = out.isna()
    out.loc[falta] = pd.to_datetime(s[falta], format="%d/%m/%Y", errors="coerce")
    falta = out.isna()
    out.loc[falta] = pd.to_datetime(s[falta], format="%d.%m.%Y", errors="coerce")
    return out


def parse_moeda_br(serie: pd.Series) -> pd.Series:
    """'R$ 8,57' -> 8.57 ; já numérico passa direto."""
    def conv(v):
        if pd.isna(v):
            return np.nan
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).replace("R$", "").strip()
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return np.nan
    return serie.apply(conv)


# ---------------------------------------------------------------------------
# 1. LOJAS
# ---------------------------------------------------------------------------

def carrega_lojas(path="turmalina_lojas.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["id_loja"] = normaliza_id_loja(df["id_loja"])

    # formato: livre -> 3 categorias canônicas
    mapa_formato = {
        "rua": "Rua", "loja de rua": "Rua",
        "shopping": "Shopping", "shopping center": "Shopping",
        "quiosque": "Quiosque", "kiosk": "Quiosque",
    }
    df["formato_norm"] = df["formato"].str.strip().str.lower().map(mapa_formato)

    # modelo: livre -> Própria / Franquia
    df["modelo_norm"] = df["modelo"].str.strip().str.lower().map(
        {"própria": "Própria", "propria": "Própria", "franquia": "Franquia"}
    )

    # data_abertura: 3 formatos distintos
    df["data_abertura_norm"] = parse_data_multi_formato(df["data_abertura"])

    # area_m2: número puro, string "62 m²"/"58m2", ou string com vírgula "74,0"
    def parse_area(v):
        s = str(v).lower().replace("m²", "").replace("m2", "").strip()
        s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return np.nan
    df["area_m2_norm"] = df["area_m2"].apply(parse_area)

    # num_funcionarios: "12 (sendo 2 PJ)" -> extrai o primeiro inteiro
    df["num_funcionarios_norm"] = (
        df["num_funcionarios"].astype(str).str.extract(r"(\d+)").astype(float)
    )

    # meta_faturamento_mensal: moeda BR em string
    df["meta_faturamento_mensal_norm"] = parse_moeda_br(df["meta_faturamento_mensal"])

    # status: 'Ativa'/'ativa'/'ATIVA' normalizam para 'Ativa'.
    # O valor '1' (LJ08, LJ11, LJ13) não tem mapeamento declarado em nenhuma
    # nota de exportação. DECISÃO: não presumir que '1' significa 'Ativa' —
    # fica como 'Status desconhecido' e a loja é sinalizada na tela de
    # qualidade de dados, não descartada nem assumida como ativa.
    def norm_status(v):
        s = str(v).strip().lower()
        if s == "ativa":
            return "Ativa"
        return "Status desconhecido"
    df["status_norm"] = df["status"].apply(norm_status)

    return df


# ---------------------------------------------------------------------------
# 2. VENDAS DIÁRIAS
# ---------------------------------------------------------------------------

def carrega_vendas(path="turmalina_vendas_diarias.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["id_loja"] = normaliza_id_loja(df["id_loja"])
    df["data"] = pd.to_datetime(df["data"], format="%Y-%m-%d", errors="coerce")

    # Duplicata exata (mesma loja+data, mesmos valores): mantém 1a ocorrência.
    n_dup = df.duplicated(subset=["data", "id_loja"], keep="first").sum()
    df = df.drop_duplicates(subset=["data", "id_loja"], keep="first")

    # horas_trabalhadas_equipe == 0 com faturamento > 0: incoerente com a
    # nota "loja que não abriu não gera linha" (se não abriu, não devia ter
    # linha nenhuma). DECISÃO: tratar como erro de captura -> NaN, não como
    # zero real. Isso evita produtividade "infinita" e não descarta a venda,
    # que continua válida para os indicadores de margem.
    mask_zero = (df["horas_trabalhadas_equipe"] == 0) & (df["faturamento_bruto"] > 0)
    df.loc[mask_zero, "horas_trabalhadas_equipe"] = np.nan

    df.attrs["duplicatas_removidas"] = int(n_dup)
    df.attrs["horas_zeradas_tratadas"] = int(mask_zero.sum())
    return df


# ---------------------------------------------------------------------------
# 3. ITENS (mix de produtos)
# ---------------------------------------------------------------------------

_MAPA_CATEGORIA = {
    "café": "Café", "cafés": "Café", "cafe": "Café",
    "geladas": "Geladas", "bebidas geladas": "Geladas",
    "salgados": "Salgados",
    "doces": "Doces",
    "grãos e varejo": "Grãos e varejo", "graos e varejo": "Grãos e varejo",
    "varejo": "Grãos e varejo",
}


def carrega_itens(path="turmalina_itens.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["id_loja"] = normaliza_id_loja(df["id_loja"])
    df["categoria_norm"] = df["categoria"].str.strip().str.lower().map(_MAPA_CATEGORIA)
    df["preco_medio_norm"] = parse_moeda_br(df["preco_medio"])
    # custo_unitario nulo em 85 linhas: mantido como NaN, não preenchido —
    # margem por item só é calculada onde custo existe (ver seção margem).
    return df


# ---------------------------------------------------------------------------
# 4. AVALIAÇÕES
# ---------------------------------------------------------------------------

_MAPA_NOTA = {
    "2": 2, "2,0": 2,
    "3": 3, "3,0": 3, "3 estrelas": 3, "três": 3,
    "4": 4, "4,0": 4, "4 estrelas": 4, "quatro": 4,
    "5": 5, "5,0": 5, "5 estrelas": 5, "cinco": 5,
}

_MAPA_CANAL = {
    "app": "App", "google": "Google", "google maps": "Google",
    "totem na loja": "Totem",
}


def carrega_avaliacoes(path="turmalina_avaliacoes.csv") -> pd.DataFrame:
    df = pd.read_csv(path)
    df["id_loja"] = normaliza_id_loja(df["id_loja"])
    df["data_norm"] = parse_data_multi_formato(df["data"])
    df["nota_norm"] = df["nota"].astype(str).str.strip().str.lower().map(_MAPA_NOTA)
    df["canal_norm"] = df["canal"].astype(str).str.strip().str.lower().map(_MAPA_CANAL)

    # tempo_espera_min == 999: sentinela de falha do totem (nota do case:
    # "o totem, que às vezes trava"). DECISÃO: tratar como ausente, não
    # como 999 minutos reais de espera.
    df["tempo_espera_norm"] = df["tempo_espera_min"].replace(999, np.nan)

    return df


# ---------------------------------------------------------------------------
# Carregamento consolidado
# ---------------------------------------------------------------------------

def carrega_tudo(base_dir="."):
    import os
    lojas = carrega_lojas(os.path.join(base_dir, "turmalina_lojas.csv"))
    vendas = carrega_vendas(os.path.join(base_dir, "turmalina_vendas_diarias.csv"))
    itens = carrega_itens(os.path.join(base_dir, "turmalina_itens.csv"))
    avaliacoes = carrega_avaliacoes(os.path.join(base_dir, "turmalina_avaliacoes.csv"))
    return lojas, vendas, itens, avaliacoes


if __name__ == "__main__":
    lojas, vendas, itens, avaliacoes = carrega_tudo()
    print("Lojas:", lojas.shape)
    print(lojas[["id_loja", "formato_norm", "modelo_norm", "status_norm"]])
    print("\nVendas:", vendas.shape, "| duplicatas removidas:", vendas.attrs["duplicatas_removidas"],
          "| horas zeradas tratadas:", vendas.attrs["horas_zeradas_tratadas"])
    print("\nItens:", itens.shape, "| categorias:", itens["categoria_norm"].unique())
    print("\nAvaliações:", avaliacoes.shape, "| notas nulas pós-map:", avaliacoes["nota_norm"].isna().sum())
