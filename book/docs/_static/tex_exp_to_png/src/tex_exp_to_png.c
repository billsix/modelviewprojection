#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

void print_usage(const char *progname) {
  printf("Usage:\n");
  printf("  %s --exp \"E = 5 + m*c^2\" --size 800 --output output.png\n",
         progname);
  printf("  %s -f input.txt --size 800 --output output.png\n", progname);
}

char *read_file(const char *filename) {
  FILE *file = fopen(filename, "r");
  if (!file) {
    perror("fopen");
    exit(EXIT_FAILURE);
  }
  fseek(file, 0, SEEK_END);
  long length = ftell(file);
  rewind(file);
  char *buffer = malloc(length + 1);
  if (!buffer) {
    perror("malloc");
    exit(EXIT_FAILURE);
  }
  fread(buffer, 1, length, file);
  buffer[length] = '\0';
  fclose(file);
  return buffer;
}

int main(int argc, char **argv) {
  char *expression = NULL;
  char *filename = NULL;
  char *size = NULL;
  char *output = NULL;

  static struct option long_options[] = {{"exp", required_argument, 0, 'e'},
                                         {"file", required_argument, 0, 'f'},
                                         {"size", required_argument, 0, 's'},
                                         {"output", required_argument, 0, 'o'},
                                         {0, 0, 0, 0}};

  int opt;
  int option_index = 0;
  while ((opt = getopt_long(argc, argv, "e:f:s:o:", long_options,
                            &option_index)) != -1) {
    switch (opt) {
    case 'e':
      expression = strdup(optarg);
      break;
    case 'f':
      filename = strdup(optarg);
      break;
    case 's':
      size = strdup(optarg);
      break;
    case 'o':
      output = strdup(optarg);
      break;
    default:
      print_usage(argv[0]);
      exit(EXIT_FAILURE);
    }
  }

  if ((!expression && !filename) || !size || !output) {
    print_usage(argv[0]);
    exit(EXIT_FAILURE);
  }

  if (filename) {
    expression = read_file(filename);
  }

  FILE *tex_file = fopen("formula.tex", "w");
  if (!tex_file) {
    perror("fopen formula.tex");
    exit(EXIT_FAILURE);
  }

  fprintf(tex_file,
          "\\documentclass{standalone}\n"
          "\\usepackage{amsmath}\n"
          "\\begin{document}\n"
          "$ %s $\n"
          "\\end{document}\n",
          expression);
  fclose(tex_file);

  int latex_status = system("latex formula.tex");
  if (latex_status != 0) {
    fprintf(stderr, "latex command failed\n");
    exit(EXIT_FAILURE);
  }

  char dvipng_cmd[512];
  snprintf(dvipng_cmd, sizeof(dvipng_cmd),
           "dvipng -D %s -T tight -o %s formula.dvi", size, output);

  int dvipng_status = system(dvipng_cmd);
  if (dvipng_status != 0) {
    fprintf(stderr, "dvipng command failed\n");
    exit(EXIT_FAILURE);
  }

  printf("PNG successfully created at %s\n", output);
  free(expression);
  free(filename);
  free(size);
  free(output);
  return 0;
}
