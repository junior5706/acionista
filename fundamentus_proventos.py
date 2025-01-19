import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

def get_proventos(ticker):
    """
    Obtém o histórico de proventos de uma ação do site Fundamentus
    
    Args:
        ticker (str): Código da ação (ex: BRAP4)
        
    Returns:
        pandas.DataFrame: DataFrame com os proventos
    """
    url = f'https://www.fundamentus.com.br/proventos.php?papel={ticker}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Faz a requisição
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Levanta exceção para status codes de erro
        
        # Parse do HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Encontra a tabela de proventos
        table = soup.find('table', {'id': 'resultado'})
        if not table:
            return pd.DataFrame()
            
        # Extrai os headers
        headers = []
        for th in table.find_all('th'):
            headers.append(th.text.strip())
            
        # Extrai os dados
        rows = []
        for tr in table.find_all('tr')[1:]:  # Pula o header
            row = []
            for td in tr.find_all('td'):
                row.append(td.text.strip())
            if row:  # Ignora linhas vazias
                rows.append(row)
                
        # Cria o DataFrame
        df = pd.DataFrame(rows, columns=headers)
        
        # Converte as colunas para os tipos corretos
        if not df.empty:
            # Converte data
            df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y')
            
            # Converte valor (remove R$ e converte para float)
            df['Valor'] = df['Valor'].str.replace('R$ ', '').str.replace(',', '.').astype(float)
            
            # Ordena por data decrescente
            df = df.sort_values('Data', ascending=False)
            
        return df
        
    except Exception as e:
        print(f"Erro ao obter proventos de {ticker}: {str(e)}")
        return pd.DataFrame()

def print_proventos(ticker):
    """Imprime os proventos de forma formatada"""
    df = get_proventos(ticker)
    if df.empty:
        print(f"Nenhum provento encontrado para {ticker}")
        return
        
    print(f"\nProventos de {ticker}:")
    print("=" * 50)
    
    for _, row in df.iterrows():
        data = row['Data'].strftime('%d/%m/%Y')
        valor = f"R$ {row['Valor']:.4f}"
        tipo = row['Tipo']
        data_pagamento = row['Data Pagamento'] if 'Data Pagamento' in row else 'N/A'
        
        print(f"Data: {data} | Tipo: {tipo:12} | Valor: {valor:10} | Pagamento: {data_pagamento}")

if __name__ == "__main__":
    # Teste com BRAP4
    print_proventos('BRAP4') 