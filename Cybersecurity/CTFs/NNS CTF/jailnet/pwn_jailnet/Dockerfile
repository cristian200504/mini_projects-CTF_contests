FROM debian:trixie-slim@sha256:d7e12182ce18b85b93007c1dedf31f2d29e01ccf3182cc4017c709b6259bc132 AS builder
ARG JANET_VERSION=1.41.2
ARG JANET_SHA256=c09ac75730de76ad2f3e28eb054ee69c7ebb56ec95ae20234c0a0c37e57de681
RUN apt-get update \
&& apt-get install -y --no-install-recommends ca-certificates wget \
&& wget -q "https://github.com/janet-lang/janet/releases/download/v${JANET_VERSION}/janet-v${JANET_VERSION}-linux-x64.tar.gz" -O /tmp/janet.tar.gz \
&& echo "${JANET_SHA256}  /tmp/janet.tar.gz" | sha256sum -c - \
&& tar xfz /tmp/janet.tar.gz -C /opt

FROM debian:trixie-slim@sha256:d7e12182ce18b85b93007c1dedf31f2d29e01ccf3182cc4017c709b6259bc132

COPY --from=builder /opt/janet-v1.41.2-linux/bin/janet /usr/local/bin/janet

RUN groupadd -g 1001 ctf \
&& useradd -u 1001 -g 1001 -m -s /usr/sbin/nologin ctf \
&& mkdir /app \
&& touch /flag.txt \
&& chown ctf:ctf /flag.txt

WORKDIR /app
COPY server.janet entrypoint.sh ./

RUN chown -R root:root /app \
&& chmod 0555 /app \
&& chmod 0444 /app/server.janet \
&& chmod 0555 /app/entrypoint.sh

USER ctf

EXPOSE 1337
ENTRYPOINT ["/app/entrypoint.sh"]