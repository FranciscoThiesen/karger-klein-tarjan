# Paired half/eighth figure preparation

Source only; no import, syntax check, synthetic plotting check, rendering or partial timing analysis has run. New [plot_eighth_sampling.py](../../../plot_eighth_sampling.py) adapts the validated packed-sampling plotter and reuses the immutable retention-control style helpers. It does not edit frozen sources, helpers or native artifacts.

After root releases postcapture work and strict plus independent numerical audits pass, the script strict-loads all 48 children/2,016 outputs and draws **ten figures, thirty panels**: both clocks for all-six eighth/half comparisons, each policy's all-five KKT comparisons, and each policy's all-six absolute solver times. Both sizes of all three family/density groups remain. Every point pools 24 paired ratios or durations; four faint markers retain six-trial graph/sampler realization medians, and every trial-range endpoint is included. Wall/CPU figures share panel bounds. KKT labels are neutral, legends explicit, and ratio captions distinguish parity/10% lead from a strong observed crossover.

The plotter saves all canonical tables, including 30 exact rational-derived crossover classifications, in plotted_values.json. It verifies all endpoints are in bounds, all thirty panels are present and all input/output hashes; SVG/PDF counterparts accompany PNGs. Repetition does not create new graphs/forests; four crossed realizations use two graphs. There are no confidence intervals, control normalization, historical pooling or interpolated thresholds. Different acceptance rates can change subsequent recursion and RNG consumption; the verifier is compressed in both policies.

Only after release, using a fresh output attempt:

```sh
/usr/bin/python3 -B benchmark/plot_eighth_sampling.py \
  --capture benchmark/results/eighth-sampling-2026-10-15/paired.json \
  --output benchmark/results/eighth-sampling-2026-10-15/figures-attempt01 --released
```

Run through the same exclusive bounded receipt wrapper used for the audit. Inspect **all ten PNGs at original resolution** and record independent visual QA before publication. The slightly taller caption/new policy labels require actual inspection; source review is not visual approval. If layout changes are needed, preserve the entire original attempt and exact plot source before rerendering.

Prepared source SHA-256: `5b044b15bd422a92d434b67b301c87f2c7a2e422622a9d534ead16ca233c1b66`.
