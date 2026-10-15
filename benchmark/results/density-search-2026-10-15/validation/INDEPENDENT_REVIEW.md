# Independent density-search validation

Reviewer: `multigraph_design`. Final source review and independently executed synthetic collector suite: **PASS**. No release-blocking finding remains.

The source-only review began while paired Edge timing was active. Only file reads occurred before root released nonperformance validation. After release, the independent run executed six mocked test groups in 2.413 seconds, all passing. It launched no native solver, build, performance benchmark or figure renderer. The exact command, runtime, source hashes and log hash are in [the execution receipt](independent-mock-tests-attempt01.json); [the full log](independent-mock-tests-attempt01.log) is retained. The five reviewed files were unchanged across the independent run.

## Reviewed guarantees

- The pinned parent freeze is checked with the complete parent strict checker outside the scoped seed substitutions. Only native command construction and child-row checking substitute seeds; `finally` restores them, including nested exceptions.
- The selected artifact is exactly the frozen direct-Edge binary, with inherited native/build/object/helper proofs. No source rebuild or historical timing substitution is permitted.
- The manifest contains exactly eight declared cases. The second graph seed reverses all cases and matched-family order. Each of 16 children has one six-solver warmup and six balanced timed repetitions: 672 outputs, 576 timed and 96 warmups.
- Both capture and strict reload validate each child certificate, exact sequence and fields, same-input fingerprints, complete hierarchy/shuffled topology twins and nonvacuous differing weighted fingerprints. The same cheap leaf attachments remain in both weight-order controls.
- Normal wrapper exit requires a retained bounded empty-group observation. Resource and clock flags remain included. Strict reload verifies raw paths, hashes, arguments, identities, timestamps, observations, exact combined-file concatenation and all declared counts.
- Analysis retains 960 clock-specific paired ratios, 80 pooled case medians, 160 graph medians and all six absolute-runtime series. Two graph seeds and one sampling realization are not presented as independent replication of all twelve timed trials.
- The protocol distinguishes exploratory two-endpoint crossover brackets from durable/asymptotic dominance and discloses seed/order confounding. It retains all competitors, losses and both clocks.

The initial nonblocking combined-CSV test coverage suggestion was addressed before this independent run: the test corrupts combined duration data, updates its hash and explicitly requires concatenation rejection after restoring the raw child.

## Plot wrapper source review

[The wrapper](../../../plot_density_search.py) reuses the unchanged retention renderer with scoped bindings restored in `finally`. Its mandatory strict loader, exact eight-case/two-endpoint validator and expected summary counts preserve all five KKT comparisons and six runtime series. Every trial-range endpoint participates in shared wall/CPU axis bounds, coverage is checked for all 16 panels, and inputs are hashed again after rendering. No exact crossover is interpolated. Provenance keeps visual review pending until the four resulting PNGs are inspected.

This review did not import or render the plot wrapper. Plot rendering and visual verification remain future gates after the density native capture; this receipt is not evidence of density performance results or completed figures.

## Reviewed file hashes

| File | SHA256 |
|---|---|
| `benchmark/run_density_search.py` | `bbae3bf88f817ddf8e06f032fd3bd211d8bbc8d70f6280db393819fc21d02021` |
| `benchmark/test_density_search.py` | `3fe0a0ee7d62e11f991cdf477f3512bafad18c18bb02ded9bc905834a9aa635d` |
| `benchmark/plot_density_search.py` | `4d8c7ba15084cfd9b5a8ba9a31f26d68273231f1a5769bfbe2f6e390d37d1ee1` |
| `benchmark/results/density-search-2026-10-15/PROTOCOL.md` | `59750e0d5da4b30f8719eaf198fc0c7eacee7411edf56f21ec3160a50935c7fa` |
| `benchmark/results/density-search-2026-10-15/manifest.csv` | `8d3d895414f9f4189961f376a8656d4ac289505427a47bf3a1839ccde489d932` |

All processes started by this independent validation finished with exit status zero. No continuing native process, build, test or plot is owned by this reviewer.
