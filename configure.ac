AC_PREREQ([2.69])
AC_INIT([modelviewprojection], [0.0.2], [billsix@gmail.com])
AC_CONFIG_SRCDIR([Makefile.in])

# Optional Automake init (uncomment if you're using Automake)
# AM_INIT_AUTOMAKE([foreign])

# --------------------------------------------------------------------
# Feature flags
# --------------------------------------------------------------------

AC_ARG_ENABLE([html],
  [AS_HELP_STRING([--enable-html], [Enable extra HTML install])],
  [enable_extra_html=$enableval],
  [enable_extra_html=no]
)

AC_ARG_ENABLE([pdf],
  [AS_HELP_STRING([--enable-pdf], [Enable extra PDF install])],
  [enable_extra_pdf=$enableval],
  [enable_extra_pdf=no]
)

AC_ARG_ENABLE([x-windows],
  [AS_HELP_STRING([--enable-x-windows], [Enable X Windows support])],
  [enable_extra_x_windows=$enableval],
  [enable_extra_x_windows=no]
)

AC_ARG_ENABLE([emacs],
  [AS_HELP_STRING([--enable-emacs], [Enable Emacs integration])],
  [enable_extra_emacs=$enableval],
  [enable_extra_emacs=no]
)

AC_ARG_ENABLE([imgui],
  [AS_HELP_STRING([--enable-imgui], [Enable ImGui integration])],
  [enable_extra_imgui=$enableval],
  [enable_extra_imgui=no]
)

AC_ARG_ENABLE([jupyter],
  [AS_HELP_STRING([--enable-jupyter], [Enable Jupyter integration])],
  [enable_extra_jupyter=$enableval],
  [enable_extra_jupyter=no]
)

AC_ARG_ENABLE([spyder],
  [AS_HELP_STRING([--enable-spyder], [Enable Spyder integration])],
  [enable_extra_spyder=$enableval],
  [enable_extra_spyder=no]
)

# --------------------------------------------------------------------
# Compute build flags
# --------------------------------------------------------------------

BUILD_DOCS_FLAG=0
BUILD_HTML_FLAG=0
BUILD_PDF_FLAG=0
USE_X_WINDOWS=0
USE_EMACS=0
USE_IMGUI=0
USE_JUPYTER=0
USE_SPYDER=0
DEFAULT_MAKE_GOAL=all

# HTML / PDF
if test "x$enable_extra_html" = "xyes"; then
  BUILD_HTML_FLAG=1
  BUILD_DOCS_FLAG=1
  DEFAULT_MAKE_GOAL=html
fi

if test "x$enable_extra_pdf" = "xyes"; then
  BUILD_PDF_FLAG=1
  BUILD_DOCS_FLAG=1
  # Only set default goal if not already set
  if test "x$DEFAULT_MAKE_GOAL" = "xall"; then
    DEFAULT_MAKE_GOAL=pdf
  fi
fi

# X Windows
if test "x$enable_extra_x_windows" = "xyes"; then
  USE_X_WINDOWS=1
fi

# Emacs
if test "x$enable_extra_emacs" = "xyes"; then
  USE_EMACS=1
fi

# ImGui
if test "x$enable_extra_imgui" = "xyes"; then
  USE_IMGUI=1
fi

# Jupyter / Spyder (higher-priority defaults)
if test "x$enable_extra_jupyter" = "xyes"; then
  USE_JUPYTER=1
  DEFAULT_MAKE_GOAL=jupyter
fi

if test "x$enable_extra_spyder" = "xyes"; then
  USE_SPYDER=1
  DEFAULT_MAKE_GOAL=spyder
fi

# --------------------------------------------------------------------
# Substitute values for Makefile / Dockerfile
# --------------------------------------------------------------------
AC_SUBST(BUILD_DOCS_FLAG)
AC_SUBST(BUILD_HTML_FLAG)
AC_SUBST(BUILD_PDF_FLAG)
AC_SUBST(USE_X_WINDOWS)
AC_SUBST(USE_EMACS)
AC_SUBST(USE_IMGUI)
AC_SUBST(USE_JUPYTER)
AC_SUBST(USE_SPYDER)
AC_SUBST(DEFAULT_MAKE_GOAL)

# --------------------------------------------------------------------
# Output files
# --------------------------------------------------------------------
AC_CONFIG_FILES([
  Makefile
  Dockerfile
])
AC_OUTPUT

