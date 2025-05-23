FROM docker.io/debian:trixie

RUN apt update && apt upgrade -y && \
    apt install    -y gnuplot \
                      texlive \
                      texlive-latex-extra \
                      graphviz \
                      python3-sphinx-rtd-theme \
                      fonts-mathjax \
                      libjs-mathjax \
                      make \
                      python3-imageio \
                      python3-matplotlib \
                      dvipng \
                      inkscape \
                      latexmk \
                      automake \
                      autoconf \
                      make \
                      gcc \
                      python3-pytest \
                      aspell-en && \
     python3 -c "import matplotlib.pyplot as plt; plt.plot([1,2,3], [4,5,6]); plt.show()"

COPY ./book /mvp/book/
COPY ./src /mvp/src/
COPY ./entrypoint/entrypoint.sh  /entrypoint.sh
COPY pytest.ini /mvp/
COPY ./tests /mvp/


COPY ./book/docs/_static/tex_exp_to_png   /tex_exp_to_png
RUN cd /tex_exp_to_png   && ./autogen.sh && ./configure --prefix=/usr && make && make install



# Run unit tests
# If any unit tests fail, exit and don't build the book
RUN cd /mvp/ && pytest --exitfirst --disable-warnings

ENTRYPOINT ["/entrypoint.sh"]
