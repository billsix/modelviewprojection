import re

def find_line_numbers(filename, pattern):
    with open(filename) as f:
        for lineno, line in enumerate(f.readlines(), start=1):
            x = re.search("begin " + pattern, line)
            if x:
                yield lineno
            x = re.search("end " + pattern, line)
            if x:
                yield lineno

def preprocess_file(filename, output_filename):
    with open(filename) as f:
        with open(output_filename, 'w') as w:
            for line in f.readlines():
                if not line.startswith('.. LINENOS'):
                    w.write(line)
                else:
                    source_file, pattern = line.split(' ')[2:]

                    begin_line_number, end_line_number = list(find_line_numbers(source_file, pattern))

                    w.write(".. literalinclude:: " + source_file + '\n')
                    w.write("   :language: python\n")
                    w.write("   :linenos:\n")
                    w.write("   :lineno-start: " + str(int(begin_line_number) + 1) + '\n')
                    w.write("   :lines: " + str(int(begin_line_number) + 1) + '-' + str(int(end_line_number) - 1) + '\n')

preprocess_file('ch01.in.rst', 'ch01.rst')
