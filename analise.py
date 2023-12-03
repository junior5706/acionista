import pandas as pd
from tabulate import tabulate
from datetime import datetime
import sys

# Constants
CRITERIO_VALORIZACAO_VENDA = 2.0
LIMITE_VENDA_MES = 20000.00  # Limit of R$20,000 for monthly sales
# valor_disponivel_para_compra = 589.98  # Value available for purchase
valor_disponivel_para_compra = float(sys.argv[1])  # Value available for purchase
alpha = 0.5
PERCENT_ABOVE_MIN = 1.10
PERCENT_BELOW_MAX = 0.90
PERCENT_NEAR_MAX_PURCHASE = 0.90
VOLATILITY_THRESHOLD = 10
LEVERAGE_THRESHOLD = 1
LIQUIDITY_THRESHOLD = 1
ROE_THRESHOLD = 10
TAKE_PROFIT_CRITERIA = 10.0 

# Weights for sell criteria
PESOS_VENDA = {
    "Preço próximo do máximo de 52 semanas. ": 0.2,
    "Preço abaixo do stop loss ponderado. ": 0.3,
    "Ação comprada próximo do máximo de 52 semanas. ": 0.1,
    "Declínio no lucro líquido nos últimos 3 meses. ": 0.1,
    "Declínio na receita líquida nos últimos 3 meses. ": 0.1,
    "Alta alavancagem financeira. ": 0.05,
    "Problemas de liquidez. ": 0.05,
    "Baixa rentabilidade (ROE). ": 0.1
}

# Weights for buy criteria
PESOS_COMPRA = {
    "Preço próximo do mínimo de 52 semanas. ": 0.4,
    "Boa valorização nos últimos 12 meses. ": 0.3,
    "Boa liquidez corrente. ": 0.1,
    "Alta rentabilidade (ROIC e ROE). ": 0.1,
    "Baixa alavancagem financeira. ": 0.1
}

# Load Data
transacoes = pd.read_csv('ResumoNegociacao.csv', sep=';', decimal=',', thousands='.', parse_dates=['Dt. Negociação'], dayfirst=True)
transacoes = transacoes.rename(columns={"Ativo": "Papel"})
transacoes['Papel'] = transacoes['Papel'].str.strip()
compras = transacoes[transacoes['Quantidade Compra'] > 0].copy()
vendas = transacoes[transacoes['Quantidade Venda'] > 0].copy()
vendas.loc[:, 'Ano'] = vendas['Dt. Negociação'].dt.year
vendas.loc[:, 'Mes'] = vendas['Dt. Negociação'].dt.month
valor_total_vendido_mes = vendas.groupby(['Ano', 'Mes']).agg({'Financeiro Venda': 'sum'}).reset_index()
# Obter mês e ano atuais
ano_atual, mes_atual = datetime.now().year, datetime.now().month
vendas_mes_atual = valor_total_vendido_mes[(valor_total_vendido_mes['Ano'] == ano_atual) & (valor_total_vendido_mes['Mes'] == mes_atual)]
if vendas_mes_atual.empty:
    valor_restante_para_venda = LIMITE_VENDA_MES
else:
    valor_restante_para_venda = LIMITE_VENDA_MES - vendas_mes_atual['Financeiro Venda'].sum()

total_compras = compras.groupby('Papel').agg({'Quantidade Compra': 'sum', 'Financeiro Compra': 'sum'})
total_vendas = vendas.groupby('Papel').agg({'Quantidade Venda': 'sum', 'Financeiro Venda': 'sum'})
total_compras = total_compras.reindex(total_vendas.index.union(total_compras.index)).fillna(0)
total_vendas = total_vendas.reindex(total_compras.index).fillna(0)
total_compras['Quantidade Atual'] = total_compras['Quantidade Compra'] - total_vendas['Quantidade Venda']
mask = total_compras['Quantidade Compra'] > 0
total_compras.loc[mask, 'Preço Medio Pago'] = total_compras['Financeiro Compra'] / total_compras['Quantidade Compra']
carteira_df = total_compras[total_compras['Quantidade Atual'] > 0][['Quantidade Atual', 'Preço Medio Pago']].reset_index()
carteira_df['Papel'] = carteira_df['Papel'].str.rstrip('F')
resultado_df = pd.read_csv('resultado.csv')
resultado_df['Cotação'] = resultado_df['Cotacao']
resultado_df["Dividendo por Ação (R$)"] = resultado_df["Cotação"] * (resultado_df["Div_Yield"] / 100)
resultado_df["Quantidade Ações Alocadas Simulada"] = (1000 / resultado_df["Cotacao"]).astype(int)
resultado_df["Div. Yield Real a Cada R$1000 Alocado (R$)"] = resultado_df["Dividendo por Ação (R$)"] * resultado_df["Quantidade Ações Alocadas Simulada"]

# Define Maximum Allowed Price for Purchase based on 52-week minimum
resultado_df['Preço Máximo Permitido Para Comprar'] = resultado_df['Min_52_sem'] * PERCENT_ABOVE_MIN

# Analyze Current Portfolio
carteira_analise = pd.merge(carteira_df, resultado_df, on='Papel', how='left')
carteira_analise['Valor da Posição'] = carteira_analise['Cotacao'] * carteira_analise['Quantidade Atual']
carteira_analise['Stop Loss'] = alpha * carteira_analise['Preço Medio Pago'] + (1 - alpha) * carteira_analise['Min_52_sem']
carteira_analise['Cotação Atual'] = carteira_analise['Cotacao']
carteira_analise['Cotação'] = carteira_analise['Cotacao']
carteira_analise['Min 52 sem'] = carteira_analise['Min_52_sem'].apply(lambda x: round(x, 2))
carteira_analise['Max 52 sem'] = carteira_analise['Max_52_sem'].apply(lambda x: round(x, 2))
carteira_analise['Diferença Para Min (%)'] = ((carteira_analise['Cotacao'] - carteira_analise['Min 52 sem']) / carteira_analise['Min 52 sem']) * 100
carteira_analise['Diferença Para Max (%)'] = ((carteira_analise['Cotacao'] - carteira_analise['Max 52 sem']) / carteira_analise['Max 52 sem']) * 100
carteira_analise['Take Profit'] = carteira_analise['Preço Medio Pago'] * (1 + TAKE_PROFIT_CRITERIA/100)
carteira_analise['Div. Yield (%)'] = carteira_analise['Div_Yield'].apply(lambda x: round(x, 2))
carteira_analise['Setor'] = carteira_analise['Setor'].str.strip()
carteira_analise['Preço Medio Pago'] = carteira_analise['Preço Medio Pago'].apply(lambda x: round(x, 2))
carteira_analise['Diferença do Preço Médio Pago (%)'] = ((carteira_analise['Cotacao'] - carteira_analise['Preço Medio Pago']) / carteira_analise['Preço Medio Pago']) * 100
carteira_analise['Div. Yield De Ações na Carteira (R$)'] = carteira_analise['Dividendo por Ação (R$)'] * carteira_analise['Quantidade Atual']
carteira_analise['Media Div. Yield De Ações na Carteira (R$)'] = carteira_analise['Div. Yield (%)'].sum() / carteira_analise['Quantidade Atual'].count()
carteira_analise['Total Div. Yield De Ações na Carteira (R$)'] = carteira_analise['Div. Yield De Ações na Carteira (R$)'].sum()
carteira_analise['Media de valor mensal de dividendos na carteira (R$)'] = carteira_analise['Div. Yield De Ações na Carteira (R$)'].sum() / 12
carteira_analise['Lucro Líquido (Últimos 3 meses)'] = carteira_analise['Lucro_Liquido_3m'].apply(lambda x: round(x, 2))
carteira_analise['Lucro Líquido (Últimos 12 meses)'] = carteira_analise['Lucro_Liquido_12m'].apply(lambda x: round(x, 2))
carteira_analise['Receita Líquida (Últimos 3 meses)'] = carteira_analise['Receita_Liquida_3m'].apply(lambda x: round(x, 2))
carteira_analise['Receita Líquida (Últimos 12 meses)'] = carteira_analise['Receita_Liquida_12m'].apply(lambda x: round(x, 2))
carteira_analise['Dív. Líquida'] = carteira_analise['Div_Liquida'].apply(lambda x: round(x, 2))
carteira_analise['Dív. Bruta'] = carteira_analise['Div_Bruta'].apply(lambda x: round(x, 2))
carteira_analise['Patrim. Líq'] = carteira_analise['Patrim_Liq'].apply(lambda x: round(x, 2))
carteira_analise['Ativo Circulante'] = carteira_analise['Ativo_Circulante'].apply(lambda x: round(x, 2))
carteira_analise['ROE (%)'] = carteira_analise['ROE'].apply(lambda x: round(x, 2))

# Recommendations for Sale based on various criteria
motivos_venda = []
pesos_venda_total = []
precos_recomendados_venda = []

for idx, row in carteira_analise.iterrows():
    motivo = ""
    peso_total = 0
    preco_recomendado = row['Cotação Atual']

    if row['Preço Medio Pago'] >= row['Max 52 sem'] * PERCENT_NEAR_MAX_PURCHASE:
        motivo += "Ação comprada próximo do máximo de 52 semanas. "
        peso_total += PESOS_VENDA["Ação comprada próximo do máximo de 52 semanas. "]
        preco_recomendado *= 0.98
    elif row['Cotação Atual'] >= row['Max 52 sem'] * PERCENT_BELOW_MAX:
        motivo += "Preço próximo do máximo de 52 semanas. "
        peso_total += PESOS_VENDA["Preço próximo do máximo de 52 semanas. "]
        preco_recomendado *= 1.05
    elif row['Cotação Atual'] < row['Stop Loss']:
        motivo += "Preço abaixo do stop loss ponderado. "
        peso_total += PESOS_VENDA["Preço abaixo do stop loss ponderado. "]
        preco_recomendado *= 0.97
    elif row['Lucro Líquido (Últimos 3 meses)'] < row['Lucro Líquido (Últimos 12 meses)'] / 4:
        motivo += "Declínio no lucro líquido nos últimos 3 meses. "
        peso_total += PESOS_VENDA["Declínio no lucro líquido nos últimos 3 meses. "]
        preco_recomendado *= 0.96
    elif row['Receita Líquida (Últimos 3 meses)'] < row['Receita Líquida (Últimos 12 meses)'] / 4:
        motivo += "Declínio na receita líquida nos últimos 3 meses. "
        peso_total += PESOS_VENDA["Declínio na receita líquida nos últimos 3 meses. "]
        preco_recomendado *= 0.96
    elif row['Dív. Líquida'] / row['Patrim. Líq'] > LEVERAGE_THRESHOLD:
        motivo += "Alta alavancagem financeira. "
        peso_total += PESOS_VENDA["Alta alavancagem financeira. "]
        preco_recomendado *= 0.95
    elif row['Ativo Circulante'] / row['Dív. Bruta'] < LIQUIDITY_THRESHOLD:
        motivo += "Problemas de liquidez. "
        peso_total += PESOS_VENDA["Problemas de liquidez. "]
        preco_recomendado *= 0.95
    elif row['ROE (%)'] < ROE_THRESHOLD:
        motivo += "Baixa rentabilidade (ROE). "
        peso_total += PESOS_VENDA["Baixa rentabilidade (ROE). "]
        preco_recomendado *= 0.97
    motivos_venda.append(motivo.strip())
    pesos_venda_total.append(peso_total)
    precos_recomendados_venda.append(preco_recomendado)

carteira_analise['Motivos Para Considerar Vender'] = motivos_venda
carteira_analise['Peso da Venda'] = pesos_venda_total
acoes_venda = carteira_analise[carteira_analise['Motivos Para Considerar Vender'] != ""].copy()
acoes_venda['Valor Venda'] = acoes_venda['Cotação'] * acoes_venda['Quantidade Atual']
acoes_venda['Lucro ou Prejuizo Esperado'] = (acoes_venda['Cotação'] - acoes_venda['Preço Medio Pago']) * acoes_venda['Quantidade Atual']

# Adjust the sale recommendations based on the monthly sale limit
acoes_venda['Valor Venda Ajustado'] = acoes_venda['Valor Venda'].where(acoes_venda['Valor Venda'] <= valor_restante_para_venda, valor_restante_para_venda)
acoes_venda['Quantidade Sugerida para Vender'] = (acoes_venda['Valor Venda Ajustado'] / acoes_venda['Cotação']).astype(int)

acoes_venda["Preço Para Vender R$"] = precos_recomendados_venda


# Define Buy Recommendations based on the 52-week minimum and available funds
acoes_compra = resultado_df[resultado_df['Cotação'] <= resultado_df['Preço Máximo Permitido Para Comprar']].copy()
acoes_compra['ROIC'] = pd.to_numeric(acoes_compra['ROIC'], errors='coerce')
# Filtering out stocks with low trading volume
acoes_compra = acoes_compra[acoes_compra['Vol_med_2m'] > 100000]
acoes_compra['Dív. Líquida'] = acoes_compra['Div_Liquida'].apply(lambda x: round(x, 2))
acoes_compra['Dív. Bruta'] = acoes_compra['Div_Bruta'].apply(lambda x: round(x, 2))
acoes_compra['Patrim. Líq'] = acoes_compra['Patrim_Liq'].apply(lambda x: round(x, 2))
acoes_compra['Ativo Circulante'] = acoes_compra['Ativo_Circulante'].apply(lambda x: round(x, 2))
acoes_compra['ROIC (%)'] = acoes_compra['ROIC']
acoes_compra['ROE (%)'] = acoes_compra['ROE']


# Buy Recommendations based on various criteria
motivos_compra = []
pesos_compra_total = []
precos_recomendados_compra = []

for idx, row in acoes_compra.iterrows():
    motivo = ""
    peso_total = 0
    preco_recomendado = row['Cotação']

    if row['Cotação'] <= row['Preço Máximo Permitido Para Comprar']:
        motivo += "Preço próximo do mínimo de 52 semanas. "
        peso_total += PESOS_COMPRA["Preço próximo do mínimo de 52 semanas. "]
        preco_recomendado *= 0.98
        
    if row['Dív. Bruta'] == 0 or row['Ativo Circulante'] / row['Dív. Bruta'] > 1.5:
        motivo += "Boa liquidez corrente. "
        peso_total += PESOS_COMPRA["Boa liquidez corrente. "]
        preco_recomendado *= 1.02

    if row['ROIC (%)'] > 10 and row['ROE (%)'] > 10:
        motivo += "Alta rentabilidade (ROIC e ROE). "
        peso_total += PESOS_COMPRA["Alta rentabilidade (ROIC e ROE). "]
        preco_recomendado *= 1.03

    if row['Dív. Líquida'] / row['Patrim. Líq'] < 0.5:
        motivo += "Baixa alavancagem financeira. "
        peso_total += PESOS_COMPRA["Baixa alavancagem financeira. "]
        preco_recomendado *= 1.01

    motivos_compra.append(motivo.strip())
    pesos_compra_total.append(peso_total)
    precos_recomendados_compra.append(preco_recomendado)

acoes_compra['Motivos Para Considerar Comprar'] = motivos_compra
acoes_compra['Peso da Compra'] = pesos_compra_total
acoes_compra['Preço Para Comprar R$'] = precos_recomendados_compra

acoes_compra['Valor Alocado Inicial'] = (acoes_compra['Peso da Compra'] / sum(acoes_compra['Peso da Compra'])) * valor_disponivel_para_compra
acoes_compra['Quantidade Inicial'] = acoes_compra.apply(lambda row: int(row['Valor Alocado Inicial'] / row['Cotação']) if row['Valor Alocado Inicial'] >= row['Cotação'] else 0, axis=1)
acoes_compra['Valor Alocado Real'] = acoes_compra['Quantidade Inicial'] * acoes_compra['Cotação']
saldo_restante = valor_disponivel_para_compra - acoes_compra['Valor Alocado Real'].sum()
acoes_compra = acoes_compra.sort_values(by='Peso da Compra', ascending=False)
for idx, row in acoes_compra.iterrows():
    if saldo_restante <= 0:
        break
    if saldo_restante >= row['Cotação']:
        quantidade_adicional = int(saldo_restante / row['Cotação'])
        acoes_compra.loc[idx, 'Quantidade Inicial'] += quantidade_adicional
        saldo_restante -= quantidade_adicional * row['Cotação']

acoes_compra['Quantidade Para Comprar'] = acoes_compra['Quantidade Inicial']
acoes_compra['Valor da Alocação R$'] = acoes_compra['Quantidade Para Comprar'] * acoes_compra['Cotação']


# First, merge acoes_compra and acoes_venda
combinado = pd.merge(acoes_compra[['Papel', 'Motivos Para Considerar Comprar', 'Peso da Compra', 'Preço Para Comprar R$', 'Quantidade Para Comprar', 'Valor da Alocação R$']],
                       acoes_venda[['Papel', 'Motivos Para Considerar Vender', 'Peso da Venda', 'Quantidade Sugerida para Vender', 'Lucro ou Prejuizo Esperado', 'Preço Para Vender R$']],
                       on='Papel', how='outer', suffixes=('_compra', '_venda'))

# Then, merge the result with carteira_analise
combinado_final = pd.merge(combinado, carteira_analise[['Papel', 'Cotação Atual', 'Valor da Posição', 'Stop Loss', 'Min 52 sem', 'Max 52 sem', 'Take Profit', 'Div. Yield (%)', 'Setor', 'Preço Medio Pago', 'Diferença Para Min (%)', 'Diferença Para Max (%)', 'Dividendo por Ação (R$)', 'Div. Yield Real a Cada R$1000 Alocado (R$)', 'Div. Yield De Ações na Carteira (R$)']],
                           on='Papel', how='outer')

# Determining which action to take based on the weight
combinado_final['Ação'] = combinado_final.apply(lambda row: 'Compra' if row['Peso da Compra'] > row['Peso da Venda'] else 'Venda', axis=1)

# Splitting back into buy and sell DataFrames based on the determined action
acoes_compra_final = combinado_final[combinado_final['Ação'] == 'Compra']

acoes_na_carteira = set(carteira_df['Papel'].unique())
acoes_venda_final = combinado_final[combinado_final['Ação'] == 'Venda']

#exclude stocks that are not in the portfolio
acoes_venda_final = acoes_venda_final[acoes_venda_final['Papel'].isin(acoes_na_carteira)]

# Print Recommendations
print('Recomendações de Venda:')
print(tabulate(acoes_venda_final[['Papel', 'Cotação Atual', 'Diferença Para Max (%)', 'Min 52 sem', 'Max 52 sem', 'Take Profit', 'Preço Para Vender R$', 'Peso da Venda', 'Stop Loss', 'Div. Yield (%)', 'Dividendo por Ação (R$)', 'Setor', 'Motivos Para Considerar Vender']], headers='keys', tablefmt='grid', maxcolwidths=10, maxheadercolwidths=10))

print('Recomendações de Compra:')
print(tabulate(acoes_compra_final[['Papel', 'Cotação Atual', 'Diferença Para Min (%)', 'Min 52 sem', 'Max 52 sem', 'Peso da Compra', 'Quantidade Para Comprar', 'Preço Para Comprar R$', 'Valor da Alocação R$', 'Div. Yield (%)', 'Dividendo por Ação (R$)', 'Setor', 'Motivos Para Considerar Comprar']], headers='keys', tablefmt='grid', maxcolwidths=10, maxheadercolwidths=10))

print('Resumo Atual da Carteira:')
print(tabulate(carteira_analise[['Papel', 'Preço Medio Pago', 'Cotação Atual', 'Diferença do Preço Médio Pago (%)', 'Min 52 sem', 'Max 52 sem', 'Valor da Posição', 'Quantidade Atual', 'Stop Loss', 'Take Profit', 'Setor']], headers='keys', tablefmt='grid', maxcolwidths=10, maxheadercolwidths=10))

print('Resumo de Dividendos da Carteira:')
print(tabulate(carteira_analise[['Papel', 'Div. Yield (%)', 'Dividendo por Ação (R$)', 'Div. Yield Real a Cada R$1000 Alocado (R$)', 'Quantidade Atual', 'Div. Yield De Ações na Carteira (R$)', 'Setor']], headers='keys', tablefmt='grid', maxcolwidths=10, maxheadercolwidths=10))

print('Limite de Venda Mensal: R$' + str(LIMITE_VENDA_MES))
print('Valor Restante para Venda: R$' + str(valor_restante_para_venda))
print('Media Div. Yield De Ações na Carteira (R$): ' + str(carteira_analise['Media Div. Yield De Ações na Carteira (R$)'][0]))
print('Total Div. Yield De Ações na Carteira (R$): ' + str(carteira_analise['Total Div. Yield De Ações na Carteira (R$)'][0]))
print('Media de valor mensal de dividendos na carteira (R$): ' + str(carteira_analise['Media de valor mensal de dividendos na carteira (R$)'][0]))
