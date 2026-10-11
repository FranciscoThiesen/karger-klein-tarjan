// Untimed, full small-instance exports for the report's graph explorer.
// Production contractions/verification are checked against independent DSU/path
// reconstructions. No timing results are obtained from this executable.
#include "common_graph_fixtures.hpp"
#include "extended_graph_fixtures.hpp"
#include "mst_certificate.hpp"
#include "kkt/kkt.hpp"
#include "kruskal/kruskal.hpp"
#include "verifier/verifier_v2.hpp"
#include <array>
#include <climits>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <unordered_map>
#include <unordered_set>

std::pair<std::vector<int>, problem> boruvka_step(const problem&);
using Graph = benchmark_fixtures::Graph;
struct DSU {
    std::vector<int> p;
    explicit DSU(int n): p(n) { std::iota(p.begin(), p.end(), 0); }
    int root(int v) { while (p[v] != v) { p[v] = p[p[v]]; v = p[v]; } return v; }
    bool join(int u, int v) { u=root(u); v=root(v); if(u==v)return false; p[u]=v; return true; }
};
void require(bool b, const char* s) { if (!b) throw std::runtime_error(s); }
Graph tuples(const problem& p) {
    Graph g; for(const auto& e:p.graph_edges) g.emplace_back(e.from,e.to,e.cost,e.id); return g;
}
void ints(const std::vector<int>& a) {
    std::cout << '['; bool first=true; for(int x:a) { if(!first)std::cout<<','; first=false; std::cout<<x; } std::cout<<']';
}
void graph_json(const problem& p) {
    std::cout << "{\"n\":" << p.num_vertices << ",\"edges\":[";
    bool first=true;
    for(const auto& e:p.graph_edges) {
        if(!first)std::cout<<','; first=false;
        std::cout<<'['<<e.from<<','<<e.to<<','<<e.cost<<','<<e.id<<']';
    }
    std::cout<<"]}";
}
// Full connected input here. Production labels components by their minimum
// old vertex. Reconstruct this independently from the emitted selected IDs.
std::vector<int> mapping(const problem& input, const std::vector<int>& selected,
                         const problem& output) {
    DSU d(input.num_vertices);
    std::unordered_set<int> ids(selected.begin(),selected.end());
    require(ids.size()==selected.size(),"duplicate selected ID");
    for(const auto& e:input.graph_edges) if(ids.count(e.id))
        require(d.join(e.from,e.to),"selected edges contain a cycle");
    std::unordered_map<int,int> labels;
    std::vector<int> map(input.num_vertices);
    for(int v=0;v<input.num_vertices;++v) {
        int r=d.root(v); if(!labels.count(r))labels[r]=static_cast<int>(labels.size());
        map[v]=labels.at(r);
    }
    if(output.graph_edges.empty()) {
        require(labels.size()<=1 || input.graph_edges.empty(),"unexpected empty contraction");
        return map;
    }
    require(static_cast<int>(labels.size())==output.num_vertices,"component count mismatch");
    std::unordered_map<long long,Edge> minimum;
    for(const auto& e:input.graph_edges) {
        int u=map[e.from],v=map[e.to]; if(u==v)continue; if(u>v)std::swap(u,v);
        long long key=static_cast<long long>(u)*output.num_vertices+v;
        auto it=minimum.find(key);
        if(it==minimum.end() || e.cost<it->second.cost)minimum.insert_or_assign(key,Edge(u,v,e.cost,e.id));
    }
    require(minimum.size()==output.graph_edges.size(),"parallel reduction count mismatch");
    for(const auto& e:output.graph_edges)
        require(minimum.at(static_cast<long long>(e.from)*output.num_vertices+e.to)==e,"contraction tuple mismatch");
    return map;
}
int path_max(const std::vector<std::vector<std::pair<int,int>>>& adj,int from,int to) {
    std::vector<std::array<int,3>> todo{{from,-1,INT_MIN}};
    while(!todo.empty()) {
        const auto x=todo.back();todo.pop_back(); if(x[0]==to)return x[2];
        for(const auto& [v,w]:adj[x[0]]) if(v!=x[1])todo.push_back({v,x[0],std::max(w,x[2])});
    }
    return INT_MAX; // Different forest components: always F-light.
}
void one(const std::string& family,int n) {
    benchmark_common::Fixture fixture;
    if(family=="small_world")fixture.graph=benchmark_extended::make_graph({family,n},42);
    else fixture=benchmark_common::make_fixture({family,n},42);
    const auto oracle=kruskal(fixture.graph,n);
    benchmark_validation::certify_mst(fixture.graph,oracle,n);
    std::vector<int> mst;for(const auto& e:oracle)mst.push_back(std::get<3>(e));
    problem p(n,fixture.graph);
    require(kkt(p,0)==std::unordered_set<int>(mst.begin(),mst.end()),"visual input KKT mismatch");
    std::cout<<"{\"family\":\""<<family<<"\",\"graph_seed\":42,\"sampling_seed\":0,\"positions\":[";
    for(std::size_t i=0;i<fixture.positions.size();++i){if(i)std::cout<<',';const auto&c=fixture.positions[i];std::cout<<'['<<c[0]<<','<<c[1]<<','<<c[2]<<']';}
    std::cout<<"],\"original_to_label\":";ints(fixture.original_to_label);
    std::cout<<",\"mst_ids\":";ints(mst);
    std::cout<<",\"stages\":[";graph_json(p);
    std::vector<std::vector<int>> maps,selections;
    for(int round=0;round<2;++round){
        auto next=boruvka_step(p);maps.push_back(mapping(p,next.first,next.second));selections.push_back(next.first);
        p=std::move(next.second);std::cout<<',';graph_json(p);
    }
    std::cout<<"],\"maps\":[";ints(maps[0]);std::cout<<',';ints(maps[1]);
    std::cout<<"],\"selected_ids\":[";ints(selections[0]);std::cout<<',';ints(selections[1]);std::cout<<']';
    const Graph reduced=tuples(p);
    Graph sample;std::mt19937 rng(0);std::vector<int> sampled;
    for(const auto&e:reduced)if(rng()&1u){sample.push_back(e);sampled.push_back(std::get<3>(e));}
    const auto forest=kruskal(sample,p.num_vertices);
    DSU forest_dsu(p.num_vertices);std::vector<std::vector<std::pair<int,int>>>adj(p.num_vertices);
    std::vector<int> forest_ids;
    for(const auto&[u,v,w,id]:forest){require(forest_dsu.join(u,v),"sample MSF cycle");adj[u].push_back({v,w});adj[v].push_back({u,w});forest_ids.push_back(id);}
    for(const auto&[u,v,w,id]:sample){(void)id;require(path_max(adj,u,v)<=w,"sample forest fails cycle property or connectivity");}
    const auto marks=verifier_detail::heavy_edge_marks(reduced,forest,p.num_vertices);
    require(marks.size()==reduced.size(),"heavy marks size mismatch");std::vector<int>heavy;
    for(std::size_t i=0;i<reduced.size();++i){const auto&[u,v,w,id]=reduced[i];bool h=w>path_max(adj,u,v);require((marks[i]!=0)==h,"heavy mark differs from independent path oracle");if(h)heavy.push_back(id);}
    std::cout<<",\"sampled_ids\":";ints(sampled);std::cout<<",\"sample_forest_ids\":";ints(forest_ids);
    std::cout<<",\"heavy_ids\":";ints(heavy);std::cout<<",\"validation\":\"pass_certified_MST_contraction_and_path_oracles\"}";
}
int main(){try{
    std::cout<<std::setprecision(10)<<"[";bool first=true;
    for(const char* family:{"unbalanced_bipartite_16","leaf_core_90","ring_cliques_16","grid3d_distance","grid3d_random","regular_8","small_world"}){
        if(!first)std::cout<<',';first=false;one(family,256);
    }
    std::cout<<"]\n";
}catch(const std::exception&e){std::cerr<<e.what()<<'\n';return 1;}}
