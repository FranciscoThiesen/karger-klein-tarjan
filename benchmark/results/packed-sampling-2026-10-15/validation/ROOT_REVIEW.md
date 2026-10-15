# Root release review

Reviewed the production diff, packed helper, actual private/public integration test, exact-record comparison and collector source. The scalar reference includes the same callback refactor; only the private packed macro differs. Existing public RNG consumption remains covered, and the packed helper uses bounded unsigned shifts and per-call partial-word discard. Native and sanitizer gates, wrong-policy/wrong-link rejection, final-object harness checks, exact shared-object proof and independent collector review passed. No speedup is inferred from those gates.

The fixed comparison has six cases, two graph seeds, two sampling seeds, adjacent variants and six balanced solver positions. Pooled medians use 24 pairs; the four realization medians share two graphs and are not four independent graph draws. Parent helper-path rebinding is scoped and restores on exceptions, with the original native provenance still fully verified. The independent audit checked explicit native-source/object/recipe/binary/receipt drift rejection.

Root preflight passed against the final source/build artifacts without launching a solver. Performance release is separate and begins only after this protocol and freeze are committed and all other native work is stopped.
