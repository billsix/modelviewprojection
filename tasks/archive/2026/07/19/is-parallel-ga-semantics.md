# `is_parallel` disagrees with the geometric-algebra sense of parallel

**Status:** **DONE 2026-07-19 — option A, renamed `is_parallel` →
`is_parallel_and_same_orientation`** (Bill's choice). The name is now precise: it IS
parallel (wedge-related) AND same orientation. Behavior unchanged.

**Deliberately NOT fixed:** the latent degenerate-triangle gap (an anti-parallel, i.e.
folded, edge pair is zero-area but not culled) is left as-is — the honest new name and a
comment at the call site now make that limitation visible instead of hiding it behind a
misleading name. If the folded-triangle case ever needs culling, switch the guard to a
wedge test (option B in the history below); not doing so now was Bill's call.