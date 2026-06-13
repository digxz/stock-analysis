from src.ingest import buscar_multiplos
from src.transform import processar_todos
from src.database import salvar, carregar

TICKERS = ["PETR4.SA", "VALE3.SA", "AAPL"]

print("1. Buscando cotações...")
df_raw = buscar_multiplos(TICKERS, periodo="1y")
print(f"   {len(df_raw)} linhas brutas\n")

print("2. Calculando métricas...")
df = processar_todos(df_raw)
print(f"   Colunas: {list(df.columns)}\n")

print("3. Salvando no DuckDB...")
salvar(df.reset_index())

print("4. Lendo do banco...")
df_lido = carregar(TICKERS)
print(df_lido[["ticker","Close","sma_20","ema_20","volatilidade"]].tail(6))

print("\nPipeline OK!")
