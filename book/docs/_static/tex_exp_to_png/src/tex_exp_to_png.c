#include <glib.h>
#include <glib/gstdio.h>
#include <glib/gprintf.h>
#include <stdlib.h>

_Noreturn void fatal_error(void) { exit(EXIT_FAILURE); }

gchar* read_file(const char* filename) {
  gchar* contents = NULL;
  gsize length;
  GError* error = NULL;
  if (!g_file_get_contents(filename, &contents, &length, &error)) {
    g_printerr("Error reading file '%s': %s\n", filename, error->message);
    g_error_free(error);
    fatal_error();
  }
  return contents;
}

void print_usage(const gchar* progname) {
  g_print("Usage:\n");
  g_print("  %s --exp \"E = 5 + m*c^2\" --size 800 --output output.png\n",
          progname);
  g_print("  %s --file input.txt --size 800 --output output.png\n", progname);
}

int main(int argc, char** argv) {
  gchar* expression = NULL;
  gchar* filename = NULL;
  gint size = 0;
  gchar* output = NULL;

  GOptionEntry entries[] = {
      {"exp", 'e', 0, G_OPTION_ARG_STRING, &expression,
       "LaTeX expression to render", "EXPRESSION"},
      {"file", 'f', 0, G_OPTION_ARG_FILENAME, &filename,
       "File containing LaTeX expression", "FILE"},
      {"size", 's', 0, G_OPTION_ARG_INT, &size, "DPI size for output", "SIZE"},
      {"output", 'o', 0, G_OPTION_ARG_FILENAME, &output, "Output PNG filename",
       "FILE"},
      {NULL, 0, 0, 0, NULL, NULL, NULL}};

  GError* error = NULL;
  GOptionContext* context =
      g_option_context_new("- render LaTeX formulas to PNG");
  g_option_context_add_main_entries(context, entries, NULL);

  if (!g_option_context_parse(context, &argc, &argv, &error)) {
    g_printerr("Option parsing failed: %s\n", error->message);
    g_error_free(error);
    g_option_context_free(context);
    fatal_error();
  }

  g_option_context_free(context);

  if ((!expression && !filename) || size == 0 || !output) {
    print_usage(argv[0]);
    fatal_error();
  }

  if (filename) {
    expression = read_file(filename);
  }

  FILE* tex_file = g_fopen("formula.tex", "w");
  if (!tex_file) {
    g_printerr("Failed to open formula.tex\n");
    fatal_error();
  }

  g_fprintf(tex_file,
            "\\documentclass{standalone}\n"
            "\\usepackage{amsmath}\n"
            "\\begin{document}\n"
            "$ %s $\n"
            "\\end{document}\n",
            expression);
  fclose(tex_file);

  gchar* stdout_output = NULL;
  gchar* stderr_output = NULL;
  gint exit_status;

  if (!g_spawn_command_line_sync("latex formula.tex", &stdout_output,
                                 &stderr_output, &exit_status, &error)) {
    g_printerr("Failed to run latex: %s\n", error->message);
    g_error_free(error);
    fatal_error();
  }

  if (exit_status != 0) {
    g_printerr("latex command failed\n");
    if (stderr_output) {
      g_printerr("%s\n", stderr_output);
    }
    g_free(stdout_output);
    g_free(stderr_output);
    fatal_error();
  }

  g_free(stdout_output);
  g_free(stderr_output);

  gchar* dvipng_cmd =
      g_strdup_printf("dvipng -D %d -T tight -o %s formula.dvi", size, output);

  if (!g_spawn_command_line_sync(dvipng_cmd, &stdout_output, &stderr_output,
                                 &exit_status, &error)) {
    g_printerr("Failed to run dvipng: %s\n", error->message);
    g_error_free(error);
    g_free(dvipng_cmd);
    fatal_error();
  }

  if (exit_status != 0) {
    g_printerr("dvipng command failed\n");
    if (stderr_output) {
      g_printerr("%s\n", stderr_output);
    }
    g_free(stdout_output);
    g_free(stderr_output);
    g_free(dvipng_cmd);
    fatal_error();
  }

  g_free(stdout_output);
  g_free(stderr_output);
  g_free(dvipng_cmd);

  g_print("PNG successfully created at %s\n", output);

  g_free(expression);
  g_free(filename);
  g_free(output);

  return 0;
}
