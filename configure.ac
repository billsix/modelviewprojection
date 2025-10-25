AC_PREREQ([2.69])
AC_INIT([modelviewprojection], [0.0.2], [billsix@gmail.com])

AC_ARG_ENABLE([html],
  [AS_HELP_STRING([--enable-html],
    [Enable extra html install])],
    [enable_extra_html=yes],
    [enable_extra_html=no]
)

AC_ARG_ENABLE([pdf],
  [AS_HELP_STRING([--enable-pdf],
    [Enable extra pdf install])],
    [enable_extra_pdf=yes],
    [enable_extra_pdf=no]
)

AC_ARG_ENABLE([x_windows],
  [AS_HELP_STRING([--enable-x_windows],
    [Enable extra x_windows install])],
    [enable_extra_x_windows=yes],
    [enable_extra_x_windows=no]
)

AC_ARG_ENABLE([emacs],
  [AS_HELP_STRING([--enable-emacs],
    [Enable extra emacs install])],
    [enable_extra_emacs=yes],
    [enable_extra_emacs=no]
)

AC_ARG_ENABLE([imgui],
  [AS_HELP_STRING([--enable-imgui],
    [Enable extra imgui install])],
    [enable_extra_imgui=yes],
    [enable_extra_imgui=no]
)

AC_ARG_ENABLE([jupyter],
  [AS_HELP_STRING([--enable-jupyter],
    [Enable extra jupyter install])],
    [enable_extra_jupyter=yes],
    [enable_extra_jupyter=no]
)

BUILD_DOCS_FLAG=0

# Write substitution variable for Makefile
if test "x$enable_extra_html" = "xyes"; then
  BUILD_HTML_FLAG=1
  BUILD_DOCS_FLAG=1
  DEFAULT_MAKE_GOAL=html
else
  BUILD_HTML_FLAG=0
  DEFAULT_MAKE_GOAL=all
fi
AC_SUBST(BUILD_HTML_FLAG)
AC_SUBST(DEFAULT_MAKE_GOAL)

if test "x$enable_extra_pdf" = "xyes"; then
  BUILD_PDF_FLAG=1
  BUILD_DOCS_FLAG=1
else
  BUILD_PDF_FLAG=0
fi
AC_SUBST(BUILD_PDF_FLAG)


AC_SUBST(BUILD_DOCS_FLAG)


if test "x$enable_extra_x_windows" = "xyes"; then
  USE_X_WINDOWS=1
else
  USE_X_WINDOWS=0
fi
AC_SUBST(USE_X_WINDOWS)


if test "x$enable_extra_emacs" = "xyes"; then
  USE_EMACS=1
else
  USE_EMACS=0
fi
AC_SUBST(USE_EMACS)


if test "x$enable_extra_imgui" = "xyes"; then
  USE_IMGUI=1
else
  USE_IMGUI=0
fi
AC_SUBST(USE_IMGUI)


if test "x$enable_extra_jupyter" = "xyes"; then
  USE_JUPYTER=1
else
  USE_JUPYTER=0
fi
AC_SUBST(USE_JUPYTER)


AC_CONFIG_FILES([
   Makefile
   Dockerfile
])
AC_OUTPUT
