%.dvi: %.gp
	gnuplot $<

%.png: %.gp
	inkscape --without-gui --export-area-drawing --file=$< --export-png=$@



OBJECTS_TO_BUILD =  \
	plot1.png \
	plot1.dvi \
	monitor.png \
	monitor.dvi \
	monitor2.png \
	monitor2.dvi \
	screenspace.png \
	screenspace.dvi \
	screenspace2.png \
	screenspace2.dvi \
	ndcSpace.png \
	ndcSpace.dvi \
	ndcSpace1.png \
	ndcSpace1.dvi \
	ndcSpace2.png \
	ndcSpace2.dvi \
	plot2.png \
	plot2.dvi \
	plot3.png \
	plot3.dvi \
	plot4.png \
	plot4.dvi \
	translate.png \
	translate.dvi \
	scale.png \
	scale.dvi \
	rotate.png \
	rotate.dvi \
	rotate2.png \
	rotate2.dvi \
	rotate3.png \
	rotate3.dvi \
	rotate4.png \
	rotate4.dvi \
	modelspace.png \
	modelspace.dvi \
	disproportionate1.png \
	disproportionate1.dvi \
	disproportionate2.png \
	disproportionate2.dvi \
	viewport.png \
	viewport.dvi


all: $(OBJECTS_TO_BUILD)
	cp *.svg *png ../
