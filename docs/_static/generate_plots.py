# Copyright (c) 2018-2024 William Emerison Six
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import math
import sys
import itertools
import imageio

import plotutils.generategridlines as generategridlines
import plotutils.mpltransformations as mplt
from collections import namedtuple

if __name__ != "__main__":
    sys.exit(0)

matplotlib.use("agg")


# TODO, generalize to any number of dimensions
def accumulate_transformation(procedures, backwards=False):
    """Given a pipeline of functions, provide all intermediate results via a function.

    >>> fs = [mplt.translate(5,0),
    ...       mplt.translate(0,10)]
    >>> f = accumulate_transformation(fs)
    >>> f1, stepsRemaining = next(f)
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))
    >>> stepsRemaining
    2
    >>> f2, stepsRemaining = next(f)
    >>> f2((1, 2, 3), (4, 5, 6))
    ((6, 7, 8), (4, 5, 6))
    >>> stepsRemaining
    1
    >>> f3, stepsRemaining = next(f)
    >>> f3((1, 2, 3), (4, 5, 6))
    ((6, 7, 8), (14, 15, 16))
    >>> stepsRemaining
    0
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))
    >>> f = accumulate_transformation(fs, backwards=True)
    >>> f1, stepsRemaining = next(f)
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))
    >>> stepsRemaining
    2
    >>> f2, stepsRemaining = next(f)
    >>> f2((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (14, 15, 16))
    >>> stepsRemaining
    1
    >>> f3, stepsRemaining = next(f)
    >>> f3((1, 2, 3), (4, 5, 6))
    ((6, 7, 8), (14, 15, 16))
    >>> stepsRemaining
    0
    >>> f1((1, 2, 3), (4, 5, 6))
    ((1, 2, 3), (4, 5, 6))


    """

    # without this function, accumulate_transformation
    # would have an error in it, because of scope in a nested
    # function being retained.  I should figure out what is actually
    # happening there.
    def python_scoping_is_dumb(r, procedures):
        def foo(x, y):
            result_x, result_y = x, y
            for current_fn_index in r:
                result_x, result_y = procedures[current_fn_index](result_x, result_y)
            return result_x, result_y

        return foo

    def id(x, y):
        return x, y

    yield id, len(procedures)

    if not backwards:
        for number_of_fns_to_apply_this_round in [
            x + 1 for x in range(len(procedures))
        ]:
            yield python_scoping_is_dumb(
                range(number_of_fns_to_apply_this_round), procedures
            ), len(procedures) - number_of_fns_to_apply_this_round
    else:
        reversed_procs = list(range(len(procedures)))
        reversed_procs.reverse()
        for proc_index in reversed_procs:
            yield python_scoping_is_dumb(
                range(proc_index, len(procedures)), procedures
            ), proc_index


import doctest

modules = [mplt, sys.modules[__name__]]
for m in modules:
    try:
        doctest.testmod(m, raise_on_error=True)
        print(doctest.testmod(m))
    except Exception:
        print(doctest.testmod(m))
        sys.exit(1)


## Translation Plots


## Translation Plots - reading the transformations forward

### Step 1
graph_bounds = (100, 100)

fig, axes = plt.subplots()
axes.set_xlim([-graph_bounds[0], graph_bounds[0]])
axes.set_ylim([-graph_bounds[1], graph_bounds[1]])

Geometry = namedtuple("Geometry", "points color")

paddle1 = Geometry(
    points=list(
        zip(
            *np.array(
                [
                    [-10.0, -30.0],
                    [10.0, -30.0],
                    [10.0, 30.0],
                    [-10.0, 30.0],
                    [-10.0, -30.0],
                ]
            )
        )
    ),
    color=(0.578123, 0.0, 1.0),
)

paddle2 = Geometry(
    points=list(
        zip(
            *np.array(
                [
                    [-10.0, -30.0],
                    [10.0, -30.0],
                    [10.0, 30.0],
                    [-10.0, 30.0],
                    [-10.0, -30.0],
                ]
            )
        )
    ),
    color=(1.0, 0.0, 0.0),
)


def create_graphs(title, filename, geometry, procedures, backwards=False):
    """Creates an animated dif of the geometry, through a sequence of transformations"""

    procs = procedures.copy()
    # when plotting the transformations is backwards order, show the axis
    # at the last step first before plotting the data
    idProc = lambda x, y: (x, y)
    if backwards:
        procs.insert(0, idProc)
        procs.insert(0, idProc)
    else:
        procs.append(idProc)

    # create a single frame of the animated gif
    def create_single_frame(accumfn, stepsRemaining, fn, frame_number):
        for round_number in [1] if backwards else [1, 2]:
            fig, axes = plt.subplots()
            axes.set_xlim([-graph_bounds[0], graph_bounds[0]])
            axes.set_ylim([-graph_bounds[1], graph_bounds[1]])

            # plot transformed basis
            for xs, ys, thickness in generategridlines.generategridlines(
                graph_bounds, interval=5
            ):
                if backwards and stepsRemaining > 1:
                    transformed_xs, transformed_ys = accumfn(xs, ys)
                elif not backwards and round_number == 1 and frame_number != 1:
                    transformed_xs, transformed_ys = fn(xs, ys)
                else:
                    transformed_xs, transformed_ys = xs, ys
                plt.plot(
                    transformed_xs,
                    transformed_ys,
                    "-",
                    lw=thickness,
                    color=(0.1, 0.2, 0.5),
                    alpha=0.3,
                )

            # x axis
            if backwards and stepsRemaining > 1:
                transformed_xs, transformed_ys = accumfn([0.0, 10.0], [0.0, 0.0])
            elif not backwards and round_number == 1 and frame_number != 1:
                transformed_xs, transformed_ys = fn([0.0, 10.0], [0.0, 0.0])
            else:
                transformed_xs, transformed_ys = [0.0, 10.0], [0.0, 0.0]
            plt.plot(transformed_xs, transformed_ys, "-", lw=4.0, color=(0.0, 0.0, 1.0))

            # y axis
            if backwards and stepsRemaining > 1:
                transformed_xs, transformed_ys = accumfn([0.0, 0.0], [0.0, 10.0])
            elif not backwards and round_number == 1 and frame_number != 1:
                transformed_xs, transformed_ys = fn([0.0, 0.0], [0.0, 10.0])
            else:
                transformed_xs, transformed_ys = [0.0, 0.0], [0.0, 10.0]
            plt.plot(transformed_xs, transformed_ys, "-", lw=4.0, color=(1.0, 0.0, 1.0))

            if stepsRemaining <= 0:
                plotCharacter = "-"
            else:
                plotCharacter = "."
            # plot the points
            transformed_xs, transformed_ys = accumfn(*geometry.points)
            plt.title(str.format("{}\nStep {}", title, str(frame_number)))
            plt.plot(
                transformed_xs,
                transformed_ys,
                plotCharacter,
                lw=2,
                color=geometry.color,
            )

            # make sure the x and y axis are equally proportional in screen space
            plt.gca().set_aspect("equal", adjustable="box")
            fig.canvas.draw()
            image = np.frombuffer(fig.canvas.tostring_rgb(), dtype="uint8")
            image = image.reshape(fig.canvas.get_width_height()[::-1] + (3,))
            plt.close(fig)

            yield image

    # create a single frame
    animated_images_list = [
        create_single_frame(accumfn, stepsRemaining, fn, frame_number)
        for (accumfn, stepsRemaining), fn, frame_number in zip(
            accumulate_transformation(procs, backwards),
            [procs[0], *procs],
            itertools.count(start=1),
        )
    ]

    flattened_animated_images_list = list(itertools.chain(*animated_images_list))

    imageio.mimsave(
        "./" + filename + ".gif", flattened_animated_images_list, duration=1000, loop=0
    )
    for number, image in enumerate(flattened_animated_images_list):
        imageio.imsave("./" + filename + "-" + str(number) + ".png", image)


create_graphs(
    title="Translation",
    filename="translation-forwards",
    geometry=paddle1,
    procedures=[mplt.translate(-90.0, 20.0)],
)


create_graphs(
    title="Translation",
    filename="translation2-forwards",
    geometry=paddle2,
    procedures=[mplt.translate(90.0, -40.0)],
)

create_graphs(
    title="Translation",
    filename="translation-backwards",
    geometry=paddle1,
    procedures=[mplt.translate(-90.0, 20.0)],
    backwards=True,
)


create_graphs(
    title="Translation",
    filename="translation2-backwards",
    geometry=paddle2,
    procedures=[mplt.translate(90.0, -40.0)],
    backwards=True,
)

create_graphs(
    title="Rotation Relative to World Space",
    filename="rotate0",
    geometry=paddle1,
    procedures=[
        mplt.rotate(math.radians(45.0)),
    ],
)


create_graphs(
    title="Scale Relative to World Space",
    filename="scale",
    geometry=paddle1,
    procedures=[
        mplt.scale(2.0, 3.0),
    ],
)


create_graphs(
    title="Rotation, Relative to World Space",
    filename="rotate1-forwards",
    geometry=paddle1,
    procedures=[
        mplt.rotate(math.radians(45.0)),
        mplt.translate(-90.0, 20.0),
    ],
)

create_graphs(
    title="Incorrect Rotation, Relative to World Space",
    filename="incorrectrotate-forwards",
    geometry=paddle1,
    procedures=[
        mplt.translate(-90.0, 20.0),
        mplt.rotate(math.radians(65.0)),
    ],
)

create_graphs(
    title="Incorrect Rotation, Relative to Local Space",
    filename="incorrectrotate-backwards",
    geometry=paddle1,
    procedures=[
        mplt.translate(-90.0, 20.0),
        mplt.rotate(math.radians(65.0)),
    ],
    backwards=True,
)


create_graphs(
    title="Correct but Sloppy Rotation, Relative to Local Space",
    filename="rotate-sloppy-backwards",
    geometry=paddle1,
    procedures=[
        mplt.translate(-90.0, 20.0),
        mplt.translate(90.0, -20.0),
        mplt.rotate(math.radians(45.0)),
        mplt.translate(-90.0, 20.0),
    ],
    backwards=True,
)

create_graphs(
    title="Correct but Sloppy Rotation, Relative to World Space",
    filename="rotate-sloppy-forwards",
    geometry=paddle1,
    procedures=[
        mplt.translate(-90.0, 20.0),
        mplt.translate(90.0, -20.0),
        mplt.rotate(math.radians(45.0)),
        mplt.translate(-90.0, 20.0),
    ],
)


create_graphs(
    title="Rotation, Relative to Local Space",
    filename="rotate1-backwards",
    geometry=paddle1,
    procedures=[
        mplt.rotate(math.radians(45.0)),
        mplt.translate(-90.0, 20.0),
    ],
    backwards=True,
)


create_graphs(
    title="Rotation, Relative to World Space",
    filename="rotate2-forwards",
    geometry=paddle2,
    procedures=[mplt.rotate(math.radians(-10.0)), mplt.translate(90.0, -40.0)],
)

create_graphs(
    title="Rotation, Relative to Local Space",
    filename="rotate2-backwards",
    geometry=paddle2,
    procedures=[
        mplt.rotate(math.radians(-10.0)),
        mplt.translate(90.0, -40.0),
    ],
    backwards=True,
)

square = Geometry(
    points=list(
        zip(
            *np.array(
                [
                    [-10.0, -10.0],
                    [10.0, -10.0],
                    [10.0, 10.0],
                    [-10.0, 10.0],
                    [-10.0, -10.0],
                ]
            )
        )
    ),
    color=(1.0, 0.0, 0.0),
)


create_graphs(
    title="Covariance, Relative to Local Space",
    filename="covariance-backwards",
    geometry=square,
    procedures=[
        mplt.rotate(math.radians(-45.0)),
        mplt.scale(scaleX=2.0, scaleY=4.5),
        mplt.rotate(math.radians(45.0)),
    ],
    backwards=True,
)

create_graphs(
    title="Covariance, Relative to World Space",
    filename="covariance-forwards",
    geometry=square,
    procedures=[
        mplt.rotate(math.radians(-45.0)),
        mplt.scale(scaleX=2.0, scaleY=4.5),
        mplt.rotate(math.radians(45.0)),
    ],
    backwards=False,
)


t = np.linspace(0, np.pi * 2, 100)
circ = [list(np.cos(t) * 10), list(np.sin(t) * 10)]
circle = Geometry(points=circ, color=(0.0, 1.0, 0.0))

create_graphs(
    title="Circle, Relative to Local Space",
    filename="circle-backwards",
    geometry=circle,
    procedures=[
        mplt.rotate(math.radians(-45.0)),
        mplt.scale(scaleX=2.0, scaleY=4.5),
        mplt.rotate(math.radians(45.0)),
    ],
    backwards=True,
)

create_graphs(
    title="Circle, Relative to World Space",
    filename="circle-forwards",
    geometry=circle,
    procedures=[
        mplt.rotate(math.radians(-45.0)),
        mplt.scale(scaleX=2.0, scaleY=4.5),
        mplt.rotate(math.radians(45.0)),
    ],
    backwards=False,
)
