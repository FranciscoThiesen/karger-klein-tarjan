# Prospective seed declaration scan

Before writing this package, a source/declaration-only scan found no exact
numeric-token matches for graph seeds `17000011`, `17000047` or sampler seed
`2801` in the seven existing study worktrees below. `rg` returned exit status
1 (no matches). No partial eighth timing files or raw performance CSVs were
read to choose these seeds.

```sh
rg -n -P '(?<![0-9])(17000011|17000047|2801)(?![0-9])' \
  /Users/random_person/Desktop/karger-klein-tarjan \
  /Users/random_person/Desktop/kkt-contraction-experiment \
  /Users/random_person/Desktop/kkt-retention-control \
  /Users/random_person/Desktop/kkt-edge-verifier-view \
  /Users/random_person/Desktop/kkt-packed-sampling \
  /Users/random_person/Desktop/kkt-compressed-queries \
  /Users/random_person/Desktop/kkt-eighth-sampling \
  -g '*.py' -g '*.md' -g '*.cpp' -g '*.hpp' \
  -g 'manifest.csv' -g 'freeze.json'
```

This is scoped evidence of fresh **declared** seeds in searched source and
protocol files, not a claim that no external or unrecorded invocation ever
used these numbers. The new declaration naturally introduces matches. Before
any future freeze, check for independent intervening declarations while
excluding this package's own copies; do not replace a seed based on outcomes.
