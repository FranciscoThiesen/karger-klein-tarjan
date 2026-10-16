# Depth-query call boundaries in the actual candidate build

This is a manual source/disassembly audit of root's completed [depth-codegen01 inspection](../../benchmark/results/scaling-investigation-2026-10-15/depth-codegen01/inspection.json). No additional disassembler or solver was executed for this review. The inspected objects are the uninstrumented verifier objects from `depth-build01`, built with Apple Clang 15.0.0, arm64, `-O3 -march=native`, assertions enabled and no LTO. The recorded disassemblies retain their command/resource/exit receipts and object bindings.

## The query itself remains out of line

Both depth variants have two static `ARM64_RELOC_BRANCH26` call sites to `depth_lca::query_depth`: object offsets `0x187c` and `0x36f8`. They are the tuple-query and direct-Edge paths, respectively—not two LCA calls for each edge. In the Edge gather loop, the returned depth is stored at `0x36fc`, and the endpoint-equality branch follows at `0x3700`–`0x3704`. Thus the self-loop still incurs its LCA query before requests are skipped, as required by the logical-counter contract.

The default and explicit-noinline query bodies have identical instruction words from `0x6744` through the two normal returns ending at `0x6884`. This includes the endpoint guards, first-visit loads, block divisions, nested microtable accesses, Euler-depth loads and sparse-depth comparisons. The visible difference starts on the failed-assertion path: the default branches to an outlined `.cold.1` helper at `0x6888`; the noinline version emits its assertion setup there. This is not a claim that their entire objects or linked binaries are identical.

The reference has two corresponding out-of-line generic `LCA::query` call sites at `0x1798` and `0x34ec`. Consequently, **automatic inlining of the depth RMQ query body is not the explanation for any eventual candidate difference in this build**. The planned noinline comparison remains useful evidence about the actual compiled controls, but it is not a query-inlined versus query-not-inlined experiment here.

## A different inlining change remains bundled

The reference gather loop also calls `compressed_tree_path_maxima::add_request` out of line, twice for each nonloop: tuple offsets `0x17b8`/`0x17d0`, Edge offsets `0x350c`/`0x3524`. In both depth builds, `add_request_depth` is inlined into gather. The Edge code shows its proper-depth checks, bit shift, requested-mask OR/stores and logical-request increment directly after the query. There are no corresponding add-request call relocations.

This is consistent with the source specialization: the old helper takes an ancestor ID, validates it and loads its depth; the new helper accepts the already-known depth and has a smaller body. The change therefore combines the removed ancestor-ID/depth indirection with a changed helper call boundary. Merely marking `query_depth` noinline does not separate those effects.

Mark scattering still calls its lookup helper out of line in both representations. Reference Edge call sites are `0x35e8`/`0x3604`; both depth variants call `lookup_depth` at `0x3834`/`0x3848`. Their return-value representation and internal loads differ, so identical call boundaries do not imply identical cost.

Any performance conclusion should describe candidate D as the **depth-specialized query/request API and its generated code**, not as a pure measurement of one removed load or query-body inlining. A later minimal helper-inlining control could isolate that narrower question if the measured gain warrants it; no such control is implemented by this note. These instructions establish access/call structure, not cache misses, instruction latency, CPU attribution or a measured speedup.

Recorded disassembly SHA-256 values (from the completed inspection receipts): reference `4a1c23b9c77cf7c370b12561da73dd8b5017a4e6dbf5b05d6dbbe132bb82676f`; depth `f316858dd3e843f533b86244e7a91fcb89af715fa5a1bc5caff641f8aa06a476`; depth-noinline `6b0e25a9e1423edb253759d95450ed8ec901052810ea0587b6319c503148f065`.
