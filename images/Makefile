%.png : %.gp
	gnuplot $<

OBJECTS_TO_BUILD = plot1.png \
	monitor.png \
	monitor2.png \
	screenspace.png \
	screenspace2.png \
	ndcSpace.png \
	ndcSpace1.png \
	ndcSpace2.png \
	plot2.png \
	plot3.png \
	plot4.png \
	translate.png \
	scale.png \
	rotate.png \
	rotate2.png \
	rotate3.png \
	rotate4.png \
	modelspace.png \
        disproportionate1.png \
        disproportionate2.png \
        viewport.png


all: plots $(OBJECTS_TO_BUILD)

%.png: %.dot
	dot -Tpng $< -o $@

graphs: demo06.png demo10.png demo11.png currency.png

plots: generatePlots.py
	python generatePlots.py
