#ifndef KKT_H
#define KKT_H

#include <unordered_set>
#include <vector>
#include <tuple>

using namespace std;

struct problem {
    int num_vertices;
    vector< tuple<int, int, int, int> > graph_edges;
    problem(int nv = 0, vector<tuple<int, int, int, int>> ge = vector<tuple<int, int, int, int>>()) : num_vertices(nv), graph_edges(ge) {}

    bool operator !=(const problem& rhs) const {
        if(num_vertices != rhs.num_vertices) return true;
        if(static_cast<int>(graph_edges.size()) != static_cast<int>(rhs.graph_edges.size())) return true;
        return false;
    };
};


int get_solution_cost(const problem& P, const unordered_set<int>& used);
// Essa função retorna os índices das arestas que pertencem a MST
unordered_set<int> kkt(problem& P);

#endif
