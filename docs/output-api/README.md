# Return the forest without hashing its IDs

7 November 2026. `kkt_edge_ids(const problem&, unsigned int)` exposes the
selected-ID vector that KKT already builds internally. It does not hash or sort
the result. The existing `kkt(problem&, unsigned int)` returns the same
`unordered_set<int>` type as before and delegates to the new entry point.

```cpp
const problem graph(n, edges);
const std::vector<int> forest_ids = kkt_edge_ids(graph, seed);
```

Each selected ID occurs once. Result order is unspecified. The input must be
an undirected, loop-free graph with distinct edge weights, unique IDs and valid
vertex indices; disconnected components and isolated vertices are supported.
IDs may be negative or sparse, including signed integer boundaries. Internal
indices must fit their existing integer representations. Preconditions are not
validated at runtime. Neither API modifies the input.

This is a representation choice, not a faster hash function. Clients needing
iteration over the forest can use the vector directly. Clients needing hash-set
membership can keep the old API, with its additional collision-cost assumption.
Changing to a sorted vector would add sorting work; allocating by the largest
ID would reintroduce the sparse-ID problem. Neither is necessary to return a
list of selected edges.

The vector removes this output-stage assumption; it does not prove every
premise needed for expected linear work in the complete implementation. The
sampling model, linear verifier and machine-word assumptions remain. No
existing benchmark return contract or timing was changed by this repair.

## Exact collision-work check

The [native result](validation/hash-witness-native-2026-11-07/RESULTS.json)
records 16 cases: four sizes, two ID layouts and both APIs. Each input is a star
with distinct weights; every edge belongs to its unique MST. The colliding
layout assigns IDs `0,b,2b,...,(k-1)b`, where `b` is the legacy output set's
reserved bucket count. These finite cases fit signed 32-bit IDs.

| Star edges | Legacy API, colliding IDs | Vector API, colliding IDs | Contraction edge visits, either API |
| ---: | ---: | ---: | ---: |
| 1,024 | 523,776 | 0 | 1,024 |
| 2,048 | 2,096,128 | 0 | 2,048 |
| 4,096 | 8,386,560 | 0 | 4,096 |
| 8,192 | 33,550,336 | 0 | 8,192 |

The middle columns count actual existing-node visits in libc++'s unique-insert
bucket loops. Dense-ID twins have zero visits through those loops for both
APIs. This is an operation-count witness, not a timing comparison or cache
measurement. Selected internal counters are identical across APIs, and every
returned ID and its uniqueness are checked. These stars make one contraction
and invoke no sampling or verifier.

The [runner](../../test/run_output_api_witness.py) copies the installed SDK's
`__hash_table` to a temporary directory and instruments exactly two inspected
loop bodies. It fails closed if either source fragment changes. The installed
SDK is untouched. Source/header hashes, commands, binary format/hash and exit
codes accompany the raw output. The compiler target is explicit, preventing a
Rosetta-hosted Python from silently selecting translated code.

```sh
python3 test/run_output_api_witness.py --output /tmp/kkt-output-api-new-run
```

This SDK-specific witness requires macOS and a matching inspected libc++
header. The ordinary tests below do not require that instrumentation.

## Correctness and toolchain checks

The existing regression helper now checks both APIs against Kruskal on the
same distinct-weight inputs, verifies vector duplicate absence and seed replay,
and verifies input preservation after each call. Fixtures include sparse and
negative IDs, disconnected forests, isolates, recursive paths, random graphs,
forced parallel quotient edges and deliberately irrelevant legacy ID metadata.
New signed-weight fixtures cover an all-negative recursive path and a random
graph with weights spanning `INT_MIN` through `INT_MAX`.

The recorded commands and outcomes are in [TEST_COMMANDS.json](validation/TEST_COMMANDS.json).
The release suite passes 8 simple tests, 16 regression groups, 214 independent
contraction-oracle cases and the positive/negative MST certificate tests.

The first Python-driven rerun used an x86_64 interpreter and failed to link
against native arm64 objects. Its separate Rosetta sanitizer build failed at
startup. Apple Clang 15's native ASan runtime also aborted before the tests ran.
Those failure logs are retained; they are not algorithm failures or successful
sanitizer checks. The final sanitizer result uses the native Homebrew LLVM
toolchain, as specified in the command receipt.
Its ASan/UBSan build passes the same complete suite, with undefined-behavior
recovery disabled; no sanitizer diagnostics appear in that successful run.

```sh
make -j3 test
```

The production repair changes only the output API boundary and constness of
the read-only internal entry point. It preserves the contraction, verification
and random sampling code.
