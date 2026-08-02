
Glossary
========

.. glossary::
   :sorted:

   Cayley Graph
     The picture this course uses to relate coordinate systems: each node is a
     coordinate system (an origin and axes -- a "space", such as
     :term:`Modelspace` or :term:`World Space`), and each directed edge is an
     invertible function that converts coordinates from one space to another.
     To take data between two spaces, trace a path through the graph and compose
     the edges, applying an edge's inverse whenever you travel against its arrow.
     The name is borrowed from group theory; here we use only the diagram, not
     the group-theoretic machinery.

     Further reading:
     `Cayley graph (Wikipedia) <https://en.wikipedia.org/wiki/Cayley_graph>`_ is
     the construct the name comes from -- but note it is written for
     mathematicians (there the nodes are a *group's elements*, not coordinate
     systems, and it assumes group theory), so it is more abstract than this
     book's usage;
     `Visual Group Theory, "Cayley graphs" <https://www.youtube.com/watch?v=vzEObOzsSKY>`_
     is a gentler, visual introduction.

   Frame Buffer
     An array of pixel values, where each pixel holds information such as
     color (red, green, blue, alpha), depth (how far a fragment is from
     the camera), and sometimes stencil values (for masking
     operations).

     Further reading:
     `Framebuffer (Wikipedia) <https://en.wikipedia.org/wiki/Framebuffer>`_ is a
     plain-language overview of the buffer that holds the on-screen image and
     the per-pixel data it stores.

   Normalized Device Coordinates
     Normalized Device Coordinates are the range of values from -1.0 to 1.0
     in the X, Y, and Z directions, the last space before drawing geometry
     in screen space.  Anything vertex outside of the NDC range will not
     be mapped to a pixel.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     shows where NDC (the -1 to 1 cube) sits among the graphics coordinate
     spaces, in beginner-friendly terms.

   World Space
     The single, shared coordinate system that every object is placed into to
     form the scene.  An object whose geometry is given in its own
     :term:`modelspace <Modelspace>` is moved into world space by a
     transformation that positions and orients it relative to one common
     world origin, so that objects defined independently share a single frame
     of reference.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     introduces world space and the transformation from an object's own space
     into it, for programmers.

   Modelspace
     The coordinate system in which a single object's geometry is defined,
     relative to that object's own local origin.  For example, a paddle's four
     corners are given as offsets from the center of the paddle, describing the
     paddle's shape independently of where it later sits in the scene.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     calls this "local space" and shows how an object's own coordinates become
     world coordinates, in beginner-friendly terms.

   Camera Space
     The coordinate system in which every position is measured relative to the
     camera, rather than relative to :term:`World Space`.  The virtual camera is
     placed into the world just like any other object; to express the scene from
     the camera's point of view, the camera's placement is *inverted* and applied
     to everything, so the camera sits at the origin looking down its own axis.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     is a beginner-friendly introduction to the same model / world / view /
     clip spaces (it calls camera space "view space").

   Screen Space
     Screen space is an index (x,y) that is mapped to a pixel on a monitor.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     covers screen space as the final step, where NDC is mapped to the pixels
     of the viewport.

   Event Loop
     An event loop is a programming construct that continuously waits for and dispatches
     events or messages in a program. At its core, it works like this:

     #. The program has a queue of tasks, events, or messages that need to
        be processed (like user input, network responses, timers, etc.).

     #. The event loop repeatedly checks this queue.  If there's an event
        waiting, it pulls it from the queue and runs the associated
        code (often a callback or handler).

     #. If the queue is empty, it waits until something new arrives.

     This pattern is common in systems where tasks happen asynchronously - such
     as GUIs or command lines because it lets programs handle many things
     (like clicks, network requests, or timers) without blocking on just one operation.

     Further reading:
     `Event loop (Wikipedia) <https://en.wikipedia.org/wiki/Event_loop>`_ is a
     language-agnostic overview of the wait-for-and-dispatch-events pattern.

   Invertible Function
     A function that can be undone: for every invertible function there is
     an :term:`Inverse` that reverses it, so applying the function and then
     its inverse leaves the input unchanged --- :inlinetex:`(f \circ
     f^{-1})(x) = x`.  In this course the directed edges of a :term:`Cayley
     Graph` are invertible functions --- each converts coordinates from one
     :term:`Coordinate System` to another, and because it is invertible you
     can also travel the edge backwards by applying its inverse.  The
     primitives the book builds scenes from --- :term:`Translation`,
     :term:`Rotation`, :term:`Scaling` --- are all invertible.

     Further reading:
     `Inverse Functions (Math is Fun) <https://www.mathsisfun.com/sets/function-inverse.html>`_
     is a plain, example-driven introduction (including the Celsius /
     Fahrenheit conversion this book also uses) to when a function has an
     inverse and what "undoing" it means.

   Function Composition
     Feeding the output of one function straight into another to make a
     single combined function: :inlinetex:`(f \circ g)(x) = f(g(x))`, read
     right-to-left as "do g first, then f".  This is how the course moves
     data across several spaces at once --- trace a path through the
     :term:`Cayley Graph` and compose the edge functions along it, and you
     get one function from the starting :term:`Coordinate System` to the
     ending one, without ever naming the coordinates in between.  In the
     Python demos, chaining method calls (or building a :term:`Function
     Stack`) is the same idea as mathematical composition.

     Further reading:
     `Composition of Functions (Math is Fun) <https://www.mathsisfun.com/sets/functions-composition.html>`_
     explains :inlinetex:`(g \circ f)(x) = g(f(x))` in plain language with
     the "functions as machines" metaphor, and stresses that order matters.

   Inverse
     The transformation that undoes another one.  Traveling *against* the
     direction of a :term:`Cayley Graph` edge means applying the inverse of
     that edge's function instead of the function itself.  Each primitive
     has a simple inverse: the inverse of a :term:`Translation` shifts back
     by the negative amount, the inverse of a :term:`Rotation` turns by the
     negative angle, and the inverse of a :term:`Scaling` multiplies by the
     reciprocal.  The inverse of a whole :term:`Function Composition` is the
     inverse of each step applied in reverse order, so ``inverse(compose([f1,
     f2]))`` equals ``compose([inverse(f2), inverse(f1)])``.

     Further reading:
     `Inverse function (Wikipedia) <https://en.wikipedia.org/wiki/Inverse_function>`_
     opens plainly ("a function that undoes the operation of f"); the later
     sections turn formal, so a reader who only wants the idea can stop after
     the introduction.

   Coordinate System
     A system of numbers used to say where things are --- an origin together
     with axes --- which this book also calls a *space*.  The same point has
     different coordinates in different systems, just as the same amount of
     money can be counted in nickels or pennies, or the same temperature read
     in Celsius or Fahrenheit.  Each node of a :term:`Cayley Graph` is a
     coordinate system (:term:`Modelspace`, :term:`World Space`, :term:`Camera
     Space`, :term:`Normalized Device Coordinates`, ...), and the whole point
     of the machinery is converting coordinates from one system to another.

     Further reading:
     `Cartesian Coordinates (Math is Fun) <https://www.mathsisfun.com/data/cartesian-coordinates.html>`_
     is a beginner-friendly walk-through of an origin, x/y (and z) axes, and
     plotting points.

   Change of Basis
     Rewriting the coordinates of a point so they are measured against a
     different set of axes (a different *basis*) --- in this book, converting
     coordinates from one :term:`Coordinate System` to another.  Every
     position is written as a scaled sum of basis vectors (the *natural
     basis* ``e_1``, ``e_2`` is one unit along x and one unit along y);
     choosing a different origin and axes gives the same geometric point a
     new set of numbers.  That conversion is exactly what a directed edge of
     the :term:`Cayley Graph` performs, so "change of basis" and "following an
     edge" describe the same operation.

     Further reading:
     `Change of basis (3Blue1Brown, Essence of Linear Algebra) <https://www.youtube.com/watch?v=P2LTAUO1TdA>`_
     is a highly visual, intuition-first video showing how the same vector
     gets different coordinates in different bases.

   Transformation
     A function that takes coordinates in and gives new coordinates out ---
     moving, turning, or resizing geometry.  Translating, rotating, and
     scaling vertices are the core transformations of computer graphics (see
     :term:`Translation`, :term:`Rotation`, :term:`Scaling`).  In this course
     every transformation is an :term:`Invertible Function`, which is what
     lets it serve as an edge of the :term:`Cayley Graph` and be combined
     with others through :term:`Function Composition`.

     Further reading:
     `Transformations (LearnOpenGL) <https://learnopengl.com/Getting-started/Transformations>`_
     covers translation, rotation, and scaling for graphics learners with
     diagrams and code --- it does lean on some trigonometry, and the author
     invites you to revisit it, so treat the matrix details as optional on a
     first read.

   Affine Function
     A function of the familiar straight-line form :inlinetex:`f(x) = m
     \times x + b` --- a constant multiple of the input plus a constant
     offset (high-school ``y = mx + b``).  The book builds one by composing a
     scaling :inlinetex:`S` (the :inlinetex:`m \times x` part) with a
     :term:`Translation` :inlinetex:`T` (the :inlinetex:`+ b` part):
     :inlinetex:`f = T \circ S`.  Recognizing the :inlinetex:`m` and
     :inlinetex:`b` in a formula, and generating a new function for chosen
     values of them, is what :term:`Partial Application` gives you.

     Further reading:
     `Equation of a Straight Line (Math is Fun) <https://www.mathsisfun.com/equation_of_line.html>`_
     is the gentlest starting point for the slope-and-intercept ``y = mx +
     b`` idea; the canonical
     `Affine transformation (Wikipedia) <https://en.wikipedia.org/wiki/Affine_transformation>`_
     names the concept but opens with abstract geometry --- skip to its
     "Examples" section, which states that :inlinetex:`f(x) = mx + c` are
     exactly the affine transformations of the line.

   Function Stack
     A stack (a last-in, first-out list) whose elements are functions, used
     to build a coordinate transformation one step at a time.  Pushing
     functions on in reverse order lets the demos read a :term:`modelspace
     <Modelspace>`-to-:term:`Normalized Device Coordinates` transformation
     from top to bottom while it still executes in the right order: the last
     function pushed is applied first (the book calls this "Last In, First
     Applied").  Because a scene is a hierarchy of relative objects, you push
     the extra edges for a child object, draw it, then pop them to return the
     stack to the parent's state --- the same idea as OpenGL's ModelView and
     Projection matrix stacks, but built from :term:`Invertible Function`\ s
     instead of matrices.

     Further reading:
     `Stack (abstract data type) (Wikipedia) <https://en.wikipedia.org/wiki/Stack_(abstract_data_type)>`_
     opens with a plain plates-stacked-on-plates picture of push/pop and the
     LIFO rule.

   First-Class Functions
     A language feature where functions are ordinary values: they can be
     stored in variables, passed as arguments to other functions, returned
     as results, and applied later zero, one, or many times.  Python has
     this, which is what lets the course treat a :term:`Transformation` as a
     piece of data --- storing an :term:`Invertible Function` on a
     :term:`Function Stack`, passing a key handler to GLFW, or building new
     functions with :term:`Partial Application`.  Without it, the book's whole
     "functions as the edges of a graph" approach could not be expressed.

     Further reading:
     `First-class Function (MDN) <https://developer.mozilla.org/en-US/docs/Glossary/First-class_Function>`_
     is a short, programmer-facing explanation with runnable examples of
     assigning, passing, and returning functions.

   Partial Application
     Fixing some of a function's arguments now to produce a new function
     that takes the remaining arguments later.  ``translate(b=...)`` is the
     book's main example: it takes the two-input idea of vector addition,
     pins one input to a constant ``b``, and hands back a one-argument
     function that shifts whatever you pass it --- written
     :inlinetex:`T_{b}(x) = x + b`.  This is how a general pattern like the
     :term:`Affine Function` :inlinetex:`m \times x + b` becomes a concrete,
     reusable :term:`Transformation` for chosen values, and it relies on
     :term:`First-Class Functions`.

     Further reading:
     `Partial Application and Currying (DigitalOcean) <https://www.digitalocean.com/community/tutorials/javascript-functional-programming-explained-partial-application-and-currying>`_
     is a beginner-friendly, code-first tutorial; the canonical
     `Partial application (Wikipedia) <https://en.wikipedia.org/wiki/Partial_application>`_
     has a clear opening definition and example but then dives into
     higher math (group actions, Lie algebras), so stop after its
     "Motivation" section.

   Black Box vs White Box
     Two ways of looking at the same piece of code.  A *black box* is used
     purely through its interface --- you know what ``translate`` does and
     that it is an :term:`Invertible Function`, and you deliberately forget
     how it is implemented ("a big part of understanding graphics is figuring
     out what to ignore").  A *white box* is the same function with its
     definition open, where you read the actual body.  The course shows both
     on purpose: it gives a primitive's white-box definition once, then
     treats it as a black box everywhere after, so you can reason about whole
     :term:`Cayley Graph` paths without re-deriving each edge.

     Further reading:
     `Black box (Wikipedia) <https://en.wikipedia.org/wiki/Black_box>`_ (the
     book's own link) describes a system viewed only through its inputs and
     outputs; its companion
     `White box (Wikipedia) <https://en.wikipedia.org/wiki/White-box_(software_engineering)>`_
     covers the opposite, internals-visible view.

   Clip Space
     The four-coordinate space (x, y, z, w) that a vertex is in right after the
     projection transformation, one step before it becomes
     :term:`Normalized Device Coordinates`.  OpenGL turns clip space into NDC by
     dividing x, y, and z each by that fourth coordinate w (in this course, the
     camera-space depth is what gets stored in w).  Carrying this extra
     dimension is what lets a *single* perspective matrix handle every vertex,
     no matter how far it is from the camera; the course otherwise stays in NDC
     because 4D is hard to picture.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     explains clip space and the "perspective divide" (dividing by w) for
     programmers --- moderately beginner-friendly, though it assumes some
     comfort with vectors and matrices.

   Translation
     The transformation that shifts a point by a fixed offset, moving it without
     rotating or resizing it.  In this course ``translate(b=...)`` is built
     directly on :term:`Vector <Vector (Vector2 / Vector3)>` addition --- it adds
     the offset ``b`` to every point you hand it --- and it is one of the three
     core transformations, alongside :term:`Scaling` and :term:`Rotation`.  Its
     inverse simply shifts back by the negative offset.

     Further reading:
     `Transformations (LearnOpenGL) <https://learnopengl.com/Getting-started/Transformations>`_
     introduces translation, scaling, and rotation together for graphics
     programmers, with diagrams and code (assumes only basic algebra and
     trig).

   Scaling
     The transformation that stretches or shrinks an object by multiplying each
     coordinate by a scale factor: a factor above 1 grows it, a factor between 0
     and 1 shrinks it.  ``uniform_scale(m=...)`` multiplies every component of a
     :term:`Vector <Vector (Vector2 / Vector3)>` by the same number ``m`` (the
     shape stays the same, only the size changes), and it is how the course
     squeezes 20-unit-wide :term:`World Space` down into the -1 to 1 range of
     :term:`Normalized Device Coordinates`.  Scaling happens relative to the
     :term:`Origin`, which is one reason objects are modeled centered on their
     own origin; its inverse scales by the reciprocal factor.

     Further reading:
     `Transformations (LearnOpenGL) <https://learnopengl.com/Getting-started/Transformations>`_
     (the same page as :term:`Translation`) covers scaling as component-wise
     multiplication --- beginner-friendly, minimal math assumed.

   Rotation
     The transformation that turns an object about a fixed point --- in 2D, the
     :term:`Origin` --- by some angle, leaving its size and shape unchanged.  The
     course first derives 2D rotation from the sine and cosine of the angle,
     then extends it to 3D as three separate turns, ``rotate_x``, ``rotate_y``,
     and ``rotate_z``, one about each axis, whose positive direction follows the
     :term:`Right-Hand Rule`.  It is the third core transformation, with
     :term:`Translation` and :term:`Scaling`; its inverse rotates back by the
     negative angle.  Combining rotations about *different* axes is
     order-dependent --- see :term:`Non-commutativity of Rotations`.

     Further reading:
     `Transformations (LearnOpenGL) <https://learnopengl.com/Getting-started/Transformations>`_
     shows rotation with diagrams for programmers; for the step-by-step 2D
     trigonometry this course works through, `2D Rotations (Alan Zucconi)
     <https://www.alanzucconi.com/2016/02/03/2d-rotations/>`_ is a good
     companion, though it moves quickly through the algebra and uses Greek-letter
     angle notation.

   Identity
     The transformation that does nothing: it hands back every point exactly as
     given, the geometric equivalent of multiplying a number by 1.  As a
     function it is ``f(x) = x``; as a matrix (introduced in demo 19 via
     ``glLoadIdentity``) it is the 4x4 with 1's down the diagonal and 0's
     everywhere else.  It is the natural starting point before building up a
     transformation --- loading the identity means "no transformation yet,"
     after which each :term:`Translation`, :term:`Rotation`, or :term:`Scaling`
     is composed on top of it.

     Further reading:
     `The identity matrix and its properties (MathBootCamps) <https://www.mathbootcamps.com/the-identity-matrix-and-its-properties/>`_
     is a beginner-friendly explanation built around the "acts like 1" analogy,
     with worked examples.

   Vertex
     A single point in space, given by its coordinates --- for example, the four
     corners that define a rectangular paddle.  The early demos hand each vertex
     to OpenGL with ``glVertex2f`` / ``glVertex3f`` to mark out a shape; later
     the same points are stored as :term:`Vectors <Vector (Vector2 / Vector3)>`
     and transformed from one space to another.  In modern OpenGL a vertex can
     also carry extra data beyond its position, such as a color.

     Further reading:
     `Hello Triangle (LearnOpenGL) <https://learnopengl.com/Getting-started/Hello-Triangle>`_
     defines vertices and vertex data for programmers; thorough but demanding,
     as it introduces buffers and shaders at the same time.

   Natural Basis / Basis Vector
     The small set of unit-length :term:`Vectors <Vector (Vector2 / Vector3)>`
     that every other vector is built from by scaling and adding.  The course
     calls them the *natural basis*: ``e_1`` is one unit along the x axis,
     ``e_2`` one unit along y, and (in 3D) ``e_3`` one unit along z.  Any vector
     is a *scaled sum* of these --- ``3 * e_1 + 2 * e_2`` is the point (3, 2) ---
     so writing a paddle's corners this way makes each one read as "a step in x
     plus a step in y" away from the :term:`Origin`.

     Further reading:
     `Linear combinations, span, and basis vectors (3Blue1Brown) <https://www.youtube.com/watch?v=k7RM-ot2NWY>`_
     is a highly visual video that shows how scaling and adding basis vectors
     reaches every point --- one of the most accessible explanations available.

   Origin
     The center point of a coordinate system --- the (0, 0) in 2D or (0, 0, 0)
     in 3D where the axes cross, and where the
     :term:`Basis Vectors <Natural Basis / Basis Vector>` all begin.  Every space
     in the course has its own origin: an object is modeled centered on its
     :term:`Modelspace` origin (which makes :term:`Scaling` and :term:`Rotation`
     about the center simple), while :term:`World Space` has one shared origin
     that every object is placed relative to.

     Further reading:
     `Cartesian Coordinates (Math is Fun) <https://www.mathsisfun.com/data/cartesian-coordinates.html>`_
     introduces the origin and the x / y axes visually, in plain language, with
     an interactive plot.

   Right-Hand Rule
     A convention for fixing which direction counts as "positive" in 3D.  Point
     the fingers of your right hand along the x axis and curl them toward the y
     axis; your thumb then points along the positive z axis --- which is why, in
     this course, positive z comes *out* of the screen toward you and negative z
     goes into it.  The same rule gives the positive direction of a
     :term:`Rotation` about any axis: curl your fingers in the direction of a
     positive angle, and your thumb points along the axis you are turning about.

     Further reading:
     `Right-hand rule (Wikipedia) <https://en.wikipedia.org/wiki/Right-hand_rule>`_
     has clear diagrams for coordinate handedness and the grip rule --- but note
     that much of the page is written for physics (magnetic fields, cross
     products) with heavy vector notation, so lean on the diagrams and the
     coordinate-system section and skip the electromagnetism.

   Vector (Vector2 / Vector3)
     A quantity with both a size and a direction, stored as a list of
     coordinates: ``Vector2`` holds an (x, y) pair for 2D work, ``Vector3`` an
     (x, y, z) triple for 3D.  The course uses vectors for two related things ---
     the position of a :term:`Vertex`, and the offset of a :term:`Translation`
     --- and gives them arithmetic that matches the geometry: adding two vectors
     adds their components, and multiplying by a number scales them.  Every
     vector is a scaled sum of the
     :term:`Basis Vectors <Natural Basis / Basis Vector>`.

     Further reading:
     `Vectors (Math is Fun) <https://www.mathsisfun.com/algebra/vectors.html>`_
     is a plain-language, illustrated introduction to magnitude, direction,
     components, and vector addition --- very beginner-friendly.

   Non-commutativity of Rotations
     The fact that the order of two :term:`Rotations <Rotation>` about
     *different* axes changes the outcome --- rotating about y and then x does
     not land in the same place as x and then y.  (Rotations about the *same*
     axis are the exception; those can be applied in any order.)  This is why
     demo 17 is careful to rotate the camera about its y axis *before* its x
     axis, and the book invites you to feel it directly: turn your head right
     then down, versus down then right, and notice the two poses differ.
     "Non-commutative" is the general term for any operation where order matters,
     unlike adding numbers, where it does not.

     Further reading:
     `Rotations are non-commutative in 3D (Robot Academy) <https://robotacademy.net.au/lesson/rotations-are-non-commutative-in-3d/>`_
     is a short video in which the presenter physically turns coordinate frames
     in two different orders to show the mismatch.  Caveat: the wider robotics
     course assumes undergraduate linear algebra, but this particular
     demonstration is intuitive on its own.

   Orthographic Projection
     The transformation, implemented by ``ortho``, that maps a rectangular
     prism defined relative to :term:`Camera Space` onto
     :term:`NDC <Normalized Device Coordinates>` -- the -1 to 1 cube.  It
     works by moving the center of the prism to the origin and then scaling
     each axis by the inverse of its width, height, and depth.  Because every
     point is scaled by the same amounts regardless of how far away it is,
     objects do *not* get smaller with distance, which is why the demo17 scene
     doesn't yet look like a real 3D application.  Contrast with
     :term:`Perspective Projection`.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     is a beginner-friendly, visual walk-through of orthographic vs.
     perspective projection for programmers.

   Perspective Projection
     The transformation, implemented by ``perspective``, that makes objects
     further from the viewer appear smaller, the way they do in real life.
     Where :term:`Orthographic Projection` maps a box, this maps a
     :term:`Frustum` (a pyramid with its tip cut off): a point's x and y are
     scaled toward the center axis in proportion to its depth, so two objects
     that subtend the same angle from the eye land at the same place on screen
     even though one is farther away.  The squished result is then handed to
     ``ortho`` to finish mapping it into
     :term:`NDC <Normalized Device Coordinates>`.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     explains perspective projection for programmers using the vanishing-point
     analogy, with diagrams and code.

   Frustum
     The shape of the region of :term:`Camera Space` that a
     :term:`Perspective Projection` actually draws: a pyramid whose tip is at
     the camera, with the top sliced off by the :term:`Near Plane` and the
     bottom by the :term:`Far Plane`.  Anything outside this pyramid is
     :term:`clipped <Clipping>` away and never appears on screen.  It is the
     perspective counterpart of the rectangular :term:`View Volume` used by
     :term:`Orthographic Projection`.

     Further reading:
     `Viewing frustum (Wikipedia) <https://en.wikipedia.org/wiki/Viewing_frustum>`_
     defines the frustum and its near/far planes -- though it leans on some
     graphics jargon, so pair it with the gentler
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_.

   Field of View
     The angle of the viewing :term:`Frustum` -- how wide an arc of the world
     the camera takes in.  In this book's ``perspective`` function it is the
     *vertical* angle, measured from the top of the frustum to the bottom, and
     together with the :term:`Aspect Ratio` it fixes the size of the viewable
     region at any given depth.  A larger field of view fits more of the scene
     onto the screen, which makes each object appear smaller; a narrower one
     zooms in.

     Further reading:
     `Field of view in video games (Wikipedia) <https://en.wikipedia.org/wiki/Field_of_view_in_video_games>`_
     shows, with examples and pictures, what widening or narrowing the FOV does
     to what a player sees (skip the trigonometry sections if the math is
     unfamiliar).

   Near Plane
   Far Plane
     The two depth boundaries of the viewable region along the camera's z
     axis.  The near plane is the closest distance the camera will draw and the
     far plane is the farthest; together they cap the :term:`Frustum` (or the
     rectangular :term:`View Volume` for :term:`Orthographic Projection`) at
     the front and back.  Any geometry nearer than the near plane or beyond the
     far plane is :term:`clipped <Clipping>` out.  Their placement also affects
     depth precision -- see :term:`Z-fighting`.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     introduces the near and far planes as part of building a projection, in
     plain terms for programmers.

   Aspect Ratio
     The width of the viewport divided by its height.  The ``perspective``
     function uses it to turn the vertical :term:`Field of View` into the
     horizontal extent of the :term:`Frustum` (``right = top * aspect_ratio``),
     so that a wide window shows a correspondingly wide slice of the world and
     the scene isn't stretched or squashed.  Use the viewport's width/height,
     which is not necessarily the same as the window's.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     shows where aspect ratio enters the projection and why it matches the
     viewport, aimed at programmers.

   Homogeneous Coordinate / Perspective Divide
     A homogeneous coordinate adds a fourth number, ``w``, to a 3D point
     ``(x, y, z)``.  The *perspective divide* is the step that turns such a
     point back into an ordinary one by dividing through by ``w`` --
     ``(x/w, y/w, z/w)``.  This is the mechanism perspective is built on: by
     arranging for ``w`` to carry the point's camera-space depth, dividing by
     it shrinks distant things automatically.  In OpenGL the divide is done for
     you when converting from :term:`Clip Space` to
     :term:`NDC <Normalized Device Coordinates>`.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     introduces perspective division gently; for a deeper, still
     programmer-oriented derivation of where ``w`` comes from, see
     `OpenGL Projection Matrix (songho) <https://www.songho.ca/opengl/gl_projectionmatrix.html>`_
     (it does use matrix algebra, which this book otherwise avoids).

   Clipping
     Discarding the parts of the geometry that fall outside the viewable
     region so they are never drawn.  Concretely, any vertex outside
     :term:`NDC <Normalized Device Coordinates>` (-1 to 1 on all three axes) --
     equivalently, outside the :term:`View Volume` or :term:`Frustum` in
     :term:`Camera Space` -- gets clipped and mapped to no pixel.  This is why,
     in demo17, parts of the scene vanish when you move the viewer: they leave
     the -1 to 1 range.

     Further reading:
     `Clipping (computer graphics) (Wikipedia) <https://en.wikipedia.org/wiki/Clipping_(computer_graphics)>`_
     gives a short overview with everyday examples; it references some related
     graphics terms in passing, so treat it as an overview rather than a
     step-by-step tutorial.

   View Volume
     The region of :term:`Camera Space` that maps into
     :term:`NDC <Normalized Device Coordinates>` and therefore actually gets
     drawn.  For :term:`Orthographic Projection` it is a rectangular prism (a
     box); for :term:`Perspective Projection` it is a :term:`Frustum`.  It is
     bounded on the sides by the left/right and bottom/top edges and front-to-
     back by the :term:`Near Plane` and :term:`Far Plane`; anything outside it
     is :term:`clipped <Clipping>`.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     describes the box- and frustum-shaped view volumes and how a projection
     maps them onto NDC, in beginner-friendly terms.

   Virtual Camera
     A camera modeled in software so the viewer can move around the scene.  It
     is a data structure holding a position and orientation, and it is placed
     into :term:`World Space` exactly like any other object.  To render the
     scene from its point of view, we do *not* draw the camera; instead we
     apply the *inverse* of its placement to every object, which is what
     produces :term:`Camera Space`.

     Further reading:
     `Camera (LearnOpenGL) <https://learnopengl.com/Getting-started/Camera>`_
     is a beginner-friendly explanation of simulating a camera by moving the
     world in the opposite direction, with code.

   Standard Perspective Matrix
     The single 4x4 matrix that OpenGL expects for perspective, which this book
     derives step by step in the "Standard Perspective Matrix" section.  The
     work of the derivation is to remove the camera-space z from inside the
     matrix -- by routing it through the ``w`` component in
     :term:`Clip Space` (see :term:`Homogeneous Coordinate / Perspective
     Divide`) -- so that *one* fixed matrix works for every vertex regardless
     of its depth, instead of needing a custom matrix per point.  Unlike the
     ``perspective`` function used earlier in the course, it spaces depth
     values non-linearly between the :term:`Near Plane` and :term:`Far Plane`.

     Further reading:
     `OpenGL Projection Matrix (songho) <https://www.songho.ca/opengl/gl_projectionmatrix.html>`_
     derives exactly this matrix with frustum diagrams and similar triangles.
     It suits programmers, but note it works entirely in matrix/linear-algebra
     terms, which this course deliberately replaces with functions and
     inverses.

   Z-fighting
     The flickering that appears when two surfaces are at almost the same
     distance from the camera and the depth buffer can't reliably tell which is
     in front, so they visibly fight over the same pixels.  It comes from the
     limited precision of the :term:`Depth Buffer`.  Because the
     :term:`Standard Perspective Matrix` distributes depth precision
     non-linearly, z-fighting is worse for far-away geometry (near the
     :term:`Far Plane`) than for close-up geometry.

     Further reading:
     `Z-fighting (Wikipedia) <https://en.wikipedia.org/wiki/Z-fighting>`_
     explains the cause and common fixes; it assumes a little rendering
     vocabulary but is otherwise readable for graphics learners.

   Shader
     A shader is a small program that runs on the :term:`GPU` rather than on
     the CPU.  Before shaders existed, the graphics card ran a fixed set of
     built-in steps (the :term:`Fixed-Function Pipeline`) that you could only
     parameterize, not rewrite; a shader lets you supply the actual math the
     card runs, once per vertex or once per fragment.  The two kinds this book
     uses are the :term:`Vertex Shader`, which moves each vertex from
     :term:`modelspace <Modelspace>` toward the screen, and the
     :term:`Fragment Shader`, which decides the color of each pixel.  From
     :term:`OpenGL Core Profile` onward, writing them is no longer optional.

     Further reading:
     `Shaders (LearnOpenGL) <https://learnopengl.com/Getting-started/Shaders>`_
     is a beginner-friendly, code-first introduction to GLSL and how the vertex
     and fragment stages pass data to each other.

   Vertex Shader
     A :term:`Shader` that runs once per vertex.  Its job is to take a vertex
     given in :term:`modelspace <Modelspace>` and output its position in
     :term:`Clip Space` (x, y, z, w), the coordinates OpenGL divides through by
     w to get :term:`Normalized Device Coordinates`.  This is the programmable
     replacement for the transformations the :term:`Fixed-Function Pipeline`
     used to apply silently inside ``glVertex`` -- the same model-view and
     projection math, now written out as code you control.  Whatever it outputs
     is handed on to the :term:`Fragment Shader`.

     Further reading:
     `Hello Triangle (LearnOpenGL) <https://learnopengl.com/Getting-started/Hello-Triangle>`_
     introduces the vertex shader in the context of the whole graphics
     pipeline, with a diagram of where it sits.

   Fragment Shader
     A :term:`Shader` that runs once per *fragment* -- roughly, once per pixel
     that a piece of geometry covers -- and whose job is to compute that
     fragment's color.  It receives values handed down from the
     :term:`Vertex Shader` (interpolated across the triangle) and writes out the
     color that ends up in the :term:`Frame Buffer`.  In fixed-function OpenGL
     the card chose fragment colors from a few built-in lighting models; a
     fragment shader lets you write that color math yourself.  The name comes
     from letting the programmer change the "shade" of a fragment.

     Further reading:
     `Shaders (LearnOpenGL) <https://learnopengl.com/Getting-started/Shaders>`_
     explains, in plain terms, that the fragment shader is "all about
     calculating the color output of your pixels," and how interpolated inputs
     reach it.

   GPU
     The Graphics Processing Unit -- the processor on your graphics card,
     separate from the CPU that runs the rest of your Python program.  It is
     built to run the same small program over enormous numbers of vertices and
     fragments at once, in parallel, which is why a :term:`Shader` is uploaded
     to and executed on the GPU rather than the CPU.  In this book, everything
     from :term:`modelspace <Modelspace>` data through to the pixels in the
     :term:`Frame Buffer` is ultimately produced by the GPU.

     Further reading:
     `Hello Triangle (LearnOpenGL) <https://learnopengl.com/Getting-started/Hello-Triangle>`_
     walks through the sequence of stages the GPU runs to turn 3D coordinates
     into colored pixels, with a diagram of the pipeline.

   Fixed-Function Pipeline
     The older style of OpenGL (used in this book through demo 19) in which the
     graphics card runs a fixed, built-in sequence of steps that you can only
     switch on or off and feed values to -- you cannot change the math itself.
     The book compares it to a graphing calculator you are not allowed to
     program: you set the projection, the current color, a lighting model, and
     so on, and ``glVertex`` quietly pulls those settings from the
     :term:`Matrix Stack` (and elsewhere) to draw.  Programmers wanting to write
     their own lighting and transformation math is exactly why
     :term:`Shader`\ s were added, and in :term:`OpenGL Core Profile` they
     replace this pipeline entirely.

     Further reading:
     `OpenGL (LearnOpenGL) <https://learnopengl.com/Getting-started/OpenGL>`_
     contrasts this older "immediate mode" with modern core-profile OpenGL and
     explains why it was considered easy to use but inefficient.

   Matrix Stack
     The OpenGL 2.1 replacement for this book's function (lambda) stack.  Where
     the :term:`Function Stack` held a list of invertible functions to compose,
     a matrix stack holds 4x4 matrices, and a single
     matrix at the top can carry an entire sequence of transformations from one
     space to another in one multiplication.  You still need the stack itself so
     you can save the current coordinate system with ``glPushMatrix`` and return
     to it later with ``glPopMatrix`` -- for example, holding onto
     :term:`World Space` while you descend into paddle 1's space, then popping
     back to draw paddle 2.  OpenGL keeps two of them: one for the
     :term:`Model-View Matrix` and one for the :term:`Projection Matrix`.

     Further reading:
     `OpenGL Transformation (songho) <https://www.songho.ca/opengl/gl_transform.html>`_
     explains ``glPushMatrix``/``glPopMatrix`` and the model-view and projection
     stacks with diagrams and short code examples.

   Model-View Matrix
     In OpenGL 2.1, the matrix that transforms vertices from
     :term:`modelspace <Modelspace>` into :term:`Camera Space`.  It combines the
     *model* transformations (placing an object into :term:`World Space`) and the
     *view* transformation (expressing the world from the camera's point of
     view) into one matrix.  It lives on its own :term:`Matrix Stack`, because
     while drawing a tree of objects you repeatedly push a copy, transform down
     into a child's space, and pop back.  It is the matrix you spend most of your
     effort on; in the :term:`Cayley Graph` there is only one edge left from
     camera space to NDC, which is the :term:`Projection Matrix`'s job.

     Further reading:
     `OpenGL Transformation (songho) <https://www.songho.ca/opengl/gl_transform.html>`_
     covers the combined ``GL_MODELVIEW`` matrix directly; the view half is
     introduced more gently as "view space" in
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_.

   Projection Matrix
     The matrix that transforms vertices from :term:`Camera Space` into
     :term:`Clip Space` (which OpenGL then divides through to get
     :term:`Normalized Device Coordinates`) -- the perspective (or orthographic)
     step that makes farther things look smaller and defines the viewing
     frustum.  It is one of OpenGL 2.1's two matrices, set with
     ``gluPerspective`` and kept on its own :term:`Matrix Stack` (though there is
     usually only one matrix on it).  The full derivation of the standard
     perspective matrix is the subject of the "Standard Perspective Matrix"
     chapter.

     Further reading:
     `Coordinate Systems (LearnOpenGL) <https://learnopengl.com/Getting-started/Coordinate-Systems>`_
     introduces perspective and orthographic projection with intuitive diagrams
     before showing the code.

   OpenGL Core Profile
     The modern, stripped-down version of OpenGL (this book targets 3.3 Core) in
     which the old convenience machinery is gone: there is no
     :term:`Fixed-Function Pipeline`, no ``glBegin``/``glVertex``, and no
     built-in :term:`Matrix Stack`.  Instead, writing a :term:`Vertex Shader` and
     a :term:`Fragment Shader` is mandatory, and you pass your own matrices to
     them as uniforms.  It trades the ease of the older immediate-mode style for
     full control over what the :term:`GPU` does, at the cost of more verbose
     setup.

     Further reading:
     `OpenGL (LearnOpenGL) <https://learnopengl.com/Getting-started/OpenGL>`_
     explains the core-profile vs. immediate-mode split and why modern OpenGL
     requires you to do more of the work yourself.

   Window
     The rectangular region of the :term:`Monitor` that a program draws its
     output into.  Desktop operating systems let many programs run at once, each
     displaying its output in its own window.  This book creates one with
     :term:`GLFW`, which opens the window in a cross-platform way and gives it an
     OpenGL context to draw into; the pixels you draw for a frame land in the
     window's :term:`Frame Buffer` before being shown.

     Further reading:
     `GLFW Window Guide <https://www.glfw.org/docs/latest/window_guide.html>`_
     is the official documentation for creating and managing windows -- thorough
     but reference-style, so skim for the ``glfwCreateWindow`` and event-handling
     parts.

   Monitor
     The physical display attached to the computer: a two-dimensional grid of
     tiny light-emitting elements called pixels, each with a red, green, and blue
     component.  At any instant the computer tells each pixel which color to
     show, and the whole grid of colors forms one :term:`Frame` -- a picture.
     Pixel (0, 0) is the lower-left corner and (width, height) is the upper-right;
     refreshing the frame rapidly (measured in :term:`Hertz`) creates the
     illusion of motion.  Compare :term:`Screen Space`, the (x, y) index of a
     pixel on the monitor.

     Further reading:
     `GLFW Monitor Guide <https://www.glfw.org/docs/latest/monitor_guide.html>`_
     shows how a program queries connected monitors, their resolutions, and
     video modes.

   GLFW
     A small, widely supported library that this book uses to open a
     :term:`Window` and obtain an OpenGL context on Windows, macOS, and Linux
     without platform-specific code.  Besides window management it also reports
     input -- keyboard, mouse, and game-controller events -- which the
     :term:`Event Loop` polls each frame with ``glfw.poll_events``.  In the demos
     it is imported as ``glfw``.

     Further reading:
     `GLFW documentation <https://www.glfw.org/docs/latest/window_guide.html>`_
     (the project home is `glfw.org <https://www.glfw.org>`_) covers opening a
     window, creating a context, and polling input.

   Pixel
     The smallest addressable element of the monitor: one tiny
     light-emitting dot in the two-dimensional grid that makes up the
     screen.  Each pixel displays a single color, usually stored as three
     numbers -- a red, a green, and a blue component.  A complete grid of
     pixel colors at one instant is a :term:`Frame`, and inside the
     :term:`Frame Buffer` each pixel is really a :term:`Fragment`, carrying
     not just a color but depth and other per-pixel data.

     Further reading:
     `Pixel (Wikipedia) <https://en.wikipedia.org/wiki/Pixel>`_ explains
     the grid-of-colored-dots idea and the RGB components in plain terms,
     with photographs of real pixels and subpixels.

   Fragment
     All of the per-pixel data OpenGL needs in order to decide the final
     color of one :term:`Pixel` -- not only a color, but also a depth (its
     z value), a stencil flag, and an alpha.  As the book puts it, "each
     pixel in the framebuffer is a fragment," which is more information than
     just the color to be drawn.  Fragments are produced during
     :term:`Rasterization`, when OpenGL works out which pixels a piece of
     geometry covers, and per-fragment checks such as the
     :term:`Depth Test`, :term:`Scissor Test`, and stencil test then decide
     whether a fragment is allowed to update the :term:`Frame Buffer`.

     Further reading:
     `Hello Triangle (LearnOpenGL) <https://learnopengl.com/Getting-started/Hello-Triangle>`_
     defines a fragment simply as "all the data required for OpenGL to
     render a single pixel," in the middle of a beginner walk-through of the
     graphics pipeline.

   Depth Buffer
   Z-buffering
     A value stored per :term:`Fragment`, alongside color in the
     :term:`Frame Buffer`, recording how far each drawn point is from the
     camera (its z value in :term:`Normalized Device Coordinates`).  When a
     new object is drawn over a pixel, its depth is compared against the
     depth already stored there, so nearer geometry can hide farther
     geometry no matter what order the objects happen to be drawn in.  This
     technique of keeping and comparing per-pixel depth is called
     z-buffering; before it existed, programs had to sort and reorder their
     draw calls by hand.  The comparison itself is the :term:`Depth Test`.

     Further reading:
     `Depth testing (LearnOpenGL) <https://learnopengl.com/Advanced-OpenGL/Depth-testing>`_
     explains the depth buffer with diagrams and code; its opening sections
     are approachable, though the later part on non-linear depth precision
     is more mathematical and can be skipped on a first read.

   Depth Test
     The check OpenGL performs for each :term:`Fragment` to decide whether
     it should overwrite the color already in the :term:`Frame Buffer`, by
     comparing the fragment's depth against the value stored in the
     :term:`Depth Buffer`.  You turn it on with ``glEnable(GL_DEPTH_TEST)``
     and choose the comparison with the depth function: this book uses
     ``GL_GREATER`` while working directly in
     :term:`Normalized Device Coordinates` (larger z means nearer), then
     switches to ``GL_LEQUAL`` in demo19, once OpenGL's projection flips the
     z axis into a left-handed system (far z becomes 1.0, near z becomes
     -1).  When the test fails, the fragment is discarded and the pixel
     keeps its old color.

     Further reading:
     `Depth testing (LearnOpenGL) <https://learnopengl.com/Advanced-OpenGL/Depth-testing>`_
     is the same beginner-friendly page as for :term:`Depth Buffer`; its
     first half covers enabling the test and picking a depth function.

   Stencil Buffer
     An extra value kept per :term:`Fragment` in the :term:`Frame Buffer`
     that acts as a mask: it marks each pixel to say whether later OpenGL
     calls are allowed to affect that pixel or must leave it alone.  The
     book first meets this masking idea early on through the
     :term:`Scissor Test`, which flags a rectangular region true or false; a
     full stencil buffer generalizes that to arbitrary shapes you draw
     yourself.  It works much like the :term:`Depth Buffer` -- a value held
     per pixel and tested before drawing -- but stores a mask rather than a
     distance.

     Further reading:
     `Stencil testing (LearnOpenGL) <https://learnopengl.com/Advanced-OpenGL/Stencil-testing>`_
     introduces the stencil buffer with diagrams and a worked object-outline
     example; it assumes you have already seen the :term:`Depth Test`, so
     read that page first.

   Viewport
     The rectangular region of the window into which OpenGL actually draws.
     Setting it (with ``glViewport``) tells OpenGL how to map
     :term:`Normalized Device Coordinates` onto :term:`Screen Space`: give
     it the whole framebuffer and geometry fills the window; give it a
     smaller rectangle and the same NDC range is squeezed into that
     sub-region.  The book uses this in ``draw_in_square_viewport`` to keep
     the paddles square no matter how the window is resized.  Note that it
     changes the coordinate mapping, unlike the :term:`Scissor Test`, which
     only restricts which pixels may be written.

     Further reading:
     `Hello Window (LearnOpenGL) <https://learnopengl.com/Getting-started/Hello-Window>`_
     introduces ``glViewport`` for beginners, showing how an NDC point maps
     to a screen-coordinate pixel and why you reset it when the window
     resizes.

   Rasterization
     The step where OpenGL turns a piece of geometry, once its vertices are
     in :term:`Screen Space`, into the set of pixels it actually covers --
     producing one :term:`Fragment` per covered :term:`Pixel`.  As the book
     notes when describing ``glEnd``, "the graphics driver will need to
     determine what pixels are within the quadrilateral or not," and it also
     interpolates values such as color across the interior.  Those fragments
     are then handed to the fragment shader and to the per-fragment tests
     (:term:`Depth Test`, :term:`Scissor Test`).

     Further reading:
     `Rasterization: overview of the algorithm (Scratchapixel) <https://www.scratchapixel.com/lessons/3d-basic-rendering/rasterization-practical-implementation/overview-rasterization-algorithm.html>`_
     walks through how covered pixels are found, with figures and pseudocode
     and no heavy-math prerequisite.

   Double Buffering
   Swap Buffers
     OpenGL keeps two framebuffers: a front buffer being shown on the
     monitor and a back buffer that the current :term:`Frame` is drawn into.
     A frame is built up incrementally in the back buffer, and only when it
     is complete is it sent to the monitor -- calling ``glfwSwapBuffers``
     flushes the finished buffer and swaps the two, so the monitor never
     shows a half-drawn frame.  Drawing off-screen and then swapping is
     called double buffering; without it the viewer would see tearing and
     partially drawn geometry.

     Further reading:
     `Buffer swapping (GLFW window guide) <https://www.glfw.org/docs/latest/window_guide.html#buffer_swap>`_
     describes the front/back buffers and ``glfwSwapBuffers`` for the exact
     library this book uses, and covers vsync via ``glfwSwapInterval``.

   Frame
   Frame Rate
   Hertz
     A frame is the two-dimensional grid of :term:`Pixel` colors that makes
     up one complete picture at a single instant -- the contents of the
     :term:`Frame Buffer` once everything has been drawn and sent to the
     monitor.  The computer generates frames one after another and, by
     refreshing them quickly, creates the illusion of motion; the rate at
     which it does so is the frame rate, measured in Hertz (Hz), i.e. frames
     per second.  The demos cap this at 60 Hz so that motion looks the same
     across monitors with different refresh rates.

     Further reading:
     `Frame rate (Wikipedia) <https://en.wikipedia.org/wiki/Frame_rate>`_
     explains frames per second and the Hz measurement for a general
     audience, with the persistence-of-vision background behind smooth
     motion.

   Scissor Test
     A per-:term:`Fragment` test that restricts drawing to a rectangular
     region of the :term:`Frame Buffer`: you enable it with
     ``glEnable(GL_SCISSOR_TEST)`` and set the rectangle with ``glScissor``,
     and OpenGL then ignores any pixel outside that box.  The book uses it in
     ``draw_in_square_viewport`` to clear a black square in the middle of an
     otherwise gray window.  Unlike the :term:`Viewport`, the scissor test
     does not change how :term:`Normalized Device Coordinates` map to
     :term:`Screen Space` -- it only decides which pixels may be touched --
     which is why the book sets both.

     Further reading:
     `glScissor (docs.gl) <https://docs.gl/gl3/glScissor>`_ is concise,
     accurate reference documentation ("only pixels that lie within the
     scissor box can be modified"); it is reference-style rather than a
     tutorial, so pair it with this chapter's own walk-through for the
     intuition.
