# Untimed attachment-work joiner

`benchmark/analyze_attachment_work.py` was integrated after the attachment pilot
timing window closed. It reads existing records; it never launches a solver.
The Python validation gate passed all 16 archived native attachment diagnostic
records and a complete join to their smoke timing capture. The temporary join
manifest in that test is explicitly synthetic and supplies no new historical
binary-provenance claim. Actual work captures need the manifest described below.

Example eventual invocation:

```sh
python3 benchmark/analyze_attachment_work.py \
  --repo-root /Users/random_person/Desktop/karger-klein-tarjan \
  --timing-csv benchmark/results/search-2026-10-13/attachment-timing.csv \
  --timing-csv /path/to/another-complete-capture.csv \
  --work-manifest /path/to/selected-work-capture.json \
  --output-dir /path/to/new-work-analysis
```

Each timing CSV must have the existing complete `mst_search_capture_v1`
metadata, child files and logs required by `analyze_mst_search.load()`. That
existing validator is reused; failed or incomplete timing captures are not
partially salvaged. Repeated timing keys must have identical fixture identity,
both fingerprints, native source inventory and profile. Matching campaigns
are listed separately; their durations are never pooled or fitted.

## Work capture manifest

The root can write this manifest after serial untimed captures finish:

```json
{
  "schema": "attachment_work_capture_v1",
  "validation": "pass",
  "instrumented": true,
  "rows_removed": 0,
  "rows_adjusted": 0,
  "working_directory": "/absolute/repository",
  "profile": "Native Make WORK_OBJS; KKT_ENABLE_WORK_STATS; exact compiler/flags here",
  "binary": "/absolute/repository/bin/search_work",
  "binary_sha256": "64 lowercase hexadecimal characters",
  "source_sha256": {
    "benchmark/search_work.cpp": "64 lowercase hexadecimal characters",
    "benchmark/work_metrics.hpp": "64 lowercase hexadecimal characters",
    "benchmark/component_moments.hpp": "64 lowercase hexadecimal characters",
    "other required production and fixture sources": "64 lowercase hexadecimal characters"
  },
  "build_recipe_sha256": {"Makefile": "64 lowercase hexadecimal characters"},
  "build_log": "relative-or-absolute-build.log",
  "build_log_sha256": "64 lowercase hexadecimal characters",
  "records": [
    {
      "command": ["/absolute/repository/bin/search_work", "--family", "leaf_hierarchy4",
                  "--n", "1048576", "--density", "2", "--graph-seed", "5009", "--kkt-seed", "149"],
      "exit_status": 0,
      "started_utc": "2026-10-14T02:00:00+00:00",
      "finished_utc": "2026-10-14T02:01:00+00:00",
      "json": "leaf_hierarchy4-work.json",
      "log": "leaf_hierarchy4-work.log",
      "json_sha256": "64 lowercase hexadecimal characters",
      "log_sha256": "64 lowercase hexadecimal characters"
    }
  ]
}
```

This is a schema illustration, not an executed record; substitute actual
paths, timestamps and hashes. `source_sha256` must include every file in the
existing analyzer's `NATIVE_FILES` except `benchmark/mst_search.cpp`, plus the
three explicit work helpers above. A full repository C++/header inventory is
accepted and is the simplest way to meet that requirement. Shared solver and
fixture hashes must equal each matched timing campaign. If a matched timing
inventory also includes the work helpers, their hashes must agree too.
The work binary is deliberately different from the uninstrumented timing
binary; matching their full binary hashes is neither required nor correct.

The recorded Makefile digest and complete work build log are retained in
output provenance. The log's actual file hash is checked. This is build
provenance, not independent proof that a binary was compiled by that command.
Record paths resolve relative to the manifest. `binary` should be absolute;
command executable paths resolve relative to `working_directory`. All five
native options must be explicit; option order may vary. Every record's stdout
and stderr must be complete, successful and uniquely listed. One work record
per case/graph/KKT key is accepted. Its matching timing campaign can contain a
larger matrix: diagnostics need not repeat every timed case.

UTC endpoints are optional, but must occur together. Reversed UTC is retained
as a descriptive untimed capture flag; no clock duration is treated as a
performance measurement. Other top-level archival metadata can be retained.

## Validation and derived outputs

The analyzer requires duplicate-key-free JSON, exact native work/statistics
schemas, integer counters, a successful native reference-certificate marker,
matching timed fingerprints, valid model dimensions and MST count/cost bounds.
It recomputes the mixed-event proxy from the hash-bound 65-field C++ registry.
The compactor trace must chain completely, have valid connected-simple
quotients, and match its aggregate contraction counters. Selected forest
counts, component moments and KKT's first-two-round counters are cross-checked.

For hierarchy/distance weights, every round must have the model's exact
component count and balanced component moments. First-star, initial-core and
terminal edge counts are exact checks. Intermediate **observed edge counts
are not required to equal their expectations**. Their signed differences
are retained. A finite pseudorandom realization is not the ideal ensemble
expectation, and no standard error or significance claim is generated.

For shuffled-core controls, only the forced first-star structural check
applies; for global-random controls even that assumption is disabled. Both
control modes have blank model-expectation columns. This is intentional.

Outputs in a new directory only:

- `summary.csv`: both contraction volumes per original m, recursive/sampling/
  verifier counters, materializations, initialization, model volume and signed
  deviation. Heavy fractions use recursive verifier incidences and are blank
  when the denominator is zero.
- `rounds.csv`: every observed compactor round, exact original/core indices,
  component moments, expected input/output edges, signed deviations, and the
  model's truncation budgets.
- `counters.csv`: both complete registered counter records, including the proxy.
- `timing_links.csv`: every matching campaign and exact identity/fingerprints;
  no elapsed-time aggregation.
- `models.json`, `report.md`, `provenance.json`: full model records, bounded
  interpretation, all raw/build/helper hashes and derived-output hashes.

Original round 1 consumes the expanded input. Original round j>=2 is core
round j-1, consuming aligned blocks of `2^(j-2)` core vertices. The final stored
quotient is empty but the original partition has one component. Model volume
includes original m once plus all edge-bearing core inputs.

`search_work_v1` does not contain the original edges or selected-ID ledger.
This analyzer therefore cannot independently recertify the MST or prove exact
vertex membership from moments alone. It binds the successful native
certificate/trace producer and checks the information that was actually
captured. Model truncation bounds exclude floating-point roundoff and random
graph variation. No counters are interpreted as instructions, bytes or time.

## Validation

Run `python3 -B benchmark/analyze_attachment_work_test.py`. Its eleven test groups
cover the 16 existing native diagnostic records, all ordered/control modes,
an independent small synthetic trajectory, exact round indexing, nonzero
observed-minus-expected differences, zero-denominator heavy fractions, valid
component moments, and separate campaign identity handling. Negative mutations
cover omitted/duplicate fields, nonfinite JSON, boolean counters, bad proxy
sums, broken trace chains, premature completion, wrong moments, absent native
certificates, changed fingerprints/source hashes, missing raw hashes, failed
statuses, duplicate records and inconsistent repeated timing identities.

The real-data smoke join validates its existing raw capture; its synthetic
manifest is an integration-test adapter only. No native binary is executed by
the tests. Actual selected work records are joined separately using their own
capture-time source/binary/build and raw-output manifest. Counter work and all
validation must remain outside native timing windows.
