FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive

# ── dependencies ─────────────────────────────────────────────────────────────
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        git cmake build-essential libgomp1 wget ca-certificates socat && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /chal

# ── clone llama.cpp ───────────────────────────────────────────────────
RUN git clone --depth 1 https://github.com/ggerganov/llama.cpp.git llama.cpp 

# ── download model ────────────────────────────────────────────────────────────
RUN mkdir -p models && \
    wget -q --show-progress -O models/gpt2.Q8_0.gguf \
        "https://huggingface.co/QuantFactory/gpt2-GGUF/resolve/main/gpt2.Q8_0.gguf" && \
    echo "51639c9cd1fc48de5af03dd58aba5ecf  models/gpt2.Q8_0.gguf" | md5sum -c

# ── build challenge binary ────────────────────────────────────────────────────
COPY thoughtful.c ./
COPY Makefile ./
COPY flag.txt ./
COPY run.sh ./

RUN make all

RUN rm thoughtful.c
RUN rm Makefile

CMD ["./run.sh"]
