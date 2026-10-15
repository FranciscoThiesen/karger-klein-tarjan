# Prospective seed checks

Before these new sources were installed or executed, source/declaration scans
in `/Users/random_person/Desktop/kkt-eighth-sampling` found no prior declared
use of graph seeds 23000003/23000029 or sampler seed 3407. The new files remain
under `/tmp`, outside the scanned worktree. Commands inspected text only:

```sh
rg -n --max-columns 350 --max-columns-preview '23000003|23000029|\b3407\b' benchmark docs \
  --glob '*.py' --glob '*.cpp' --glob '*.hpp' --glob '*.md' --glob '*manifest.csv' \
  --glob '!**/figures*/**' --glob '!**/analysis*/**' --glob '!**/distance_cases/**'
rg -n --max-count 1 --max-columns 500 \
  '(graph_seed|kkt_seed|sampling_seed)[" :]+(23000003|23000029|3407)([^0-9]|$)' \
  benchmark/results --glob '*.log' --glob '!**/*power*/**' \
  --glob '!**/current-complexity-2026-10-15/**'
```

Both scoped searches returned no matches (rg exit1). An earlier overly broad
numeric search also searched arbitrary raw graph IDs and private power-log UUID
fragments; those incidental numeric occurrences do not establish seed use and
were not used as freshness evidence. The accepted checks concern source,
declaration and archived certificate seed fields, not every arbitrary number
on the machine. The active Google study is excluded from archived-log reading;
its seed declarations are already covered by source text. No durations or
partial active timings informed this matrix. Recheck the same declaration
scope, excluding this new package, before its eventual prospective freeze.
