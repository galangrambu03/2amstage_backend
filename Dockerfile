FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# PERHATIKAN BARIS INI: diganti dari "app:app" menjadi "run:app"
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]