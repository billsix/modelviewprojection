bin_PROGRAMS = math4graphics
math4graphics_SOURCES = \
	main.c 

math4graphics_CFLAGS = \
	-std=c99 \
	$(GLEW_CFLAGS) \
	$(SDL_CFLAGS)

math4graphics_CXXFLAGS= \
	$(GLEW_CFLAGS) \
	$(SDL_CFLAGS)

math4graphics_LDADD = \
	$(GLEW_LIBS) \
	$(SDL_LIBS) \
	$(OPENGL_LIB) \
	-lm
