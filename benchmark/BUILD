load("@rules_cc//cc:defs.bzl", "cc_binary")

cc_binary(
    name = "scaling_benchmark",
    srcs = ["scaling_benchmark.cpp"],
    copts = ["-std=c++17"],
    deps = ["//kkt:kkt", "//kruskal:kruskal"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "mst_benchmark",
    srcs = ["mst_benchmark.cpp"],
    deps = [
        "@com_google_benchmark//:benchmark",
        "//boruvka:boruvka",
        "//graph_utils:graph_utils",
        "//kkt:kkt",
        "//kruskal:kruskal",
        "//prim:prim",
    ],
    visibility = ["//visibility:public"]
)
