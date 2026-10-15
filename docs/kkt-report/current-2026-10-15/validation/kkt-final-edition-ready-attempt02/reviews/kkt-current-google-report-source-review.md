# Google report insertion and acceptance checklist: source review

Source-only PASS for `kkt-current-google-report-integration.md` and
`kkt-current-google-postcapture-qa.md`. No results were populated, partial timing
data read, scripts imported or executed, or artifact hashes recomputed.

The insertion correctly distinguishes native steady/native process CPU from
library manual/library process CPU. The driver explicitly registers process
CPU and manual time; its manual measurement equals the native steady solver
interval, while library CPU includes a different benchmark timer envelope.
The v1.5.2 CPU-selected `oAuto` label is reused for the manual coefficient;
exported CPU RMS and independently reconstructed manual RMS are not conflated.
The upper-six minimum remains a custom restricted-window result.

Counts agree with the fixed sources: 24 curves, 264 curve-size instances,
792 callbacks/certificates, 2,376 calls (1,584 timed/792 warmups), 1,632 library
reports, 3,168 four-clock means, 1,152 model fits, 1,056 size summaries,
192 full/upper slopes, 960 adjacent slopes and 24 Google choices. The plots
retain 1,056 normalized points and 288 model cells. Full11 uses 33 two-call
means per curve/clock; upper6 uses 18, for n=32,768 through 1,048,576.

All three selected paper filenames match the installed v2 source. Its six
figures use 7.05-by-9-inch canvases and specified text at least 8.5 points,
without tight-bbox resizing. Original-resolution and assembled-page QA remain
required. The checklist accurately records the prior completed installation
and four mocked groups without proposing an unjustified rerun.

Collector, analyzer, independent arithmetic audit and standalone/paper CLI
arguments match their installed parsers. The older execution handoff is
explicitly treated as historical where launch/install status changed. No new
performance launch is implied. The arithmetic-audit scope is correctly limited
to means/fits/choices; summary/slopes/flags/ordinary aggregate independence is
not claimed. Reused realizations, graph/order confounding, all clocks/models,
finite-window limitations, resource qualifications and the actual 40-page gate
remain explicit. No blocking semantic, count, filename or command issue found.
