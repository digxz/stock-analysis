# src/transform.py
import pandas as pd


def calcular_metricas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy().sort_index()

    df["sma_20"] = df["Close"].rolling(window=20).mean()
    df["sma_50"] = df["Close"].rolling(window=50).mean()
    df["ema_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["retorno"] = df["Close"].pct_change()
    df["retorno_acum"] = (1 + df["retorno"]).cumprod() - 1
    df["volatilidade"] = (
        df["retorno"].rolling(window=20).std() * (252 ** 0.5) * 100
    )

    return df


def processar_todos(df: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for ticker, grupo in df.groupby("ticker"):
        processado = calcular_metricas(grupo)
        frames.append(processado)
    return pd.concat(frames)