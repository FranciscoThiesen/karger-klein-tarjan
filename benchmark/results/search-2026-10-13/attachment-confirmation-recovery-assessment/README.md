# Numerical assessment after the declared recovery

A completed its frozen execution. Original B failed; its 60 completed native children are combined only with the separately declared remaining 12 recovery children. The original B capture and controller remain failed. This assessment concerns the numerical rule, not successful execution of the original protocol. Monitoring changed for the recovery and broad B disturbance remains a limitation. A and composite B are retained separately. Ratios are paired within each graph, sampling seed and repetition, then medians are taken over repetitions, sampling seeds and graphs. They are not ratios of separate runtime medians.

The declared advantage rule requires a paired case median ≤0.90 and every graph median <1 at both 1,048,576 and 2,097,152 vertices, in both campaigns and on both wall and process-CPU clocks. Onset is reported separately; a 10% advantage does not by itself establish a parity crossing.

| Family | Competitor | Upper-size rule | Smaller loss/tie in each campaign/clock | Observed adjacent parity bracket in each |
|---|---|---|---|---|
| leaf_hierarchy4 | compacting_boruvka | PASS | yes | yes |
| leaf_hierarchy4 | kruskal | FAIL | yes | no |
| leaf_hierarchy4 | prim | FAIL | yes | no |
| leaf_hierarchy4 | boruvka | FAIL | yes | no |
| leaf_distance4 | compacting_boruvka | PASS | yes | yes |
| leaf_distance4 | kruskal | FAIL | yes | no |
| leaf_distance4 | prim | FAIL | yes | no |
| leaf_distance4 | boruvka | FAIL | yes | no |

## Campaign A

1,800 timed calls and 360 checked warmups; 0 flagged calls retained. Capture/child UTC flags are preserved in assessment.json.

| Case | Clock | Compactor | Kruskal | Prim | Original Borůvka |
|---|---|---:|---:|---:|---:|
| leaf_distance4_n1048576_d16_p0 | wall | 0.841600 | 3.662724 | 2.182523 | 1.935220 |
| leaf_distance4_n1048576_d16_p0 | cpu | 0.841597 | 3.662261 | 2.182521 | 1.934982 |
| leaf_hierarchy4_n262144_d16_p0 | wall | 0.979178 | 2.291848 | 2.438904 | 1.889751 |
| leaf_hierarchy4_n262144_d16_p0 | cpu | 0.979180 | 2.291853 | 2.438913 | 1.889741 |
| leaf_shuffled4_n2097152_d16_p0 | wall | 0.983319 | 3.896082 | 2.680150 | 2.858066 |
| leaf_shuffled4_n2097152_d16_p0 | cpu | 0.983319 | 3.896055 | 2.680138 | 2.858077 |
| leaf_distance4_n262144_d16_p0 | wall | 0.987627 | 2.304426 | 1.750625 | 1.887661 |
| leaf_distance4_n262144_d16_p0 | cpu | 0.987625 | 2.304431 | 1.750623 | 1.887660 |
| leaf_hierarchy4_n65536_d16_p0 | wall | 1.210162 | 1.496621 | 1.856939 | 1.588910 |
| leaf_hierarchy4_n65536_d16_p0 | cpu | 1.210139 | 1.496623 | 1.856871 | 1.588906 |
| leaf_hierarchy4_n524288_d16_p0 | wall | 0.882276 | 3.018247 | 2.922694 | 1.980349 |
| leaf_hierarchy4_n524288_d16_p0 | cpu | 0.882276 | 3.018055 | 2.922670 | 1.980365 |
| leaf_distance4_n2097152_d16_p0 | wall | 0.812233 | 4.092548 | 2.085755 | 1.729715 |
| leaf_distance4_n2097152_d16_p0 | cpu | 0.812233 | 4.092545 | 2.085759 | 1.729715 |
| leaf_random4_n2097152_d16_p0 | wall | 1.035935 | 3.302334 | 1.755119 | 2.641068 |
| leaf_random4_n2097152_d16_p0 | cpu | 1.035940 | 3.302328 | 1.755116 | 2.641061 |
| leaf_distance4_n524288_d16_p0 | wall | 0.890803 | 3.062982 | 2.111563 | 1.984888 |
| leaf_distance4_n524288_d16_p0 | cpu | 0.890802 | 3.062994 | 2.111585 | 1.984952 |
| leaf_hierarchy4_n1048576_d16_p0 | wall | 0.835514 | 3.664262 | 3.013437 | 1.953759 |
| leaf_hierarchy4_n1048576_d16_p0 | cpu | 0.835517 | 3.664254 | 3.013426 | 1.953759 |
| leaf_hierarchy4_n2097152_d16_p0 | wall | 0.815342 | 4.131089 | 2.789164 | 1.736129 |
| leaf_hierarchy4_n2097152_d16_p0 | cpu | 0.815343 | 4.131068 | 2.789124 | 1.736226 |
| leaf_distance4_n65536_d16_p0 | wall | 1.197777 | 1.449845 | 1.315875 | 1.541409 |
| leaf_distance4_n65536_d16_p0 | cpu | 1.197757 | 1.449838 | 1.315840 | 1.541409 |

## Interrupted B plus recovery

1,800 timed calls and 360 checked warmups; 149 flagged calls retained. Capture/child UTC flags are preserved in assessment.json.

| Case | Clock | Compactor | Kruskal | Prim | Original Borůvka |
|---|---|---:|---:|---:|---:|
| leaf_distance4_n65536_d16_p0 | wall | 1.204041 | 1.449056 | 1.320646 | 1.549412 |
| leaf_distance4_n65536_d16_p0 | cpu | 1.204028 | 1.449068 | 1.320625 | 1.549415 |
| leaf_hierarchy4_n2097152_d16_p0 | wall | 0.814883 | 4.124739 | 2.747483 | 1.782821 |
| leaf_hierarchy4_n2097152_d16_p0 | cpu | 0.814866 | 4.124781 | 2.798318 | 1.782814 |
| leaf_hierarchy4_n1048576_d16_p0 | wall | 0.828766 | 4.055106 | 2.967186 | 1.862335 |
| leaf_hierarchy4_n1048576_d16_p0 | cpu | 0.828783 | 4.055682 | 2.967224 | 1.862397 |
| leaf_distance4_n524288_d16_p0 | wall | 0.868735 | 3.620820 | 2.204479 | 2.074110 |
| leaf_distance4_n524288_d16_p0 | cpu | 0.868653 | 3.618429 | 2.204444 | 2.074896 |
| leaf_random4_n2097152_d16_p0 | wall | 1.035169 | 3.549764 | 1.532357 | 2.529370 |
| leaf_random4_n2097152_d16_p0 | cpu | 1.035158 | 3.549699 | 1.532474 | 2.529413 |
| leaf_distance4_n2097152_d16_p0 | wall | 0.860366 | 5.032710 | 1.630586 | 1.616108 |
| leaf_distance4_n2097152_d16_p0 | cpu | 0.859479 | 4.974375 | 1.578043 | 1.641551 |
| leaf_hierarchy4_n524288_d16_p0 | wall | 0.887746 | 4.835742 | 2.416487 | 1.828774 |
| leaf_hierarchy4_n524288_d16_p0 | cpu | 0.879162 | 4.707907 | 2.385202 | 1.868948 |
| leaf_hierarchy4_n65536_d16_p0 | wall | 1.105695 | 1.758695 | 1.891640 | 1.683605 |
| leaf_hierarchy4_n65536_d16_p0 | cpu | 1.104772 | 1.758097 | 1.892436 | 1.684677 |
| leaf_distance4_n262144_d16_p0 | wall | 0.907205 | 2.960996 | 1.958865 | 2.092754 |
| leaf_distance4_n262144_d16_p0 | cpu | 0.906997 | 2.960804 | 1.959086 | 2.092212 |
| leaf_shuffled4_n2097152_d16_p0 | wall | 0.992436 | 4.293670 | 2.273762 | 2.539421 |
| leaf_shuffled4_n2097152_d16_p0 | cpu | 0.992965 | 4.226203 | 2.242736 | 2.542139 |
| leaf_hierarchy4_n262144_d16_p0 | wall | 0.874608 | 2.584201 | 2.460652 | 1.917170 |
| leaf_hierarchy4_n262144_d16_p0 | cpu | 0.874517 | 2.580743 | 2.457116 | 1.920456 |
| leaf_distance4_n1048576_d16_p0 | wall | 0.820171 | 4.072321 | 1.991785 | 1.845100 |
| leaf_distance4_n1048576_d16_p0 | cpu | 0.821210 | 4.062572 | 2.001912 | 1.838814 |

## Matched topology at the shared control size

At n = 2,097,152 and m = 16n, all four leaf families are checked together for each graph seed in each campaign. Matching captured topology/order fingerprints corroborate the generator's weight-intervention invariant; these finite noncryptographic fingerprints are not a proof of graph identity.

| Campaign | Graph seed | All four topology fingerprints equal | All four weighted fingerprints distinct |
|---|---:|---|---|
| A | 1000039 | yes | yes |
| A | 1000081 | yes | yes |
| A | 1000099 | yes | yes |
| B | 1000039 | yes | yes |
| B | 1000081 | yes | yes |
| B | 1000099 | yes | yes |

Distinct weighted fingerprints are reported from the captured data, not assumed for every seed: randomized ranks can in principle coincide and a finite fingerprint can collide. Equality is retained and flagged for review; it is not silently treated as a proven identical weighted graph or discarded.

Leaf-mode star spokes remain forced MST edges even under global-random weights because their outer endpoints have degree one. Ordered and shuffled-core modes put all local spokes below all core edges, so the first round forms exactly the star blocks. Global random retains the forced spokes but may also select core edges in that round and merge multiple blocks.

All 12 cases, including shuffled-core and global-random controls, all four competitors, all individual paired ratios and every call-clock diagnostic are retained in the accompanying CSVs. No clock flag causes exclusion or adjustment. B repeats A's graphs; it is not a new independent graph sample.

assessment.json gives each of the eight upper-size checks per family/comparator and all adjacent measured parity/10% brackets separately by campaign and clock. Brackets are between tested points, not fitted transition locations. A parity crossing and meeting the 10% threshold are different observations. There are no confidence intervals, statistical-significance claims, pooled campaigns, extrapolation above the tested range or claims about all graph instances.

This assessor rereads the completed A capture, independently validates all 60 interrupted-prefix children, validates the 12-child recovery through its separate strict adapter, and independently recomputes the paired aggregation. The original strict assessor continues to reject failed B. Scoped power audits for A, the interrupted prefix, and the recovery tail are retained separately, with no row corrections or exclusions. Source, frozen plan, raw and derived hashes are in provenance.json.
