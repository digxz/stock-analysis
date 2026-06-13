# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.ingest import buscar_multiplos
from src.transform import processar_todos
from src.database import salvar, carregar

# ── Configuração da página ──────────────────────────────────────────
st.set_page_config(
    page_title="Análise de Ações",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Análise de Ações")
st.caption("Dados via yfinance · Métricas calculadas com Pandas · Armazenado em DuckDB")

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Configurações")

    tickers_input = st.text_input(
        "Tickers (separados por vírgula)",
        value="PETR4.SA, VALE3.SA, AAPL",
        help="Use .SA para ações brasileiras. Ex: PETR4.SA, VALE3.SA"
    )

    periodo = st.selectbox(
        "Período",
        options=["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        index=3,
    )

    atualizar = st.button("🔄 Buscar / Atualizar dados", use_container_width=True)

    st.divider()
    st.markdown("**Como usar**")
    st.markdown("1. Digite os tickers desejados\n2. Escolha o período\n3. Clique em Buscar")

# ── Lógica de dados ─────────────────────────────────────────────────
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

if atualizar:
    with st.spinner("Buscando cotações..."):
        try:
            df_raw = buscar_multiplos(tickers, periodo=periodo)
            df = processar_todos(df_raw)
            salvar(df.reset_index())
            st.sidebar.success(f"{len(df)} registros salvos!")
        except Exception as e:
            st.sidebar.error(f"Erro: {e}")

# Carrega do banco — se vazio, busca automaticamente na primeira vez
try:
    df = carregar(tickers)
    if df.empty:
        raise ValueError("banco vazio")
except Exception:
    with st.spinner("Primeira execução — buscando dados..."):
        try:
            df_raw = buscar_multiplos(tickers, periodo=periodo)
            df = processar_todos(df_raw)
            salvar(df.reset_index())
            df = carregar(tickers)
        except Exception as e:
            st.error(f"Erro ao buscar dados: {e}")
            st.stop()

# ── Seletor de ticker principal ──────────────────────────────────────
ticker_sel = st.selectbox("Ativo principal", options=sorted(df["ticker"].unique()))
df_sel = df[df["ticker"] == ticker_sel].copy()

# ── Métricas de topo ────────────────────────────────────────────────
ultimo        = df_sel["Close"].iloc[-1]
anterior      = df_sel["Close"].iloc[-2]
variacao_dia  = (ultimo - anterior) / anterior * 100
retorno_total = df_sel["retorno_acum"].iloc[-1] * 100
vol_atual     = df_sel["volatilidade"].iloc[-1]
sma20         = df_sel["sma_20"].iloc[-1]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Último preço",     f"R$ {ultimo:.2f}",       f"{variacao_dia:+.2f}% hoje")
col2.metric("Retorno no período", f"{retorno_total:+.1f}%")
col3.metric("Volatilidade (anual)", f"{vol_atual:.1f}%")
col4.metric("SMA 20",           f"R$ {sma20:.2f}",
            "acima" if ultimo > sma20 else "abaixo")

st.divider()

# ── Gráfico principal: Candlestick + médias ──────────────────────────
fig = make_subplots(
    rows=2, cols=1,
    shared_xaxes=True,
    row_heights=[0.7, 0.3],
    vertical_spacing=0.04,
)

# Candlestick
fig.add_trace(go.Candlestick(
    x=df_sel.index,
    open=df_sel["Open"], high=df_sel["High"],
    low=df_sel["Low"],   close=df_sel["Close"],
    name="Preço",
    increasing_line_color="#1D9E75",
    decreasing_line_color="#D85A30",
), row=1, col=1)

# Médias móveis
for col_name, cor, label in [
    ("sma_20", "#378ADD", "SMA 20"),
    ("sma_50", "#F5A623", "SMA 50"),
    ("ema_20", "#9B59B6", "EMA 20"),
]:
    fig.add_trace(go.Scatter(
        x=df_sel.index, y=df_sel[col_name],
        name=label, line=dict(color=cor, width=1.5),
        opacity=0.85,
    ), row=1, col=1)

# Volume
cores_volume = [
    "#1D9E75" if r >= 0 else "#D85A30"
    for r in df_sel["retorno"].fillna(0)
]
fig.add_trace(go.Bar(
    x=df_sel.index, y=df_sel["Volume"],
    name="Volume", marker_color=cores_volume, opacity=0.6,
), row=2, col=1)

fig.update_layout(
    height=520,
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", y=1.02, x=0),
    margin=dict(l=0, r=0, t=30, b=0),
)
fig.update_yaxes(title_text="Preço (R$)", row=1, col=1)
fig.update_yaxes(title_text="Volume",     row=2, col=1)

st.plotly_chart(fig, use_container_width=True)

# ── Volatilidade histórica ───────────────────────────────────────────
st.subheader("Volatilidade histórica (anualizada)")

fig_vol = go.Figure(go.Scatter(
    x=df_sel.index, y=df_sel["volatilidade"],
    fill="tozeroy", line=dict(color="#7F77DD", width=1.5),
    name="Volatilidade %",
))
fig_vol.update_layout(
    height=220,
    margin=dict(l=0, r=0, t=10, b=0),
    yaxis_ticksuffix="%",
)
st.plotly_chart(fig_vol, use_container_width=True)

# ── Comparação de retorno acumulado ─────────────────────────────────
st.subheader("Retorno acumulado — comparação")

fig_ret = go.Figure()
cores = ["#378ADD", "#1D9E75", "#D85A30", "#F5A623", "#9B59B6"]
for i, ticker in enumerate(sorted(df["ticker"].unique())):
    df_t = df[df["ticker"] == ticker]
    fig_ret.add_trace(go.Scatter(
        x=df_t.index,
        y=df_t["retorno_acum"] * 100,
        name=ticker,
        line=dict(color=cores[i % len(cores)], width=2),
    ))

fig_ret.update_layout(
    height=280,
    margin=dict(l=0, r=0, t=10, b=0),
    yaxis_ticksuffix="%",
    legend=dict(orientation="h"),
)
st.plotly_chart(fig_ret, use_container_width=True)

# ── Tabela de dados ──────────────────────────────────────────────────
with st.expander("Ver dados brutos"):
    st.dataframe(
        df_sel[["Open","High","Low","Close","Volume","sma_20","sma_50","ema_20","volatilidade"]]
          .sort_index(ascending=False)
          .style.format("{:.2f}", subset=["Open","High","Low","Close","sma_20","sma_50","ema_20","volatilidade"]),
        use_container_width=True,
    )