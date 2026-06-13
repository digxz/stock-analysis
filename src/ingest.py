# src/ingest.py
import yfinance as yf
import pandas as pd


def buscar_cotacoes(ticker: str, periodo: str = "1y") -> pd.DataFrame:
    """
    Busca cotações históricas de um ticker.

    Args:
        ticker:  símbolo da ação (ex: 'PETR4.SA', 'AAPL', 'VALE3.SA')
        periodo: '1mo', '3mo', '6mo', '1y', '2y', '5y'

    Returns:
        DataFrame com colunas: Open, High, Low, Close, Volume
    """
    ativo = yf.Ticker(ticker)
    df = ativo.history(period=periodo)

    if df.empty:
        raise ValueError(f"Ticker '{ticker}' não encontrado ou sem dados.")

    # Mantém só as colunas que vamos usar
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()

    # Garante que o índice é só a data (sem fuso horário)
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "Date"

    # Adiciona coluna com o ticker para identificar a ação no banco
    df["ticker"] = ticker.upper()

    return df


def buscar_multiplos(tickers: list[str], periodo: str = "1y") -> pd.DataFrame:
    """
    Busca cotações de vários tickers e retorna tudo num DataFrame único.
    """
    frames = []
    for ticker in tickers:
        try:
            df = buscar_cotacoes(ticker, periodo)
            frames.append(df)
            print(f"  OK  {ticker} — {len(df)} pregões")
        except ValueError as e:
            print(f"  ERRO {e}")

    if not frames:
        raise RuntimeError("Nenhum ticker retornou dados.")

    return pd.concat(frames)