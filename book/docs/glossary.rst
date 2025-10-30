
Glossary
========

.. glossary::

   Frame Buffer
     An array of pixel values, where each pixel holds information such as
     color (red, green, blue, alpha), depth (how far a fragment is from
     the camera), and sometimes stencil values (for masking
     operations).

   Normalized Device Coordinates
     Normalized Device Coordinates are the range of values from -1.0 to 1.0
     in the X, Y, and Z directions, the last space before drawing geometry
     in screen space.  Anything vertex outside of the NDC range will not
     be mapped to a pixel.

   World Space
     World space

   Modelspace
     Modelspace

   Screen Space
     Screen space is an index (x,y) that is mapped to a pixel on a monitor.

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
