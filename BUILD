load("@rules_cc//cc:defs.bzl", "cc_binary")

cc_binary(
    name = "verification",
    srcs = ["verification.cpp"],
    deps = [
        "//boruvka:boruvka",
        "//prim:prim",
        "//kruskal:kruskal",
        "//union_find:union_find",
        "//lca:lca",
        "//graph_utils:graph_utils", 
    ],
)
