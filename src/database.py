# src/database.py
import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "stocks.db"

COLUNAS = [
    "Date", "ticker", "Open", "High", "Low", "Close", "Volume",
    "sma_20", "sma_50", "ema_20", "retorno", "retorno_acum", "volatilidade"
]


def get_conn() -> duckdb.DuckDBPyConnection:
    DB_PATH.parent.mkdir(exist_ok=True)
    return duckdb.connect(str(DB_PATH))


def criar_tabela() -> None:
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cotacoes (
                Date         TIMESTAMP,
                ticker       VARCHAR,
                Open         DOUBLE,
                High         DOUBLE,
                Low          DOUBLE,
                Close        DOUBLE,
                Volume       BIGINT,
                sma_20       DOUBLE,
                sma_50       DOUBLE,
                ema_20       DOUBLE,
                retorno      DOUBLE,
                retorno_acum DOUBLE,
                volatilidade DOUBLE,
                PRIMARY KEY (Date, ticker)
            )
        """)


def salvar(df: pd.DataFrame) -> None:
    criar_tabela()

    # Garante ordem e colunas corretas
    dados = df[COLUNAS].copy()

    with get_conn() as conn:
        # Registra o DataFrame como view temporária
        conn.register("df_temp", dados)
        conn.execute("""
            INSERT INTO cotacoes
            SELECT * FROM df_temp
            ON CONFLICT (Date, ticker) DO UPDATE SET
                Open         = EXCLUDED.Open,
                High         = EXCLUDED.High,
                Low          = EXCLUDED.Low,
                Close        = EXCLUDED.Close,
                Volume       = EXCLUDED.Volume,
                sma_20       = EXCLUDED.sma_20,
                sma_50       = EXCLUDED.sma_50,
                ema_20       = EXCLUDED.ema_20,
                retorno      = EXCLUDED.retorno,
                retorno_acum = EXCLUDED.retorno_acum,
                volatilidade = EXCLUDED.volatilidade
        """)
        conn.unregister("df_temp")

    print(f"  Salvo: {len(dados)} registros no banco.")


def carregar(tickers: list[str] | None = None) -> pd.DataFrame:
    with get_conn() as conn:
        if tickers:
            lista = ", ".join(f"'{t.upper()}'" for t in tickers)
            query = f"SELECT * FROM cotacoes WHERE ticker IN ({lista}) ORDER BY ticker, Date"
        else:
            query = "SELECT * FROM cotacoes ORDER BY ticker, Date"

        df = conn.execute(query).df()

    df["Date"] = pd.to_datetime(df["Date"])
    return df.set_index("Date")