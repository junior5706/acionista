import pandas as pd
import numpy as np
import fundamentus

# Seus critérios e dados iniciais
papeis_que_possuo = ["ROMI3", "GGBR4"]
minDivYield = 0.05  # 5%
maxDivYield = 0.20  # 20%
minPL = 0
csv_path = "resultado.csv"

# Obter dados e aplicar filtro
df = fundamentus.get_resultado_raw()

# Transformar o índice 'Papel' em uma coluna regular
df.reset_index(inplace=True)

# Aplicar filtro
df_filtrado = df[
    (df['P/L'] > minPL) &
    (df['Div.Yield'] > minDivYield) &
    (df['Div.Yield'] < maxDivYield)
]

# Calcular medianas
median_pl = np.median(df_filtrado['P/L'].dropna())
median_roe = np.median(df_filtrado['ROE'].dropna())

# Filtrar empresas com P/L abaixo da mediana e ROE acima da mediana
selected_companies = df_filtrado[
    (df_filtrado['P/L'] < median_pl) &
    (df_filtrado['ROE'] > median_roe)
]

# Adicionar papeis que o usuário possui, se não estiverem na lista
for papel in papeis_que_possuo:
    if papel not in selected_companies['papel'].values:
        papel_data = df[df['papel'] == papel]
        selected_companies = pd.concat([selected_companies, papel_data])

# Percorrer os papeis selecionados e obter detalhes
papel_detalhes = []
for papel in selected_companies['papel'].values:
    detalhes = fundamentus.get_papel(papel)
    detalhes['papel'] = papel  # Adicionar uma coluna com o nome do papel
    papel_detalhes.append(detalhes)

# Concatenar todos os DataFrames em um único DataFrame
detalhes_completos = pd.concat(papel_detalhes)

# Percorrer todas as colunas e substituir '%' por nada
for col in detalhes_completos.columns:
    detalhes_completos[col] = detalhes_completos[col].str.replace('%', '')

# Exportar detalhes_completos para CSV
detalhes_completos.to_csv(csv_path, index=False)
