# Small actual density-16 illustrations

These four additional graphs use n=1,024, d=16, graph seed 5009 and sampling seed 149. They match the selected density and weight controls, but are separately generated small illustrations, not measured pilot inputs or downsampled large inputs. Coordinates are illustrative.

- [Leaf hierarchy, b=4](leaf_hierarchy4.html)
- [Leaf distance, b=4](leaf_distance4.html)
- [Leaf shuffled core, b=4](leaf_shuffled4.html)
- [Leaf global random, b=4](leaf_random4.html)

The slider shows actual compacting Borůvka rounds computed from exported edge costs. The first two contractions are shared with KKT; sampling, filtering and recursion are not depicted. There are respectively 9, 9, 5 and 4 contractions in these particular examples. No large-input transition or timing conclusion follows from those small round counts.

Every export passed independent native and Python MST certificates and exact KKT output checks. The displayed minimum-edge ledger equals the complete certified MST; native physical quotient order is not asserted. [Native export provenance](exports.json) and [renderer validation/hashes](render_validation.json) preserve the inputs. Browser launch failed before rendering; see the explicit [QA limitation](../attachment-round-views/QA.md).
