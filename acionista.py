import fundamentus
import os

# Verificar se o arquivo http_cache.sqlite existe no path atual e se existir apagar
if os.path.exists('http_cache.sqlite'):
    os.remove('http_cache.sqlite')

# Verificar se o arquivo resultado.xlsx existe no path atual e se existir apagar
if os.path.exists('resultado.xlsx'):
    os.remove('resultado.xlsx')

# Seus critérios e dados iniciais
minPVP = 0.5
maxPVP = 2
minPL = 3
maxPL = 10
minDivYield = 0.07  # 6%
maxDivYield = 0.14  # 14%
minROE = 0.15  # 15%
maxROE = 0.30  # 30%
liquidez_minima = 1000000  # R$ 1 milhão
crescimento_minimo = 0.10  # 10%

xlsx_path = "resultado.xlsx"

# Obter dados e aplicar filtro
df = fundamentus.get_resultado_raw()

# Transformar o índice 'Papel' em uma coluna regular
df.reset_index(inplace=True)

# Aplicar filtro
df_filtrado = df[
    (df['P/L'] > minPL) &
    (df['P/L'] < maxPL) &
    (df['P/VP'] > minPVP) &
    (df['P/VP'] < maxPVP) &
    (df['Div.Yield'] > minDivYield) &
    (df['Div.Yield'] < maxDivYield) &
    (df['ROE'] > minROE) &
    (df['ROE'] < maxROE) &
    (df['Liq.2meses'] > liquidez_minima) &
    (df['Cresc. Rec.5a'] > crescimento_minimo)
]

# Criar um campo de pontuação no data frame para ranquear as ações de acordo com os critérios de ordenação acima considerando o top 5 de cada ordenação para somar 1 ponto a cada ação que aparecer no top 5
# Inicializa a pontuação
df_filtrado['Pontuação'] = 0
# Adiciona 1 ponto para cada ação que aparecer no top 5 de cada ordenação por P/L, P/VP, Div.Yield, ROE e Dív.Brut/ Patrim.
top_pl = df_filtrado.nsmallest(5, 'P/L')['papel']
df_filtrado.loc[df_filtrado['papel'].isin(top_pl), 'Pontuação'] += 1
top_pvp = df_filtrado.nsmallest(5, 'P/VP')['papel']
df_filtrado.loc[df_filtrado['papel'].isin(top_pvp), 'Pontuação'] += 1
top_divyield = df_filtrado.nlargest(5, 'Div.Yield')['papel']
df_filtrado.loc[df_filtrado['papel'].isin(top_divyield), 'Pontuação'] += 1
top_roe = df_filtrado.nlargest(5, 'ROE')['papel']
df_filtrado.loc[df_filtrado['papel'].isin(top_roe), 'Pontuação'] += 1
top_divbrutpatrim = df_filtrado.nsmallest(5, 'Dív.Brut/ Patrim.')['papel']
df_filtrado.loc[df_filtrado['papel'].isin(top_divbrutpatrim), 'Pontuação'] += 1

# Ordenar por Pontuação do maior para o menor
df_filtrado.sort_values(by='Pontuação', inplace=True, ascending=False)

# Converter a coluna 'Div.Yield' para porcentagem legível
df_filtrado['Div.Yield'] = df_filtrado['Div.Yield'] * 100

# Converter a coluna 'ROE' para porcentagem legível
df_filtrado['ROE'] = df_filtrado['ROE'] * 100

# Converter a coluna 'Cresc. Rec.5a' para porcentagem legível
df_filtrado['Cresc. Rec.5a'] = df_filtrado['Cresc. Rec.5a'] * 100

# Excluir colunas que não serão utilizadas no data frame final
colunas_para_excluir = [
    'PSR', 'P/Ativo', 'P/Cap.Giro', 'P/EBIT', 'P/Ativ Circ.Liq',
    'EV/EBIT', 'EV/EBITDA', 'Mrg Ebit', 'Mrg. Líq.',
    'Liq. Corr.', 'ROIC'
]
df_filtrado.drop(colunas_para_excluir, axis=1, inplace=True)

# Verificar se o arquivo resultado.xlsx existe no path atual e se existir apagar
if os.path.exists('resultado.xlsx'):
    os.remove('resultado.xlsx')

# Exportar para XLSX o resultado
df_filtrado.to_excel(xlsx_path, index=False)

# Abrir o Excel com o resultado
os.system("xdg-open resultado.xlsx")
