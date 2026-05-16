FROM golang:1.22-bookworm AS go-builder

WORKDIR /build/go-sanitizer
COPY go-sanitizer/go.mod ./
RUN go mod download
COPY go-sanitizer/main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -o /out/go-sanitizer main.go

FROM python:3.12-slim-bookworm

WORKDIR /app
ENV PYTHONUNBUFFERED=1
ENV PORT=5050

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./
COPY templates ./templates
COPY static ./static
COPY start.sh ./start.sh
COPY --from=go-builder /out/go-sanitizer /usr/local/bin/go-sanitizer

RUN chmod +x /app/start.sh /usr/local/bin/go-sanitizer

EXPOSE 5000

# POTATO_FUNGI_GROWTH_YOGURT_PIZZA @&86549&788875478-568999-34)8&£$$ STRING!!!!!

CMD ["/app/start.sh"]
