import fundamentus
import pandas as pd
from datetime import datetime, timedelta
from tabulate import tabulate
from fundamentus_proventos import get_proventos
import warnings
warnings.filterwarnings('ignore')

def analisa_acoes():
    """Analisa ações com base nos três critérios fundamentalistas"""
    
    print("\nAnalisando ações da B3...")
    print("\nCritérios de Análise:")
    print("1. Liquidez mínima diária: R$ 3.000.000")
    print("2. Histórico de pagamentos de Dividendos por mais de 5 anos")
    print("3. Altos Dividendos médios nos últimos 3 anos")
    
    # Obtém dados básicos de todas as ações
    df = fundamentus.get_resultado_raw()
    df.reset_index(inplace=True)
    
    # Primeiro filtro: Liquidez
    df_filtrado = df[df['Liq.2meses'] > 3000000].copy()
    print(f"\nAções com liquidez > R$ 3M: {len(df_filtrado)}")
    
    resultados = []
    
    # Analisa cada ação que passou no filtro de liquidez
    for _, row in df_filtrado.iterrows():
        ticker = row['papel']
        try:
            print(f"\nAnalisando {ticker}...")
            
            # Obtém histórico de proventos
            proventos = get_proventos(ticker)
            if proventos.empty:
                print(f"{ticker}: Sem histórico de proventos")
                continue
            
            # Filtra apenas dividendos (exclui JCP por enquanto)
            dividendos = proventos[proventos['Tipo'].str.contains('DIVIDENDO', case=False, na=False)]
            
            # Verifica histórico de 5+ anos
            anos_pagando = dividendos['Data'].dt.year.nunique()
            if anos_pagando < 5:
                print(f"{ticker}: Menos de 5 anos de histórico ({anos_pagando} anos)")
                continue
                
            # Calcula dados dos últimos 12 meses
            um_ano_atras = datetime.now() - timedelta(days=365)
            dividendos_12m = dividendos[dividendos['Data'] >= um_ano_atras]
            total_12m = dividendos_12m['Valor'].sum()
            
            # Calcula média dos últimos 3 anos
            tres_anos_atras = datetime.now() - timedelta(days=3*365)
            dividendos_3y = dividendos[dividendos['Data'] >= tres_anos_atras]
            media_3y = dividendos_3y['Valor'].sum() / 3
            
            # Calcula DY usando preço atual
            preco_atual = row['Cotação']
            dy_atual = (total_12m / preco_atual) * 100
            dy_medio_3y = (media_3y / preco_atual) * 100
            
            # Obtém dados adicionais
            detalhes = fundamentus.get_papel(ticker)
            setor = detalhes['Setor'].iloc[0] if 'Setor' in detalhes else 'N/A'
            
            # Adiciona JCP aos cálculos
            jcp = proventos[proventos['Tipo'].str.contains('JRS CAP|JUROS', case=False, na=False)]
            if not jcp.empty:
                # Últimos 12 meses
                jcp_12m = jcp[jcp['Data'] >= um_ano_atras]['Valor'].sum()
                total_12m += jcp_12m
                
                # Média 3 anos
                jcp_3y = jcp[jcp['Data'] >= tres_anos_atras]['Valor'].sum() / 3
                media_3y += jcp_3y
                
                # Recalcula DY com JCP
                dy_atual = (total_12m / preco_atual) * 100
                dy_medio_3y = (media_3y / preco_atual) * 100
            
            resultados.append({
                'Ticker': ticker,
                'Setor': setor,
                'Preço': preco_atual,
                'P/VP': row['P/VP'],
                'DY Atual (%)': dy_atual,
                'DY Médio 3Y (%)': dy_medio_3y,
                'Anos Pagando': anos_pagando,
                'Total 12m': total_12m,
                'ROE (%)': row['ROE'] * 100,
                'Liquidez': row['Liq.2meses']
            })
            
            print(f"✓ {ticker} - {anos_pagando} anos | DY Atual: {dy_atual:.2f}% | DY Médio: {dy_medio_3y:.2f}%")
            
        except Exception as e:
            print(f"Erro ao processar {ticker}: {str(e)}")
            continue
    
    if not resultados:
        print("\nNenhuma ação atendeu a todos os critérios!")
        return
    
    # Cria DataFrame com resultados
    df_final = pd.DataFrame(resultados)
    
    # Ordena por DY médio
    df_final = df_final.sort_values('DY Médio 3Y (%)', ascending=False)
    
    # Formata números para exibição
    df_display = df_final.copy()
    df_display['Preço'] = df_display['Preço'].apply(lambda x: f"R$ {x:.2f}")
    df_display['P/VP'] = df_display['P/VP'].apply(lambda x: f"{x:.2f}")
    df_display['DY Atual (%)'] = df_display['DY Atual (%)'].apply(lambda x: f"{x:.2f}%")
    df_display['DY Médio 3Y (%)'] = df_display['DY Médio 3Y (%)'].apply(lambda x: f"{x:.2f}%")
    df_display['ROE (%)'] = df_display['ROE (%)'].apply(lambda x: f"{x:.2f}%")
    df_display['Liquidez'] = df_display['Liquidez'].apply(lambda x: f"R$ {x:,.2f}")
    
    # Mostra TOP 10
    print("\nTOP 10 - Melhores Pagadoras de Dividendos:")
    df_top10 = df_display.head(10).copy()
    colunas = ['Ticker', 'Setor', 'Preço', 'P/VP', 'DY Atual (%)', 'DY Médio 3Y (%)', 'Anos Pagando', 'ROE (%)']
    print(tabulate(df_top10[colunas], headers='keys', tablefmt='grid', showindex=False))
    
    # Mostra análise por setor (baseado no TOP 10)
    print("\nMelhores Ações por Setor (do TOP 10):")
    df_setores = df_top10.drop_duplicates(subset=['Setor'], keep='first')
    df_setores = df_setores.sort_values('DY Médio 3Y (%)', ascending=False)
    print(tabulate(df_setores[colunas], headers='keys', tablefmt='grid', showindex=False))
    
    # Mostra estatísticas do TOP 10
    dy_medio = pd.to_numeric(df_top10['DY Médio 3Y (%)'].str.rstrip('%')).mean()
    print(f"\nDividend Yield médio do TOP 10: {dy_medio:.2f}%")
    
    setores_representados = len(df_setores)
    print(f"Setores representados no TOP 10: {setores_representados}")
    print("\nSetores presentes no TOP 10:")
    for setor in df_setores['Setor'].unique():
        tickers = df_top10[df_top10['Setor'] == setor]['Ticker'].tolist()
        print(f"- {setor}: {', '.join(tickers)}")

if __name__ == "__main__":
    analisa_acoes() 