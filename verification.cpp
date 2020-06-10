#include <bits/stdc++.h>

using namespace std;

struct union_find 
{
    int n, cc;
    vector<int> parent, rank;

    union_find(int _n) : n(_n), cc(_n) 
    {
        parent.resize(n);
        rank.assign(n, 1);
        iota(parent.begin(), parent.end(), 0);
    }

    int find_parent(int node) 
    {
        if(parent[node] != node) parent[node] = find_parent(parent[node]);
        return parent[node];
    }

    bool unite(int x, int y)
    {
        x = find_parent(x); y = find_parent(y);
        if(x == y) return false;
        if(rank[x] < rank[y]) parent[x] = y;
        else parent[y] = x;
        rank[x] += (rank[x] == rank[y]);
        cc--; 
        return true;
    }
};

// Aqui vou implementar o processo de reducao de uma Spanning Tree T, para 
// uma Full Branching Tree B, como descrito no paper de King.
vector< tuple<int, int, int> > fbt_reduction(int total_nodes, const vector<tuple<int, int, int> >& edges)
{
    // para cada nó do grafo original, vamos criar uma folha nova em B
    int current_node_count = total_nodes;
    union_find components(total_nodes);
    int graph_cc = total_nodes;
    // [0, current_node_count - 1] -> folhas
    int total_edges = static_cast<int>(edges.size());
    unordered_map<int, int> f_node;
    for(int i = 0; i < total_nodes; ++i) f_node[i] = i;

    while(graph.cc > 1)
    {
        unordered_map<int, int> cheapest_edge;
        
        for(int i = 0; i < total_edges; ++i)
        {
            int from, to, cost;
            tie(from, to, cost) = edges[i];
            
            // Nesse caso os nós já pertencem a mesma componente conexa
            if(components.find(from) == components.find(to)) continue;
            if(cheapest_edge.count(from) == 0 || cost < get<2>(edges[cheapest_edge[from]]))
                cheapest_edge[from] = i;
            if(cheapest_edge.count(to) == 0|| cost < get<2>(edges[cheapest_edge[to]]))
                cheapest_edge[to] = i;
        }
        
        for(const auto& cluster : cheapest_edge)
        {
            int from, to, cost;
            tie(from, to, cost) = edges[cluster.second];

        }
    }
}

int main()
{

}
