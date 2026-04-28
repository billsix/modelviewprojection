# Notes — /superbible C++ structural map (Task 1)

> Self-notes from studying the OpenGL SuperBible 4e source tree at `/superbible/`. Future-Claude: this is what you found last time; verify rather than trust if the tree may have changed.

## Top-level layout

```
/superbible/
├── readme.txt          # Richard S. Wright Jr., last update 2007-07-22
├── contrib/
│   └── imgui/          # bundled imgui (added later, not part of original 4e shipped code)
└── examples/
    ├── src/            # all the actual source — by chapter
    └── projects/       # platform-specific build files
```

Authored by Richard S. Wright Jr. 4e shipped 2007. **This is the codebase Bill ports from**, in his style, into MVP — it's not a library to depend on, it's a quarry.

## examples/src/ layout

```
examples/src/
├── chapt01/ … chapt22/ # one folder per book chapter
│   └── <demoName>/     # one folder per demo
│       └── <demoName>.cpp   # usually a single .cpp file, 200–400 lines
│       └── shaders/    # only present from chapt17+ (shader era)
└── shared/             # library code reused across demos
```

Per-demo files: typically **one** `.cpp` file. Shaders, when present (chapt17+), live in a `shaders/` subdir as paired `.vs`/`.fs` files. No headers per demo. Earlier chapters (1–16) are pure fixed-function — no shaders at all.

**Chapter→concept mapping** (high-level, from skim):
- chapt01: `block/Block.cpp` — first 3D demo (corresponds to mvp's demo22)
- chapt05: `litjet/`, `shadow/`, `sphereworld/`, `ambient/`, `ccube/`, `jet/`, `shinyjet/`, `spot/`, `triangle/` — fixed-function lighting & first sphereworld
- chapt09: `cubemap/`, `multitexture/`, `pointsprites/`, `sphereworld/` (re-skinned), `texgen/`, `anisotropic/` — texturing
- chapt17: `lighting/`, `bumpmap/`, `fragmentshaders/`, `imageproc/`, `proctex/` — **first shader chapter**, demos now have a `shaders/` subdir
- chapt18: `fbodrawbuffers/`, `fboenvmap/`, `fboshadowmap/`, `hdrbloom/`, `pixbufobj/`, `texfloat/` — FBO / advanced
- chapt19: `SphereWorld32/`, etc. — modern (3.x) SphereWorld port, plus widget/text demos
- chapt20: macOS-specific (Carbon, Cocoa) — likely irrelevant for porting

## examples/src/shared/ — the framework

This is where the reusable library lives. Five logical pieces:

| File | Lines | Purpose |
|------|------:|---------|
| `math3d.h` / `.cpp` | 785 / 1143 | The math library (vectors, matrices, geometry helpers). All names prefixed `m3d`. |
| `gltools.h` / `.cpp` | 161 / 563 | OpenGL utility: TGA loader (`gltLoadTGA`/`gltWriteTGA`), shape draws (`gltDrawTorus`/`gltDrawSphere`/`gltDrawUnitAxes`), shader loader (`bLoadShaderFile`, `gltLoadShaderPair`), version/extension detection. **Also pulls in `gl.h`/`glu.h`/`glut.h` per-platform** — this is the demo's "include this and you're set" header. |
| `glframe.h` | 432 | `GLFrame` class — orthonormal frame (origin + forward + up). Wraps "place an actor in space" or "use as camera" with `ApplyActorTransform()` / `ApplyCameraTransform()`. **Used as both the camera and as per-object frame in sphereworld and many later demos.** |
| `glfrustum.h` | 232 | `GLFrustum` — view frustum / projection helper. |
| `GLee.c` / `GLee.h` | — | OpenGL Extension Easy — extension autoloader (the era's pre-GLEW solution). |
| `TriangleMesh.{h,cpp}`, `VBOMesh.{h,cpp}` | — | mesh loaders (later chapters). |
| `stopwatch.h`, `wglext.h`, `openexr-*` | — | timing, Windows GL ext, OpenEXR for HDR demo. |

**Key insight:** `gltools.h` is the equivalent of mvp's "boilerplate at the top of every demo." `GLFrame` is roughly mvp's `Camera` dataclass *plus* an orthonormal basis — but applied to objects too, not just the camera. `GLFrustum` corresponds to mvp's `mathutils.perspective`.

## examples/projects/ — build system

Per-platform, per-demo Makefiles/projects. **Linux uses plain Makefiles**, one per demo:

```
projects/linux/chapt05/litjet/Makefile
```

Sample Makefile (from `litjet`):
```make
MAIN = litjet
INCDIRS = -I/usr/include -I/usr/local/include/GL -I../../../../src/shared -I/usr/include/GL
SRCPATH = ../../../../src/chapt05/$(MAIN)/
SHAREDPATH = ../../../../src/shared/
LIBS = -lglut -lGL -lGLU -lm

$(MAIN) : $(MAIN).o gltools.o math3d.o
    $(CC) $(CFLAGS) -o $(MAIN) ... $(SRCPATH)$(MAIN).cpp $(SHAREDPATH)math3d.cpp $(SHAREDPATH)gltools.cpp $(SHAREDPATH)GLee.c $(LIBS)
```

So **every demo links the same three shared `.cpp` files**: `math3d.cpp`, `gltools.cpp`, `GLee.c`, plus its own `.cpp`. Direct `glut`/`GL`/`GLU`/`m` system libs. No CMake, no autoconf — just Makefiles. Period-typical (2007).

Apple and Microsoft have separate project trees (`projects/apple/`, `projects/microsoft/`) — Xcode and VS projects respectively. We don't need them for porting.

## Per-demo entry-point pattern (fixed-function era, chapt01–16)

Every demo follows the same skeleton:

```cpp
#include "../../shared/gltools.h"   // pulls in glut, gl, glu
#include "../../shared/math3d.h"    // pulls in math3d API

// Globals: rotation, light position, world state
static GLfloat xRot = 0.0f, yRot = 0.0f;

void RenderScene(void) {
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
    glPushMatrix();
    glRotatef(xRot, 1, 0, 0);
    glRotatef(yRot, 0, 1, 0);
    /* ... glBegin / glVertex3fv / glEnd ... */
    glPopMatrix();
    glutSwapBuffers();
}

void SetupRC(void) { /* glEnable(GL_DEPTH_TEST), lights, materials, clear color */ }
void ChangeSize(int w, int h) { /* viewport + gluPerspective + glLightfv */ }
void SpecialKeys(int key, int x, int y) { /* arrow keys → mutate rotations */ }

int main(int argc, char *argv[]) {
    glutInit(&argc, argv);
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH);
    glutInitWindowSize(800, 600);
    glutCreateWindow("Lighted Jet");
    glutReshapeFunc(ChangeSize);
    glutSpecialFunc(SpecialKeys);
    glutDisplayFunc(RenderScene);
    SetupRC();
    glutMainLoop();
    return 0;
}
```

**Toolkit:** GLUT (not GLFW). Callback-driven (`glutDisplayFunc`/`glutReshapeFunc`/`glutSpecialFunc`/`glutTimerFunc`), not a polling loop. **MVP uses GLFW with a polling loop** — that's the first shape difference when porting.

**Camera handling:** chapt05+ demos with a movable camera use a global `GLFrame frameCamera;` and call `frameCamera.ApplyCameraTransform()` at the top of `RenderScene`. Same `GLFrame` type is used to position objects in the scene (e.g. `GLFrame spheres[NUM_SPHERES];`). Mvp doesn't have a unified "frame" abstraction — it uses a separate `Camera` dataclass and per-object position/rotation fields.

## Per-demo entry-point pattern (shader era, chapt17+)

Same `RenderScene`/`SetupRC`/`ChangeSize`/`main` skeleton, **plus** in `SetupRC` it calls `gltLoadShaderPair("shaders/foo.vs", "shaders/foo.fs")` and stashes the resulting `GLhandleARB`. Still uses the fixed-function matrix stack (`glPushMatrix`, `glRotatef`) — they didn't switch to a hand-rolled matrix stack until very late.

## How this maps to porting into MVP

When Bill says "port chapt05/sphereworld" or similar, the target structure on the mvp side is **already documented in `/mvp/CLAUDE.md`**:
- Pre-demo20 / fixed-function: a single `demoNN.py` matching the surrounding numbered demo (uses `glPushMatrix`, `gluPerspective`, etc.)
- Demo20+: a `demoNN/` subfolder with `demoNN.py` + paired `.vert`/`.frag` shaders + asset files; uses `pyMatrixStack`, `compile_program()`, VAO/VBO

The translation rules of thumb (derived from observed differences):
- GLUT callbacks → GLFW polling loop
- `GLFrame` actor → mvp's per-object `position` + `rotation` fields (or, for camera, a `Camera` dataclass)
- `M3DVector3f`/`M3DMatrix44f` C arrays → `Vector3D` / `pyMatrixStack`
- `m3dRotationMatrix44(...)` + `glMultMatrixf` → `pyMatrixStack` translate/rotate calls (modern era) or `rotate_x/y/z` `InvertibleFunction`s (early era)
- `glBegin(GL_TRIANGLES)` + `glVertex3fv` → keep that style for early demos; modernize to VAO/VBO at demo20+
- Shaders: `.vs`/`.fs` → `.vert`/`.frag` (different extensions, same content)
- Build: drop the Makefile, `setup.py` already has the demo entry points

## What was deliberately *not* studied

- Full body of math3d (that's Task 2)
- VBOMesh / TriangleMesh internals (relevant only if porting a model-loading demo)
- Apple/Microsoft project trees (not relevant for Linux/cross-platform port)
- Individual chapter contents beyond a representative sample (Bill picks demos to port; structure is uniform within an era)
- imgui in `contrib/` — it's just bundled, not used by the demos

## Open questions for Bill (if relevant later)

- For shader-era demos (chapt17+): port to mvp's modern style (demo21+) or to fixed-function-with-shaders style (demo20)?
- For demos that use `GLFrame` heavily (sphereworld, anything with multiple frames-of-reference): mvp doesn't have an analogous abstraction. Should we introduce one, or unfold every `GLFrame` into manual position/rotation? (My read: Bill's pedagogy avoids unified frame abstractions — unfold them.)
