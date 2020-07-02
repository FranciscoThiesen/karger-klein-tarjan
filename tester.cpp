#include <bits/stdc++.h>
#include "verification.hpp"
#include "Kruskal/Kruskal.hpp"
#include "Prim/Prim.hpp"
#include "Boruvka/Boruvka.hpp"

using namespace std;

int main()
{
	cout << "test" << endl;
	ios::sync_with_stdio(false); cin.tie(nullptr);

	vector< tuple<int, int, int> > graph;
	graph.emplace_back(0, 1, 1);
	graph.emplace_back(1, 2, 1);
	graph.emplace_back(2, 3, 4);
	graph.emplace_back(0, 3, 2);

	auto X = kruskal(graph, 4);
	auto Y = boruvka(graph, 4);
	auto Z = prim(graph, 4);

	return 0;
}
