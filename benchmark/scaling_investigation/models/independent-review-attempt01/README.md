# Independent focused model review

PASS, 2026-10-15. This review launched no solver and imported neither analyzer.

Source review checked the duration-space least-squares objective, scale conversion, pointwise-relative weighting, fixed hinge mapping from n to N, rank-deficient train windows, whole-size train/test separation, residual SSE decomposition, and all four clock identities. The six small algebra tests cover nonzero/negative intercepts and singular hinges. No arithmetic blocker was found.

An independent standard-library calculation reread the 24 archived CSV/Google JSON pairs and checked all 3,168 means exactly. Centered closed-form affine regression checked all 192 full/upper curve-clock intercepts. Direct one-column least squares checked 192 N/NlogN final-three-size holdout errors. All agreed within stated floating tolerances; all 192 affine intercepts were negative, and NlogN beat N in all 96 final-three curve/clock comparisons. The command exited 0 in 0.497 seconds; it was a finite numerical script, with no native or detached child process.

The detailed result and input digests are in [review.json](review.json). This is not an independent recomputation of every hinge fit, every blocked fold or every summary. Those were source-reviewed. Original native lifecycle proof remains inherited from the completed study.

Required interpretation: these are retrospective blocked extrapolation checks on an already observed campaign, not blind prospective validation. Fixed hinges represent candidate size regimes, not measured cache capacities. Negative fitted intercepts do not support a positive constant-overhead explanation. Overlapping holdouts, repeated calls and sampler-irrelevant Boruvka labels are not independent graph replications. No statistical confidence or hardware cause follows from winning a model menu.

Reviewed artifact hashes:

- `PLAN.md`: `606d8d8c52a4c77ebe759ff0c2fe11480cbd7fb7120742fc4e37b0f18352b13b`
- `analyze_models.py`: `aaa6fa4c6b60ec40fdcd5c86e0f82b73b4d440621ae9c67a43c9d79fda180714`
- `test_analyze_models.py`: `3bb0e9d30f421d6dce04fcf1d496e57dc32ab474ef12cec1aa96732713ab0923`
- `attempt03/provenance.json`: `2891ec028e28cc687ebd1f31b914885e448e93ced85f59d2ba5c2adefd24e4cd`
- `independent-review-attempt01/review.json`: `59a2a2799c28ff6cfd298301ba150bd9c7e71d836055ff59de4c1402298586a3`
