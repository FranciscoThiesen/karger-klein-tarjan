# Attachment logical-work and occupancy comparison

Validated 16 selected work records and 254 compactor rounds against 1 complete timing capture(s). Every selected fixture/seed matches both timed fingerprints and the required native source hashes. Campaigns remain separate; no times are pooled or inferred from work counts.

The occupancy column is an ideal random-subset expectation. A single observed graph need not equal it; signed differences are descriptive, not test failures or statistical residual scores. Controls have no dyadic occupancy prediction. Repeated sampling seeds are not additional graph draws.

| Case | Graph seed | KKT seed | Compactor volume/m | KKT volume/m | Model compactor volume/m | Sampling calls | Verifier incidence heavy fraction |
|---|---:|---:|---:|---:|---:|---:|---:|
| leaf_hierarchy4_n16384_d16_p0 | 5009 | 149 | 4.207745 | 2.824219 | 4.207282 | 13 | 97.7101% |
| leaf_hierarchy4_n65536_d16_p0 | 5009 | 149 | 5.120745 | 2.994527 | 5.120420 | 20 | 97.9514% |
| leaf_hierarchy4_n262144_d16_p0 | 5009 | 149 | 6.050346 | 3.129602 | 6.050528 | 28 | 98.2270% |
| leaf_hierarchy4_n1048576_d16_p0 | 5009 | 149 | 6.986520 | 3.249560 | 6.986155 | 31 | 98.3607% |
| leaf_distance4_n16384_d16_p0 | 5009 | 149 | 4.207745 | 2.810959 | 4.207282 | 16 | 97.7731% |
| leaf_distance4_n65536_d16_p0 | 5009 | 149 | 5.120745 | 2.991589 | 5.120420 | 23 | 97.9700% |
| leaf_distance4_n262144_d16_p0 | 5009 | 149 | 6.050346 | 3.129265 | 6.050528 | 33 | 98.2337% |
| leaf_distance4_n1048576_d16_p0 | 5009 | 149 | 6.986520 | 3.249319 | 6.986155 | 41 | 98.3554% |
| leaf_shuffled4_n1048576_d16_p0 | 5009 | 149 | 3.805032 | 2.933122 | n/a | 12 | 99.2069% |
| leaf_random4_n1048576_d16_p0 | 5009 | 149 | 2.857212 | 2.458840 | n/a | 7 | 99.7748% |
| community_hierarchy4_n1048576_d16_p0 | 5009 | 149 | 6.986520 | 3.249560 | 6.986155 | 31 | 98.3607% |
| community_distance4_n1048576_d16_p0 | 5009 | 149 | 6.986520 | 3.249319 | 6.986155 | 41 | 98.3554% |
| leaf_hierarchy16_n1048576_d16_p0 | 5009 | 149 | 5.100141 | 2.942395 | 5.100237 | 25 | 99.4868% |
| leaf_distance16_n1048576_d16_p0 | 5009 | 149 | 5.100141 | 2.946206 | 5.100237 | 32 | 99.4928% |
| leaf_hierarchy4_n1048576_d2_p0 | 5009 | 149 | 5.399806 | 2.807497 | 5.400090 | 34 | 81.0351% |
| leaf_distance4_n1048576_d2_p0 | 5009 | 149 | 5.399806 | 2.794679 | 5.400090 | 49 | 80.8398% |

Original round 1 consumes the expanded graph and contracts the cheap stars in ordered modes. Original round j>=2 is core round j-1, consuming blocks of 2^(j-2) core vertices. The terminal stored quotient has zero vertices/edges while the original partition has one component. [rounds.csv](rounds.csv) retains every observed round, its explicit indices, model expectation, signed difference and truncation budget. Budgets exclude floating-point roundoff and graph-sampling variation.

[summary.csv](summary.csv) keeps recursive volumes, materializations, initialized slots, sampling and verifier counts. Heavy fractions use recursive verifier input incidences, not distinct root edges; a zero verifier denominator is n/a. [counters.csv](counters.csv) retains the complete registered schema and checks its mixed-event proxy against the frozen registry. These event classes have different costs and cannot predict elapsed time by treating every unit equally.

[timing_links.csv](timing_links.csv) identifies every matching complete campaign without combining its durations. [models.json](models.json) archives complete model outputs; [provenance.json](provenance.json) binds raw work/log/build records, timing inputs, source inventories, helper hashes and derived files. This joiner verifies the captured native certificate marker; it does not reconstruct input edges or independently recompute the MST. Moment checks cannot prove vertex membership because selected-edge ledgers are absent from search_work_v1.
