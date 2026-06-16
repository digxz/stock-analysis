# src/ingest.py
import yfinance as yf
import pandas as pd



# Função com param. ticker obrigatório e string,
# e param.periodo opcional, com valor padrão de 1y, e string
# Retorna um Data Frame
def buscar_cotacoes(ticker: str, periodo: str = "1y") -> pd.DataFrame:
    """
    Busca cotações históricas de um ticker.

    Args:
        ticker:  símbolo da ação (ex: 'PETR4.SA', 'AAPL', 'VALE3.SA')
        periodo: '1mo', '3mo', '6mo', '1y', '2y', '5y'

    Returns:
        DataFrame com colunas: Open, High, Low, Close, Volume
    """

    # Armazena um objeto da classe Ticker
    ativo = yf.Ticker(ticker)
    # Requisição HTTP quw retorna um Data Frame
    df = ativo.history(period=periodo)


    # Tratamento de erro - Caso o DataFrame retorne vazio (True):
    if df.empty:
        raise ValueError(f"Ticker '{ticker}' não encontrado ou sem dados.")


    # Mantém só as colunas que vamos usar
    # O .copy() cria um novo DataFrame indepentende, e evita que o df seja apenas uma view do original
    df = df[["Open", "High", "Low", "Close", "Volume"]].copy()


    # Garante que o índice é só a data (sem fuso horário)
    # pd.to_datetime() garante que seja do tipo padrão de data do Pandas
    # tz_localize(None) remove a informação de fuso horário
    df.index = pd.to_datetime(df.index).tz_localize(None)
    df.index.name = "Date"


    # Adiciona coluna com o ticker para identificar a ação no banco
    # Importante no caso de pesquisa de dois ou mais ativos (identificação de qual 
    # linha pertence a qual ativo)
    df["ticker"] = ticker.upper()

    # Retorna o Data Frame final
    return df




# Agora o param. ticker se torna uma lista de string, de resto segue a mesma premissa
def buscar_multiplos(tickers: list[str], periodo: str = "1y") -> pd.DataFrame:
    """
    Busca cotações de vários tickers e retorna tudo num DataFrame único.
    """

    # Criação da lista vazia, servirá de armazenamento para os DFs retornados de cada ticker 
    frames = []

    # Loop pelos tickers dentro da lista recebida nos params.
    for ticker in tickers:
        
        try:
            # Reaproveita a função anterior
            df = buscar_cotacoes(ticker, periodo)
            
            # Adiciona o item df ao final da lista
            frames.append(df)

            # Retorna uma mensagem de sucesso - len(df) retorna o número de linhas do DF
            print(f"  OK  {ticker} — {len(df)} pregões")
        
        
        # Tratamento de erro, caso não tenha retorno no try
        except ValueError as e:
            print(f"  ERRO {e}")


    # Mesma coisa que frames == 0 ou len(frames) == 0
    if not frames:

        # Tratamento de erro (se a lista frames estiver vazia, 
        # é porque não foi adicionado nenhum ticker nela)
        raise RuntimeError("Nenhum ticker retornou dados.")

    # Retorna um Data Frame unificado, após o uso do concat na lista frames
    return pd.concat(frames)