# Independent counter-audit source review

Result: **SOURCE REVIEW PASS**, 2026-10-15, after the two certificate hardenings below. Reviewer: `/root/multigraph_candidate`, independently of the author. No imports, syntax checks, mocked tests, native execution, plots or partial timing reads were performed. Runtime gates remain pending. The design agent was explicitly freed to finish the report instead of duplicating this review.

Reviewed files and SHA-256:

| File | SHA-256 |
|---|---|
| `audit_counters.py` | `03f8b9af8a3445cebe0c7b5dbbca89ef6b69552fbfc4330418247c04abecb8eb` |
| `test_audit_counters.py` | `ecee5fa9583f56d56d2a6e62f47568183641099b663edbe805dc77448741c4f5` |
| `SOURCE_PREPARATION.md` | `191f4b1362dba9af67517fca753a8ed894348118abf8ea630353afc0a244df6c` |

The preparation-note hash was refreshed after the author's status-only update documenting this source PASS and the reviewed certificate/zero-numerator additions. Audit and test source hashes did not change.

The literal schedule covers all six cases, two graph seeds, two sampling seeds and both policies in the declared reversed/balanced order: 48 inputs, 144 three-solver rows and 9,360 counter cells. Exactly 96 comparator `hash_insert_items` cells remain unmeasured/null. The audit independently reconstructs 96 complete connected contraction chains and their sums, 48 cumulative Q/U and scalar engine-word rows, and 24×65=1,560 rate-paired fields. The 1,608 exact-ratio records retain undefined denominator statuses, defined zero numerators, increases and decreases.

All 65 raw fields are checked against a literal inventory and the bound header's name-to-actual-member mapping. Native integers reject bools, negatives and values ≥2^64. Current recursion depth must be zero. The first-two-contraction root witness uses the unchanged retained comparator replay. Every comparator counter and round sequence must agree across rates and sampler seeds at each graph identity; KKT work is allowed to change. There is no compression experiment's 61+4 identity and no accidental cross-rate all-counter equality. `U=path_query_visits−2Q` remains in [0,Q], including Q=0; exact engine words equal visited sampling edges for these two scalar policies. At least one full-matrix Q must be positive, without excluding individual zero-query cases.

The raw audit binds the completed timing freeze and all 48 timing certificate/fingerprint joins, rehashes the frozen bound inventory, checks exact commands/evidence paths, and checks ordered resource observations, the 1,800-second native-exit bound and final empty owned groups. Canonical path resolution is correct when installed under the declared study `work/` directory; the mock fixtures pass an explicit bound registry from a resolved temporary root. CSV/metadata hashes are taken before reading, retained in the input inventory and checked again before success. All five numerical tables are rebuilt from raw JSON rather than imported collector aggregation.

Two findings were repaired before PASS: (1) the parser now examines every `reference_certificate` marker and rejects an extra or unsupported version; (2) raw, sidecar and timing certificates now require exact schemas and per-field types, preventing float/integer aliases. Prepared negatives recompute log hashes to reach these checks, rather than failing only a stale digest. The author also added a half-positive/eighth-zero counter fixture and an explicit defined-zero-ratio assertion.

The six synthetic groups cover a separate literal Cartesian table oracle, schema/domain/round/control mutations, complete raw/analysis fixtures, certificate/schedule/resource/hash/timing joins, same-identity numeric/null/table mutations, strict JSON, registry drift and provenance. They have not run. This audit explicitly supplements the separate strict collector/build proof: it rehashes that complete inventory but does not independently reconstruct its 43 compile commands or rerun the native MST certificate. Its receipt states that limitation and makes no runtime-performance claim.
