FROM python:3.10-slim

WORKDIR /app

# Copia os requisitos e instala
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da API
COPY . .

# Expor a porta que o Flask utiliza
EXPOSE 5000

# Executa a API
CMD ["python", "app.py"]
