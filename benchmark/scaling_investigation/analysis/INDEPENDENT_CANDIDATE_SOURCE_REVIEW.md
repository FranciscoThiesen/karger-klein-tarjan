# Independent candidate-analysis source review

PASS, source-only review; no imports, tests, captured-data analysis or native
execution by this reviewer.

- `analyze_candidate.py`: `ac982d24ea72149aaa33abd04fafb1b2b5eeb1b972e6c4ba4f05178a0c16cf11`
- `test_analyze_candidate.py`: `25f82ec4f9295656cd017d86de1ce1888b7f30131f28d11f2ac2550c2738e59f`
- `CANDIDATE_ANALYSIS.md`: `ff33b089b58307ce72cd6b44aedd096090901a27459f3f3e934a41a84acc7b4f`

The loader checks and binds the candidate source before importing its strict
provenance validator, then independently enumerates the complete case/policy/
repetition matrix. Fresh timing retains 108 pairs per clock, both graph medians,
all wins/losses/ties and paired medians separately from ratios of medians. The
three-policy control includes each intended comparison direction.

The 96 custom zero-intercept N/NlogN fits and 1,152 residuals have consistent
18-call/six-mean counting, scaled least squares and mean-normalized RMS. They
are explicitly numerical reanalysis rather than library-emitted BigO output.
All 4,680 work-field comparisons require the single initialization delta; phase
means include outside-collector time and exact additive checks. Allocation
tables distinguish cumulative quantities from live peaks and leave zero ratios
undefined. The eight prepared synthetic groups exercise independent identities,
Fraction ratios, linear fits, losses, zeros, phase additivity and allocation
labels. Their execution and actual capture reloads remain separate gates.
