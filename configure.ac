AC_INIT([modelviewprojection], [0.0.1],  [William Emerison Six <billsix@gmail.com>], [modelviewprojection])
AC_CANONICAL_SYSTEM
AC_CONFIG_SRCDIR([doc/modelviewprojection.man.in])
AC_CONFIG_HEADER([config.h])
AC_CHECK_HEADER([stdio.h])
AC_REVISION([: 0.0.1 $])
AM_INIT_AUTOMAKE()
AC_PROG_CC
AC_PROG_CXX
AC_PROG_INSTALL
AC_CONFIG_FILES([Makefile
        doc/Makefile
        doc/modelviewprojection.man
        src/Makefile])

case "$target_os" in
    darwin*)
             LDFLAGS="-framework OpenGL $LDFLAGS"
             OPENGL_LIB=""
             ;;
    ming*)
             OPENGL_LIB="-lopengl32 -lglu32"
             ;;
    *)
             OPENGL_LIB="-lGL -lGLU"
             ;;

esac
AC_SUBST(OPENGL_LIB)

AC_ARG_ENABLE(pdf,
              AC_HELP_STRING([--enable-pdf],
                             [build the PDF version of the code (default is NO)]),
              ENABLE_PDF=$enableval,
              ENABLE_PDF=no)
if test "$ENABLE_PDF" = yes; then
   echo MAKE PDF
fi
AC_SUBST(ENABLE_PDF)
AM_CONDITIONAL(BUILD_PDF, [test x"$ENABLE_PDF" = xyes])
AC_SUBST(BUILD_PDF)


dnl PKG_CHECK_MODULES(GLFW, glfw >= 3.0)


dnl Check for glew and set cflags/libs
PKG_CHECK_MODULES(GLEW, glew >= 1.10)


MVP_BUILD_DATE=$(date +'%d %B %Y')
AC_SUBST(MVP_BUILD_DATE)


AC_OUTPUT
