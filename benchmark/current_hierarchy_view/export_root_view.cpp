// Untimed explanatory root reconstruction; no full recursive trace or timings.
#define KKT_RETENTION_HARNESS_NO_MAIN
#include "benchmark/retention_control.cpp"
#include "kkt/experimental_eighth_sampling.hpp"
#include "verifier/verifier_v2.hpp"
#include <climits>
#include <iomanip>
#include <map>
#include <numeric>
#include <random>

namespace root_view {
constexpr int n=1024, density=32;
constexpr unsigned graph_seed=17000011, sampling_seed=2801;
void check(bool value,const char* message) { if(!value) throw std::runtime_error(message); }
struct Ledger {
    std::vector<int> p;
    explicit Ledger(int size):p(size) { std::iota(p.begin(),p.end(),0); }
    int root(int v) { while(p[v]!=v) { p[v]=p[p[v]];v=p[v]; }return v; }
    bool join(int u,int v) {u=root(u);v=root(v);if(u==v)return false;p[u]=v;return true;}
};
void ints(const std::vector<int>& values) {
    std::cout<<'[';for(std::size_t i=0;i<values.size();++i){if(i)std::cout<<',';std::cout<<values[i];}std::cout<<']';
}
Graph tuples(const problem& input) {
    Graph output;for(const auto& e:input.graph_edges)output.emplace_back(e.from,e.to,e.cost,e.id);return output;
}
std::vector<int> ids_of(const Graph& input) {
    std::vector<int> output;for(const auto& e:input)output.push_back(std::get<3>(e));return output;
}
void graph_json(const problem& input) {
    std::cout<<"{\"n\":"<<input.num_vertices<<",\"m\":"<<input.graph_edges.size()<<",\"edges\":[";
    bool first=true;for(const auto& e:input.graph_edges){if(!first)std::cout<<',';first=false;
        std::cout<<'['<<e.from<<','<<e.to<<','<<e.cost<<','<<e.id<<']';}std::cout<<"]}";
}
using Adjacency=std::vector<std::vector<std::pair<int,int>>>;
int path_max(const Adjacency& adjacent,int from,int to) {
    std::vector<std::array<int,3>> stack{{from,-1,INT_MIN}};
    while(!stack.empty()) {auto item=stack.back();stack.pop_back();if(item[0]==to)return item[2];
        for(auto [v,w]:adjacent[item[0]])if(v!=item[1])stack.push_back({v,item[0],std::max(w,item[2])});}
    return INT_MAX;
}
// This independently checks parallel records and disconnected forests. It does
// not reuse the simple-input certificate or the production union-find/verifier.
Adjacency certify_forest(const Graph& input,const Graph& forest,int vertices) {
    std::map<int,Graph::value_type> by_id;std::unordered_set<int> weights;
    for(const auto& e:input){auto [u,v,w,id]=e;check(u>=0&&u<vertices&&v>=0&&v<vertices&&u!=v,"invalid quotient edge");
        check(by_id.emplace(id,e).second&&weights.insert(w).second,"nonunique quotient ID/weight");}
    Ledger ledger(vertices);Adjacency adjacent(vertices);
    for(const auto& e:forest){auto [u,v,w,id]=e;check(by_id.count(id)&&by_id.at(id)==e,"forest record not in input");
        check(ledger.join(u,v),"forest cycle");adjacent[u].push_back({v,w});adjacent[v].push_back({u,w});}
    for(const auto& e:input){auto [u,v,w,id]=e;(void)id;
        check(ledger.root(u)==ledger.root(v),"forest does not span an input component");
        check(path_max(adjacent,u,v)<=w,"forest fails independent path maximum");}
    return adjacent;
}
std::vector<int> contraction_map(const problem& input,const std::vector<int>& chosen,const problem& output) {
    std::vector<int> cheapest(input.num_vertices,-1);std::map<int,std::size_t> positions;
    for(std::size_t i=0;i<input.graph_edges.size();++i){const auto& e=input.graph_edges[i];positions.emplace(e.id,i);
        for(int v:{e.from,e.to})if(cheapest[v]<0||e.cost<input.graph_edges[cheapest[v]].cost)cheapest[v]=static_cast<int>(i);}
    std::unordered_set<int> expected,actual(chosen.begin(),chosen.end());
    for(int i:cheapest)if(i>=0)expected.insert(input.graph_edges[i].id);
    check(expected==actual&&actual.size()==chosen.size(),"contraction selection differs from independent minima");
    Ledger ledger(input.num_vertices);
    for(int id:chosen){const auto& e=input.graph_edges.at(positions.at(id));check(ledger.join(e.from,e.to),"contraction selection cycle");}
    std::map<int,int> labels;std::vector<int> mapping(input.num_vertices);
    for(int v=0;v<input.num_vertices;++v){int r=ledger.root(v);if(!labels.count(r))labels[r]=static_cast<int>(labels.size());mapping[v]=labels.at(r);}
    check(output.num_vertices==static_cast<int>(labels.size())&&output.num_vertices>1,"unexpected terminal/isolated quotient");
    std::vector<Edge> expected_edges;
    for(const auto& e:input.graph_edges){int u=mapping[e.from],v=mapping[e.to];if(u!=v)expected_edges.emplace_back(std::min(u,v),std::max(u,v),e.cost,e.id);}
    check(expected_edges==output.graph_edges,"retained quotient records or input order differ");return mapping;
}
void sample_json(const problem& root,bool eighth,const std::unordered_set<int>& root_mst) {
    std::mt19937 engine(sampling_seed),replay(sampling_seed);Graph sampled;std::vector<int> selected_positions;
    for(std::size_t position=0;position<root.graph_edges.size();++position){
        const auto word=static_cast<std::uint32_t>(engine());
        const bool selected=eighth?kkt_detail::accept_scalar_sample_word<true>(word):kkt_detail::accept_scalar_sample_word<false>(word);
        const auto independent=static_cast<std::uint32_t>(replay());
        check(word==independent&&selected==(independent%(eighth?8u:2u)==(eighth?7u:1u)),"scalar acceptance/draw replay mismatch");
        if(selected){const auto& e=root.graph_edges[position];sampled.emplace_back(e.from,e.to,e.cost,e.id);selected_positions.push_back(static_cast<int>(position));}}
    check(engine==replay,"root scalar engine state mismatch");
    const auto forest=kruskal(sampled,root.num_vertices);const auto adjacent=certify_forest(sampled,forest,root.num_vertices);
    const auto marks=verifier_detail::heavy_edge_marks(root.graph_edges,forest,root.num_vertices);
    check(marks.size()==root.graph_edges.size(),"heavy mark size mismatch");std::vector<int> heavy;
    for(std::size_t i=0;i<root.graph_edges.size();++i){const auto& e=root.graph_edges[i];const bool expected=e.cost>path_max(adjacent,e.from,e.to);
        check((marks[i]!=0)==expected,"production verifier differs from independent path maximum");
        check(!expected||!root_mst.count(e.id),"root MST edge removed");if(expected)heavy.push_back(e.id);}
    std::cout<<"{\"policy\":\""<<(eighth?"eighth":"half")<<"\",\"mask\":"<<(eighth?7:1)
        <<",\"engine_words\":"<<root.graph_edges.size()<<",\"sample_edges\":"<<sampled.size()
        <<",\"forest_edges\":"<<forest.size()<<",\"forest_components\":"<<root.num_vertices-forest.size()
        <<",\"heavy_edges\":"<<heavy.size()<<",\"light_edges\":"<<root.graph_edges.size()-heavy.size()
        <<",\"selected_parent_positions\":";ints(selected_positions);
    std::cout<<",\"sampled_ids\":";ints(ids_of(sampled));std::cout<<",\"forest_ids\":";ints(ids_of(forest));
    std::cout<<",\"heavy_ids\":";ints(heavy);std::cout<<'}';
}
void one(const char* family) {
    auto generated=benchmark_attachments::make_fixture({family,n,density,0},graph_seed);
    const auto& input=generated.graph;check(input==fixture({family,n,density,0},graph_seed),"different timing fixture generation");
    const auto tree=kruskal(input,n);benchmark_validation::certify_mst(input,tree,n);
    const auto expected=ids(tree);problem original(n,input);check(kkt(original,sampling_seed)==expected,"frozen eighth KKT differs from certified MST");
    std::vector<problem> stages{original};std::vector<std::vector<int>> mappings,choices;
    for(int round=0;round<2;++round){auto [chosen,reduced]=kkt_experiment::retain_parallel_step(stages.back());
        for(int id:chosen)check(expected.count(id)==1,"contraction chose non-MST edge");
        mappings.push_back(contraction_map(stages.back(),chosen,reduced));choices.push_back(chosen);stages.push_back(std::move(reduced));}
    std::unordered_set<int> root_mst;
    for(const auto& stage:stages){Graph surviving;for(const auto& e:stage.graph_edges)if(expected.count(e.id))surviving.emplace_back(e.from,e.to,e.cost,e.id);
        certify_forest(tuples(stage),surviving,stage.num_vertices);if(&stage==&stages.back())root_mst=ids(surviving);}
    if(std::string(family)=="leaf_hierarchy4")check(stages[1].num_vertices==256&&stages[1].graph_edges.size()==32000&&
        stages[2].num_vertices==128&&stages[2].graph_edges.size()==31872,"ordered root count formula differs");
    std::cout<<"{\"family\":"<<std::quoted(family)<<",\"n\":"<<n<<",\"m\":"<<input.size()<<",\"density\":"<<density
        <<",\"graph_seed\":"<<graph_seed<<",\"sampling_seed\":"<<sampling_seed<<",\"input_fingerprint\":\""<<fingerprint(input,n,true)
        <<"\",\"topology_fingerprint\":\""<<fingerprint(input,n,false)<<"\",\"original_to_label\":";ints(generated.original_to_label);
    std::cout<<",\"mst_ids\":";ints(ids_of(tree));std::cout<<",\"stages\":[";
    for(std::size_t i=0;i<stages.size();++i){if(i)std::cout<<',';graph_json(stages[i]);}
    std::cout<<"],\"maps\":[";ints(mappings[0]);std::cout<<',';ints(mappings[1]);std::cout<<"],\"selected_ids\":[";
    ints(choices[0]);std::cout<<',';ints(choices[1]);std::cout<<"],\"samples\":[";
    sample_json(stages.back(),false,root_mst);std::cout<<',';sample_json(stages.back(),true,root_mst);
    std::cout<<"],\"validation\":\"pass\"}";
}
} // namespace root_view
int main(){try{std::cout<<"{\"schema\":\"current_hierarchy_root_view_v1\",\"trace_scope\":\"reconstructed_root_only\",\"graphs\":[";
    root_view::one("leaf_hierarchy4");std::cout<<',';root_view::one("leaf_shuffled4");std::cout<<"]}\n";
}catch(const std::exception& error){std::cerr<<error.what()<<'\n';return 1;}}
