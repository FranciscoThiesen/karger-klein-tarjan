# Makefile for KKT MST Algorithm
# Provides alternative build system to Bazel

CXX = clang++
CXXFLAGS = -std=c++17 -O3 -Wall -Wextra -march=native
DEBUG_FLAGS = -std=c++17 -O0 -g -Wall -Wextra -fsanitize=address,undefined

ifeq ($(shell uname -s),Darwin)
# Use the system toolchain and SDK together; command-line CXX still overrides.
CXX = /usr/bin/clang++
MACOS_SDK := $(shell xcrun --show-sdk-path)
CPPFLAGS += -isysroot $(MACOS_SDK)
LDFLAGS += -L$(MACOS_SDK)/usr/lib
endif

# Directories
BUILD_DIR = .build
BIN_DIR = bin

# Source files (excluding verifier.cpp to avoid duplicate symbols with verifier_v2.cpp)
SRCS = boruvka/boruvka.cpp \
       kruskal/kruskal.cpp \
       prim/prim.cpp \
       lca/lca.cpp \
       union_find/union_find.cpp \
       graph_utils/graph_utils.cpp \
       verifier/verifier_v2.cpp \
       kkt/kkt.cpp

OBJS = $(SRCS:%.cpp=$(BUILD_DIR)/%.o)

# Headers
HDRS = $(wildcard */*.hpp)

.PHONY: all clean test benchmark scaling-benchmark diverse-benchmark work-sweep shape-work common-work mst-search mst-search-large-stack debug

all: $(BIN_DIR)/test_runner $(BIN_DIR)/regression_runner

# Benchmark (requires google benchmark library)
benchmark: $(BIN_DIR)/benchmark

scaling-benchmark: $(BIN_DIR)/scaling_benchmark

diverse-benchmark: $(BIN_DIR)/diverse_benchmark

work-sweep: $(BIN_DIR)/work_sweep

shape-work: $(BIN_DIR)/shape_work

common-work: $(BIN_DIR)/common_work

mst-search: $(BIN_DIR)/mst_search

mst-search-large-stack: $(BIN_DIR)/large_stack/mst_search

WORK_OBJS = $(SRCS:%.cpp=$(BUILD_DIR)/workstats/%.o)

$(BUILD_DIR)/workstats/%.o: %.cpp $(HDRS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -DKKT_ENABLE_WORK_STATS -I. -c $< -o $@

$(BIN_DIR)/work_sweep: benchmark/work_sweep.cpp benchmark/work_metrics.hpp benchmark/graph_fixtures.hpp benchmark/mst_certificate.hpp $(WORK_OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -DKKT_ENABLE_WORK_STATS -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/shape_work: benchmark/shape_work.cpp benchmark/work_metrics.hpp benchmark/extended_graph_fixtures.hpp benchmark/graph_fixtures.hpp benchmark/mst_certificate.hpp $(WORK_OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -DKKT_ENABLE_WORK_STATS -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/shapes_test: benchmark/shapes_test.cpp benchmark/extended_graph_fixtures.hpp benchmark/graph_fixtures.hpp
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $< $(LDFLAGS) -o $@

$(BIN_DIR)/common_work: benchmark/common_work.cpp benchmark/work_metrics.hpp benchmark/common_graph_fixtures.hpp benchmark/graph_fixtures.hpp benchmark/mst_certificate.hpp $(WORK_OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -DKKT_ENABLE_WORK_STATS -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/common_test: benchmark/common_test.cpp benchmark/common_graph_fixtures.hpp benchmark/graph_fixtures.hpp
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $< $(LDFLAGS) -o $@

$(BIN_DIR)/export_graph_views: benchmark/export_graph_views.cpp benchmark/common_graph_fixtures.hpp benchmark/extended_graph_fixtures.hpp benchmark/mst_certificate.hpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/contraction_ablation: benchmark/contraction_ablation.cpp benchmark/common_graph_fixtures.hpp benchmark/extended_graph_fixtures.hpp benchmark/mst_certificate.hpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/continuation_search: benchmark/continuation_search.cpp benchmark/continuation_fixtures.hpp benchmark/crossover_fixtures.hpp benchmark/component_moments.hpp benchmark/graph_fixtures.hpp benchmark/mst_certificate.hpp benchmark/work_metrics.hpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/continuation_search_work: benchmark/continuation_search.cpp benchmark/continuation_fixtures.hpp benchmark/crossover_fixtures.hpp benchmark/component_moments.hpp benchmark/graph_fixtures.hpp benchmark/mst_certificate.hpp benchmark/work_metrics.hpp $(WORK_OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -DKKT_ENABLE_WORK_STATS -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/continuation_test: benchmark/continuation_test.cpp benchmark/continuation_fixtures.hpp benchmark/mst_certificate.hpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/crossover_test: benchmark/crossover_test.cpp benchmark/crossover_fixtures.hpp benchmark/component_moments.hpp benchmark/continuation_fixtures.hpp benchmark/mst_certificate.hpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/crossover_baselines: benchmark/crossover_baselines.cpp benchmark/crossover_fixtures.hpp benchmark/continuation_fixtures.hpp benchmark/mst_certificate.hpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

MST_SEARCH_DEPS = benchmark/mst_search.cpp benchmark/core_attachment_fixtures.hpp benchmark/search_fixtures.hpp benchmark/crossover_fixtures.hpp benchmark/continuation_fixtures.hpp benchmark/mst_certificate.hpp $(OBJS)

$(BIN_DIR)/search_fixtures_test: benchmark/search_fixtures_test.cpp benchmark/search_fixtures.hpp benchmark/continuation_fixtures.hpp benchmark/mst_certificate.hpp $(OBJS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/search_work: benchmark/search_work.cpp benchmark/core_attachment_fixtures.hpp benchmark/search_fixtures.hpp benchmark/continuation_fixtures.hpp benchmark/component_moments.hpp benchmark/work_metrics.hpp benchmark/mst_certificate.hpp $(WORK_OBJS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -DKKT_ENABLE_WORK_STATS -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

ATTACHMENT_FIXTURE_DEPS = benchmark/core_attachment_fixtures.hpp benchmark/continuation_fixtures.hpp benchmark/graph_fixtures.hpp benchmark/mst_certificate.hpp

$(BIN_DIR)/core_attachment_test: benchmark/core_attachment_test.cpp $(ATTACHMENT_FIXTURE_DEPS) $(OBJS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/workstats/core_attachment_test: benchmark/core_attachment_test.cpp $(ATTACHMENT_FIXTURE_DEPS) benchmark/work_metrics.hpp $(WORK_OBJS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -DKKT_ENABLE_WORK_STATS -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/export_attachment_view: benchmark/export_attachment_view.cpp $(ATTACHMENT_FIXTURE_DEPS) $(OBJS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/mst_search: $(MST_SEARCH_DEPS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

# Keep the original recursive Boruvka baseline unchanged. This opt-in macOS
# profile enlarges only the executable's main-thread stack to 512 MiB; its
# compiler flags and production objects are identical to the default target.
ifeq ($(shell uname -s),Darwin)
$(BIN_DIR)/large_stack/mst_search: $(MST_SEARCH_DEPS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -Wl,-stack_size,0x20000000 -o $@
else
$(BIN_DIR)/large_stack/mst_search:
	@echo "mst-search-large-stack requires the macOS linker; use mst-search on this platform" >&2
	@exit 1
endif

# Build object files
$(BUILD_DIR)/%.o: %.cpp $(HDRS)
	@mkdir -p $(dir $@)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. -c $< -o $@

# Simple test runner (no gtest dependency)
$(BIN_DIR)/test_runner: test/simple_test.cpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $^ $(LDFLAGS) -o $@

$(BIN_DIR)/regression_runner: test/regression_test.cpp $(filter-out $(BUILD_DIR)/prim/prim.o,$(OBJS))
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $^ $(LDFLAGS) -o $@

$(BIN_DIR)/contraction_runner: test/contraction_test.cpp $(filter-out $(BUILD_DIR)/prim/prim.o,$(OBJS))
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $^ $(LDFLAGS) -o $@

$(BIN_DIR)/scaling_benchmark: benchmark/scaling_benchmark.cpp $(filter-out $(BUILD_DIR)/prim/prim.o,$(OBJS))
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $^ $(LDFLAGS) -o $@

$(BIN_DIR)/diverse_benchmark: benchmark/diverse_benchmark.cpp benchmark/mst_certificate.hpp benchmark/graph_fixtures.hpp benchmark/extended_graph_fixtures.hpp benchmark/common_graph_fixtures.hpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $(filter %.cpp %.o,$^) $(LDFLAGS) -o $@

$(BIN_DIR)/certificate_test: benchmark/certificate_test.cpp benchmark/mst_certificate.hpp
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $< $(LDFLAGS) -o $@

# Benchmark
$(BIN_DIR)/benchmark: benchmark/mst_benchmark.cpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -I. $^ $(LDFLAGS) -o $@ -lbenchmark -lpthread

# Debug build
debug:
	$(MAKE) CXXFLAGS="$(DEBUG_FLAGS)" BUILD_DIR="$(BUILD_DIR)/debug" BIN_DIR="$(BIN_DIR)/debug" all

test: $(BIN_DIR)/test_runner $(BIN_DIR)/regression_runner $(BIN_DIR)/contraction_runner $(BIN_DIR)/certificate_test
	$(BIN_DIR)/test_runner
	$(BIN_DIR)/regression_runner
	$(BIN_DIR)/contraction_runner
	$(BIN_DIR)/certificate_test

clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)
