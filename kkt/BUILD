load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "kkt",
    srcs = ["kkt.cpp"],
    hdrs = ["kkt.hpp", "random_sampling.hpp"],
    copts = [
        "-std=c++17",
    ],
    deps = ["//verifier:verifier_v2"],
    visibility = ["//visibility:public"],
)
