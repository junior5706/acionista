import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
from tabulate import tabulate
import pytz
import warnings
warnings.filterwarnings('ignore')

def get_dividend_history(ticker, years=5):
    """Obtém o histórico de dividendos de uma ação nos últimos X anos"""
    # Adiciona .SA ao ticker para buscar na B3
    ticker_sa = f"{ticker}.SA"
    print(f"\nAnalisando {ticker_sa}...")
    
    try:
        # Obtém os dados do Yahoo Finance
        stock = yf.Ticker(ticker_sa)
        
        # Adicionar obtenção do P/VP
        info = stock.info
        pvp = info.get('priceToBook', 0)  # Obtém P/VP, retorna 0 se não disponível
        
        # Adicionar obtenção do setor
        sector = info.get('sector', 'N/A')  # 'N/A' se não encontrar o setor
        
        # Debug dos dados disponíveis
        actions = stock.actions
        if actions.empty:
            print("Nenhum dado de ações encontrado")
            return None, 0, False, 0, 0, 0, 0, 'N/A'
            
        print(f"Ações disponíveis: {actions}")
        
        # Tenta obter o preço atual do histórico
        hist = stock.history(period="1d")
        if hist.empty:
            print("Erro: Não foi possível obter histórico de preços")
            return None, 0, False, 0, 0, 0, 0, 'N/A'
            
        current_price = hist['Close'].iloc[-1]
        print(f"Preço atual: R$ {current_price:.2f}")
        
        # Obtém dividendos das actions
        if 'Dividends' not in actions.columns:
            print("Nenhum dividendo encontrado")
            return None, 0, False, 0, 0, 0, 0, 'N/A'
            
        dividends = actions['Dividends']
        dividends = dividends[dividends > 0]
        
        if dividends.empty:
            print("Nenhum dividendo encontrado")
            return None, 0, False, 0, 0, 0, 0, 'N/A'
            
        # Primeiro verifica se tem 5+ anos de pagamentos no histórico completo
        all_years_with_payments = len(dividends.groupby(dividends.index.year))
        print(f"Anos com pagamentos: {all_years_with_payments}")
        consistent_5y = all_years_with_payments >= 5
        
        # Calcula as datas para análise dos últimos anos
        end_date = datetime.now(pytz.UTC)
        start_date = end_date - timedelta(days=years*365)
        
        # Converte o index para UTC se necessário
        if dividends.index.tz is None:
            dividends.index = dividends.index.tz_localize('UTC')
        else:
            dividends.index = dividends.index.tz_convert('UTC')
        
        # Filtra pelos últimos X anos para análise de DY
        recent_dividends = dividends[dividends.index >= start_date]
        
        if len(recent_dividends) == 0:
            print(f"Nenhum dividendo nos últimos {years} anos")
            return None, 0, consistent_5y, 0, all_years_with_payments, pvp, 0, 'N/A'
        
        # Calcula a média dos últimos 3 anos
        three_year_start = end_date - timedelta(days=3*365)
        last_3y_dividends = recent_dividends[recent_dividends.index >= three_year_start]
        
        if len(last_3y_dividends) == 0:
            avg_3y_dividend_yield = 0
        else:
            avg_3y_dividend_yield = (sum(last_3y_dividends) / 3 / current_price) * 100
        
        # Calcular DY atual (últimos 12 meses)
        one_year_ago = end_date - timedelta(days=365)
        last_year_dividends = dividends[dividends.index >= one_year_ago]
        current_dy = (sum(last_year_dividends) / current_price) * 100
        
        print(f"✓ DY Atual: {current_dy:.2f}% | DY Médio: {avg_3y_dividend_yield:.2f}% | Anos pagando: {all_years_with_payments} | P/VP: {pvp:.2f} | Setor: {sector}")
        return dividends, avg_3y_dividend_yield, consistent_5y, current_price, all_years_with_payments, pvp, current_dy, sector
    except Exception as e:
        print(f"Erro: {str(e)}")
        return None, 0, False, 0, 0, 0, 0, 'N/A'

def main():
    # Importa os tickers do primeiro script
    import estrategia_dividendos
    tickers = estrategia_dividendos.df_final['Papel'].tolist()
    
    print("\nAnalisando histórico de dividendos...")
    print("Isso pode demorar alguns minutos...")
    
    # Lista para armazenar os resultados
    results_list = []
    
    # Analisa cada ticker
    for ticker in tickers:
        try:
            _, avg_3y_yield, consistent_5y, current_price, years_paying, pvp, current_dy, sector = get_dividend_history(ticker)
            
            if consistent_5y and avg_3y_yield > 0:
                results_list.append({
                    'Ticker': ticker,
                    'Setor': sector,
                    'Preço': current_price,
                    'P/VP': pvp,
                    'DY Atual': current_dy,
                    'DY Médio 3 Anos': avg_3y_yield,
                    'Anos Pagando': years_paying,
                    'Histórico 5+ Anos': consistent_5y
                })
        except Exception as e:
            print(f"Erro ao processar {ticker}: {str(e)}")
            continue
    
    # Cria DataFrame e ordena por DY
    if results_list:
        df_results = pd.DataFrame(results_list)
        df_results = df_results.sort_values('DY Médio 3 Anos', ascending=False)
        
        df_top10 = df_results.head(10).copy()
        df_top10.insert(0, 'Ranking', range(1, len(df_top10) + 1))
        
        # Formatação das colunas (removendo Histórico 5+ Anos e Status)
        df_top10['Preço'] = df_top10['Preço'].apply(lambda x: f"R$ {x:.2f}")
        df_top10['P/VP'] = df_top10['P/VP'].apply(lambda x: f"{x:.2f}")
        df_top10['DY Atual'] = df_top10['DY Atual'].apply(lambda x: f"{x:.2f}%")
        df_top10['DY Médio 3 Anos'] = df_top10['DY Médio 3 Anos'].apply(lambda x: f"{x:.2f}%")
        df_top10['Anos Pagando'] = df_top10['Anos Pagando'].apply(lambda x: f"{x} anos")
        
        # Selecionar apenas as colunas que queremos mostrar
        colunas_para_mostrar = ['Ranking', 'Ticker', 'Setor', 'Preço', 'P/VP', 'DY Atual', 'DY Médio 3 Anos', 'Anos Pagando']
        df_top10 = df_top10[colunas_para_mostrar]
        
        print("\nTOP 10 - Ranking de Ações por Dividend Yield")
        print("Ordenado por DY Médio dos últimos 3 anos (maiores primeiro)")
        print(tabulate(df_top10, headers='keys', tablefmt='grid', showindex=False))
        
        print("\nCritérios analisados:")
        print("1. ✓ Liquidez mínima diária de R$3 milhões")
        print("2. ✓ Histórico de pagamentos de Dividendos por mais de 5 anos")
        print("3. ✓ Altos Dividendos médios nos últimos 3 anos")
    else:
        print("\nNenhuma ação atendeu a todos os critérios!")

if __name__ == "__main__":
    main() 