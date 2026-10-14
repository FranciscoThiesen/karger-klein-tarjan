# Further attachment search: mechanism-led choices

These are prospective suggestions after reading `ATTACHMENT_PROTOCOL.md`, not selections from holdout data. The declared 80-case pilot remains unchanged. No attachment code, numerical model, benchmark or visualization was executed to prepare this note.

## What the existing matrix should resolve

Write `q=n/b`, `B=n(d-1)+1`, and `U=(q-1)(q-2)/2`. For either dyadic weight mode, the shortcut occupancy of a nonadjacent pair of core blocks of size `s` is controlled approximately by

```
lambda = B*s*s/U ~= 2*b*b*(d-1)*s*s/n.
```

This is a mechanism parameter, not a runtime predictor. A fourfold increase in `n` roughly adds one core halving before quotient-pair collisions become substantial. The existing 16K→64K→256K→1M ladder therefore spans about three additional potentially expensive compactor scans. Increasing `b` from 4 to 16 removes roughly two such scans while reducing root verifier vertices fourfold. Both pilot block sizes are justified; neither is guaranteed superior.

The `b=16,d=16` smallest pilot core is already fairly dense: `q=1024,E=246784` of `523776` possible core pairs. Its rapid early edge collapse is a finite-size property of this fixed family. A subsequent crossover could arise from delayed parallel-edge collisions as `n` increases. It should not be described solely as a cache threshold or generic linear-versus-logarithmic crossover.

The core-only `shuffled` control is essential. It preserves initial star reduction while removing the dyadic ordering. A hierarchy/distance advantage over this control would support the slow-core-merging explanation. Comparing only with global-random weights would confound that mechanism with the first contraction.

## Justified extensions after discovery

1. **Continue the same families to 2M and 4M vertices.** At either declared density these stay within the 4M-vertex/134M-edge limits (`d=16,n=4M` uses 64M edges). Relative to 1M, this adds only about half and one extra near-full core scan, respectively. It is a meaningful but modest escalation, not a prediction of a dramatic gain. Freeze the extension before running it, keep both points and all comparators, and do not omit an unfavorable intermediate point when choosing the two largest confirmation sizes.

2. **Bracket an all-winning small end with feasible smaller instances.** The following prospective points can distinguish an observed crossover from a range whose onset was never measured:

   | Family parameters | Smaller useful dyadic points below 16K | Absolute smallest feasible n |
   |---|---|---:|
   | b4,d2 | 4,096; 1,024; 256 | 64 |
   | b16,d2 | 4,096; 1,024 | 1,024 |
   | b4,d16 | 4,096; 1,024; 512 | 512 |
   | b16,d16 | 8,192 only | 8,192 |

   Below those minima the requested connected simple core does not exist. If the family wins at its smallest feasible point, report an all-winning observed range; do not change its definition to manufacture a smaller loss. Very small calls can also have substantial relative timing noise, so any claimed crossing still needs the declared graph/seed confirmation.

3. **Interpolate with b8, rather than immediately escalating to b32/64.** This gives a direct intermediate point in the verifier-vertex-versus-edge-retention tradeoff. At `d=2/16`, first retention is 56.25%/94.53125%; minimum feasible dyadic `n` is 256/2,048. It requires a separately declared fixture extension, its paired controls and a fresh source revision. It is useful if the b4/b16 results indicate opposing costs, not as an unrestricted parameter sweep.

4. **Interpolate density with d4.** First retention is 81.25% for b4 and 76.5625% for b16, between the pilot's sparse and dense cases. Minimum feasible sizes are 128 and 2,048. This may balance full-edge sorting cost against filtering opportunity better than either endpoint. A d4 result must be a separate discovery group, not pooled with d2 or d16.

5. **Consider a fixed sparse core degree if comparison with all four algorithms remains the goal.** A core with `c*q` edges gives total `m=n+(c-1)q`. The natural `c=4` case matches the previously investigated sparse leaf/core mechanism more closely than `m=16n`: density is `1+3/b`, and the first quotient retains `4/(b+3)` of all edges (about 57.1% at b4, 21.1% at b16). Dyadic ordering can add repeated core scans while maintaining the sparse total edge list. For fixed b and c>1, `B=(c-1)q+1` is still Theta(n), so the ideal compactor lower-bound mechanism survives. This changes the edge-budget parameterization: it needs a clearly named new family/schema, exact displayed `m`, and separate comparison against its shuffled-core/global-random controls. Never label it `density=2` or substitute it for the declared cases.

Large b is not an automatic escalation. It leaves fewer variable core MST edges, speeds parallel-edge elimination, and makes the output's `n-1` IDs and first root pass an increasingly large fixed cost. At d1 there is only one core shortcut, so the repeated-heavy-background lower-bound argument disappears. A fast d1 result would be a valid observation but would not explain an asymptotic filtering advantage.

## What the endpoint pairing can and cannot distinguish

For hierarchy, distance and shuffled-core weights, center versus random-clone endpoints has identical original weights/ID order, first selected IDs, first physical quotient and subsequent algorithmic inputs. KKT and the repeated compactor should therefore have identical registered work counters. This makes the pairing a useful test of constants that those counters do not measure:

* **First contraction:** endpoint accesses, conditional minimum updates and memory locality differ. Global label permutation means centers are not a packed low-index array, so a q-sized center set must not be casually equated with a contiguous q-sized cache footprint.
* **Kruskal:** the sorted weight/ID sequence and union success pattern agree. Leaf endpoints add parent traversals and can change union-find locality; these costs are not sorting improvements.
* **Prim:** center edges target only q core centers. Random-clone edges can maintain external candidates for many different clones in an unvisited block, increasing queue activity even though cheap local stars are eventually exhausted before the next expensive inter-block edge. This is an algorithmic constant difference, not a different MST objective.
* **Original Boruvka:** it repeatedly reads original endpoint component labels and traverses the selected original forest. Its component partitions match across endpoint modes once stars collapse, while memory accesses and DFS shape can differ.

Identical suffix inputs do not force identical suffix wall time: the first pass can leave different cache state, and allocator/system effects remain. Counter equality plus timing differences identifies missing hardware/operation detail, but does not by itself assign a precise fraction of time to a cache or branch cause. Avoid adding a first-pass subtraction benchmark and treating that subtraction as exact attribution without an independently declared profiling experiment.

All of these families are engineered weighted stress tests. A successful construction establishes a reproducible useful class for these implementations; it does not establish that most application graphs have the same weight ordering, or that KKT dominates every larger instance.
