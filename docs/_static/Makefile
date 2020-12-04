all: plots
	cd gnuplot && make
	cd graphviz && make

plots: generate_plots.py
	python generate_plots.py
