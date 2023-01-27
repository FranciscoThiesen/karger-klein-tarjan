#include "boruvka.hpp"

#include <iostream>
#include <tuple>
#include <unordered_set>
#include <vector>
#include <functional>

using namespace std;

vector<tuple<int, int, int, int>>
	boruvka(const vector<tuple<int, int, int, int>>& edges, int n)
{
	vector<int> component(n, -1);
	vector<int> cheapest(n, -1);
	vector<tuple<int, int, int, int>> ans;
	vector< vector<int> > selected_graph(n);

	int m = static_cast<int>(edges.size());
	int graph_cc = n;
	while (graph_cc > 1)
	{
		// tenho que descobrir as componentes do grafo já selecionado
		fill(cheapest.begin(), cheapest.end(), -1);
		fill(component.begin(), component.end(), -1);
		int cur_cc = 0;

		function<void(int, int)> explore = [&] (int root, int cc) {
			component[root] = cc;
			for(const auto& viz : selected_graph[root]) {
				if(component[viz] == -1) explore(viz, cc);
			}
		};

		for(int i = 0; i < n; ++i) {
			if(component[i] == -1) {
				explore(i, cur_cc);
				cur_cc++;
			}
		}

		for (int i = 0; i < m; ++i)
		{
			int from, to, cost;
			tie(from, to, cost, ignore) = edges[i];
			to = component[to];
			from = component[from];
			if (from == to) continue;
			if (cheapest[from] == -1 || cost < get<2>(edges[cheapest[from]]))
				cheapest[from] = i;
			if (cheapest[to] == -1 || cost < get<2>(edges[cheapest[to]]))
				cheapest[to] = i;
		}
		
		unordered_set<int> inserted_edges_id;

		for (int i = 0; i < n; ++i)
		{
			if (cheapest[i] == -1) continue;

			int from, to, cost, id;
			tie(from, to, cost, id) = edges[cheapest[i]];
			if(inserted_edges_id.find(id) != inserted_edges_id.end()) continue;
			else {
				selected_graph[from].push_back(to);
				selected_graph[to].push_back(from);
				inserted_edges_id.insert(id);
				ans.emplace_back(from, to, cost, id);
			}			
		}
		graph_cc = cur_cc;
	}

	return ans;
}
