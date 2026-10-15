# Independent audit preparation — not executed

`independent_numerical_audit.py` is prepared during the serial native capture.
It has not been imported, syntax-checked, tested or executed. It imports only
Python standard-library modules and never imports a collector or aggregator.
The frozen collector, native files and protocol remain untouched.

After root explicitly releases nonperformance work and strict analysis exists,
run from `/Users/random_person/Desktop/kkt-packed-sampling`:

```sh
python3 -B benchmark/results/packed-sampling-2026-10-15/validation/independent_numerical_audit.py \
  --capture benchmark/results/packed-sampling-2026-10-15/paired.json \
  --analysis-dir benchmark/results/packed-sampling-2026-10-15/analysis \
  --output-dir benchmark/results/packed-sampling-2026-10-15/validation/independent-numerical-audit
```

Archive the exact invocation, exit status, source hash and stdout/stderr using
fresh attempt-numbered files. Preserve failures; the script refuses to overwrite
an existing audit output directory. Its outputs include exact numerator and
denominator columns for ratios, all medians and ranges, plus a concise review.

It independently reconstructs 48 children, 2,016 outputs, 1,728 cross-variant
clock pairs and 2,880 within-variant comparator pairs. All 3,024 medians cover
case, four crossed realizations, two graph marginals and two sampling marginals,
including absolute durations. All 30 prespecified crossover classifications use
exact rational predicates on both clocks. It rereads declared artifact hashes,
raw certificates, graph identities across variants/samplers, four topology twins,
clock flags, resource/group-exit records and exact raw/combined concatenation.
The audit supplements the frozen strict collector's full build-recipe proof;
it does not make an independent power or sleep-prevention claim.
