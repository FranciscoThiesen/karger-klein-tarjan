# Why does current KKT fit N log N? Diagnostic declaration

Base: `a8f506b`, isolated branch `codex/kkt-linear-scaling`. This is a new investigation. Earlier Google labels and timings remain unchanged.

The question is whether measured superlinear growth comes from increasing logical work per represented input, increasing cost per operation, or finite-model limitations. A linear label is not the success criterion; a supported explanation and a validated improvement are.

Before looking at new native output, the first diagnostics use the exact current Google families and seeds: hierarchy and shuffled twins at m=32n, connected random at m=16n; graph seeds 19000013/19000043, sampler seeds 3001/3011. Selected sizes are 1024,4096,16384,65536,262144,1048576. These are a subset of the old ladder, with no changed generator. Graph 1 ascends and graph 2 descends; this confounding remains explicit rather than being interpreted as independent order control.

Three separate instrumentations are compared with an uninstrumented reference: exclusive phase clocks; phase clocks plus global new/delete allocation accounting; logical counters. Phase boundaries contain no per-edge clock calls. The allocation build counts requested/usable bytes and simultaneous live usable bytes during the solver interval; this is not RSS or all libc allocation. Work timing is not used as a performance estimate. Sample/filter identities and deterministic vertex-volume bounds are checked alongside exact MST certificates.

Phase capture: all72 selected graph/seed/size/family inputs, one checked warmup and three recorded calls. Work capture: the same72 inputs, one warmup and one recorded call (replayed counters must match). Allocation capture:18 inputs (16K,256K,1M; both graphs; sampler3001), one warmup and one recorded call. Calibration: six inputs (1K/1M, three families, graph19000013/sampler3001), paired reference/phase executables with alternating launch order, one warmup and three calls. It diagnoses instrumentation overhead; it is not a six-solver speedup campaign. All loops, clocks, outputs, ranges, failures and fixture fingerprints remain.

The new driver's tuple-input boundary includes conversion, solver, and temporary-input destruction, and excludes generation, independent certification, result checking/destruction. Every result is checked against the exact unique-MST edge-ID set from a separately certified Kruskal reference. Each child is a fresh process with a 512MiB stack. Process CPU and wall time are recorded; phase attribution uses exclusive monotonic wall intervals. Sequential controller:300s per child,12GiB sampled process-group RSS ceiling,7200s campaign limit, owned process-group teardown and actual exits. Compilation has separate bounded records. No other native benchmark runs concurrently.

Primary hypotheses, before this capture:

1. Logical work/N is stable but indirect per-edge operations become more costly at large working sets.
2. Parent graphs, samples and verifier buffers survive past their last use, raising simultaneous memory use and allocation/free costs.
3. Verifier disconnected-forest partitioning introduces data-dependent extra work; it must be distinguished from per-visit latency.
4. LCA preprocessing/query representation has finite-size and locality costs despite its linear operation bound.
5. Google's one-parameter zero-intercept model menu can select NlogN without identifying the physical cause; alternate models require explicit held-out predictions and must not replace the exported Google answer.

Source audit and primary-literature research proceed separately. Any proposed production change will first preserve exact MSTs and applicable trajectory/counter identities, then receive its own paired uninstrumented comparison including losses. Diagnostics, model selection, and implementation wins are distinct outcomes.
