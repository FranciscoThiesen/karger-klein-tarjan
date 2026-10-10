load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "lca",
    srcs = ["lca.cpp"],
    hdrs = ["lca.hpp"],
    copts = [
        "-std=c++17",
    ],
    deps = ["//common:work_stats"],
    visibility = ["//visibility:public"],
)

cc_library(
    name = "lca_work_stats",
    srcs = ["lca.cpp"],
    hdrs = ["lca.hpp"],
    copts = ["-std=c++17"],
    defines = ["KKT_ENABLE_WORK_STATS"],
    deps = ["//common:work_stats"],
    visibility = ["//visibility:public"],
)
