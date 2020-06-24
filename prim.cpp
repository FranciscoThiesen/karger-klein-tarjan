#include <bits/stdc++.h>

using namespace std;

const int INF = 1000000000;

struct Edge {
    int w = INF, to = -1;
    Edge(int _w, int _to) : w(_w), to(_to) {}
    Edge() {
        w = INF;
        to = -1;
    }
    bool operator<(Edge const& other) const {
        return make_pair(w, to) < make_pair(other.w, other.to);
    }
};

int n;
vector<vector<Edge>> adj;

void prim() {
    int total_weight = 0;
    vector<Edge> min_e(n);
    min_e[0].w = 0;
    set<Edge> q;
    q.insert({0, 0});
    vector<bool> selected(n, false);
    for (int i = 0; i < n; ++i) {
        if (q.empty()) {
            cout << "No MST!" << endl;
            exit(0);
        }

        int v = q.begin()->to;
        selected[v] = true;
        total_weight += q.begin()->w;
        q.erase(q.begin());

        //if (min_e[v].to != -1)
        //    cout << v << " " << min_e[v].to << endl;

        for (Edge e : adj[v]) {
            if (!selected[e.to] && e.w < min_e[e.to].w) {
                q.erase({min_e[e.to].w, e.to});
                min_e[e.to] = {e.w, v};
                q.insert({e.w, e.to});
            }
        }
    }

    cout << total_weight << endl;
}

int main()
{
    ios::sync_with_stdio(false); cin.tie(nullptr);
    int m;
    cin >> n >> m;
    adj.resize(n);
    for(int i = 0; i < m; ++i)
    {
        int from, to, cost;
        cin >> from >> to >> cost;
        to--; from--;
        adj[from].push_back(Edge(cost, to));

        adj[to].push_back(Edge(cost, from));
    }
    prim();
    return 0;
}
