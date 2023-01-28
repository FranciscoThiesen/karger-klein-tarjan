#include "graph_utils/graph_utils.hpp"
#include "kkt/kkt.hpp"
#include <iostream>


int main()
{
	constexpr int N = 10'000;
	constexpr int M = 1'250'000;
	auto G = build_random_connected_graph(N, M);
	auto P = problem(N, G);

	auto ans = kkt(P);
	
	std::cout << "Optimal value is = " << *(ans.begin()) << std::endl;
	return 0;
}