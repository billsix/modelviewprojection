import re
import sys


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
        with open(output_filename, "w") as w:
            for line in f.readlines():
                if not line.startswith(".. LINENOS"):
                    w.write(line)
                else:
                    try:
                        source_file, pattern = line.split(" ")[2:]
                        begin_line_number, end_line_number = list(
                            find_line_numbers(source_file, pattern)
                        )
                    except Exception as e:
                        # import pdb
                        # pdb.set_trace()
                        print(pattern)
                        print(e)
                        sys.exit(1)

                    w.write(".. literalinclude:: " + source_file + "\n")
                    w.write("   :language: python\n")
                    w.write("   :linenos:\n")
                    w.write(
                        "   :lineno-start: " + str(int(begin_line_number) + 1) + "\n"
                    )
                    w.write(
                        "   :lines: "
                        + str(int(begin_line_number) + 1)
                        + "-"
                        + str(int(end_line_number) - 1)
                        + "\n"
                    )


preprocess_file("ch01.in.rst", "ch01.rst")
preprocess_file("ch02.in.rst", "ch02.rst")
preprocess_file("ch03.in.rst", "ch03.rst")
preprocess_file("ch04.in.rst", "ch04.rst")
preprocess_file("ch05.in.rst", "ch05.rst")
preprocess_file("ch06.in.rst", "ch06.rst")
preprocess_file("ch07.in.rst", "ch07.rst")
preprocess_file("ch08.in.rst", "ch08.rst")
preprocess_file("ch09.in.rst", "ch09.rst")
preprocess_file("ch10.in.rst", "ch10.rst")
preprocess_file("ch11.in.rst", "ch11.rst")
preprocess_file("ch12.in.rst", "ch12.rst")
preprocess_file("ch13.in.rst", "ch13.rst")
preprocess_file("ch14.in.rst", "ch14.rst")
preprocess_file("ch15.in.rst", "ch15.rst")
preprocess_file("ch16.in.rst", "ch16.rst")
preprocess_file("ch17.in.rst", "ch17.rst")
preprocess_file("ch18.in.rst", "ch18.rst")
preprocess_file("ch19.in.rst", "ch19.rst")
