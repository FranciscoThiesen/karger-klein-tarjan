load("@rules_cc//cc:defs.bzl", "cc_binary", "cc_library", "cc_test")

cc_library(
    name = "fixtures",
    hdrs = ["graph_fixtures.hpp", "extended_graph_fixtures.hpp", "common_graph_fixtures.hpp", "continuation_fixtures.hpp", "crossover_fixtures.hpp", "component_moments.hpp", "mst_certificate.hpp"],
    visibility = ["//visibility:public"],
)

cc_library(
    name = "work_metrics",
    hdrs = ["work_metrics.hpp"],
    deps = ["//common:work_stats"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "work_sweep",
    srcs = ["work_sweep.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", ":work_metrics", "//kkt:kkt_work_stats", "//kruskal:kruskal"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "shape_work",
    srcs = ["shape_work.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", ":work_metrics", "//kkt:kkt_work_stats", "//kruskal:kruskal"],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "shapes_test",
    srcs = ["shapes_test.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures"],
)

cc_binary(
    name = "common_work",
    srcs = ["common_work.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", ":work_metrics", "//kkt:kkt_work_stats", "//kruskal:kruskal"],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "common_test",
    srcs = ["common_test.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures"],
)

cc_binary(
    name = "complexity_benchmark",
    srcs = ["complexity_benchmark.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", "@com_google_benchmark//:benchmark", "//kkt:kkt", "//kruskal:kruskal"],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "certificate_test",
    srcs = ["certificate_test.cpp", "mst_certificate.hpp"],
    copts = ["-std=c++17"],
)

cc_binary(
    name = "diverse_benchmark",
    srcs = ["diverse_benchmark.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", "//kkt:kkt", "//kruskal:kruskal", "//prim:prim", "//boruvka:boruvka"],
    visibility = ["//visibility:public"],
)

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

cc_binary(
    name = "contraction_ablation",
    srcs = ["contraction_ablation.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", "//kkt:kkt", "//kruskal:kruskal"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "export_graph_views",
    srcs = ["export_graph_views.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", "//kkt:kkt", "//kruskal:kruskal", "//verifier:verifier_v2"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "continuation_search",
    srcs = ["continuation_search.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", ":work_metrics", "//kkt:kkt", "//kruskal:kruskal"],
    visibility = ["//visibility:public"],
)

cc_binary(
    name = "continuation_search_work",
    srcs = ["continuation_search.cpp"],
    copts = ["-std=c++17", "-DKKT_ENABLE_WORK_STATS"],
    deps = [":fixtures", ":work_metrics", "//kkt:kkt_work_stats", "//kruskal:kruskal"],
    visibility = ["//visibility:public"],
)

cc_test(
    name = "continuation_test",
    srcs = ["continuation_test.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", "//kkt:kkt", "//kruskal:kruskal"],
)

cc_test(
    name = "crossover_test",
    srcs = ["crossover_test.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", "//kkt:kkt", "//kruskal:kruskal"],
)

cc_binary(
    name = "crossover_baselines",
    srcs = ["crossover_baselines.cpp"],
    copts = ["-std=c++17"],
    deps = [":fixtures", "//kkt:kkt", "//kruskal:kruskal", "//prim:prim", "//boruvka:boruvka"],
    visibility = ["//visibility:public"],
)
