import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_pipeline import carrega_tudo
from indicadores import (
    indicadores_triagem, indicadores_margem, indicadores_cliente, indicadores_equipe
)

st.set_page_config(page_title="Turmalina Café · Visão da Semana", layout="wide")

CORES = {
    "Prioridade": "#C0392B",
    "Atenção": "#E5A02E",
    "Estável": "#4C8C4A",
    "Dado insuficiente": "#9AA0A6",
}

# ---------------------------------------------------------------------------
# Carga (cacheada — os CSVs não mudam durante a sessão)
# ---------------------------------------------------------------------------

@st.cache_data
def carregar():
    return carrega_tudo(".")

lojas, vendas, itens, avaliacoes = carregar()

semanas_disponiveis = sorted(
    vendas["data"].dt.to_period("W-SUN").apply(lambda p: p.start_time).unique()
)
# a última semana do arquivo costuma estar incompleta (corte no meio da semana);
# a penúltima é a última semana fechada — é essa que abre por padrão.
semana_default = semanas_disponiveis[-2]

# ---------------------------------------------------------------------------
# Sidebar — seleção de semana e loja
# ---------------------------------------------------------------------------

st.sidebar.title("☕ Turmalina Café")
st.sidebar.caption("Sistema de apoio à decisão operacional")

semana_ref = st.sidebar.selectbox(
    "Semana de referência",
    options=semanas_disponiveis[1:],  # precisa de ao menos 1 semana anterior p/ tendência
    index=list(semanas_disponiveis[1:]).index(semana_default),
    format_func=lambda d: f"{d.strftime('%d/%m/%Y')} a {(d + pd.Timedelta(days=6)).strftime('%d/%m/%Y')}",
)
fim_semana = semana_ref + pd.Timedelta(days=6)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Capacidade real de intervenção: no máximo **2 lojas por semana** "
    "(premissa do case, seção 1.4). As classificações abaixo priorizam "
    "para caber nesse limite."
)

# ---------------------------------------------------------------------------
# Cálculo dos indicadores para a semana escolhida
# ---------------------------------------------------------------------------

tri = indicadores_triagem(vendas, lojas, semana_ref)

periodo_margem_ini = semana_ref - pd.Timedelta(weeks=3)  # 4 semanas fechadas, incl. a de referência
marg, marg_rede = indicadores_margem(vendas, periodo_margem_ini, fim_semana)

# Avaliações são raras (380 no total p/ 14 lojas em ~1 ano): uma janela de
# 4 semanas deixa quase toda loja com "dado insuficiente". Usamos 90 dias
# corridos só para o indicador de cliente — decisão registrada na
# documentação, não presume-se dado que a janela curta não sustenta.
cli = indicadores_cliente(avaliacoes, fim_semana - pd.Timedelta(days=90), fim_semana)

equi = indicadores_equipe(vendas, lojas, periodo_margem_ini, fim_semana)

tabs = st.tabs(["📊 Visão da Semana", "🔍 Diagnóstico da Loja"])

# ===========================================================================
# TELA 1 — VISÃO DA SEMANA
# ===========================================================================
with tabs[0]:
    st.header("Visão da Semana")
    st.caption(
        f"Semana de **{semana_ref.strftime('%d/%m/%Y')}** a **{fim_semana.strftime('%d/%m/%Y')}** · "
        f"Atingimento = faturamento da semana ÷ meta mensal proporcional · "
        f"Tendência = variação entre as últimas 2 semanas e as 2 anteriores"
    )

    n_prioridade = (tri["classificacao"] == "Prioridade").sum()
    n_atencao = (tri["classificacao"] == "Atenção").sum()
    n_insuf = (tri["classificacao"] == "Dado insuficiente").sum()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lojas em prioridade", n_prioridade)
    c2.metric("Lojas em atenção", n_atencao)
    c3.metric("Lojas estáveis", (tri["classificacao"] == "Estável").sum())
    c4.metric("Dado insuficiente", n_insuf)

    plot_df = tri.dropna(subset=["atingimento_pct", "tendencia_pct"])
    fig = px.scatter(
        plot_df, x="atingimento_pct", y="tendencia_pct",
        color="classificacao", color_discrete_map=CORES,
        text="id_loja", hover_data={"nome_loja": True, "atingimento_pct": ":.1f", "tendencia_pct": ":.1f"},
        labels={"atingimento_pct": "Atingimento de meta (%)", "tendencia_pct": "Tendência recente (%)"},
    )
    fig.add_vline(x=100, line_dash="dash", line_color="gray")
    fig.add_hline(y=0, line_dash="dash", line_color="gray")
    fig.update_traces(textposition="top center", marker=dict(size=14))
    fig.update_layout(height=450, legend_title_text="Classificação")
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Quadrante inferior-esquerdo (abaixo da meta **e** em queda) = prioridade máxima. "
        "Lojas cinzas não têm histórico suficiente nas últimas 4 semanas para calcular tendência "
        "(caso típico de loja recém-aberta)."
    )

    st.subheader("Ranking completo")
    tabela = tri.sort_values(
        by="classificacao", key=lambda s: s.map({"Prioridade": 0, "Atenção": 1, "Estável": 2, "Dado insuficiente": 3})
    )[["nome_loja", "formato_norm", "modelo_norm", "atingimento_pct", "tendencia_pct", "classificacao"]]
    tabela.columns = ["Loja", "Formato", "Modelo", "Atingimento (%)", "Tendência (%)", "Classificação"]
    st.dataframe(
        tabela.style.format({"Atingimento (%)": "{:.1f}", "Tendência (%)": "{:.1f}"}, na_rep="—"),
        use_container_width=True, hide_index=True,
    )

# ===========================================================================
# TELA 2 — DIAGNÓSTICO DA LOJA
# ===========================================================================
with tabs[1]:
    st.header("Diagnóstico da Loja")

    opcoes = tri.sort_values("atingimento_pct")[["id_loja", "nome_loja", "classificacao"]]
    label_map = {
        row.id_loja: f"{row.id_loja} · {row.nome_loja} ({row.classificacao})"
        for row in opcoes.itertuples()
    }
    loja_sel = st.selectbox("Loja", options=opcoes["id_loja"], format_func=lambda x: label_map[x])

    info_loja = lojas[lojas["id_loja"] == loja_sel].iloc[0]
    tri_loja = tri[tri["id_loja"] == loja_sel].iloc[0]

    st.markdown(
        f"### {info_loja['nome_loja']} — {info_loja['formato_norm']} · {info_loja['modelo_norm']}"
    )
    st.caption(
        f"Aberta em {info_loja['data_abertura_norm'].strftime('%d/%m/%Y') if pd.notna(info_loja['data_abertura_norm']) else '—'} · "
        f"{info_loja['area_m2_norm']:.0f} m² · {info_loja['num_funcionarios_norm']:.0f} funcionários · "
        f"Status cadastral: {info_loja['status_norm']}"
    )
    if info_loja["status_norm"] == "Status desconhecido":
        st.warning(
            "O campo de status desta loja no cadastro original não corresponde a nenhum valor "
            "documentado ('Ativa'/'ativa'/'ATIVA'). Ela é tratada como ativa para fins de cálculo "
            "(está gerando vendas), mas o status cadastral precisa de confirmação — não presumido."
        )

    col_a, col_b = st.columns(2)
    col_a.metric("Atingimento de meta (semana)", f"{tri_loja['atingimento_pct']:.1f}%" if pd.notna(tri_loja['atingimento_pct']) else "—")
    col_b.metric("Tendência (4 semanas)", f"{tri_loja['tendencia_pct']:.1f}%" if pd.notna(tri_loja['tendencia_pct']) else "—")

    st.markdown("---")
    b1, b2, b3 = st.columns(3)

    # --- Margem ---
    with b1:
        st.subheader("💰 Margem")
        m = marg[marg["id_loja"] == loja_sel]
        if len(m):
            m = m.iloc[0]
            st.metric("Margem sobre insumos", f"{m['margem_pct']:.1f}%", delta=f"{m['margem_pct'] - marg_rede['margem_pct']:.1f} pp vs rede")
            st.metric("% desconto concedido", f"{m['desconto_pct']:.1f}%", delta=f"{m['desconto_pct'] - marg_rede['desconto_pct']:.1f} pp vs rede", delta_color="inverse")
            st.metric("% desperdício sobre insumos", f"{m['desperdicio_pct']:.1f}%", delta=f"{m['desperdicio_pct'] - marg_rede['desperdicio_pct']:.1f} pp vs rede", delta_color="inverse")
        else:
            st.info("Sem dados de vendas no período.")
        st.caption("Período: 4 semanas fechadas até a semana de referência. Comparação: média da rede.")

    # --- Cliente ---
    with b2:
        st.subheader("😊 Cliente")
        c = cli[cli["id_loja"] == loja_sel]
        if len(c) and c.iloc[0]["dado_suficiente"]:
            c = c.iloc[0]
            st.metric("Nota média", f"{c['nota_media']:.1f} / 5")
            st.metric("Tempo médio de espera", f"{c['tempo_espera_medio']:.1f} min")
            st.caption(f"Baseado em {int(c['n_avaliacoes'])} avaliações.")
        else:
            n = int(c.iloc[0]["n_avaliacoes"]) if len(c) else 0
            st.info(f"Dado insuficiente ({n} avaliações nos últimos 90 dias, mínimo de 5). Sem leitura confiável de experiência do cliente.")
        st.caption("Período: 90 dias corridos (janela maior que a de margem — avaliações são raras).")

    # --- Equipe ---
    with b3:
        st.subheader("👥 Equipe")
        e = equi[equi["id_loja"] == loja_sel]
        if len(e):
            e = e.iloc[0]
            st.metric("Produtividade (tickets/hora)", f"{e['tickets_por_hora']:.2f}",
                       delta=f"{e['desvio_pct_formato']:.1f}% vs média do formato")
        else:
            st.info("Sem dados de equipe no período.")
        st.caption(f"Comparação: lojas do mesmo formato ({info_loja['formato_norm']}). "
                    "Não cobre cobertura por horário de pico — dado disponível é diário, não por hora.")

    st.markdown("---")
    st.subheader("Histórico de faturamento (12 semanas)")
    hist = vendas[vendas["id_loja"] == loja_sel].copy()
    hist["semana"] = hist["data"].dt.to_period("W-SUN").apply(lambda p: p.start_time)
    hist_sem = hist.groupby("semana", as_index=False)["faturamento_bruto"].sum()
    hist_sem = hist_sem[hist_sem["semana"] <= semana_ref].tail(12)
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=hist_sem["semana"], y=hist_sem["faturamento_bruto"], mode="lines+markers", name="Faturamento"))
    meta_sem_valor = info_loja["meta_faturamento_mensal_norm"] / 4.345
    fig2.add_hline(y=meta_sem_valor, line_dash="dash", line_color="gray", annotation_text="Meta semanal")
    fig2.update_layout(height=300, yaxis_title="R$", xaxis_title=None)
    st.plotly_chart(fig2, use_container_width=True)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Dados: 4 CSVs originais, sem edição manual. "
    "Ver DECISIONS.md para decisões de tratamento e limitações."
)
