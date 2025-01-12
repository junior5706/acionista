import fundamentus
from tabulate import tabulate

# Critérios da estratégia (adaptados para dados disponíveis no Fundamentus)
liquidez_minima = 3000000  # Critério 1: R$ 3 milhões por dia
min_div_yield = 0.06  # Critério 3 (adaptado): mínimo de 6% ao ano
max_div_yield = 0.20  # Limite superior para evitar armadilhas de dividendos

# Obter dados do Fundamentus
df = fundamentus.get_resultado_raw()

# Transformar o índice 'Papel' em uma coluna regular
df.reset_index(inplace=True)

# Aplicar filtros básicos
df_filtrado = df[
    (df['Liq.2meses'] > liquidez_minima) &
    (df['Div.Yield'] > min_div_yield) &
    (df['Div.Yield'] < max_div_yield)
].copy()

# Adicionar coluna para o setor
df_filtrado['Setor'] = ''

# Buscar informações de setor para cada ação
for index, row in df_filtrado.iterrows():
    papel = row['papel']
    try:
        detalhes_papel = fundamentus.get_papel(papel)
        setor = detalhes_papel['Setor'][0]
        df_filtrado.at[index, 'Setor'] = setor
    except Exception as e:
        print(f"Erro ao obter informações para o papel {papel}: {e}")
        df_filtrado.at[index, 'Setor'] = 'Erro na obtenção de dados'

# Remover duplicatas mantendo apenas a ação mais líquida de cada empresa
df_filtrado['Raiz'] = df_filtrado['papel'].str.extract(r'([A-Za-z]+)')
df_filtrado.sort_values(by='Liq.2meses', ascending=False, inplace=True)
df_filtrado = df_filtrado.drop_duplicates(subset='Raiz', keep='first')

# Sistema de pontuação
df_filtrado['Pontuação'] = 0

# Pontuação por Dividend Yield
top_divyield = df_filtrado.nlargest(5, 'Div.Yield')['papel']
df_filtrado.loc[df_filtrado['papel'].isin(top_divyield), 'Pontuação'] += 2

# Pontuação por Liquidez
top_liquidez = df_filtrado.nlargest(5, 'Liq.2meses')['papel']
df_filtrado.loc[df_filtrado['papel'].isin(top_liquidez), 'Pontuação'] += 1

# Ordenar por Pontuação
df_filtrado.sort_values(by=['Pontuação', 'Div.Yield'], ascending=[False, False], inplace=True)

# Converter valores para percentuais mais legíveis
df_filtrado['Div.Yield'] = df_filtrado['Div.Yield'] * 100
df_filtrado['ROE'] = df_filtrado['ROE'] * 100
df_filtrado['Cresc. Rec.5a'] = df_filtrado['Cresc. Rec.5a'] * 100

# Selecionar e renomear colunas relevantes
colunas_finais = {
    'papel': 'Papel',
    'Setor': 'Setor',
    'Cotação': 'Cotação',
    'P/L': 'P/L',
    'P/VP': 'P/VP',
    'Div.Yield': 'Div.Yield%',
    'ROE': 'ROE%',
    'Liq.2meses': 'Liquidez',
    'Dív.Brut/ Patrim.': 'Dív/PL',
    'Pontuação': 'Score'
}

df_final = df_filtrado[colunas_finais.keys()].copy()
df_final.columns = colunas_finais.values()

# Formatar números para melhor visualização
df_final['Div.Yield%'] = df_final['Div.Yield%'].round(2)
df_final['ROE%'] = df_final['ROE%'].round(2)
df_final['P/L'] = df_final['P/L'].round(2)
df_final['P/VP'] = df_final['P/VP'].round(2)
df_final['Liquidez'] = df_final['Liquidez'].apply(lambda x: f"{x:,.0f}".replace(",", "."))
df_final['Cotação'] = df_final['Cotação'].round(2)
df_final['Dív/PL'] = df_final['Dív/PL'].round(2)

# Mostrar resultados no terminal
print("\nRanking de Ações por Dividendos")
print("Critérios implementados:")
print(f"1. Liquidez mínima: R$ {liquidez_minima:,.2f}")
print(f"2. Dividend Yield atual: entre {min_div_yield*100:.1f}% e {max_div_yield*100:.1f}%")
print("\nObservações:")
print("- Não foi possível implementar o critério de '5 anos de pagamento de dividendos'")
print("- O Div.Yield mostrado é apenas o atual, não a média de 3 anos")
print("\nResultados:")
print(tabulate(df_final, headers='keys', tablefmt='grid', showindex=False)) 