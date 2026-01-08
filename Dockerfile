# Usa uma imagem leve do Python
FROM python:3.9-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia o arquivo de dependências para o container
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante dos arquivos do seu projeto
COPY . .

# Expõe a porta que o Flask vai usar (geralmente 5000 ou 8080)
EXPOSE 8080

# Comando para rodar a aplicação usando Gunicorn (recomendado para produção)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]