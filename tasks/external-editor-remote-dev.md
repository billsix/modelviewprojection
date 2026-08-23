# Drive the dev container from an external editor (VS Code / Zed) via `make lsp-start`

**Status:** **blocked (2026-08-23) — do not start.** Deferred by William Emerison Six
<billsix@gmail.com> until the ecosystem standardizes. Research is done and captured below;
four design decisions are open and must be answered before any code.
**Priority:** 8
**Difficulty:** 6
**Blocked on:** Zed's dev-container / remote support reaching VS Code parity — the "still in
development" caveats on Zed's dev-containers docs being gone (auto-rebuild on
`devcontainer.json` change, a stable podman path), OR a common cross-editor "attach an
external editor to a running container" standard emerging.
**Recheck:** `WebFetch https://zed.dev/docs/dev-containers` and check whether the "still in
development" / "must be manually restarted" / "do not trigger automatic rebuilds" caveats
are **gone**. *Cleared* = the page no longer flags the feature as in-development (stable
auto-rebuild + podman path). Also glance at `https://zed.dev/docs/remote-development` for any
container-native (non-SSH) attach story.

**Type:** dev-environment / container tooling. No book or `src/` changes.

## Goal

Add a `make lsp-start` target so a person can run **one** container of this project and
edit it from an **external** IDE / editor running on their own machine — VS Code, Zed,
JetBrains Gateway, neovim — instead of the in-container embedded Emacs. Concretely:
- Editing this project from **Zed**, whose GUI needs graphics that are painful to run
  inside the container.
- Editing from **VS Code on Windows, with the project in WSL**.

The win: the editor **GUI runs on the user's host**, and only a headless backend +
language servers run in the container — so **no OpenGL/graphics is needed in the
container** for editing, which is exactly the Zed pain point.

## Research findings (2026-08-23)

Both VS Code and Zed drive a container by running **their own backend AND the language
servers inside the container**, with only the editor UI on the local machine. Three
architectures:

### A. SSH remote (universal) — the recommended shape for `make lsp-start`
Run `sshd` in the container, publish a port; VS Code Remote-SSH, Zed remote, JetBrains
Gateway, and neovim all attach over SSH. Works identically on macOS, Linux, and
Windows+WSL (SSH to the published port).
- **Zed:** requires key-based SSH; downloads a `~/.zed_server` binary matching the local
  Zed version. Air-gapped option: `"upload_binary_over_ssh": true` pushes the binary from
  the user's machine instead. Linux host must be x86_64/arm64 (32-bit unsupported), which
  the Fedora image satisfies. Requires Zed ≥ v0.159.
- **VS Code:** installs `~/.vscode-server` into the container home over SSH on first
  connect.
- Fits the "one container that `make` launches and an external client attaches to" model
  best, and is the same for every editor.

### B. Native dev containers (`.devcontainer/devcontainer.json`)
VS Code's Dev Containers extension `podman exec`s straight in — no SSH. **Zed now supports
this too** (`"use_podman": true` in Zed settings), but the docs flag it **still in
development** (config changes don't auto-rebuild; containers must be restarted manually).
Downside: the *editor* owns the container lifecycle from `devcontainer.json`, which
competes with this repo's elaborate Makefile flag/mount machinery.
**This is the maturity gap the task is waiting on** (see "Trigger to revisit").

### C. Bare LSP-over-TCP — REJECTED
Expose only a language server on a socket (`socat` / `lsp-ws-proxy` bridging stdio↔TCP).
Fragile, editor-specific, and the editor still needs the files locally so path mapping
breaks. This is **not** how VS Code/Zed attach. Do not pursue.

**Sources:**
- Zed remote development: <https://zed.dev/docs/remote-development>
- Zed dev containers (podman): <https://zed.dev/docs/dev-containers>
- VS Code dev containers: <https://code.visualstudio.com/docs/devcontainers/containers>
- VS Code develop on a remote Docker host:
  <https://code.visualstudio.com/remote/advancedcontainers/develop-remote-host>

## Current state of this repo (what the task builds on)

- In-container language servers already installed for the embedded Emacs `lsp-mode`:
  **`python3-lsp-server` (pylsp)**, **`ty server`** (registered as a custom lsp-mode
  client in `entrypoint/dotfiles/.emacs.d/init.el`), and **`ruff`** (lint/format).
- **No `openssh-server`** in the image — architecture A needs it added as a flag-gated
  install group (`entrypoint/07-install-ssh.sh`, dispatched by a Dockerfile ARG per the
  "Host-agnostic setup belongs in a script" convention; ARG defaults 0, Makefile flag
  defaults 1).
- Container is ephemeral `--rm`, launched by Makefile `podman run` targets. This is the
  main design tension (editor-server binaries re-download each session — see Q2).

## Proposed implementation (once un-parked, pending the four answers)

Architecture A as the primary:
1. New flag-gated install group `entrypoint/07-install-ssh.sh` (openssh-server, and
   whichever extra LSP server Q3 selects), dispatched from the Dockerfile ARG block.
2. `entrypoint/lsp-start.sh` (or `sshd.sh`): host-key gen if absent, install the user's
   authorized_keys (Q4), `exec /usr/sbin/sshd -D -e` in the foreground.
3. Makefile `lsp-start:` target — `.PHONY`, `## `-documented — `podman run` the image with
   `-p $(LSP_SSH_PORT):22` (default `LSP_SSH_PORT := 2222`), the repo mounted at
   `/modelviewprojection/:Z` as usual, the authorized_keys mount, and (Q2) the persistent
   editor-server mount. Print the exact `ssh -p 2222 …@localhost` connect line and Zed/VS
   Code hints at start.
4. Optionally (Q1) also add `.devcontainer/devcontainer.json` pointing at the same image
   for the VS Code Dev Containers / Zed native path.
5. README: a commands-forward "Editing from an external editor" section; design rationale
   into a `tasks/reference/` doc, linked (per the README convention).

Verify per conventions: nested `make image` across flag permutations (SSH group present
iff flag on); actually attach VS Code Remote-SSH and Zed remote to a running
`make lsp-start` container and confirm pylsp/ty/ruff drive completions, hover, diagnostics.

## Open questions (must be answered before any code)

1. **Transport.** SSH-only `make lsp-start` (recommended — universal, fits one-container
   model, works from WSL), SSH **plus** a `.devcontainer/devcontainer.json`, or
   devcontainer-only? Recommendation: **SSH-only** now; add `devcontainer.json` when
   architecture B matures.
2. **Ephemeral `--rm` handling of `~/.vscode-server` / `~/.zed_server`.** Persistent
   host-mounted dir (recommended — download once, no image bloat, no offline-build
   violation), bake into image (offline but version-brittle), or accept re-download each
   session?
3. **Extra LSP server.** Add `basedpyright` (recommended — strong completions/hover for
   both VS Code and Zed, alongside pylsp+ty+ruff), add Microsoft `pyright` (npm-based), or
   keep pylsp+ty+ruff only (leaner, weaker completions)?
4. **SSH auth.** Mount host `~/.ssh/authorized_keys` read-only (recommended — key-based,
   required by Zed, nothing in the repo), generate a gitignored project keypair, or
   password auth (not recommended; Zed can't save password prompts)?

Also settled without needing an answer: SSH port is a Makefile var (`LSP_SSH_PORT := 2222`);
primarily intended for the user's real host, and works nested in the sandbox too (bridged
netavark + a published port).

## Trigger to revisit

See the `**Blocked on:**` / `**Recheck:**` fields in the header — run `/recheck-blocked` to
test the gate. In short: un-block when Zed's dev-container / remote support standardizes to
VS Code parity, or a common cross-editor "attach to a running container" standard emerges.
Until then the maintainer is deliberately not investing — the approaches are too
editor-specific and in-flux (William Emerison Six <billsix@gmail.com>, 2026-08-23).
