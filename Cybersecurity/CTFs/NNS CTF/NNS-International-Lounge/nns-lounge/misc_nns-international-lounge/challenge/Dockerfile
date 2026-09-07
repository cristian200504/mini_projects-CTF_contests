FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends libzbar0 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY templates templates
COPY static static
RUN useradd --system --uid 10000 challenge
USER challenge
EXPOSE 3000

CMD ["gunicorn", "--bind", "0.0.0.0:3000", "app:app"]
