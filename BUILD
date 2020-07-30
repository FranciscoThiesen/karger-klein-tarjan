load("@rules_cc//cc:defs.bzl", "cc_binary")

cc_binary(
    name = "verification",
    srcs = ["verification.cpp"],
    deps = [
        "//Boruvka:boruvka",
        "//Prim:prim",
        "//Kruskal:kruskal",
        "//UnionFind:union_find",
        "//LCA:lca",
        "//test:hello",
    ],
)
