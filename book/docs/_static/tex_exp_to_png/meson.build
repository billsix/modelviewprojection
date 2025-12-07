project('texExpToPng', 'c',
  version: '0.1',
  default_options: ['c_std=gnu11']
)

glib_dep = dependency('glib-2.0')
math_dep = meson.get_compiler('c').find_library('m')

# Source files
source_files = files(
  'src/tex_exp_to_png.c',
)

# Executable
texExpToPng_exe = executable('texExpToPng',
  source_files,
  dependencies: [glib_dep, math_dep],
  install: true
)
