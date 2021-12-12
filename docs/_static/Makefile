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


currency.png: currency.dot
	dot -Tpng -Gsize=6,9\! -Gdpi=200 $< -o $@

demo11.png: demo11.dot
	dot -Tpng -Gsize=6,9\! -Gdpi=200 $< -o $@

demo10.png: demo10.dot
	dot -Tpng $< -o $@

demo10-2.png: demo10-2.dot
	dot -Tpng $< -o $@

demo06.png: demo06.dot
	dot -Tpng $< -o $@

demo08.png: demo08.dot
	dot -Tpng $< -o $@

demo02.png: demo02.dot
	dot -Tpng $< -o $@

demo03.png: demo03.dot
	dot -Tpng $< -o $@

demo05.png: demo05.dot
	dot -Tpng $< -o $@

cayleygraph.png: cayleygraph.dot
	dot -Tpng $< -o $@



pythonplots: rotate0.gif



rotate0.gif: generate_plots.py
	python generate_plots.py
