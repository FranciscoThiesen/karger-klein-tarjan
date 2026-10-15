# Independent source review of the hierarchy explanations

**Source-only PASS, 2026-10-15.** Reviewer: `multigraph_candidate`. This
review ran no imports, checks, mathematics scripts, native programs or plots,
and read no partial larger-screen timings. It does not replace the deferred
enumeration checks, execution validation or visual inspection.

Reviewed `benchmark/plot_hierarchy_retention.py`,
`HIERARCHY_EXPECTATION.md`, the existing hierarchy-retention derivation and
the generator's path/chord tier construction. The aligned-block internal-pair
count, expected crossing volume and cumulative closed form agree. Including
the star input and core inputs at b=1,2,4,...,q/2 gives 15, 19 and 21 calls:
55 data rows and 110 plotted points across two panels. The proposed independent
enumerations cover 18 pair partitions and 10 fixed-chord-count ensembles
(1,592 subsets); these counts were checked by hand, not executed. The exact
vertex/edge shrinkage fractions and distinction between sampled-edge volume
and the expected light-edge bound are correct. No shuffled-family formula or
runtime prediction is implied. The requested wording clarification was
subsequently applied: the note and caption explicitly spell the block
sequence `1,2,4,...,q/2`. No formula or code path changed in that follow-up.

Also reviewed the source-only note `/tmp/kkt-sampling-breaks-hierarchy.md`.
With isolated vertices retained in the counting universe, its identities
`C_F=q-c_H-S`, `p E[Y]=q-E[c_H]` and
`E[Y-(q-1)]=E[C_F]/p` are correct under independent sampling and distinct
weights. The connectivity-conditioning caveat is necessary and correctly
stated. The eight-vertex witness has 28 edges, retains 10 after filtering,
and permits three full-graph versus two sampled-graph Boruvka rounds. This
demonstrates possibility, without establishing typicality or a timing gain.
The distinction between disruption in the sampled branch and preserved
dyadic partitions in the filtered branch is sound. The special all-cheap-path
argument is appropriately withheld from `leaf_distance4`.

No blocking source, formula, counting or claim-scope issue was found.
