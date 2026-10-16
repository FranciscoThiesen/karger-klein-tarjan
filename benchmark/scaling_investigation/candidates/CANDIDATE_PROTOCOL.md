# Depth-query experiment declaration

Prepared before candidate execution. This is an isolated KKT before/after study, not a six-solver benchmark or a replacement Google Benchmark fit. No command in this preparation has been executed by its author.

The only production change is the reviewed opt-in ancestor-depth query representation (`depth_queries.patch`). Existing retained-parallel contraction, direct Edge queries, compressed path requests, fixed one-eighth scalar sampling, input generation and public API boundary remain selected. Generic LCA and original helper methods stay available. The candidate's private header also enables inlining; that is an explicit possible contributor, not an attributed representation-only gain.

## Preservation and builds

Before applying the patch, `run_candidate.py snapshot` copies **every** source in the passing baseline build record to a fresh directory. The manifest records original absolute paths, original SHA-256 values and exact copy paths. All original bytes are rechecked before success. Only source paths may later resolve through these copies; raw files, binaries, objects and native receipts stay in their original locations. The live frozen `run.py` and work-field definitions must still match their old hashes. Preserve every prior failed build/capture.

The new builder compiles ten fresh same-source binaries: reference/depth × uninstrumented, work, phase, allocation; plus depth-noinline uninstrumented/phase. Every compiler/link child uses the unchanged `run.py` process monitor, cleaned toolchain environment, Apple arm64 compiler, same SDK and 512 MiB native stack. Full commands, source/object/binary/log hashes and native group exits are retained. Rebuilding all objects is deliberately simple. In each main pair, only `verifier_v2.o` may differ; every other production object and diagnostic main must be byte-identical. The noinline pair may differ only in that verifier object. No production source, generic helper or old runner is edited by this script.

## Correctness and work before performance

The focused dual-verifier test and existing full-solver independent MSF suites must pass natively and under the matching sanitizer toolchain, including an actual wrong-linked-policy rejection. The dual-object candidate verifier requires **four** renames: `heavy_edge_marks`, `verify_mst`, `verify_general_graph` and `fbt_reduction`. The optional noinline definition must be consistent in the candidate verifier and test TU. New depth-bound negative modes must terminate with SIGABRT, not an arbitrary error. No runner receipt substitutes for actual suite execution.

A small externally reviewed `kkt_depth_correctness_gate_v1` receipt must bind the exact new build's `source_sha256`, actual native/sanitizer artifact inventory (`bound_sha256`), literal `native_pass`, `sanitizers_pass`, `owned_groups_empty` true, and validation pass. It is a summary of real archived evidence, never a synthesized success placeholder.

Then:

* `smoke`: fresh reference-work and depth-work on the three 1,024-vertex Google families, G19000013/S3001; one warmup plus one checked call. Six children, 12 outputs. Reference counters equal the completed baseline exactly; candidate counters satisfy the single delta below.
* `work`: candidate-work on all 72 original baseline inputs: three families, six sizes 1,024/4,096/16,384/65,536/262,144/1,048,576, G19000013/19000043 and S3001/3011. One warmup plus one checked call: 72 children, 144 outputs. Compare to **completed** baseline work01 at identical case identities; do not repeat 72 expensive reference certifications. No baseline timing is reused.

Every native call already compares its exact returned unique-MST ID set with an independently certified Kruskal reference outside the measured interval. Fingerprints join the frozen Google fixture identities. All 65 work fields are checked: reference minus depth is exactly `reference.lca_vertices` for `initialized_slots`, and zero for every other field. Warmup and recorded counters repeat exactly. Positive LCA volume is the linked depth-policy witness. These gates establish the supported tested trajectory; no sampling/RNG modification is included.

## Fresh timing and controls

The primary paired timing matrix is fixed at **36 inputs**: the same three families and six sizes, both graph seeds, **sampler 3001 only**. Hierarchy/shuffled use m=32n, connected G(n,m) uses m=16n. G1 ascends and G2 descends; graph/order confounding remains. Each input launches fresh uninstrumented reference and depth processes, reversing policy launch order at alternate inputs. One checked warmup plus three timed calls gives 72 children, 288 outputs, **108 paired timed observations per clock**. Pair by exact input/repetition, preserve both raw wall and CPU clocks, every case, range and loss. Report the one-sampler scope and do not pool these timings with old diagnostics or Google curves. No interpolation or asymptotic conclusion follows from a finite speedup.

`inline-control` fixes six endpoint inputs: all three families at 1,024 and 1,048,576, G19000013/S3001. It compares reference, depth and depth-noinline, rotating the three launch positions across the six cases. One warmup plus three calls: 18 children/72 outputs. `inline-phase` repeats this declared six-case matrix with phase builds; it is diagnostic only. Equal results/counters do not prove inlining boundaries; actual compile definitions and, if needed, generated calls must be inspected. If gain is explained by inlining alone, test a separately declared generic-inline control before adopting extra representation complexity.

Optional `phase` and `allocation` diagnostics use the predeclared 18-case subset (16,384/262,144/1,048,576, all three families, both graphs, S3001). Paired phase: 36 children/144 outputs; paired allocation: 36 children/72 outputs. They cannot establish uninstrumented speedup. No literal CPU fraction is inferred from exclusive wall phases or logical work.

The unchanged per-child controller applies 300 s and 12 GiB sampled group RSS limits with three unavailable samples/poisoned monitor stopping progression. The new campaign adds 7,200 s through final checks. Every command requires known direct exit and empty owned group; failures remain archived and stop the next launch. Root must explicitly release each build/capture. Snapshot and strict `check` are read-only with respect to existing artifacts.

## Future commands and analysis interface

Unexecuted command shapes (choose fresh output paths):

```
python3 -B benchmark/scaling_investigation/candidates/run_candidate.py snapshot SNAPSHOT_DIR --baseline-build BUILD04/build.json
# Root reviews/applies patch only after baseline modes have stopped.
python3 -B benchmark/scaling_investigation/candidates/run_candidate.py build NEW_BUILD --snapshot SNAPSHOT_DIR/snapshot.json --released
python3 -B benchmark/scaling_investigation/candidates/run_candidate.py capture SMOKE_DIR --build NEW_BUILD/build.json --baseline-work WORK01/capture.json --mode smoke --released
python3 -B benchmark/scaling_investigation/candidates/run_candidate.py capture WORK_DIR --build NEW_BUILD/build.json --baseline-work WORK01/capture.json --mode work --released
python3 -B benchmark/scaling_investigation/candidates/run_candidate.py capture TIMING_DIR --build NEW_BUILD/build.json --baseline-work WORK01/capture.json --mode timing --gate SMOKE_DIR/capture.json --gate WORK_DIR/capture.json --gate NATIVE_SANITIZER_GATE.json --released
```

`load(capture_path)` returns `(info, rows, bound_sha256)`, after checking the exact schedule, native receipts, typed raw schemas, Google fixture joins, source snapshots, old/new build artifacts, and applicable work/prerequisite gates. Rows retain the native schema and add only `policy`, `variant` and `case_index`; warmup remains explicit. `info.captures` records case, policy, variant, label, row count, exact raw/receipt paths. Analysis should independently pair the typed native rows and derive both clocks, without treating diagnostic rows or warmups as timing observations. No analysis output or successful run is supplied by this declaration.
