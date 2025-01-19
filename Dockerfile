FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema necessárias
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copiar os arquivos de requisitos primeiro
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar os scripts
COPY fundamentus_proventos.py .
COPY analise_completa_dividendos.py .

# Comando para executar o script
CMD ["python", "analise_completa_dividendos.py"] 