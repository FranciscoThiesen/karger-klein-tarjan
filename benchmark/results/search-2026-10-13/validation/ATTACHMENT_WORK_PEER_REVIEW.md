# Final source/data review of attachment mechanism evidence

Reviewed the integrated occupancy proof, work joiner and its generated 16-record
report/provenance, the attachment fixture and work producer source, viewer
metadata and explanatory README text. This review performed no imports, tests,
solver runs, plotting or browser actions. The larger native pilot has begun;
this note is outside the watched repository.

No blocking correctness or benchmark-fairness defect was found.

## Proof and model

The deterministic partition argument is valid for the two ordered modes.
Cheap stars select all local edges in the first round. In hierarchy mode the
core path's lowest remaining dyadic bridge connects each aligned block to its
sibling; all other path exits have higher level and every shortcut ranks after
the path. In distance mode all actual core edges are ranked by dyadic level;
the two siblings share the same unique minimum between them, while leaving
their parent requires a higher level. Both produce the stated aligned
partitions independently of the drawn shortcut set. Within-level shuffling
can change selected IDs without changing those partitions.

The hypergeometric expression correctly treats adjacent quotient pairs as
already occupied by path edges, and gives exactly s-squared eligible shortcut
slots for each nonadjacent pair. It includes parallel-edge collapse and
internalization, does not assume pairwise independence, and handles the last
one/two-component states separately. The original m is counted once before the
core input sum. The lower-bound constant and eligible-round count are valid.
The d=1 exception and fixed-parameter qualification are essential and present.
The earlier b=1 issue is resolved by requiring b>=2 (actual models use 4/16).

The resulting expected Theta(m log n) statement applies to compactor
**edge-input volume**, an ideal uniform shortcut-subset ensemble, and fixed
b,d>=2 as n grows. It is not an empirical time fit, a complexity certificate
for the KKT implementation, or an asymptotic statement along a density-growing
sequence. The finite PRNG/cap and floating-point truncation limitations are
explicit. No concentration or global timing-dominance claim is made.

The README's expected-linear theorem wording needed the explicit O(n+m)
input-size meaning (O(m) for connected graphs). Parent reports that this
clarification is now incorporated. O(n) alone is justified here only when
d is fixed and m=dn.

## Join and work interpretation

The integrated helper reuses complete timing-capture validation, matches case,
graph seed, sampling seed and both fingerprints, compares required native
sources, and keeps campaigns separate. Raw work/log hashes, the recorded
instrumented binary/build provenance and the counter registry are retained.
The work profile is intentionally different from the uninstrumented timing
profile; work durations are not treated as benchmark samples.

Trace chaining, selected-edge totals, component moments, exact star/core
endpoints and aggregate contraction counters are checked. Original round j>=2
consumes core blocks of size 2^(j-2); the final stored quotient is empty while
the original graph has one component. Intermediate edge counts are compared
to expectations without falsely requiring exact equality. Shuffled and random
controls have no dyadic prediction. The helper acknowledges that moments do
not establish exact memberships and that captured records lack edge tuples
for independent recertification. The native certificate marker is bound to
the recorded fixture instead.

The generated report retains all 16 records and 254 native rounds. For the
largest leaf hierarchy b4,d16 diagnostic, the displayed compactor volume/m
6.986520 and KKT contraction volume/m 3.249560 match the summary, alongside
31 sampling calls and 98.3607% heavy **recursive verifier incidences**. These
are different event classes and denominators: that percentage must not become
"98% of distinct original edges removed," nor imply a proportional wall-time
speedup. The report already makes the denominator and mixed-event caveats.
The d2 and shuffled/global-random diagnostics remain visible; reduced KKT
contraction volume does not itself establish a net runtime advantage.

## Fairness and illustrations

No solver change, benchmark boundary change, repeated-work insertion or
relabeling of a hybrid as KKT is part of this evidence. The compactor repeatedly
uses the same production contraction operation as KKT. The deliberately
ordered weights favor prolonged continuation, but the model is explicitly
engineered, all classical losses remain, and matched shuffled/global-random
controls expose the initial-star versus later-ordering distinction. Leaf and
community twins are coupled inputs, not independent replications.

The graph viewers contain actual certified small exported edges and an
independent minimum-edge contraction ledger. Their first two rounds are
shared with KKT; the remainder depicts compacting Boruvka, not KKT sampling
or recursion. The d2 set's 99-stage native count/moment match is distinguished
from the extra four d16 examples, whose native traces were not separately
captured. Both are clearly small illustrations, not downsampled timing inputs.
Browser rendering remains unverified because both headless browsers aborted
before loading a page; the README/QA preserves that limitation.

No pending browser result, expected occupancy, theoretical lower bound or
untimed counter is presented as a measured confirmation result. The fresh-seed
criterion and 4M stress-only exclusion were fixed before the new captures.
