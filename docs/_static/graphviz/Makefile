all: graphs
	mv *.png ../

%.png: %.dot
	dot -Tpng $< -o $@

graphs: demo06.png demo10.png demo11.png currency.png
