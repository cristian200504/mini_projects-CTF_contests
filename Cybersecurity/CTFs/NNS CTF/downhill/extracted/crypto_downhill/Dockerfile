FROM sagemath/sagemath:10.9

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends socat \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN chown sage:sage /app

COPY --chown=sage:sage requirements.txt ./

USER sage
RUN sage -pip install --no-cache-dir -r requirements.txt

COPY --chown=sage:sage . ./

ENTRYPOINT ["socat", "TCP-LISTEN:3000,fork,reuseaddr", "EXEC:sage /app/chall.sage"]
