load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "verifier",
    srcs = ["verifier.cpp"],
    hdrs = ["verifier.hpp"],
    copts = [
        "-std=c++17",
    ],
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

cc_library(
    name = "verifier_v2",
    srcs = ["verifier_v2.cpp"],
    hdrs = ["verifier_v2.hpp"],
    copts = [
        "-std=c++17",
    ],
    deps = [
        "//lca:lca",
    ],
    visibility = ["//visibility:public"],
)
