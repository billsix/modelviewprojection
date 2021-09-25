%.png: %.dot
	dot -Tpng $< -o $@

all: plots graphs
	cd gnuplot && make



graphs: currency.png demo11.png demo10.png demo06.png



plots: generate_plots.py
	python generate_plots.py
