# Evidence provenance and correctness inventory

This inventory audits the archived common-family campaign at measured revision **`c9ed4cae8ee3bfce913cceb5298cbb961280baac`**. It reads source, metadata, binaries, logs and raw data; reruns the Python data validators; and independently reconstructs the seven small graph exports. It does **not** rerun C++ tests or collect new timings. Exact hashes, counts and qualifications are in [validation_summary.json](validation_summary.json).

## Provenance

All **15 collection-hashed raw artifacts** match their recorded SHA-256 values: six main CSV/log files, eight diagnostic CSV/stdout/log files, and the Google Benchmark JSON. Both recorded runner hashes match the archived runners. The four distinct binaries still present locally—native timing, native instrumented work, native contraction ablation, and Bazel Google Benchmark—match their collection-time hashes.

Both [main metadata](metadata.json) and [diagnostic metadata](diagnostics/metadata.json) list the same **47 C++ source/header files**. Every entry matches both the current file and the Git object at the measured revision. These are 47 distinct files checked against two manifests, not 94 independent source files. The production algorithm files also match final production revision `2d4fbf1`; the common campaign changes coverage and diagnostics rather than the algorithms.

The source manifests cover one-directory-deep C++ sources and headers. They do not hash build files, SDK contents or entire external dependency trees. Logged native compiler commands, recorded Bazel profile, revision and binary hashes complement that manifest; this is provenance evidence, not a reproducible-build proof. The recorded native compiler is Apple clang 15 on an Apple M3 Max, arm64 macOS.

| Profile | Recorded configuration | Evidence use |
|---|---|---|
| Native timing and ablation | C++17, `-O3 -march=native -Wall -Wextra`, matching Apple SDK, assertions enabled | Paired main and ablation timing |
| Native work | Same native flags, separately compiled with `KKT_ENABLE_WORK_STATS` | Untimed logical-work observations |
| Google Benchmark | Bazel `-c opt --copt=-O3`, `NDEBUG`, no `-march=native`; Google Benchmark v1.5.2 | Separate manual-time scaling diagnostic |

The main analyzer's collection-time hash is `64bd26b2de5b7fb525cb3316c0ebb96d3fa4e1f948f1750053bf7cf75be55f2f`. Its final hash is `cc44bac5ad6ec78a7bf4643557866b6517d313d57e7f8ab7290a4d45e46a15c8`: the post-collection diff improves spatial-plot tick labels and caption. Both final analysis manifests name that final hash. Raw observations and measured C++ sources are unchanged. The inventory also records the final hashes of the other analysis modules.

Smoke outputs, fixture logs and `graph_views.json` were not individually hashed by the collection runners. This inventory hashes those supporting artifacts **at audit time**, without implying an earlier cryptographic record.

## Counts, with distinct units

Every CSV result marker is successful, and the complete main, work, ablation and Google Benchmark matrices pass their strict validators. Counts below are intentionally separate: a trace row is one contraction, a Google Benchmark raw record averages three calls, and a warmup is checked but is not a retained timing row.

| Dataset | Cases | Case/graph-seed realizations | Retained timing rows / timed calls | Checked warmup calls | Untimed observations |
|---|---:|---:|---:|---:|---:|
| Common smoke | 13 | 39 | 1,872 / 1,872 | 468 | — |
| Main primary | 52 | 156 | 7,488 / 7,488 | 1,872 | — |
| Main repeat | Same 52 | Same 156 | 7,488 / 7,488 | 1,872 | — |
| Main work | Same 52 | Same 156 | — | — | 468 KKT calls |
| Ablation smoke | 12 | 36 | 864 / 864 | 216 | — |
| Ablation smoke trace | Same 12 | Same 36 | — | — | 36 complete calls, 132 round rows |
| Ablation primary | 20 | 60 | 1,440 / 1,440 | 360 | — |
| Ablation repeat | Same 20 | Same 60 | 1,440 / 1,440 | 360 | — |
| Ablation trace | Same 20 | Same 60 | — | — | 60 complete calls, 386 round rows |
| Google Benchmark diagnostic | 45 family/size pairs | 135 | 810 / 2,430 | No explicit warmups | — |
| Explanatory graph export | 7 | 7 | — | — | Seven 256-vertex instances |

The Google Benchmark JSON additionally contains **810 mean/median/stddev rows and 60 BigO/RMS rows**: 1,680 JSON records total, still only 810 raw timing records. Derived aggregate records are not extra executions. Its 270 algorithm/family/size/graph instances each have three raw repetition batches of three calls.

The main work matrix has **153 distinct full-input fingerprints among 156 labeled graph realizations**. The fixed-256 and square-root bipartite cases intentionally coincide at n=65,536 for all three graph seeds. Spatial random/distance pairs intentionally reuse topology with different weights. Repetitions, sampling labels and repeat campaigns do not create additional independent graphs. Deterministic competitors also repeat under KKT-seed labels for matching purposes.

## Correctness and data checks

The archived [Bazel log](bazel.log) reports **10/10 executed test targets passed**: complexity, contraction, KKT, MST, regression, legacy verifier, verifier v2, certificate, common fixtures and shape fixtures. This is a count of executables, not ten individual test cases. Current Bazel test logs corroborate:

- Six complexity GTests, three KKT GTests, one MST GTest, five legacy-verifier GTests and one verifier-v2 GTest: **16 registered GTests**. Stress loops inside them are not counted again here.
- The standalone regression executable: **15 passed, zero failed**.
- The standalone contraction oracle: **214 cases passed**.
- Common fixture suite: **222 fixture realizations**, plus paired spatial-weight, control and invalid-input checks.
- Shape fixture suite: **96 seeded fixtures**, plus unchanged controls and invalid-input checks.
- Independent certificate suite: positive and negative cases passed; its log supplies no numerical subcase count.

Both native fixture logs also report the same 222-fixture suite passed. They and the Bazel run repeat that suite; they do not establish 666 distinct fixtures. The diagnostics-build log records a successful build, not additional test executions. Build warnings about an assertion-only unused variable, a third-party variable and test-size annotations are retained. No sanitizer run is claimed for this campaign.

For each benchmark input, an independent certificate checks the reference's source-edge membership, unique IDs, tree/forest structure and cycle optimality. Distinct weights make the MST unique. Every retained call and warmup must match the certified exact edge IDs; tuple-returning competitors also have endpoints and weights checked. Validators require complete matrices, valid dimensions/seeds, positive durations, successful results and the prescribed schedule. Instrumented work additionally checks its counter schema, internal identities and derived fields.

The common analyzer matches **54 work observations across 18 graph realizations and six overlapping control cases** to the earlier shape campaign, including fingerprints and all shared fields. The ablation trace crosscheck matches **all 60 original fingerprints and the residual n/m after two contractions or earlier termination**, for all three KKT seeds, to independently collected common/shape work. It does not compare intermediate residual edge contents. Timing CSVs do not contain per-call fingerprints; their input identity rests on frozen fixture source/binary provenance and these separately collected checks.

All archived analyzer selftest records were inspected:

| Analyzer | Positive evidence | Malformed inputs |
|---|---|---|
| Common | Six successful synthetic/matrix/arithmetic/control checks | 25 cases rejected, recorded in [analyzer_selftest.json](analyzer_selftest.json) |
| Ablation | Complete synthetic matrices and known paired/hierarchical medians | 43 cases rejected; [portable script and log](diagnostics/ablation_validation.md) |
| Common complexity adapter | Complete 810-raw/60-built-in matrix validated through the existing strict timing module; full 468-row work matrix validated | **No new malformed-data suite was run for this adapter** |

The final inventory revalidated all three common timing matrices, the work matrix, both main ablation matrices and the main traces, historical controls, and Google Benchmark raw/built-in records. Separate checks confirmed the full ablation-smoke matrix and its trace accounting. Independent arithmetic review of scaling means/exponents is additional review evidence, not a new selftest count or an asymptotic proof.

All seven [graph exports](graph_views.json) carry successful certified-MST, contraction and path-oracle markers. The exporter throws on failure. As an additional audit of the archived data, fresh Python DSU/path reconstructions agreed on all seven MST ID sets, **14 contraction mappings and minimum-parallel reductions**, all seven sample MSFs and all seven heavy-edge ID sets. This recheck does not regenerate fixtures or independently reproduce the `mt19937` sample stream. These 256-vertex illustrations are separate from performance evidence.

## Timing boundary and interpretation

Source review and [boundary_audit.json](boundary_audit.json) confirm that the diverse harness's measurement function, existing presets, timed schedule, original fixture headers and certificate are unchanged from the earlier shape campaign at `1a3fc3c`. The common extension adds dispatch and options around that code.

All four algorithms begin from the tuple edge list. The timed interval includes algorithm-specific conversion, temporary KKT-input destruction and output construction. It excludes fixture generation, reference certification, output validation and returned-result destruction. KKT returns an ID hash set while the repository competitors return edge vectors; that public-interface difference remains part of the comparison. Four timed repetitions rotate each algorithm through every position. Warmups use a fixed order; case order is a single deterministic shuffle reused across campaigns.

The ablation gives both strategies the same tuple-input conversion and reserved ID-set output boundary. It repeatedly invokes the exact production `boruvka_step`; it is not the repository's original Borůvka implementation. It compares **whole continuation strategies**, including iterative versus recursive storage lifetimes, RNG, sampling and verification. It does not isolate verifier instructions or demonstrate that no better Borůvka implementation exists.

Google Benchmark uses `UseManualTime` and `SetIterationTime` around the same conversion/result boundary. Validation and returned-result destruction occur with CPU timing paused. The harness sets N=n+m and cycles seeds 0/1/7 across each three-call batch. Its registration order is fixed, unlike the paired campaign. In v1.5.2 the automatic model is selected using CPU time and then fitted to manual time; those finite-range labels are not complexity proofs. Manual-time fits and all built-in records are preserved separately.

The collection was serial, on an ordinary desktop without controlled affinity or power state. Separate builds, repeated observations and descriptive three-graph ranges do not eliminate environmental variation. Main, smoke, work, Google Benchmark and ablation data are retained separately rather than pooled into one performance or correctness count.
