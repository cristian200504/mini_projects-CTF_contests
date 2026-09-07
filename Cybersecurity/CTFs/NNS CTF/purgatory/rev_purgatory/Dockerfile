FROM erlang:28-alpine

WORKDIR /app

RUN apk add --no-cache socat \
    && adduser -D -H purgatory

COPY purgatory_runner.erl ./
COPY releases ./releases
COPY entrypoint.sh ./entrypoint.sh
COPY run.sh ./run.sh

RUN erlc +deterministic +no_debug_info purgatory_runner.erl \
    && chmod +x entrypoint.sh run.sh

USER purgatory
EXPOSE 1337

ENTRYPOINT ["/app/entrypoint.sh"]
