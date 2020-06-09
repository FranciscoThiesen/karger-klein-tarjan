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
        edges.emplace_back(c, a - 1, b - 1); 
    }

    long long ans = 0;
    
    sort(edges.begin(), edges.end());
    
    for(const auto& edge : edges) 
    {
        int cost, from, to;
        tie(cost, from, to) = edge;
        if(graph.unite(from, to)) ans += cost;
    }

    cout << ans << endl;
    return 0;
}
