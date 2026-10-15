# Source preparation receipt — execution deferred

Prepared during the separate eighth performance hold on 2026-10-15. Only
source/declaration reads and new `/tmp` source writes were performed. No
Python import, syntax check, test, preflight, build, render, native solver call
or partial timing-data read was performed for this package. No frozen file,
helper or binary changed; no worktree was installed or created.

The adaptive-sampling theory review is a separate future proposal, saved at
`/tmp/kkt-adaptive-sampling-review.md`. This extension fixes the existing eighth
policy and does not implement that adaptive selector.

Source inventory at review handoff:

| Relative path | SHA-256 |
|---|---|
| `overlay/benchmark/run_eighth_extension.py` | `8b1332ce7bff2f0cca09188c98c74d1adb0e486e107acb0a1cd99691afdde3d4` |
| `overlay/benchmark/test_eighth_extension.py` | `07d2f5eb40b54bff4c8c19de7718ea71c75b75f5309599524711f94ea6299d8d` |
| `overlay/benchmark/results/eighth-extension-2026-10-15/PROTOCOL.md` | `7e7a5ef1d4d6e52a631c10d834b27c90518d4121aae216803cb9c7cc4ff06ebe` |
| `overlay/benchmark/results/eighth-extension-2026-10-15/manifest.csv` | `b950d44ffd0c01e47b26a6e54064aad3349ecd0c3a6b956c21be6e7f8351084a` |

Adaptation source: completed `benchmark/run_larger_hierarchy.py` and its
eleven-group test suite, with the parent switched to full eighth freeze
validation, candidate variant fixed to `eighth`, new local seeds and seven
literal sizes. Read-only diff inspection found the capture/monitor/cleanup
control flow unchanged. Extended crossover fixtures cover early lead then
reversal, late sustained recovery, a largest-only lead, all-leading/all-losing,
strict smaller-endpoint ties, inclusive 9/10 and exact rational epsilon above
it, one unfavorable clock/graph, and missing/duplicate trial identities.

During independent source review, a documentation error initially described
the acceptance predicate as zero low bits. It was corrected to the actual
frozen predicate `(rng() & 7) == 7` after reading the native header; no collector
or binary behavior changed. Eleven groups remain prepared, not passed.

Independent source review is recorded separately when complete. Runtime mocks,
freeze, independent numerical audit, plotting and visual QA are future gates,
not implied by this receipt. The preparing agent owns no running processes.
