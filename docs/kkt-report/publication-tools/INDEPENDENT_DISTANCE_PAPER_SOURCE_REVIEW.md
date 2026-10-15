# Independent distance paper adapter source review

Reviewer: `/root/experiment_design`, 2026-10-15. **Source review PASS; no
blocking defect found.** No module was imported, no tests/figures/native jobs
were run, and no partial distance timing was read. This is not visual QA.

Reviewed sources:

- `plot_distance_paper.py`: SHA256 `f1dd86f18e45579a847950716bb187969f246572415560e5c48e64cb63c5bd51`
- `DISTANCE_PAPER_PREPARATION.md`: SHA256 `cb611c39a84148b1a6005a6ff55dffac55074068817be01187ae4bd5e3d67c47`

Cross-checked the installed `benchmark/plot_eighth_distance.py` preparation API
and independent numerical audit source/schema. The new adapter requires the
completed strict 24-child/1,008-output capture and a matching independent audit,
rehashes the original standalone inputs/outputs, and exactly compares all
raw-derived canonical tables before presentation. It retains the 60 point,
150 bracket and ten outcome tables without interpreting partial results.

The 264 plotted case/solver/clock summaries comprise 120 paired-ratio summaries
and 144 absolute-time summaries. Both graph medians (528 values) and both trial
range endpoints (528 values) are retained. Complete identities are checked
before and after drawing; all five comparator ratios and all six absolute
series remain. Wall and CPU family-specific axis bounds are matched, and all
observed plotted endpoints must lie within those bounds.

The four figures use the declared 7.1-by-8.8-inch canvas, two vertically stacked
family panels, six explicit size labels, minimum 8.5pt tick/legend/caption type,
and source-consistent private-eighth KKT labels. No normalized control timing,
historical pooling, confidence interval, or interpolated crossover is introduced.
Exclusive outputs preserve failure artifacts and remain pending visual QA.

Runtime/data binding tests, actual standalone/paper rendering, all four PNG
reviews (especially the final two size labels, right edge and legend/caption
separation), and final PDF physical-size/page QA remain future gates.
