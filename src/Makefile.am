bin_PROGRAMS = modelviewprojection

EXTRA_DIST = monitor.gp \
	monitor2.gp \
	ndcSpace.gp \
	ndcSpace1.gp \
	ndcSpace2.gp \
	plot1.gp \
	plot1.dat \
	plot2.gp \
	plot2.dat \
	plot3.gp \
	plot3.dat \
	plot4.gp \
	plot4.dat \
	screenspace.gp \
	screenspace2.gp \
        translate.gp \
	translate.dat \
        scale.gp \
	scale.dat \
        rotate.gp \
        rotate.dat \
        rotate2.gp \
        rotate2.dat \
        rotate3.gp \
        rotate3.dat \
        rotate4.gp \
        rotate4.dat \
        modelspace.gp \
        disproportionate1.gp \
        disproportionate2.gp \
        viewport.gp




ENABLE_PDF = @ENABLE_PDF@

OBJECTS_TO_BUILD = main.book.cpp


if BUILD_PDF
   OBJECTS_TO_BUILD += plot1.png \
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
        viewport.png \
	modelviewprojection.html
endif

# main.book.cpp is the book in my private Git repository, with
# the source code embedded into it.  To make public releases
# of the LGPL/Apache `main.cpp', (the code without the book's
# contents, run "make dist"

# In my private repo, do nothing
# In the public repo, do nothing
main.book.cpp:
	echo

%.png : %.gp
	gnuplot $<



# In my private repo, remove all of the LaTeX code embedded
#   in CPP comments
# In the public repo, do nothing
main.cpp:  $(OBJECTS_TO_BUILD)
	if [ -e main.book.cpp ] ; then sed -e '/^\/\// d' main.book.cpp | sed -e '/^$$/d' > main.cpp; fi;

# In my private repo, remove all of the double forward slashes at the beginning
#   of lines which were there to denote LaTeX code
# In the public repo, do nothing
main.tex: main.book.cpp $(EXTRA_DIST)
	if [ -e main.book.cpp ]; then  sed -e 's/^\/\///g' main.book.cpp > main.tex; fi;

modelviewprojection.html: main.tex
	asciidoc -b html5 -a icons -a toc2 -a theme=flask -n main.tex

main.pdf: main.tex
	a2x -dbook --dblatex-opts "-P latex.output.revhistory=0 -P doc.publisher.show=0 -P doc.pdfcreator.show=0" --no-xmllint main.tex



modelviewprojection_SOURCES = \
	main.cpp \
	main.h

modelviewprojection_CXXFLAGS= \
	$(GLEW_CFLAGS) \
	-std=c++11

modelviewprojection_LDADD = \
	$(GLEW_LIBS) \
	$(OPENGL_LIB) \
	-lglfw \
	-lm
