# Five-solver capture

Strict validation passed for 80 cases, 1 graph seeds and 1 sampling seeds: 2000 timed calls and 400 retained warmup calls. Each child has 5 timed repetitions and 1 warmups per algorithm.

All five positions are balanced within each timed seed pair. Every native reference has an independent MST certificate; every returned result must match that exact unique MST. Warmups are validated and retained, but excluded from timing summaries.

Ratios below one favor KKT. Each ratio is paired within the same graph, sampling seed and repetition, then aggregated by median over repetitions, sampling seeds and graphs in that order. Runtime summaries apply the same hierarchy separately to each algorithm; a ratio of those summaries is a different statistic. Graph and individual-trial ranges are descriptive spreads, not confidence intervals. Sampling seeds repeat identical inputs for deterministic competitors; they are not additional graph samples.

`compacting_boruvka` repeatedly uses production contraction; `boruvka` is the original public baseline. No other campaign is mixed into these comparisons, and no finite result establishes asymptotic dominance.

0 calls carry diagnostic clock flags, and 0 capture/child UTC interval flags are retained in provenance; all calls remain in every relevant table. Wall and process-CPU results are separate. Resource observations are periodic sums of process-group RSS in KiB, not continuous peaks or unique physical footprints. Polling itself can perturb measurements; the same rule is applied throughout this campaign.

| Case | Metric | KKT / compacting Borůvka | KKT / Kruskal | KKT / Prim | KKT / original Borůvka |
|---|---|---:|---:|---:|---:|
| community_distance16_n262144_d16_p0 | wall | 1.0239 | 2.0963 | 0.6750 | 1.8819 |
| community_distance16_n262144_d16_p0 | cpu | 1.0240 | 2.0961 | 0.6750 | 1.8819 |
| leaf_hierarchy16_n65536_d16_p0 | wall | 1.1833 | 1.1794 | 2.2557 | 1.4571 |
| leaf_hierarchy16_n65536_d16_p0 | cpu | 1.1833 | 1.1784 | 2.2558 | 1.4574 |
| community_distance16_n1048576_d2_p0 | wall | 1.0676 | 1.6995 | 0.2035 | 0.1952 |
| community_distance16_n1048576_d2_p0 | cpu | 1.0676 | 1.6995 | 0.2035 | 0.1952 |
| community_hierarchy16_n1048576_d2_p0 | wall | 1.0817 | 1.7221 | 0.2097 | 0.1960 |
| community_hierarchy16_n1048576_d2_p0 | cpu | 1.0817 | 1.7220 | 0.2097 | 0.1960 |
| leaf_distance16_n262144_d2_p0 | wall | 1.1877 | 1.3227 | 0.5179 | 0.3698 |
| leaf_distance16_n262144_d2_p0 | cpu | 1.1878 | 1.3225 | 0.5179 | 0.3699 |
| community_distance16_n16384_d16_p0 | wall | 1.2589 | 0.8340 | 0.3851 | 1.2909 |
| community_distance16_n16384_d16_p0 | cpu | 1.2589 | 0.8341 | 0.3851 | 1.2909 |
| leaf_hierarchy16_n262144_d2_p0 | wall | 1.1926 | 1.3194 | 0.5989 | 0.3601 |
| leaf_hierarchy16_n262144_d2_p0 | cpu | 1.1926 | 1.3194 | 0.5989 | 0.3601 |
| community_hierarchy4_n16384_d16_p0 | wall | 1.2366 | 1.2174 | 0.7569 | 1.3594 |
| community_hierarchy4_n16384_d16_p0 | cpu | 1.2366 | 1.2174 | 0.7569 | 1.3594 |
| community_distance4_n262144_d2_p0 | wall | 1.5002 | 2.0381 | 0.3722 | 0.3492 |
| community_distance4_n262144_d2_p0 | cpu | 1.5004 | 2.0381 | 0.3723 | 0.3492 |
| leaf_hierarchy4_n16384_d2_p0 | wall | 1.6167 | 2.1873 | 0.8376 | 0.7021 |
| leaf_hierarchy4_n16384_d2_p0 | cpu | 1.6168 | 2.1887 | 0.8375 | 0.7022 |
| community_shuffled4_n1048576_d2_p0 | wall | 1.2222 | 2.0136 | 0.2393 | 0.2950 |
| community_shuffled4_n1048576_d2_p0 | cpu | 1.2222 | 2.0136 | 0.2393 | 0.2950 |
| leaf_hierarchy16_n65536_d2_p0 | wall | 1.2392 | 1.3270 | 0.7030 | 0.4715 |
| leaf_hierarchy16_n65536_d2_p0 | cpu | 1.2394 | 1.3241 | 0.7032 | 0.4716 |
| leaf_distance16_n65536_d2_p0 | wall | 1.2427 | 1.3024 | 0.6258 | 0.4759 |
| leaf_distance16_n65536_d2_p0 | cpu | 1.2427 | 1.3025 | 0.6258 | 0.4758 |
| community_distance4_n262144_d16_p0 | wall | 0.9283 | 2.5876 | 0.8063 | 1.7358 |
| community_distance4_n262144_d16_p0 | cpu | 0.9283 | 2.5875 | 0.8063 | 1.7358 |
| community_hierarchy4_n1048576_d16_p0 | wall | 0.8387 | 4.0381 | 0.9724 | 1.4081 |
| community_hierarchy4_n1048576_d16_p0 | cpu | 0.8387 | 4.0380 | 0.9724 | 1.4081 |
| community_distance16_n65536_d2_p0 | wall | 1.2345 | 1.3035 | 0.2880 | 0.4449 |
| community_distance16_n65536_d2_p0 | cpu | 1.2346 | 1.3036 | 0.2879 | 0.4450 |
| leaf_hierarchy16_n1048576_d16_p0 | wall | 0.9184 | 3.3614 | 4.9551 | 2.0884 |
| leaf_hierarchy16_n1048576_d16_p0 | cpu | 0.9184 | 3.3614 | 4.9552 | 2.0885 |
| community_random4_n1048576_d16_p0 | wall | 0.9925 | 3.6586 | 0.9945 | 2.6354 |
| community_random4_n1048576_d16_p0 | cpu | 0.9925 | 3.6585 | 0.9945 | 2.6354 |
| leaf_hierarchy16_n16384_d16_p0 | wall | 1.2544 | 0.8368 | 1.8412 | 1.3686 |
| leaf_hierarchy16_n16384_d16_p0 | cpu | 1.2556 | 0.8360 | 1.8408 | 1.3685 |
| community_distance4_n16384_d2_p0 | wall | 1.5851 | 2.1186 | 0.5230 | 0.5090 |
| community_distance4_n16384_d2_p0 | cpu | 1.5847 | 2.1180 | 0.5229 | 0.5090 |
| leaf_hierarchy4_n1048576_d16_p0 | wall | 0.8309 | 3.9591 | 3.0725 | 1.9091 |
| leaf_hierarchy4_n1048576_d16_p0 | cpu | 0.8309 | 3.9589 | 3.0724 | 1.9091 |
| leaf_shuffled16_n1048576_d2_p0 | wall | 1.1608 | 1.5844 | 0.5219 | 0.3394 |
| leaf_shuffled16_n1048576_d2_p0 | cpu | 1.1606 | 1.5843 | 0.5219 | 0.3393 |
| leaf_distance16_n1048576_d2_p0 | wall | 1.0691 | 1.7900 | 0.5096 | 0.2349 |
| leaf_distance16_n1048576_d2_p0 | cpu | 1.0692 | 1.7899 | 0.5096 | 0.2349 |
| community_random4_n1048576_d2_p0 | wall | 1.2077 | 2.2113 | 0.2712 | 0.3226 |
| community_random4_n1048576_d2_p0 | cpu | 1.2077 | 2.2113 | 0.2712 | 0.3226 |
| leaf_distance4_n1048576_d2_p0 | wall | 1.3146 | 2.6924 | 0.5368 | 0.2611 |
| leaf_distance4_n1048576_d2_p0 | cpu | 1.3146 | 2.6924 | 0.5367 | 0.2611 |
| leaf_shuffled16_n1048576_d16_p0 | wall | 1.0338 | 3.1555 | 4.7632 | 3.5335 |
| leaf_shuffled16_n1048576_d16_p0 | cpu | 1.0339 | 3.1560 | 4.7635 | 3.5337 |
| leaf_random4_n1048576_d2_p0 | wall | 1.1685 | 1.6930 | 0.2816 | 0.3145 |
| leaf_random4_n1048576_d2_p0 | cpu | 1.1686 | 1.6936 | 0.2816 | 0.3145 |
| leaf_hierarchy16_n262144_d16_p0 | wall | 1.0152 | 2.0581 | 3.9811 | 2.0322 |
| leaf_hierarchy16_n262144_d16_p0 | cpu | 1.0152 | 2.0580 | 3.9810 | 2.0323 |
| leaf_hierarchy16_n16384_d2_p0 | wall | 1.3245 | 1.3198 | 0.7329 | 0.5405 |
| leaf_hierarchy16_n16384_d2_p0 | cpu | 1.3229 | 1.3187 | 0.7323 | 0.5405 |
| leaf_distance16_n16384_d16_p0 | wall | 1.2423 | 0.8323 | 1.5287 | 1.3666 |
| leaf_distance16_n16384_d16_p0 | cpu | 1.2423 | 0.8320 | 1.5286 | 1.3667 |
| community_hierarchy16_n16384_d16_p0 | wall | 1.2395 | 0.8407 | 0.5165 | 1.2848 |
| community_hierarchy16_n16384_d16_p0 | cpu | 1.2394 | 0.8407 | 0.5170 | 1.2846 |
| community_distance16_n262144_d2_p0 | wall | 1.1803 | 1.2574 | 0.2262 | 0.3349 |
| community_distance16_n262144_d2_p0 | cpu | 1.1803 | 1.2574 | 0.2263 | 0.3350 |
| leaf_distance16_n1048576_d16_p0 | wall | 0.9138 | 3.3165 | 3.9250 | 2.1213 |
| leaf_distance16_n1048576_d16_p0 | cpu | 0.9138 | 3.3164 | 3.9249 | 2.1212 |
| community_distance4_n16384_d16_p0 | wall | 1.2602 | 1.2222 | 0.5727 | 1.4314 |
| community_distance4_n16384_d16_p0 | cpu | 1.2603 | 1.2222 | 0.5727 | 1.4314 |
| community_hierarchy4_n65536_d16_p0 | wall | 1.1415 | 1.5110 | 0.8092 | 1.3237 |
| community_hierarchy4_n65536_d16_p0 | cpu | 1.1415 | 1.5110 | 0.8091 | 1.3236 |
| leaf_hierarchy4_n65536_d16_p0 | wall | 1.1445 | 1.5223 | 1.8745 | 1.5938 |
| leaf_hierarchy4_n65536_d16_p0 | cpu | 1.1446 | 1.5223 | 1.8744 | 1.5937 |
| community_hierarchy4_n262144_d16_p0 | wall | 0.9276 | 2.5891 | 1.1386 | 1.6966 |
| community_hierarchy4_n262144_d16_p0 | cpu | 0.9275 | 2.5889 | 1.1386 | 1.6964 |
| leaf_hierarchy4_n262144_d16_p0 | wall | 0.9292 | 2.6108 | 2.6056 | 2.0350 |
| leaf_hierarchy4_n262144_d16_p0 | cpu | 0.9292 | 2.6108 | 2.6054 | 2.0350 |
| community_hierarchy4_n65536_d2_p0 | wall | 1.6036 | 2.1405 | 0.5343 | 0.4418 |
| community_hierarchy4_n65536_d2_p0 | cpu | 1.6034 | 2.1409 | 0.5342 | 0.4418 |
| community_distance4_n1048576_d16_p0 | wall | 0.8469 | 3.8602 | 0.7206 | 1.4146 |
| community_distance4_n1048576_d16_p0 | cpu | 0.8469 | 3.8602 | 0.7206 | 1.4146 |
| community_distance16_n1048576_d16_p0 | wall | 0.9266 | 3.3492 | 0.6374 | 1.8349 |
| community_distance16_n1048576_d16_p0 | cpu | 0.9266 | 3.3489 | 0.6374 | 1.8348 |
| community_shuffled4_n1048576_d16_p0 | wall | 0.9926 | 3.8013 | 0.9479 | 2.7540 |
| community_shuffled4_n1048576_d16_p0 | cpu | 0.9926 | 3.8011 | 0.9480 | 2.7540 |
| leaf_hierarchy4_n16384_d16_p0 | wall | 1.2559 | 1.2114 | 1.6723 | 1.6475 |
| leaf_hierarchy4_n16384_d16_p0 | cpu | 1.2560 | 1.2114 | 1.6723 | 1.6475 |
| leaf_distance16_n65536_d16_p0 | wall | 1.2637 | 1.1532 | 1.9959 | 1.4905 |
| leaf_distance16_n65536_d16_p0 | cpu | 1.2637 | 1.1532 | 1.9955 | 1.4901 |
| community_distance4_n1048576_d2_p0 | wall | 1.2834 | 2.5282 | 0.3048 | 0.1693 |
| community_distance4_n1048576_d2_p0 | cpu | 1.2834 | 2.5280 | 0.3048 | 0.1693 |
| community_distance16_n65536_d16_p0 | wall | 1.2328 | 1.1454 | 0.4425 | 1.3710 |
| community_distance16_n65536_d16_p0 | cpu | 1.2326 | 1.1453 | 0.4425 | 1.3710 |
| leaf_distance4_n65536_d2_p0 | wall | 1.6205 | 2.2821 | 0.7376 | 0.6676 |
| leaf_distance4_n65536_d2_p0 | cpu | 1.6202 | 2.2820 | 0.7377 | 0.6676 |
| leaf_distance4_n1048576_d16_p0 | wall | 0.8386 | 3.6644 | 2.1523 | 1.9254 |
| leaf_distance4_n1048576_d16_p0 | cpu | 0.8386 | 3.6644 | 2.1523 | 1.9254 |
| community_hierarchy16_n65536_d2_p0 | wall | 1.2180 | 1.2607 | 0.3043 | 0.4220 |
| community_hierarchy16_n65536_d2_p0 | cpu | 1.2181 | 1.2609 | 0.3043 | 0.4220 |
| leaf_hierarchy4_n262144_d2_p0 | wall | 1.5270 | 2.2044 | 0.7194 | 0.5366 |
| leaf_hierarchy4_n262144_d2_p0 | cpu | 1.5269 | 2.2042 | 0.7193 | 0.5366 |
| leaf_hierarchy4_n1048576_d2_p0 | wall | 1.3286 | 2.5180 | 0.5998 | 0.2943 |
| leaf_hierarchy4_n1048576_d2_p0 | cpu | 1.3286 | 2.5179 | 0.5998 | 0.2943 |
| leaf_distance4_n65536_d16_p0 | wall | 1.2143 | 1.4731 | 1.3399 | 1.5889 |
| leaf_distance4_n65536_d16_p0 | cpu | 1.2143 | 1.4731 | 1.3399 | 1.5889 |
| leaf_distance16_n16384_d2_p0 | wall | 1.3427 | 1.3050 | 0.6589 | 0.5456 |
| leaf_distance16_n16384_d2_p0 | cpu | 1.3422 | 1.3043 | 0.6586 | 0.5459 |
| community_shuffled16_n1048576_d16_p0 | wall | 1.0524 | 2.9758 | 0.8952 | 3.1034 |
| community_shuffled16_n1048576_d16_p0 | cpu | 1.0524 | 2.9758 | 0.8953 | 3.1034 |
| community_hierarchy16_n262144_d2_p0 | wall | 1.1904 | 1.2812 | 0.2567 | 0.3546 |
| community_hierarchy16_n262144_d2_p0 | cpu | 1.1905 | 1.2812 | 0.2567 | 0.3546 |
| leaf_random4_n1048576_d16_p0 | wall | 1.0429 | 2.7871 | 1.9679 | 2.8018 |
| leaf_random4_n1048576_d16_p0 | cpu | 1.0429 | 2.7870 | 1.9679 | 2.8018 |
| leaf_random16_n1048576_d16_p0 | wall | 1.0405 | 2.2239 | 2.5744 | 3.0387 |
| leaf_random16_n1048576_d16_p0 | cpu | 1.0405 | 2.2239 | 2.5744 | 3.0387 |
| community_distance16_n16384_d2_p0 | wall | 1.3109 | 1.3358 | 0.3172 | 0.5058 |
| community_distance16_n16384_d2_p0 | cpu | 1.3111 | 1.3351 | 0.3171 | 0.5057 |
| community_hierarchy16_n65536_d16_p0 | wall | 1.2639 | 1.0758 | 0.5950 | 1.3082 |
| community_hierarchy16_n65536_d16_p0 | cpu | 1.2639 | 1.0758 | 0.5951 | 1.3081 |
| leaf_shuffled4_n1048576_d2_p0 | wall | 1.2373 | 1.9902 | 0.4686 | 0.3955 |
| leaf_shuffled4_n1048576_d2_p0 | cpu | 1.2373 | 1.9902 | 0.4686 | 0.3955 |
| community_random16_n1048576_d2_p0 | wall | 1.2088 | 1.8499 | 0.2499 | 0.3415 |
| community_random16_n1048576_d2_p0 | cpu | 1.2088 | 1.8499 | 0.2499 | 0.3415 |
| community_hierarchy16_n16384_d2_p0 | wall | 1.3122 | 1.3114 | 0.3345 | 0.4937 |
| community_hierarchy16_n16384_d2_p0 | cpu | 1.3127 | 1.3116 | 0.3348 | 0.4936 |
| community_hierarchy4_n1048576_d2_p0 | wall | 1.3289 | 2.4095 | 0.3327 | 0.2030 |
| community_hierarchy4_n1048576_d2_p0 | cpu | 1.3289 | 2.4095 | 0.3327 | 0.2030 |
| leaf_hierarchy16_n1048576_d2_p0 | wall | 1.0913 | 1.6428 | 0.6014 | 0.2556 |
| leaf_hierarchy16_n1048576_d2_p0 | cpu | 1.0913 | 1.6428 | 0.6015 | 0.2556 |
| leaf_distance4_n262144_d16_p0 | wall | 0.9323 | 2.2856 | 1.6790 | 1.8624 |
| leaf_distance4_n262144_d16_p0 | cpu | 0.9323 | 2.2856 | 1.6790 | 1.8624 |
| community_random16_n1048576_d16_p0 | wall | 1.0080 | 3.3600 | 1.0151 | 2.7867 |
| community_random16_n1048576_d16_p0 | cpu | 1.0080 | 3.3600 | 1.0151 | 2.7867 |
| leaf_hierarchy4_n65536_d2_p0 | wall | 1.6048 | 2.2276 | 0.8505 | 0.6578 |
| leaf_hierarchy4_n65536_d2_p0 | cpu | 1.6049 | 2.2278 | 0.8507 | 0.6580 |
| leaf_random16_n1048576_d2_p0 | wall | 1.1527 | 1.2025 | 0.2767 | 0.3524 |
| leaf_random16_n1048576_d2_p0 | cpu | 1.1527 | 1.2025 | 0.2767 | 0.3524 |
| community_hierarchy16_n262144_d16_p0 | wall | 1.0324 | 1.8617 | 0.8210 | 1.7668 |
| community_hierarchy16_n262144_d16_p0 | cpu | 1.0324 | 1.8617 | 0.8210 | 1.7667 |
| community_hierarchy4_n262144_d2_p0 | wall | 1.4975 | 2.0725 | 0.4438 | 0.3584 |
| community_hierarchy4_n262144_d2_p0 | cpu | 1.4975 | 2.0725 | 0.4438 | 0.3584 |
| leaf_distance4_n16384_d2_p0 | wall | 1.5753 | 2.0659 | 0.7225 | 0.6938 |
| leaf_distance4_n16384_d2_p0 | cpu | 1.5755 | 2.0653 | 0.7224 | 0.6938 |
| community_hierarchy4_n16384_d2_p0 | wall | 1.5839 | 2.0640 | 0.5523 | 0.4821 |
| community_hierarchy4_n16384_d2_p0 | cpu | 1.5840 | 2.0631 | 0.5524 | 0.4823 |
| leaf_distance16_n262144_d16_p0 | wall | 1.0256 | 1.7148 | 2.7059 | 1.7532 |
| leaf_distance16_n262144_d16_p0 | cpu | 1.0256 | 1.7148 | 2.7059 | 1.7532 |
| community_hierarchy16_n1048576_d16_p0 | wall | 0.9198 | 3.1313 | 0.8858 | 1.9057 |
| community_hierarchy16_n1048576_d16_p0 | cpu | 0.9199 | 3.1313 | 0.8858 | 1.9057 |
| leaf_distance4_n16384_d16_p0 | wall | 1.2612 | 1.2221 | 1.2186 | 1.6629 |
| leaf_distance4_n16384_d16_p0 | cpu | 1.2612 | 1.2221 | 1.2186 | 1.6629 |
| community_distance4_n65536_d2_p0 | wall | 1.5914 | 2.1161 | 0.5062 | 0.4561 |
| community_distance4_n65536_d2_p0 | cpu | 1.5913 | 2.1159 | 0.5062 | 0.4561 |
| community_distance4_n65536_d16_p0 | wall | 1.2096 | 1.4522 | 0.6021 | 1.3394 |
| community_distance4_n65536_d16_p0 | cpu | 1.2096 | 1.4523 | 0.6021 | 1.3394 |
| community_shuffled16_n1048576_d2_p0 | wall | 1.1673 | 1.3971 | 0.1979 | 0.3398 |
| community_shuffled16_n1048576_d2_p0 | cpu | 1.1673 | 1.3971 | 0.1979 | 0.3398 |
| leaf_shuffled4_n1048576_d16_p0 | wall | 0.9877 | 3.4824 | 2.8877 | 3.4272 |
| leaf_shuffled4_n1048576_d16_p0 | cpu | 0.9877 | 3.4824 | 2.8877 | 3.4272 |
| leaf_distance4_n262144_d2_p0 | wall | 1.5231 | 2.1784 | 0.6200 | 0.5385 |
| leaf_distance4_n262144_d2_p0 | cpu | 1.5231 | 2.1785 | 0.6200 | 0.5386 |

Every individual ratio, including losses, is in [paired_ratios.csv](paired_ratios.csv). [comparisons.csv](comparisons.csv) and [graph_comparisons.csv](graph_comparisons.csv) retain spreads and win/loss counts. [summary.csv](summary.csv) reports separate algorithm runtimes in nanoseconds. [validated_calls.csv](validated_calls.csv) includes warmups; [call_diagnostics.csv](call_diagnostics.csv) contains every clock flag. [resources.csv](resources.csv) reports sampled resource observations.

Raw capture: [attachment-timing.csv](../attachment-timing.csv). Exact raw/child/log/manifest hashes and the captured source/binary inventories are retained in [provenance.json](provenance.json).
