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

constexpr int inf = 0x3f3f3f3f;

int main()
{
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    union_find graph(n);
    vector< tuple<int, int, int> > edges;


    for(int i = 0; i < m; ++i)
    {
        int a, b, c;
        cin >> a >> b >> c;
        edges.emplace_back((a - 1), (b - 1), c);
    }

    long long ans = 0;

    while(graph.cc > 1)
    {
        vector<int> cheapest(n, -1);
        
        for(int i = 0; i < m; ++i)
        {
            int from, to, cost;
            tie(from, to, cost) = edges[i];
            to = graph.find_parent(to);
            from = graph.find_parent(from);
            if(graph.find_parent(from) == graph.find_parent(to)) continue;
            if(cheapest[from] == -1 || cost < get<2>(edges[cheapest[from]]) ) cheapest[from] = i;
            if(cheapest[to] == -1 || cost < get<2>(edges[cheapest[to]]) ) cheapest[to] = i;
        }
        
        for(int i = 0; i < n; ++i)
        {
            if(graph.parent[i] != i) continue;
            int from, to, cost;
            tie(from, to, cost) = edges[cheapest[i]];
            
            bool pay;
            if(i == from) pay = graph.unite(i, to);
            else pay = graph.unite(i, from);
            if(pay) ans += cost; 
        }
    }
    cout << ans << endl;
    return 0;
}
