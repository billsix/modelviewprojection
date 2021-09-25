ModelViewProjection
===================

Learn how to build 3D graphics from the ground up.
This codebase demonstrates how to create objects, put
them where you want them to go, view the scene with a camera
that can move, and how to project that 3D data to a 2D screen.


For further information, such as lighting, shadows, and
OpenGL in more explicit detail, consult
1) OpenGL redbook/bluebook. (OpenGL superbible v4, because it covers fixed function and shaders)
2) Mathematics for 3D Game Programming and Computer Graphics
3) Computer Graphics: Principles and Practice in C (2nd Edition)

For RayTracing
1) Physically Based Rendering
2) Ray Tracing from the Ground Up


Approach
--------
This book uses "mistake-driven-development".  I show incrementally
how to build a more complex graphics application, making mistakes along
the way, and then fixing the mistakes.

Windows
-------
Use Visual Studio 2019 (Tested on community, but I'm sure it will work on others).

Using Developer Command Prompt

        python -m venv venv
        cd venv\Scripts
        activate.bat
        cd ..\..\
        python -m pip install --upgrade pip setuptools
        python -m pip install -r requirements.txt
        python src\demo05\demo.py


Linux
-----
Install Python3, glfw via a package manager.  Use pip and virtualenv to install dependencies


#### Linux


        python -m venv venv
        source venv/bin/activate
        python -m pip install --upgrade pip setuptools
        python -m pip install -r requirements.txt
        python src/demo05/demo.py


Mac
---
Python Python3 (via anaconda, homebrew, macports, whatever), and use pip and virtualenv to install dependencies.

#### Mac OS X

        python -m venv venv
        source venv/bin/activate
        python -m pip install --upgrade pip setuptools
        python -m pip install -r requirements.txt
        python src/demo05/demo.py


### Build the book

Install Python, either through Cygwin, Visual Studio, brew, or apt.

#### Windows, using Developer Command Prompt

        python -m venv venv
        cd venv\Scripts
        activate.bat
        cd ..\..\
        python -m pip install --upgrade pip setuptools
        python -m pip install -r requirements.txt
        cd doc
        make html

#### Mac OS X

        python -m venv venv
        source venv/bin/activate
        python -m pip install --upgrade pip setuptools
        python -m pip install -r requirements.txt
        cd doc
        make html

#### Linux


        python -m venv venv
        source venv/bin/activate
        python -m pip install --upgrade pip setuptools
        python -m pip install -r requirements.txt
        cd doc
        make html
        make latexpdf
