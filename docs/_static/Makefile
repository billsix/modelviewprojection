%.png: %.dot
	dot -Tpng $< -o $@

all: graphs pythonplots
	cd gnuplot && make



graphs: currency.png demo11.png demo10.png demo10-2.png demo06.png demo08.png



pythonplots: rotate0.gif



rotate0.gif: generate_plots.py
	python generate_plots.py
