# Independent depth-query patch review

Source-only PASS, 2026-10-15. Reviewed `depth_queries.patch`, `depth_queries_test.cpp` and `DEPTH_QUERIES_PREPARATION.md`; no patch application, import, build, test or native call performed. Runtime gates remain pending.

The private Euler-depth/middle-depth RMQ preserves the same first visits, masks, relative microtable argmins, partial final-block rules and block shapes. The lower-level consumer stores the same proper-ancestor depth bit and reconstructs the same maximum. Self-loops retain their LCA count, produce no requests and remain unmarked; disconnected remapping and position-based repeated-ID classification remain intact. The exact sole work delta is reference initialization minus candidate initialization equal to reference LCA vertices.

The parent-walk all-pair oracle is independent of RMQ; the forest BFS oracle is independent of FBT/path compression. Tuple and Edge queries are both checked, including signed extremes, empty inputs, loops and repeated IDs. The explicit extreme-weight expected-mark vector is consistent with strict F-heavy comparison. Four new bounded assertion modes supplement the old ID-helper guard tests.

Dual verifier linkage needs the documented fourth `fbt_reduction` rename: it is a global strong symbol, unlike anonymous `test_graph`. The other three externally visible entry points are renamed; shared helper definitions remain identical. The noinline header attribute must match candidate verifier and focused-test translation units to avoid an ODR mismatch. Macro-off helper bodies remain unchanged.

No new per-edge child-array assertions remain in the proposed fast path; leafness is established by construction and tests. Noinline control is required to distinguish the new inlining opportunity from depth storage; a total speed difference cannot be attributed solely to representation. Test execution must include a wrong-linked candidate that fails the initialization discriminator, the native/sanitizer suite and actual final-object proof.
