# Optional condensed report: independent source review

Status: source/editorial PASS after the narrow qualifier corrections. This is
only an optional fallback if actual pagination later requires it; the primary
final-edition source was not changed by this review.

Compared `/tmp/kkt-final-edition-condensed-fallback.md` with
`/tmp/kkt-final-edition-condensation-source-snapshot.md` using text reads. The
review covered the changed opening, historical complexity prose, comparisons,
implementation mechanisms, half-policy size results and validation section.
No material numerical evidence, table, figure, loss, comparator or clock was
removed in the reviewed changes. The current Google finite-fit scope and
pending lower-density sections remain intact.

The author restored these precise qualifiers before PASS:

- Compression ratios explicitly mean compressed/reference, use verifier-edge
  and verifier-vertex field names, and define all accounting sums over one
  solve's connected verifier-tree calls.
- The million-vertex 0.97 comparison is explicitly from the compressed
  half-policy study, rather than the newer eighth-policy campaign.
- Cached LCAs survive longer and replace per-edge maxima during traversal;
  no peak-RSS or hardware-locality gain is inferred.
- The native profile describes recent timing, preserving the separately
  qualified historical Bazel/NDEBUG profile.
- Prim has at most one tentative set entry per vertex; the opening refers to
  being fastest of all six solvers.

Other important qualifications remain: paired-ratio medians, seed/order
confounding, repeated fixed realizations, unchanged-control drift, sustained
versus narrow/reversed brackets, changed private random streams, engine-word
bounds rather than observations, unmeasured counters, finite PRNG/domain
limitations, and distinct scopes for source reasoning, work counts and timing.

No imports, tests, hashes, word/page counts, numerical scripts, rendering,
native calls or partial timing inspection were performed. This review does not
establish a word saving, the final 40-page gate, physical figure legibility,
complete publication-link verification or browser acceptance. Those remain
actual publication gates after the quiet captures.
