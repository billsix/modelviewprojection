bin_PROGRAMS = modelviewprojection

main.cpp:
	sed -e '/^\/\// d' main.book.cpp > main.cpp

main.tex: main.book.cpp
	sed -e 's/^\/\///g' main.book.cpp > main.tex

main.pdf: main.tex
	pdflatex main.tex
	makeindex main.idx
	pdflatex main.tex


modelviewprojection_SOURCES = \
	main.cpp \
	main.h

modelviewprojection_CXXFLAGS= \
	$(GLEW_CFLAGS) \
	$(SDL_CFLAGS) \
	-std=c++11

modelviewprojection_LDADD = \
	$(GLEW_LIBS) \
	$(SDL_LIBS) \
	$(OPENGL_LIB) \
	-lm
