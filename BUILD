load("@rules_cc//cc:defs.bzl", "cc_test")

cc_test(
    name = "verifier_test",
    srcs = ["test/verifier_test.cpp"],
    deps = [
        "@gtest//:gtest_main",
        "//kruskal:kruskal",
        "//boruvka:boruvka",
        "//prim:prim",
        "//graph_utils:graph_utils",
        "//verifier:verifier",
    ],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "verifier_v2_test",
    srcs = ["test/verifier_v2_test.cpp"],
    deps = [
        "@gtest//:gtest_main",
        "//kruskal:kruskal",
        "//boruvka:boruvka",
        "//prim:prim",
        "//graph_utils:graph_utils",
        "//verifier:verifier_v2",
    ],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "mst_test",
    srcs = ["test/mst_test.cpp"],
    deps = [
        "@gtest//:gtest_main", 
        "//boruvka:boruvka",
        "//kruskal:kruskal",
        "//prim:prim",
        "//graph_utils:graph_utils",
    ],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "kkt_test",
    srcs = ["test/kkt_test.cpp"],
    deps = [
        "@gtest//:gtest_main",
        "//kruskal:kruskal",
        "//prim:prim",
        "//boruvka:boruvka",
        "//graph_utils:graph_utils",
        "//kkt:kkt",
    ],
    visibility = ["//visibility:public"],
)
