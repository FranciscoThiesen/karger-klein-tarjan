# Independent source review — PASS, execution deferred

Reviewed by `/root/multigraph_design` on 2026-10-15 during the eighth-sampling
performance hold. This was source and upstream-document inspection only:
no import, build, test, local library installation, solver invocation or
partial timing read. PASS is **not** compilation or performance validation.

| File | Reviewed SHA-256 |
|---|---|
| `current_complexity.cpp` | `ccc746954240cb7432cf137357b32f077994729df6fa01e092aadec1f53629a4` |
| `DESIGN.md` | `aa085c47e0da1b0f0ce1c7979d10b5f8f75592c6f70d853bdb816bda0edb4a7f` |
| `BUILD_PLAN.md` | `82fc571e806897cb7a1e303dbcf00e18aaf6d74524baed29eba28ad81dd3fb56` |

One issue was corrected during review: after a callback error, Google
Benchmark would continue invoking later callbacks and the driver originally
continued generating/solving them. The first statement in `run_size` now
rejects an already-failed context before graph generation, invocation counting
or a solver call. `SkipWithError` records those callbacks as errors and the
final whole-process checks reject the incomplete campaign. A later smoke gate
should demonstrate this with an injected failure, not only inspect the guard.

The timing lifetime is consistent by source. Setup, certified reference and
one checked warmup precede State loop entry. The manual interval includes
tuple conversion, solver and temporary-input destruction. The returned ID set
stays alive until after PauseTiming; equality checks, trace I/O and destruction
occur while paused, then ResumeTiming runs before loop continuation. Graph and
reference destruction happen after the loop timer stops. Error handling stops
an active timer through SkipWithError. These contracts match the pinned
[State implementation](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/benchmark.cc).
The separately recorded process-CPU envelope differs slightly from the
library's CPU interval, as the design explicitly states.

The pinned [registration implementation](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/benchmark_register.cc)
permits MeasureProcessCPUTime with UseManualTime and retains explicit Arg
insertion order. The [runner](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/benchmark_runner.cc)
accepts explicit iteration counts without adaptive calibration and appends
each successful repetition to the fit inputs. Counts check independently:
24 curves × 11 sizes × 3 callbacks = 792 callbacks/certificates; two timed
calls and one warmup each give 1,584 timed plus 792 warmup rows. Each curve
supplies 33 two-call means and one BigO/RMS pair, not eleven median timings.
Exact JSON rendering/schema remains an actual-library gate.

The [v1.5.2 fit source](https://raw.githubusercontent.com/google/benchmark/v1.5.2/src/complexity.cc)
supports the stated six-model, zero-intercept least-squares interpretation:
coefficient Σ(tg)/Σ(g²), RMS normalized by mean observed time. Its automatic
choice uses CPU measurements and fits manual/real values to that same chosen
model. Strict improvement chooses a replacement model; tie ordering matters
to future exact reconstruction. It does not minimize uniformly weighted
pointwise relative residuals, despite an imprecise source comment. Independent
fits of raw CPU and steady times remain separate from the library output.

`N=n+m` comes from actual generated edge count; family-specific density stays
fixed within each curve. The n=1,024 leaf/d32 boundary fits: q=256, m=32,768,
local=768 and core=32,000≤32,640 simple pairs. The proposal accurately limits
inference to finite windows and fixed graph/stream realizations, explicitly
retains ascending/descending and algorithm-block confounding, and makes no
new all-six ranking, probability expectation or asymptotic proof claim.

The new main's compile/link plan preserves the eight frozen production objects
and excludes the old main. The actual Google Benchmark source/library artifact,
build record, smoke gates, bounded outer controller, seeds, exact schema/fit
analyzer and freeze do not yet exist in this package. They must be completed
and independently checked before any performance release. No remaining source
blocker was found in this prepared scope. The reviewer owns no running jobs.
