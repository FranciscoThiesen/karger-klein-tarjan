#ifndef EDGE_HPP
#define EDGE_HPP

#include <tuple>
#include <cstdint>

// Optimized edge representation replacing tuple<int, int, int, int>
// Direct member access is faster than std::get<N>()
struct Edge {
    int from;
    int to;
    int cost;
    int id;

    Edge() : from(0), to(0), cost(0), id(0) {}
    Edge(int f, int t, int c, int i) : from(f), to(t), cost(c), id(i) {}

    // Conversion from tuple for backwards compatibility
    Edge(const std::tuple<int, int, int, int>& t)
        : from(std::get<0>(t)), to(std::get<1>(t)),
          cost(std::get<2>(t)), id(std::get<3>(t)) {}

    // Conversion to tuple for backwards compatibility
    operator std::tuple<int, int, int, int>() const {
        return std::make_tuple(from, to, cost, id);
    }

    bool operator==(const Edge& other) const {
        return from == other.from && to == other.to &&
               cost == other.cost && id == other.id;
    }
};

// For sorting by cost (used in Kruskal)
inline bool edge_cost_less(const Edge& a, const Edge& b) {
    return a.cost < b.cost;
}

#endif // EDGE_HPP
