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




plots: generatePlots.py
	python generatePlots.py
	convert -loop 0 -delay 100 translation-forwards* translationF.gif
	rm translation-f*png
	convert -loop 0 -delay 100 translation2-forwards* translation2F.gif
	rm translation2-f*png
	convert -loop 0 -delay 100 rotate1-forwards* rotation1F.gif
	rm rotate1-f*png
	convert -loop 0 -delay 100 rotate1-ba* rotation1B.gif
	rm rotate1-b*png
	convert -loop 0 -delay 100 rotate2-forwards* rotation2F.gif
	rm rotate2-f*png
	convert -loop 0 -delay 100 rotate2-ba* rotation2B.gif
	rm rotate2-b*png
