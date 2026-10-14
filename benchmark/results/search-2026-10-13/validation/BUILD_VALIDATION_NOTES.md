# Deferred build/CLI validation and wrapper smoke

`validate_attachment_build.py` is a standard-library source draft whose native
validation entry point has not been executed.
It validates already-built binaries and never invokes a build or a valid
benchmark case. Its output directory must be new; logs from unsuccessful CLI
checks, timeouts, interruptions and partial validation are preserved.

After integration and the scheduled build, run from the repository root:

```
python3 /tmp/kkt-core-attachments/validate_attachment_build.py \
  --output-dir benchmark/results/search-2026-10-13/attachment-build-validation \
  --build-log <archived-build-log>
```

The defaults inspect `bin/mst_search` and `bin/large_stack/mst_search`; explicit
`--normal-binary`, `--large-binary` and `--root` arguments are also accepted.
The validator requires thin native arm64 Mach-O executables, checks normal
stack zero versus 536,870,912 bytes, and compares the actual bytes of the full
`__TEXT,__text` section. It records complete binary hashes, source and Makefile
hashes, the six Python helper hashes, production object hashes, the validator
source, and all command output hashes. Identity of executable instructions is
not identity of all data sections and does not replace archived build commands.

Both binaries receive all invalid CLI checks. These include every one of the
sixteen attachment family names with an independently impossible core capacity,
unsupported names, malformed protocol/seeds/dimensions, and old fixture-domain
regressions. Every rejection must occur before the native `Running ...` marker
and produce no timing CSV. Valid-capacity correctness and exact maximum-count
acceptance belong to the separate fixture test; this driver does not allocate
a huge graph to test a cap.

`attachment-smoke.csv` contains all sixteen families at `n=1024,m=2048,p=0`.
Both block sizes are feasible: `b=4` gives `q=256,E=1280`, while `b=16` gives
`q=64,E=1088`. Use it only after the validator and independent fixture tests:

```
python3 benchmark/run_mst_search.py \
  --binary bin/large_stack/mst_search \
  --manifest /tmp/kkt-core-attachments/attachment-smoke.csv \
  --graph-seeds 17 --sampling-seeds 0 --repetitions 5 --warmups 1 \
  --output <new-smoke-output.csv>
python3 benchmark/analyze_mst_search.py \
  --timing-csv <new-smoke-output.csv> --output-dir <new-smoke-analysis-directory>
```

Archive/copy the manifest to its permanent evidence location before running the
wrapper so the captured path is durable. Expected smoke counts are 400 timed
calls, 80 checked warmups, and 640 wall/CPU paired ratios. This is integration
evidence only; its timings do not establish a practical family crossover.

No command above has been executed as part of preparing this draft. After the
root released Python-only checks, import/syntax validation and a synthetic
Mach-O parser check passed: normal/large text identity and distinct stack
fields were accepted, and seven malformed header/architecture/section cases
were rejected. `python_source_validation.json` binds these outcomes to source
hashes. The driver contains 43 negative CLI cases per binary, so its later
native execution should perform 86 rejection checks plus two help checks.
