load("@rules_cc//cc:defs.bzl", "cc_library")

cc_library(
    name = "kruskal",
    srcs = ["kruskal.cpp"],
    hdrs = ["kruskal.hpp"],
    copts = [
        "-std=c++17",
    ],
    deps = ["//union_find:union_find"], 
    visibility = ["//visibility:public"],
)
