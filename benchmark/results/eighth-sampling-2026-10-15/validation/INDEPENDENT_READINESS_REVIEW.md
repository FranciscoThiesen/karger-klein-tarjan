# Independent completed-artifact readiness review

**PASS.** [Readiness proof](independent-readiness-attempt01.stdout) and
[owned execution receipt](independent-readiness-attempt01.json) record a read-only
reload of the completed artifacts. The reviewer launched no native solver,
compiler, performance driver or work driver, and created no freeze or commit.
The Python review exited 0; its owned group 40459 was verified empty. Source
hashes were unchanged throughout the review.

The review reran the complete compressed-parent proof at its original working
root, including the original helper files, sources, recipes, objects and
executables. The local immutable helper copies matched by unique basename and
hash; the temporary helper-path mapping was restored. Parent freeze SHA-256 is
`bd65da13058d3e9cfa58919a0fe5e02b8a46b1d0b8fe7f05801692d5a0866df9`.
The current native source inventory differs only by the declared predicate
refactor/header and two new tests.

All 25 saved mock groups (4 controller, 7 builder, 14 collector) passed. Actual
native and sanitizer receipts each contain the full 20 positive and four
wrong-policy negative executions. The reviewer reloaded all 1,344 fixture/order/
seed records and their exact 65-field schemas for both rates. Input fingerprints,
MSF IDs and initial two-contraction dimensions agree across rates; all 65 half
reference counters exactly replay the frozen parent. Recursive work differs in
543 pairs, independently recalculated in both profiles. The substitution gate
rejects replacing the eighth records with half records.

Every timing command matches the reconstructed twelve-command recipe. Seven
non-KKT production objects and the harness object are physically shared;
only the KKT object differs, with the single declared private sampling macro.
Typed descriptors require half/mask 1 or eighth/mask 7, one engine word per
visited edge, and a fixed compressed verifier. Actual Mach-O headers and load
commands were read directly: arm64 executables and 512 MiB main stacks.

The final-object gate contains four positive checks, two wrong-policy negatives
and two byte-identical KKT rebuilds. Two positives use the actual final production
objects for full solver certificates; two are explicitly separate same-flags
source-inclusion RNG oracles. This does not claim a direct RNG trace from the
separately linked final KKT object. All final binaries, rebuilds and logs were
rehash-checked. Across the review, 331 directly pinned artifacts were reread,
in addition to the inherited full parent proof.

All saved inner command/outcome multisets match their process receipts:
67 native, 64 sanitizer, 12 timing-build and 15 final-object owned groups. Each
has affirmative known-exit and empty-group evidence; all outer phases also
completed before their deadlines. No performance/work execution is recorded.

Timing binary SHA-256 values:

- Half: `516df4fedcf5c1c82b398685c372bf660cd21ffa6d546ce637d94ed58aacd2f7`
- Eighth: `954068775a83e1c42db62ffb6777c398dc05fd5792c60d2f293df6532130951a`

The archived [review script](review_readiness.py) is reproducible through the
existing postcapture wrapper at the compressed worktree's
`benchmark/results/heldout-families-2026-10-15/validation/run_postcapture_validation.py`.
An initial invocation incorrectly assumed that wrapper was already present in
this new worktree; Python exited 2 before any review child or attempt artifact
was created. The corrected absolute wrapper path produced the preserved first
review attempt above. No existing artifact was overwritten.
