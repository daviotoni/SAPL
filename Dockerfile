FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    "psycopg[binary]>=3.2" "gunicorn>=23.0" "whitenoise>=6.7"

COPY . .

EXPOSE 8000
CMD ["gunicorn", "sapldc.wsgi", "-b", "0.0.0.0:8000"]
