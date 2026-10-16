# Fresh Google Benchmark depth-query comparison

Prospective source preparation, not executed results. This is a new six-curve
comparison of reference and depth-query KKT, using the unchanged pinned Google
Benchmark v1.5.2 library and unchanged `current_complexity.cpp` main.

Three families are fixed: `leaf_hierarchy4`, `leaf_shuffled4` (m=32n), and
connected `gnm_random` (m=16n). Every curve uses G=19000013 and S=3001, with all
11 ascending powers of two from n=1,024 through 1,048,576. The declared workload
is the same historical workload, whose input fingerprints must match exactly.
There are no fresh unseen seeds and no claim about seed generality.

Policy order is reference/depth for hierarchy, depth/reference for shuffled,
reference/depth for random. This alternation is not fully balanced across three
families. Each curve runs three callbacks per size, each with a checked warmup
and two timed calls: six curves, 594 native records (198 warmups, 396 timed),
198 reference certificates, and six actual Google BigO/RMS report pairs. All
losses, raw records, native wall/CPU clocks and library manual/CPU clocks remain.
No old duration enters the fresh comparison; old data supplies only artifact
proof and input identity.

The new executable links the eight physical uninstrumented production objects
from `depth-build01` for each policy. Only their verifier object differs. One
fresh common main object is compiled with the historical main's exact flags,
with only the root include path relocated. The existing static library is not
rebuilt. Its complete immutable historical freeze inventory, archive bytes,
library source and real schema-smoke receipt are rechecked at their original
paths. New object/binary/recipe proof is separate: the historical collector's
binary restriction is never weakened or redirected. Existing pure trace,
certificate and library-schema validators are reused without changing globals.

Build costs three owned commands (one compile, two links). Capture requires
the candidate smoke, full 72-input counter comparison and completed native /
sanitizer gate. Each curve is allowed 600 seconds until observed native exit,
and the whole capture including validation 4,200 seconds. These ceilings were
declared before execution: the historical completed curves took 74.19–244.75
seconds. The sampled owned-group ceiling remains 12 GiB; three consecutive
unavailable samples, poison, unknown/nonempty cleanup or any validation failure
stops the campaign. Every attempt uses an exclusive output directory and retains
failures. This is not an assertion that sampled RSS bounds unsampled peaks.

Google selects `oAuto` using library process CPU on all 11 sizes, then fits the
manual coefficient to that selected model. Its exported RMS is CPU-only.
The raw library label is retained without replacement by a custom fit. A finite
model fit is neither a complexity proof nor an eventual-crossover guarantee.
Only one graph and one sampling seed are represented here, and ascending order
can confound size with machine history. The separate paired native study has
broader graph coverage; it must not be pooled with these library observations.

Pending gates: independent source review, focused mocked checks, actual common
main build/profile checks, three prerequisite proofs, explicit quiet release,
six successful actual curves, and strict reload. No native job is launched by
source preparation.
