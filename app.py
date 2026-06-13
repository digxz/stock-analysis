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