FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000

CMD ["gunicorn","myapp.asgi:application","-k","uvicorn.workers.UvicornWorker","--bind","0.0.0.0:8000","--workers", "1","--timeout","120"]