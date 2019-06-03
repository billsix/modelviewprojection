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

diffs:
	diff -C 10 ../modelviewprojection1.py ../modelviewprojection2.py  > modelviewprojection2.diff ; \
	diff -C 10 ../modelviewprojection2.py ../modelviewprojection3.py  > modelviewprojection3.diff ; \
	diff -C 10 ../modelviewprojection3.py ../modelviewprojection4.py  > modelviewprojection4.diff ; \
	diff -C 10 ../modelviewprojection4.py ../modelviewprojection5.py  > modelviewprojection5.diff ; \
	diff -C 10 ../modelviewprojection5.py ../modelviewprojection6.py  > modelviewprojection6.diff ; \
	diff -C 10 ../modelviewprojection6.py ../modelviewprojection7.py  > modelviewprojection7.diff ; \
	diff -C 10 ../modelviewprojection7.py ../modelviewprojection8.py  > modelviewprojection8.diff ; \
	diff -C 10 ../modelviewprojection8.py ../modelviewprojection9.py  > modelviewprojection9.diff ; \
	diff -C 10 ../modelviewprojection9.py ../modelviewprojection10.py > modelviewprojection10.diff ; \
	diff -C 10 ../modelviewprojection10.py ../modelviewprojection11.py > modelviewprojection11.diff ; \
	diff -C 10 ../modelviewprojection11.py ../modelviewprojection12.py > modelviewprojection12.diff ; \
	diff -C 10 ../modelviewprojection12.py ../modelviewprojection13.py > modelviewprojection13.diff ; \
	diff -C 10 ../modelviewprojection13.py ../modelviewprojection14.py > modelviewprojection14.diff ; \
	diff -C 10 ../modelviewprojection14.py ../modelviewprojection15.py > modelviewprojection15.diff ; \
	diff -C 10 ../modelviewprojection15.py ../modelviewprojection16.py > modelviewprojection16.diff ; \
	echo diffs

dist: modelviewprojection.html plots
	mkdir -p dist
	cp *png *gif dist/
	cp modelviewprojection.html dist/index.html

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


modelviewprojection.html: modelviewprojection.adoc
	asciidoc -b html5 -a icons -a toc2 -a theme=flask -n modelviewprojection.adoc


modelviewprojection.adoc:  ../modelviewprojection.py $(OBJECTS_TO_BUILD)
	sed -e 's/^\#\#//g' ../modelviewprojection.py > modelviewprojectionbad.adoc
	# delete first line of generated file, as it just runs python,
	# which would cause docbook to fail
	tail -n +2 modelviewprojectionbad.adoc > modelviewprojection.adoc


main.pdf: modelviewprojection.adoc plots
	a2x -dbook --dblatex-opts "-P latex.output.revhistory=0 -P doc.publisher.show=0 -P doc.pdfcreator.show=0" --no-xmllint modelviewprojection.adoc
