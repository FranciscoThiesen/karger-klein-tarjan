# Makefile for KKT MST Algorithm
# Provides alternative build system to Bazel

CXX = clang++
CXXFLAGS = -std=c++17 -O3 -Wall -Wextra -march=native
DEBUG_FLAGS = -std=c++17 -O0 -g -Wall -Wextra -fsanitize=address,undefined

# Directories
BUILD_DIR = build
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

.PHONY: all clean test benchmark debug

all: $(BIN_DIR)/test_runner $(BIN_DIR)/regression_runner

# Benchmark (requires google benchmark library)
benchmark: $(BIN_DIR)/benchmark

# Build object files
$(BUILD_DIR)/%.o: %.cpp $(HDRS)
	@mkdir -p $(dir $@)
	$(CXX) $(CXXFLAGS) -I. -c $< -o $@

# Simple test runner (no gtest dependency)
$(BIN_DIR)/test_runner: test/simple_test.cpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -I. $^ -o $@

$(BIN_DIR)/regression_runner: test/regression_test.cpp $(filter-out $(BUILD_DIR)/prim/prim.o,$(OBJS))
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -I. $^ -o $@

# Benchmark
$(BIN_DIR)/benchmark: benchmark/mst_benchmark.cpp $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(CXX) $(CXXFLAGS) -I. $^ -o $@ -lbenchmark -lpthread

# Debug build
debug: CXXFLAGS = $(DEBUG_FLAGS)
debug: clean $(BIN_DIR)/test_runner

test: $(BIN_DIR)/test_runner $(BIN_DIR)/regression_runner
	./$(BIN_DIR)/test_runner
	$(BIN_DIR)/regression_runner

clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)
