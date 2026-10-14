# How far the attachment models resemble published network models

Retrieved 13 October 2026 (America/Los_Angeles session date), using remote web access only. This is a focused four-source note, not a systematic review. No data archive was downloaded locally, no benchmark ran, and no repository source changed.

The defensible connection is **component-wise**: published work supports core–periphery organization, weights correlated with communities, and hierarchical distance orderings. None of these sources establishes that the conjunction used here—equal cheap leaf stars, a connected sparse high-degree core, strict dyadic weight tiers, and uniformly scattered heavy shortcuts—is a common empirical distribution. None reports KKT timings on this attachment family.

## 1. Core–periphery is an established structural concept, but leaves are a special case

Rombach, Porter, Fowler and Mucha, *Core-Periphery Structure in Networks*, SIAM Journal on Applied Mathematics 74(1), 167–190 (published 18 February 2014). [Author-hosted paper](https://www.math.ucla.edu/~mason/papers/cp-siam-published.pdf), [DOI](https://doi.org/10.1137/120881683).

The authors model and measure densely connected cores with sparsely connected peripheral nodes, including weighted examples. Their London Underground example uses connection multiplicity as weight, not travel cost. This supports discussing core–periphery topology independently of community structure. It does not assert that peripheral nodes all have degree one, that each core node receives an equal number of leaves, or that peripheral connections are the cheapest edges.

**Our inference:** the leaf fixture is a deliberately extreme, analytically transparent core–periphery construction. Its core remains sparse asymptotically at fixed b,d: q=n/b and E=q[b(d−1)+1], with average core degree 2[b(d−1)+1]. At b=4,d=16 this is 122. Calling it a relatively high-degree core is accurate; calling it a dense graph in the asymptotic sense is not.

## 2. Weighted LFR gives a reproducible alternative with correlated weights

Lancichinetti and Fortunato, *Benchmarks for testing community detection algorithms on directed and weighted graphs with overlapping communities*, Physical Review E 80, 016118 (31 July 2009). [Paper](https://arxiv.org/abs/0904.3940), [author resources](https://www.santofortunato.net/resources), [author-linked generator repository](https://github.com/andrealancichinetti/LFRbenchmarks).

Section II.B generates a topology with heterogeneous degrees/communities, then assigns positive weights to approach node strength s_i=k_i^beta and separately specified internal/external strength fractions. Thus topology mixing and weight mixing are distinct controls. The author's resources also advertise a hierarchical benchmark, but this check has not established that the distributed hierarchical variant combines all weighted features. Do not silently describe it as a ready-made weighted multilevel generator.

**Our inference:** use the published weighted generator as a separate future test, preserving its output rather than adding cheap leaves until it wins. If weights denote connection strength, minimizing them has the wrong usual interpretation; an explicitly declared decreasing transform would instead test a maximum-strength spanning tree through the MST API. Such a transform is a model choice, not original measured cost data. Neither exact dyadic contractions nor a planted MST follows from LFR.

## 3. Dyson hierarchical networks justify the ordering concept, not our sparse topology

Agliari, Barra, Galluzzi, Guerra, Tantari and Tavani, *Topological properties of hierarchical networks*, Physical Review E 91, 062807 (2015). [Author preprint](https://arxiv.org/abs/1412.5918), [full text](https://arxiv.org/pdf/1412.5918), [DOI](https://doi.org/10.1103/PhysRevE.91.062807). The fetched PDF carries a later generated title-page date; journal publication is 2015.

Section III constructs a complete graph on 2^K vertices with dyadic hierarchical separation r and coupling J_K(r)=sum_{l=r}^K 4^(−sigma*l). Coupling decreases with separation, and the hierarchy defines an ultrametric. This is an explicit mathematical model used for statistical-mechanics systems, not a measured ISP or road dataset.

**Our inference:** applying a decreasing cost transform to positive J produces increasing hierarchical cost tiers, conceptually close to the core distance ordering. Our sparse path-plus-shortcuts selection, added pendant stars and within-tier unique ranks are extra engineering choices. The stored rank weights are not claimed to satisfy an ultrametric inequality after tie breaking. The all-backbone-cheap hierarchy mode is even more specialized: it prescribes the core MST. This source validates a modeling vocabulary, not practical prevalence or a KKT advantage.

## 4. Rocketfuel supplies actual weighted network inputs worth testing as a falsifier

Mahajan, Spring, Wetherall and Anderson, *Inferring Link Weights using End-to-End Measurements*, Internet Measurement Workshop 2002. [Author-hosted paper](https://www.cs.washington.edu/research/networking/rocketfuel/papers/imw2002.pdf), [UW project and data links](https://research.cs.washington.edu/networking/rocketfuel/).

The project advertises backbone topologies with inferred routing weights and link latencies. The paper's six backbone graphs contain 80–323 routers. Weights are inferred to reproduce observed shortest-path routing, not guaranteed to equal operators' actual weights; latency is a different field. The weighted subset does not simply equal the much larger router-map collection advertised on the project page. The archive link was located but its contents were not inspected or downloaded in this task.

**Our inference:** this is the strongest concrete real-data lead here, despite being far too small to demonstrate the million-vertex crossover. It can test whether cost/topology correlations and leaf/core structure resemble the fixture at all. A future import must inspect directionality, reciprocal weights, ties, connectivity and the chosen cost field before defining an undirected MST instance. Do not append synthetic leaves and still label the result an untouched real network.

## Recommended framing and next step

“The construction isolates two plausible ingredients—rapid removal of peripheral vertices and persistent edges across a weighted hierarchy—but enforces their conjunction exactly. Published core–periphery and hierarchical models motivate testing those ingredients; they do not make this fixture representative of real networks.”

First inspect native weighted data structurally, without selecting inputs by a KKT win: leaf fraction, core size/degree, costs on peripheral versus core edges, ties, and residual edge volume under ordinary production contraction. Then separately test a published weighted model with predeclared parameters and its same-topology weight permutation control. Report generated adaptations as adaptations, not empirical data.

Cheap leaves alone cannot supply the full argument. Every true pendant edge belongs to every spanning tree regardless of its weight. Putting all local-star weights below every core weight additionally prevents a center from selecting a core edge in the first round, enforcing the exact quotient used in our proof. Nor does a power-law weight histogram alone explain comparison-based MST behavior: a strictly increasing transform preserves the complete edge order. The relevant variation is how ranks correlate with topology and how that changes contraction/filtering work. These are mathematical observations and future test recommendations, not timing predictions or new results.
