FROM oven/bun:1.3.14-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates xz-utils tini && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production
ENV LANG=C.UTF-8 
ENV LC_ALL=C.UTF-8 
ENV PERCHANCE=PERCHANCE
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app
COPY ./package.json /app/package.json
COPY ./bun.lock /app/bun.lock
RUN bun install --frozen-lockfile --production
RUN bun x playwright install firefox --with-deps --no-shell && chmod -R a+rX /ms-playwright

COPY ./src /app/src
COPY ./extension /app/extension
ENV HOME=/tmp
USER 10000:10000
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["bun","run","/app/src/index.ts"]
EXPOSE 3000
