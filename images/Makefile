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
	convert -loop 0 -delay 100 translation-forwards* translationF.gif
	convert -loop 0 -delay 100 translation2-forwards* translation2F.gif
	convert -loop 0 -delay 100 translation-back* translationB.gif
	convert -loop 0 -delay 100 translation2-back* translation2B.gif
	convert -loop 0 -delay 100 rotate1-forwards* rotation1F.gif
	convert -loop 0 -delay 100 rotate1-ba* rotation1B.gif
	convert -loop 0 -delay 100 rotate2-forwards* rotation2F.gif
	convert -loop 0 -delay 100 rotate2-ba* rotation2B.gif
	convert -loop 0 -delay 100 covariance-for* covarF.gif
	convert -loop 0 -delay 100 covariance-ba* covarB.gif
	convert -loop 0 -delay 100 circle-for* circleF.gif
	convert -loop 0 -delay 100 circle-ba* circleB.gif
