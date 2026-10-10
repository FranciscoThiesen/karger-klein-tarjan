// Simple test runner for KKT MST algorithm - no external dependencies
#include <cassert>
#include <iostream>
#include <random>
#include <chrono>
#include <vector>
#include <tuple>
#include <unordered_set>
#include <algorithm>
#include <numeric>

#include "kkt/kkt.hpp"
#include "boruvka/boruvka.hpp"
#include "kruskal/kruskal.hpp"
#include "prim/prim.hpp"

using namespace std;

// Test utilities
int tests_passed = 0;
int tests_failed = 0;

#define TEST(name) void test_##name()
#define RUN_TEST(name) do { \
    cout << "Running " #name "... "; \
    try { \
        test_##name(); \
        cout << "PASSED" << endl; \
        tests_passed++; \
    } catch (const exception& e) { \
        cout << "FAILED: " << e.what() << endl; \
        tests_failed++; \
    } \
} while(0)

#define ASSERT_EQ(a, b) do { \
    if ((a) != (b)) { \
        throw runtime_error("Assertion failed: " #a " != " #b); \
    } \
} while(0)

#define ASSERT_TRUE(x) do { \
    if (!(x)) { \
        throw runtime_error("Assertion failed: " #x); \
    } \
} while(0)

// Generate a random connected graph
vector<tuple<int, int, int, int>> generate_random_graph(int n, int m, mt19937& rng) {
    vector<tuple<int, int, int, int>> edges;
    vector<int> weights(m);
    iota(weights.begin(), weights.end(), 1);
    shuffle(weights.begin(), weights.end(), rng);

    // First create a spanning tree to ensure connectivity
    for (int i = 1; i < n; ++i) {
        int parent = rng() % i;
        int cost = weights[edges.size()];
        edges.emplace_back(parent, i, cost, static_cast<int>(edges.size()));
    }

    // Add remaining edges
    while (static_cast<int>(edges.size()) < m) {
        int u = rng() % n;
        int v = rng() % n;
        if (u != v) {
            int cost = weights[edges.size()];
            edges.emplace_back(u, v, cost, static_cast<int>(edges.size()));
        }
    }

    return edges;
}

// Compute MST cost using Kruskal (ground truth)
long long compute_mst_cost_kruskal(const vector<tuple<int, int, int, int>>& edges, int n) {
    auto mst = kruskal(edges, n);
    long long cost = 0;
    for (const auto& e : mst) {
        cost += get<2>(e);
    }
    return cost;
}

// Compute MST cost using KKT
long long compute_mst_cost_kkt(vector<tuple<int, int, int, int>> edges, int n) {
    problem P(n, edges);
    auto result = kkt(P);
    long long cost = 0;
    for (const auto& e : edges) {
        if (result.count(get<3>(e))) {
            cost += get<2>(e);
        }
    }
    return cost;
}

// === TESTS ===

TEST(small_triangle) {
    // Simple triangle graph
    vector<tuple<int, int, int, int>> edges = {
        {0, 1, 1, 0},
        {1, 2, 2, 1},
        {0, 2, 3, 2}
    };

    auto kruskal_cost = compute_mst_cost_kruskal(edges, 3);
    auto kkt_cost = compute_mst_cost_kkt(edges, 3);

    ASSERT_EQ(kruskal_cost, 3);  // MST should be edges 0 and 1
    ASSERT_EQ(kkt_cost, kruskal_cost);
}

TEST(small_path) {
    // Path graph: 0-1-2-3
    vector<tuple<int, int, int, int>> edges = {
        {0, 1, 5, 0},
        {1, 2, 3, 1},
        {2, 3, 7, 2}
    };

    auto kruskal_cost = compute_mst_cost_kruskal(edges, 4);
    auto kkt_cost = compute_mst_cost_kkt(edges, 4);

    ASSERT_EQ(kruskal_cost, 15);  // All edges are in MST
    ASSERT_EQ(kkt_cost, kruskal_cost);
}

TEST(complete_graph_4) {
    // Complete graph K4
    vector<tuple<int, int, int, int>> edges = {
        {0, 1, 1, 0}, {0, 2, 2, 1}, {0, 3, 3, 2},
        {1, 2, 4, 3}, {1, 3, 5, 4}, {2, 3, 6, 5}
    };

    auto kruskal_cost = compute_mst_cost_kruskal(edges, 4);
    auto kkt_cost = compute_mst_cost_kkt(edges, 4);

    ASSERT_EQ(kkt_cost, kruskal_cost);
}

TEST(prim_and_kkt_in_same_binary) {
    const vector<tuple<int, int, int, int>> edges = {
        {0, 1, 7, 10}, {0, 2, 2, 11}, {0, 3, 9, 12},
        {1, 2, 4, 13}, {1, 3, 1, 14}, {2, 3, 6, 15}
    };
    unordered_set<int> expected;
    for (const auto& edge : kruskal(edges, 4)) expected.insert(get<3>(edge));
    unordered_set<int> actual;
    for (const auto& edge : prim(edges, 4)) actual.insert(get<3>(edge));
    ASSERT_EQ(actual, expected);
    problem input(4, edges);
    ASSERT_EQ(kkt(input), expected);
}

TEST(random_small) {
    mt19937 rng(42);
    for (int trial = 0; trial < 10; ++trial) {
        int n = 10 + rng() % 20;
        int m = n - 1 + rng() % (n * 2);

        auto edges = generate_random_graph(n, m, rng);

        auto kruskal_cost = compute_mst_cost_kruskal(edges, n);
        auto kkt_cost = compute_mst_cost_kkt(edges, n);

        ASSERT_EQ(kkt_cost, kruskal_cost);
    }
}

TEST(random_medium) {
    mt19937 rng(123);
    for (int trial = 0; trial < 5; ++trial) {
        int n = 100 + rng() % 200;
        int m = n - 1 + rng() % (n * 3);

        auto edges = generate_random_graph(n, m, rng);

        auto kruskal_cost = compute_mst_cost_kruskal(edges, n);
        auto kkt_cost = compute_mst_cost_kkt(edges, n);

        ASSERT_EQ(kkt_cost, kruskal_cost);
    }
}

TEST(random_large) {
    mt19937 rng(456);
    int n = 1000;
    int m = n * 5;

    auto edges = generate_random_graph(n, m, rng);

    auto kruskal_cost = compute_mst_cost_kruskal(edges, n);
    auto kkt_cost = compute_mst_cost_kkt(edges, n);

    ASSERT_EQ(kkt_cost, kruskal_cost);
}

TEST(boruvka_comparison) {
    mt19937 rng(789);
    for (int trial = 0; trial < 5; ++trial) {
        int n = 50 + rng() % 100;
        int m = n - 1 + rng() % (n * 2);

        auto edges = generate_random_graph(n, m, rng);

        auto boruvka_mst = boruvka(edges, n);
        long long boruvka_cost = 0;
        for (const auto& e : boruvka_mst) {
            boruvka_cost += get<2>(e);
        }

        auto kkt_cost = compute_mst_cost_kkt(edges, n);

        ASSERT_EQ(kkt_cost, boruvka_cost);
    }
}

// Performance test
void benchmark_comparison() {
    cout << "\n=== Performance Comparison ===" << endl;

    mt19937 rng(999);

    for (int n : {1000, 5000, 10000}) {
        int m = n * 4;
        auto edges = generate_random_graph(n, m, rng);

        // Kruskal timing
        auto start = chrono::high_resolution_clock::now();
        for (int i = 0; i < 10; ++i) {
            auto mst = kruskal(edges, n);
        }
        auto end = chrono::high_resolution_clock::now();
        auto kruskal_time = chrono::duration_cast<chrono::microseconds>(end - start).count() / 10.0;

        // KKT timing
        start = chrono::high_resolution_clock::now();
        for (int i = 0; i < 10; ++i) {
            problem P(n, edges);
            auto result = kkt(P, i);
        }
        end = chrono::high_resolution_clock::now();
        auto kkt_time = chrono::duration_cast<chrono::microseconds>(end - start).count() / 10.0;

        cout << "n=" << n << ", m=" << m << ": "
             << "Kruskal=" << kruskal_time/1000 << "ms, "
             << "KKT=" << kkt_time/1000 << "ms, "
             << "Ratio=" << kkt_time/kruskal_time << "x" << endl;
    }
}

int main() {
    cout << "=== KKT MST Algorithm Tests ===" << endl << endl;

    RUN_TEST(small_triangle);
    RUN_TEST(small_path);
    RUN_TEST(complete_graph_4);
    RUN_TEST(prim_and_kkt_in_same_binary);
    RUN_TEST(random_small);
    RUN_TEST(random_medium);
    RUN_TEST(random_large);
    RUN_TEST(boruvka_comparison);

    cout << endl << "=== Results ===" << endl;
    cout << "Passed: " << tests_passed << endl;
    cout << "Failed: " << tests_failed << endl;

    if (tests_failed == 0) {
        benchmark_comparison();
    }

    return tests_failed > 0 ? 1 : 0;
}
