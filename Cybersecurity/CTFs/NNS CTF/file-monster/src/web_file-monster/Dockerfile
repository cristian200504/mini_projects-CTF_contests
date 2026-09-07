FROM oven/bun:1 AS builder
WORKDIR /usr/src/app
COPY package.json bun.lock /usr/src/app/
COPY src /usr/src/app/src
COPY public /usr/src/app/public
RUN cd /usr/src/app && bun install --forzen-lockfile --production
RUN cd /usr/src/app && bun build ./src/index.ts --compile --minify --bytecode --format esm --outfile /backend

FROM mongo:8.2.10
COPY --chmod=0644 mongod.conf /etc/mongod.conf
COPY --chmod=0644 init.js /docker-entrypoint-initdb.d/mongo-init.js
COPY --chmod=0755 entrypoint.sh /entrypoint.sh
COPY --chmod=0755 --from=builder /backend /backend
ENV NODE_ENV=production
EXPOSE 3000
EXPOSE 27017
ENTRYPOINT [ "/entrypoint.sh" ]
