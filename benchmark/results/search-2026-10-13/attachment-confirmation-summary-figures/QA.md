# Confirmation figure QA

All ten final PNGs were opened and inspected after native timing stopped: the two compact summaries and eight separate A/B-composite appendices (both clocks, paired ratios and five-solver runtimes). Titles, legends, axis labels, range bars and footer qualifications are readable without overlap or clipping. The final appendix layout leaves space between the lower x labels and legends. The first rendering is retained unchanged in `../attachment-confirmation-summary-initial-layout/`; only its appendix layout was superseded.

The compact figures distinguish all four series, label B as **B interrupted + recovery**, show parity and 0.90, and retain every observed A/B graph-median endpoint. Those bars are observed ranges of three graph medians, not confidence intervals. Discovery spreads are uniformly omitted in the compact view and retained in the complete copied data. Controls remain visible, including their losses.

The complete appendices retain all four families, all five solver runtimes and all four paired comparisons for A and composite B separately. Full individual-trial ranges determine the axes. The broad B wall-time ranges, including the approximately 805-second Prim observation and heavily disturbed shuffled case, remain visible; shared family axes consequently compress some A series. Process-CPU plots are separate evidence and do not establish a quiet host. No call is removed, adjusted or rerun by these helpers.

[Final bounded checks](../validation/composite-figure-caption-checks.json) passed the actual composite/assessment bindings, all 72 child bindings, seven malformed composite gates, five protocol negatives, selected/control coverage, and real/extreme graph and individual-trial range containment. The unchanged generic loader still rejects the composite schema. Synthetic malformed inputs were disposable tests, never benchmark observations.

[Output checks](../validation/composite-figure-output-checks.json) verified all generation artifact and input hashes and raw/derived copies. All 72 copied native CSVs contain 30 calls each; the complete composite has 2,160 calls. The explicitly incomplete failed combined B CSV has 1,770 calls (59 children); completed child 60 is retained through its own native CSV. The separate recovery combined CSV has 360 calls. The original failed capture/controller remain failed.

PNG visual QA is complete. SVG and PDF were generated but have not been separately rendered for format-specific QA; use the inspected PNGs in the report. This note does not claim browser QA of the interactive viewers.

The original generation-time README/provenance are retained as generation-README.md and generation-provenance.json. The current metadata records subsequent PNG inspection; no rendered image, input, timing or derived numerical table changed in this amendment. The output check binds the archived generation state.

A final caption-only review changed the compact figure sentence to explicitly say that B includes the interrupted prefix and declared recovery. Both compact PNGs were regenerated and re-opened; their axes, values and ranges are unchanged. The preceding six PNG/SVG/PDF bytes and prior provenance are retained in previous-caption/. All eight appendix image files are unchanged. The figure helper source hash was refreshed, and the bounded composite checks passed again.
