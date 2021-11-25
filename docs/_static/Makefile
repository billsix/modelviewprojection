%.png: %.dot
	dot -Tpng -Gsize=6,9\! -Gdpi=200 $< -o $@


all: graphs pythonplots
	cd gnuplot && make



graphs: currency.png \
	demo11.png \
	demo10.png \
	demo10-2.png \
	demo06.png \
	demo08.png \
	demo02.png \
	demo03.png \
	demo05.png \
	cayleygraph.png



pythonplots: rotate0.gif



rotate0.gif: generate_plots.py
	python generate_plots.py
