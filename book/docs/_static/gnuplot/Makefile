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

plot1.svg: plot1.gp plot1.dat
	gnuplot plot1.gp

plot1.png: plot1.svg
	inkscape plot1.svg --export-filename=plot1.png

plot2.svg: plot2.gp plot2.dat
	gnuplot plot2.gp

plot2.png: plot2.svg
	inkscape plot2.svg --export-filename=plot2.png

plot3.svg: plot3.gp plot3.dat
	gnuplot plot3.gp

plot3.png: plot3.svg
	inkscape plot3.svg --export-filename=plot3.png

plot4.svg: plot4.gp plot4.dat
	gnuplot plot4.gp

plot4.png: plot4.svg
	inkscape plot4.svg --export-filename=plot4.png

rotate.svg: rotate.gp rotate.dat
	gnuplot rotate.gp

rotate.png: rotate.svg
	inkscape rotate.svg --export-filename=rotate.png

rotate2.svg: rotate2.gp rotate2.dat
	gnuplot rotate2.gp

rotate2.png: rotate2.svg
	inkscape rotate2.svg --export-filename=rotate2.png

rotate3.svg: rotate3.gp rotate3.dat
	gnuplot rotate3.gp

rotate3.png: rotate3.svg
	inkscape rotate3.svg --export-filename=rotate3.png

rotate4.svg: rotate4.gp rotate4.dat
	gnuplot rotate4.gp

rotate4.png: rotate4.svg
	inkscape rotate4.svg --export-filename=rotate4.png

scale.svg: scale.gp scale.dat
	gnuplot scale.gp

scale.png: scale.svg
	inkscape scale.svg --export-filename=scale.png

translate.svg: translate.gp translate.dat
	gnuplot translate.gp

translate.png: translate.svg
	inkscape translate.svg --export-filename=translate.png

disproportionate1.svg: disproportionate1.gp
	gnuplot disproportionate1.gp

disproportionate1.png: disproportionate1.svg
	inkscape disproportionate1.svg --export-filename=disproportionate1.png

disproportionate2.svg: disproportionate2.gp
	gnuplot disproportionate2.gp

disproportionate2.png: disproportionate2.svg
	inkscape disproportionate2.svg --export-filename=disproportionate2.png

modelspace.svg: modelspace.gp
	gnuplot modelspace.gp

modelspace.png: modelspace.svg
	inkscape modelspace.svg --export-filename=modelspace.png

monitor.svg: monitor.gp
	gnuplot monitor.gp

monitor.png: monitor.svg
	inkscape monitor.svg --export-filename=monitor.png

monitor2.svg: monitor2.gp
	gnuplot monitor2.gp

monitor2.png: monitor2.svg
	inkscape monitor2.svg --export-filename=monitor2.png

ndcSpace.svg: ndcSpace.gp
	gnuplot ndcSpace.gp

ndcSpace.png: ndcSpace.svg
	inkscape ndcSpace.svg --export-filename=ndcSpace.png

ndcSpace1.svg: ndcSpace1.gp
	gnuplot ndcSpace1.gp

ndcSpace1.png: ndcSpace1.svg
	inkscape ndcSpace1.svg --export-filename=ndcSpace1.png

ndcSpace2.svg: ndcSpace2.gp
	gnuplot ndcSpace2.gp

ndcSpace2.png: ndcSpace2.svg
	inkscape ndcSpace2.svg --export-filename=ndcSpace2.png

screenspace.svg: screenspace.gp
	gnuplot screenspace.gp

screenspace.png: screenspace.svg
	inkscape screenspace.svg --export-filename=screenspace.png

screenspace2.svg: screenspace2.gp
	gnuplot screenspace2.gp

screenspace2.png: screenspace2.svg
	inkscape screenspace2.svg --export-filename=screenspace2.png

viewport.svg: viewport.gp
	gnuplot viewport.gp

viewport.png: viewport.svg
	inkscape viewport.svg --export-filename=viewport.png
