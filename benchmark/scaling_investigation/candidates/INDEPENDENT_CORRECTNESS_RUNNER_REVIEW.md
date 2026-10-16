# Independent correctness-runner source review

PASS, source review only. No imports, mocked tests, compiles or native tests were
performed by this reviewer. Actual execution remains a root-owned gate.

Reviewed sources:

- `run_correctness.py`: `f42304ab6b76a03ee613b419b21d82f9165ce173e12780c30d74776aeebc84b7`
- `CORRECTNESS_RUNNER.md`: `20351bd419dad0942bb0290731e1584c974f42fcab3d2b873412973392bb0d44`

The dual verifier link applies all four required exported-symbol renames to the
candidate verifier only; the focused main has the depth macro without renames.
The original generic LCA remains available for the independent depth oracle.
Native full-solver tests reuse the eight checked depth-work objects; sanitizer
objects are freshly and consistently compiled. Positive outputs must agree
across profiles. The suite gate now requires all 1,344 ordered fixture/order/
seed identities, exact integer types, valid IDs and all 65 counters, alongside
the fixed positional and retention-suite completion counts.

Expected failures are distinguished from arbitrary crashes: four specific
SIGABRT assertions and the wrong-dispatch exit 1/exact diagnostic each require
the bounded receipt's matching exit cause, deadline, RSS and affirmative empty
group proof. Interruption, poison, missing receipt and unknown cleanup cannot
qualify. Source/artifact inventories bracket every command and final success;
the unsuccessful-attempt sidecar is retained. Leak detection is explicitly off,
so this gate must be reported as ASan+UBSan, not LeakSanitizer. The noinline
attribute control is outside this focused correctness gate as documented.
