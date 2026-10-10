load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "kkt",
    srcs = ["kkt.cpp"],
    hdrs = ["kkt.hpp", "random_sampling.hpp"],
    copts = [
        "-std=c++17",
    ],
    deps = [
        "//common:edge",
        "//common:work_stats",
        "//verifier:verifier_v2",
    ],
    visibility = ["//visibility:public"],
)

# Instrumented variants must stay separate from the normal timing binary.
cc_library(
    name = "kkt_work_stats",
    srcs = ["kkt.cpp"],
    hdrs = ["kkt.hpp", "random_sampling.hpp"],
    copts = ["-std=c++17"],
    defines = ["KKT_ENABLE_WORK_STATS"],
    deps = ["//common:edge", "//common:work_stats", "//verifier:verifier_v2_work_stats"],
    visibility = ["//visibility:public"],
)
