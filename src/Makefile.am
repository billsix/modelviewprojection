bin_PROGRAMS = modelviewprojection
modelviewprojection_SOURCES = \
	main.cpp

modelviewprojection_CXXFLAGS= \
	$(GLEW_CFLAGS) \
	$(SDL_CFLAGS) \
	-std=c++11

modelviewprojection_LDADD = \
	$(GLEW_LIBS) \
	$(SDL_LIBS) \
	$(OPENGL_LIB) \
	-lm
