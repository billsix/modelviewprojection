%.svg : %.gp
	gnuplot $<

OBJECTS_TO_BUILD = plot1.svg \
	monitor.svg \
	monitor2.svg \
	screenspace.svg \
	screenspace2.svg \
	ndcSpace.svg \
	ndcSpace1.svg \
	ndcSpace2.svg \
	plot2.svg \
	plot3.svg \
	plot4.svg \
	translate.svg \
	scale.svg \
	rotate.svg \
	rotate2.svg \
	rotate3.svg \
	rotate4.svg \
	modelspace.svg \
        disproportionate1.svg \
        disproportionate2.svg \
        viewport.svg


all: $(OBJECTS_TO_BUILD)
	cp *.svg ../
