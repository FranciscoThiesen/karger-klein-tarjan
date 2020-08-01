#ifndef LCA_H
#define LCA_H

#include <vector>

using namespace std;

// Implementation of Farach-Colton-Bender LCA
// Source: https://cp-algorithms.com/graph/lca_farachcoltonbender.html
// Complexity: Preprocessing in O(n), Query in O(1)

class LCA
{
  private:
	int n;
	vector<vector<int>> adj;
	int block_size, block_cnt;
	vector<int> first_visit;
	vector<int> euler_tour;
	vector<int> height;
	vector<int> log_2;
	vector<vector<int>> st;
	vector<vector<vector<int>>> blocks;
	vector<int> block_mask;

	void dfs(int v, int p, int h);

	int min_by_h(int i, int j);

	void precompute_lca(int root);

	int lca_in_block(int b, int l, int r);

  public:
	LCA(int n, vector<vector<int>>& graph, int root);
	LCA();
	int query(int v, int u);
};

#endif
