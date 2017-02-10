bin_PROGRAMS = modelviewprojection

# main.book.cpp is the book in my private Git repository, with
# the source code embedded into it.  To make public releases
# of the LGPL/Apache `main.cpp', (the code without the book's
# contents, run "make dist"

# In my private repo, do nothing
# In the public repo, do nothing
main.book.cpp:
	echo


# In my private repo, remove all of the LaTeX code embedded
#   in CPP comments
# In the public repo, do nothing
main.cpp: main.book.cpp
	if [ -e main.book.cpp ] ; then sed -e '/^\/\// d' main.book.cpp > main.cpp; fi;

# In my private repo, remove all of the double forward slashes at the beginning
#   of lines which were there to denote LaTeX code
# In the public repo, do nothing
main.tex: main.book.cpp
	if [ -e main.book.cpp ]; then  sed -e 's/^\/\///g' main.book.cpp > main.tex; fi;

main.html: main.tex
	asciidoc -b html5 -a icons -a toc2 -a theme=flask main.tex

main.pdf: main.tex
	a2x -dbook --no-xmllint main.tex



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
