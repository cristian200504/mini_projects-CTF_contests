FROM fedora:42

RUN dnf update -y && dnf install -y \
    socat \
    && dnf clean all


COPY ./dist/libc.so /srv/dist/libc.so
COPY ./dist/chall /srv/dist/chall
COPY ./dist/flag.txt /srv/dist/flag.txt

RUN useradd -m -s /bin/bash user
USER user

WORKDIR /srv/dist

EXPOSE 1337

CMD socat TCP-LISTEN:1337,reuseaddr,fork EXEC:"/srv/dist/libc.so /srv/dist/chall",stderr