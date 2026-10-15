# Existing native-domain source check

This prospective source check executed no generator, solver, import or test.
The following paths are existing frozen implementation sources relative to
`/Users/random_person/Desktop/kkt-eighth-sampling`:

- `benchmark/core_attachment_fixtures.hpp:18`: the family inventory contains
  `leaf_distance4` and `leaf_shuffled4`.
- `benchmark/core_attachment_fixtures.hpp:42`: `edge_count()` admits n powers
  of two in [32, 2^22], d in [1, 512], intrusion zero, m≤2^27 and m below the
  represented-weight limit; it independently checks q−1≤core_m≤q(q−1)/2.
- `benchmark/core_attachment_fixtures.hpp:57`: `make_fixture()` uses b=4,
  q=n/4, local=3q, core_m=m−3q, forced consecutive core path and unique random
  additional pairs. Separate seeded streams control topology, ranks, labels and
  physical order. Both named twins preserve the latter common structure.
- `benchmark/retention_control.cpp:103`: the existing six-solver CLI accepts
  n∈[32,4194304] and the same global edge budget; its `edge_count()` and
  `make_graph()` dispatch to the existing attachment generator.
- `benchmark/run_mst_search.py:64`: the unchanged parent manifest parser uses
  the same dimension/edge limits and attachment simple-core inequality.

For b=4, core_m=(4d−3)q. The upper simple-core inequality is q≥8d−5, or
n≥32d−20. The proposed minimum powers are n512 at d16 and n256 at d8; their
core counts are 7808≤8128 and 1856≤2016. Every larger listed size is also valid;
both maximum inputs have m33554432, with n at most the existing inclusive2^22.
No new family alias, dimension allowance, integer encoding, solver behavior or
resource ceiling is needed. A later real freeze must still recheck the entire
native provenance; source reasoning does not guarantee memory fit or runtime.
