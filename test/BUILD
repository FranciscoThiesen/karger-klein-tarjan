load("@rules_cc//cc:defs.bzl", "cc_test")

cc_test(
    name = "hello",
    srcs = ["hello_test.cpp"],
    deps = ["@gtest//:gtest_main"], 
    visibility = ["//visibility:public"],
)
