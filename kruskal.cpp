#include <bits/stdc++.h>
#include "UnionFind/UnionFind.hpp"

using namespace std;

constexpr int inf = 0x3f3f3f3f;



int main()
{
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int n, m;
    cin >> n >> m;
    UnionFind graph(n);
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
