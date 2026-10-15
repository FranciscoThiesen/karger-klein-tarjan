# Held-out families: source-only preparation

Historical source-preparation note. The draft below was written before the parent timing completed. The files have since been installed for nonperformance validation; current receipts are in `validation/`, and [PROTOCOL.md](PROTOCOL.md) remains the prospective declaration. This historical note does not grant a performance release.

Prepared while compressed-query performance capture was active. **No imports, syntax checks, tests, freeze, native solver execution or plots have been performed for these new files.** Source-only review is permitted now; execution requires a separate root release. No existing native or frozen Python source was edited.

Files:

- `run_heldout_families.py`: new single-binary collector, strict reload, canonical comparisons and exact-rational sustained-crossover tables.
- `test_heldout_families.py`: nine prepared mock groups, including a full 72-child synthetic schedule, parent/source/object drift, matched twins, malformed raw rows/certificates, exact Fraction oracles, crossover boundary/reversal negatives and fail-closed monitoring.
- `manifest.csv`: exact 36-case order, independently spelled in the tests.
- `PROTOCOL.md`: prospective matrix, seeds, scientific limits and release gates.

After nonperformance release, install the two Python files under `benchmark/` in `/Users/random_person/Desktop/kkt-compressed-queries`, and this protocol/manifest under `benchmark/results/heldout-families-2026-10-15/`. The parent binary and helpers must stay unchanged. This directory is a draft, not an alternative import root to run during current timing. The study path is a proposed namespace; update it prospectively before freeze if root chooses a different date.

Planned mocked command, from the worktree root after installation:

```sh
python3 -B benchmark/test_heldout_families.py
```

Archive exact argv, start/end status, source hashes and stdout/stderr under a fresh `validation/*-attemptNN` prefix; retain failed attempts. No test launches the native benchmark binaries. First validate the mocked fixture interoperability and all count/schema claims; these have only been reviewed as source so far. Then obtain independent review, recheck fresh-seed nonreuse, install study-specific private power-log ignore rules and commit the preparation. The parent full checker must pass before generating a new freeze.

Planned preflight (no native solver calls):

```sh
python3 -B benchmark/run_heldout_families.py preflight \
  --parent-freeze benchmark/results/compressed-query-2026-10-15/freeze.json \
  --manifest benchmark/results/heldout-families-2026-10-15/manifest.csv \
  --protocol benchmark/results/heldout-families-2026-10-15/PROTOCOL.md \
  --freeze benchmark/results/heldout-families-2026-10-15/freeze.json
```

Commit the resulting freeze and final protocol before capture. The following command is **not released**; it belongs to the root's later quiet serial timing window:

```sh
python3 -B benchmark/run_heldout_families.py capture \
  --freeze benchmark/results/heldout-families-2026-10-15/freeze.json \
  --output benchmark/results/heldout-families-2026-10-15/heldout.csv \
  --released
```

After all owned groups are known empty and timing completes, planned strict analysis:

```sh
python3 -B benchmark/run_heldout_families.py analyze \
  --capture benchmark/results/heldout-families-2026-10-15/heldout.json \
  --output-dir benchmark/results/heldout-families-2026-10-15/analysis
```

Optional `--power-log PATH` correlates an independently archived private log without copying raw private events into the analysis. It does not certify active sleep inhibition or log coverage. Raw evidence and analysis directories refuse overwrite; preserve rejected attempts separately.

Expected outputs: 72 children; 3,024 checked rows (2,592 timed, 432 warmups); 4,320 clock-specific ratio pairs; 360 case/720 graph comparison summaries; 432 case/864 graph absolute summaries; 180 point classifications; all 450 measured endpoint pairs and 30 crossover summaries. Both clocks, all five comparators and all six sizes remain included. No historical data is pooled.
