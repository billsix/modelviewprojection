FROM docker.io/debian:trixie


RUN apt update && apt upgrade -y && \
    apt install -y texlive  \
                   dvipng  \
                   texlive-latex-extra \
                   automake \
                   autoconf \
                   make \
                   gcc


COPY entrypoint/entrypoint.sh  /entrypoint.sh
COPY src/  /src/src
COPY autogen.sh /src/
COPY configure.ac /src/
COPY Makefile.am /src/
RUN cd /src && ./autogen.sh && ./configure --prefix=/usr && make && make install


ENTRYPOINT ["/entrypoint.sh"]
