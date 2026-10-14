# Attachment work-analysis validation

The helper passed `python3 -B benchmark/analyze_attachment_work_test.py`:
11 test groups, all 16 archived native diagnostic records, their complete smoke
timing capture, and malformed schema/counter/trace/certificate/provenance
mutations. The smoke integration uses an explicitly synthetic temporary
manifest; it is a parser test and creates no new native capture evidence.
The command, output and source hashes are archived beside this file.

The subsequent real 16-record work capture was joined with:

```sh
python3 -B benchmark/analyze_attachment_work.py --repo-root /Users/random_person/Desktop/karger-klein-tarjan --timing-csv benchmark/results/search-2026-10-13/attachment-timing.csv --work-manifest benchmark/results/search-2026-10-13/attachment-work/capture.json --output-dir benchmark/results/search-2026-10-13/attachment-work-analysis
```

Result: **PASS, 16 records and 254 compactor rounds**. All selected cases match
their complete timed counterparts by both fingerprints, dimensions/seeds and
required native source hashes. Outputs retain every selected record, all
registered counters, raw/build/helper hashes, model expectations and signed
observed deviations. The joiner verifies existing native certificate markers;
it does not reconstruct the graph or independently recertify the MST from
`search_work_v1`, which lacks original edge tuples.

Scientific figures were generated with:

```sh
python3 -B benchmark/plot_attachment_work.py --analysis-dir benchmark/results/search-2026-10-13/attachment-work-analysis --output-dir benchmark/results/search-2026-10-13/attachment-work-figures
```

Result: **PASS, four PNG/SVG figure pairs and all 16 records retained**. Each PNG
was opened for visual QA; the result is documented in the figure directory.
The plot helper verifies the analysis's derived-file hashes before reading its
tables. Figures contain only logical work/edge counts, without timing fits.

No native binaries, benchmarks or timing runs were launched by this validation
and plotting work. The parent agent separately owns the instrumented work
capture recorded in `attachment-work/capture.json`.
