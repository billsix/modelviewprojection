%.svg: %.gp
	gnuplot $<

%.png: %.svg
	inkscape $< --export-filename=$@



OBJECTS_TO_BUILD =  \
	plot1.png \
	plot1.svg \
	monitor.png \
	monitor.svg \
	monitor2.png \
	monitor2.svg \
	screenspace.png \
	screenspace.svg \
	screenspace2.png \
	screenspace2.svg \
	ndcSpace.png \
	ndcSpace.svg \
	ndcSpace1.png \
	ndcSpace1.svg \
	ndcSpace2.png \
	ndcSpace2.svg \
	plot2.png \
	plot2.svg \
	plot3.png \
	plot3.svg \
	plot4.png \
	plot4.svg \
	translate.png \
	translate.svg \
	scale.png \
	scale.svg \
	rotate.png \
	rotate.svg \
	rotate2.png \
	rotate2.svg \
	rotate3.png \
	rotate3.svg \
	rotate4.png \
	rotate4.svg \
	modelspace.png \
	modelspace.svg \
	disproportionate1.png \
	disproportionate1.svg \
	disproportionate2.png \
	disproportionate2.svg \
	viewport.png \
	viewport.svg


all: $(OBJECTS_TO_BUILD)
	cp *.svg *png ../
