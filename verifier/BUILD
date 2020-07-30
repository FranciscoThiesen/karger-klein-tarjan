load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "verifier",
    srcs = ["verifier.cpp"],
    hdrs = ["verifier.hpp"],
    deps = [
        "//union_find:union_find",
        "//boruvka:boruvka",
        "//kruskal:kruskal",
        "//prim:prim",
        "//lca:lca",
        "//graph_utils:graph_utils",
    ],
    visibility = ["//visibility:public"],
)
