load("@rules_cc//cc:defs.bzl", "cc_library", "cc_test")

cc_library(
    name = "boruvka",
    srcs = ["boruvka.cpp"],
    hdrs = ["boruvka.hpp"],
    deps = ["//union_find:union_find"],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "boruvka_test",
    srcs = ["boruvka_test.cpp"],
    deps = [
        "@gtest//:gtest_main",
        ":boruvka",
        "//kruskal:kruskal",
        "//prim:prim",
        "//graph_utils:graph_utils"
    ],
    visibility = ["//visibility:public"],
)
