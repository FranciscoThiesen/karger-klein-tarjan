// One certified input, fixed seeds, separate timing/phase/allocation/work builds.
#include "benchmark/core_attachment_fixtures.hpp"
#include "benchmark/crossover_fixtures.hpp"
#include "benchmark/mst_certificate.hpp"
#include "benchmark/work_metrics.hpp"
#include "common/phase_stats.hpp"
#include "kkt/kkt.hpp"
#include "kruskal/kruskal.hpp"
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <new>
#include <stdexcept>
#include <string>
#include <time.h>
#include <unordered_set>
#ifdef KKT_SCALING_ALLOCATIONS
#include <malloc/malloc.h>
void* operator new(std::size_t size) {
    void* p=std::malloc(size ? size : 1);
    if (!p) throw std::bad_alloc();
    kkt_phase::allocated(size,malloc_size(p)); return p;
}
void operator delete(void* p) noexcept {
    if (p) { kkt_phase::deallocated(malloc_size(p)); std::free(p); }
}
void* operator new[](std::size_t size) { return ::operator new(size); }
void operator delete[](void* p) noexcept { ::operator delete(p); }
void operator delete(void* p,std::size_t) noexcept { ::operator delete(p); }
void operator delete[](void* p,std::size_t) noexcept { ::operator delete(p); }
void* operator new(std::size_t size,std::align_val_t alignment) {
    void* p=nullptr;
    if (posix_memalign(&p,static_cast<std::size_t>(alignment),size ? size : 1)) throw std::bad_alloc();
    kkt_phase::allocated(size,malloc_size(p)); return p;
}
void operator delete(void* p,std::align_val_t) noexcept { ::operator delete(p); }
void* operator new[](std::size_t n,std::align_val_t a) { return ::operator new(n,a); }
void operator delete[](void* p,std::align_val_t) noexcept { ::operator delete(p); }
void operator delete(void* p,std::size_t,std::align_val_t) noexcept { ::operator delete(p); }
void operator delete[](void* p,std::size_t,std::align_val_t) noexcept { ::operator delete(p); }
#endif

namespace {
using Graph=benchmark_fixtures::Graph;
using Ids=std::unordered_set<int>;
using Clock=std::chrono::steady_clock;
void require(bool ok,const char* why) { if (!ok) throw std::runtime_error(why); }
unsigned number(const char* text) {
    std::string value(text);std::size_t used=0;
    require(!value.empty() && value.find_first_not_of("0123456789")==std::string::npos,"invalid number");
    auto n=std::stoull(value,&used);
    require(used==value.size() && n<=std::numeric_limits<unsigned>::max(),"number overflow"); return static_cast<unsigned>(n);
}
std::uint64_t fingerprint(const Graph& graph,int n,bool weighted) {
    std::uint64_t h=UINT64_C(14695981039346656037);
    auto add=[&](int x) { for (unsigned k=0;k<32;k+=8) { h^=(static_cast<std::uint32_t>(x)>>k)&255u;h*=UINT64_C(1099511628211); } };
    add(n);for (const auto& [u,v,w,id]:graph) { add(u);add(v);if(weighted)add(w);add(id); } return h;
}
std::uint64_t ns(clockid_t kind) {
    timespec t{}; require(clock_gettime(kind,&t)==0,"clock failure");
    return static_cast<std::uint64_t>(t.tv_sec)*1000000000+static_cast<std::uint64_t>(t.tv_nsec);
}
void work_json(const kkt_work::WorkStats& stats) {
    std::cout<<'{';bool first=true;
    for(const auto& field:benchmark_work::fields) {
        if(!first)std::cout<<',';first=false;
        std::cout<<'"'<<field.name<<"\":"<<stats.*field.member;
    }std::cout<<'}';
}
void phase_json(const kkt_phase::Stats& stats) {
    std::cout<<'{';
    for(std::size_t i=0;i<kkt_phase::names.size();++i) {
        if(i)std::cout<<',';const auto& x=stats.phases[i];
        std::cout<<'"'<<kkt_phase::names[i]<<"\":{\"wall_ns\":"<<x.wall_ns
          <<",\"calls\":"<<x.calls<<",\"allocations\":"<<x.allocations
          <<",\"requested_bytes\":"<<x.requested_bytes<<",\"usable_bytes\":"<<x.usable_bytes
          <<",\"deallocations\":"<<x.deallocations<<",\"freed_usable_bytes\":"<<x.freed_usable_bytes<<'}';
    }std::cout<<'}';
}
}
int main(int argc,char** argv) {
    try {
        require(argc==6,"usage: diagnostic FAMILY N GRAPH_SEED SAMPLING_SEED REPETITIONS");
        const std::string family(argv[1]);const unsigned n=number(argv[2]),g=number(argv[3]),s=number(argv[4]),reps=number(argv[5]);
        require(family=="leaf_hierarchy4" || family=="leaf_shuffled4" || family=="gnm_random","unsupported family");
        require(n>=1024 && n<=(1u<<20) && reps>=1 && reps<=12,"size/repetitions outside diagnostic bounds");
        const int density=family=="gnm_random"?16:32;
        Graph graph=family=="gnm_random"
            ? benchmark_crossover::make_fixture({family,static_cast<int>(n),density},g).graph
            : benchmark_attachments::make_fixture({family,static_cast<int>(n),density,0},g).graph;
        require(graph.size()==static_cast<std::size_t>(n)*density,"wrong edge target");
        const auto reference=kruskal(graph,n);benchmark_validation::certify_mst(graph,reference,n);
        Ids expected;expected.reserve(reference.size());for(const auto& e:reference)expected.insert(std::get<3>(e));
        require(expected.size()==n-1,"invalid unique-MST reference");
        const auto weighted=fingerprint(graph,n,true),topology=fingerprint(graph,n,false);
        for(unsigned rep=0;rep<=reps;++rep) {
            kkt_phase::Stats phases;kkt_work::WorkStats work;
            const auto utc_start=ns(CLOCK_REALTIME),cpu_start=ns(CLOCK_PROCESS_CPUTIME_ID);
            const auto start=Clock::now();
            const auto result=[&] {
#ifdef KKT_ENABLE_PHASE_STATS
                kkt_phase::Collector collector(phases);
#endif
#ifdef KKT_ENABLE_WORK_STATS
                kkt_work::ScopedWorkStats collector(work);
#endif
                problem input=[&] { KKT_PHASE(input); return problem(n,graph); }();
                return kkt(input,s);
            }();
            const auto wall=std::chrono::duration_cast<std::chrono::nanoseconds>(Clock::now()-start).count();
            const auto cpu=ns(CLOCK_PROCESS_CPUTIME_ID)-cpu_start,utc_end=ns(CLOCK_REALTIME);
            require(result==expected,"MST differs from independently certified reference");
            require(wall>0 && cpu>0,"nonpositive clocks");
            require(phases.invalid_free_accounting==0,"allocation scope freed preexisting storage");
            std::uint64_t total_phase=0;for(const auto& x:phases.phases)total_phase+=x.wall_ns;
            require(total_phase<=static_cast<std::uint64_t>(wall),"exclusive phases exceed measured interval");
            std::cout<<"{\"schema\":\"kkt_scaling_diagnostic_v1\",\"family\":\""<<family<<"\",\"n\":"<<n
              <<",\"m\":"<<graph.size()<<",\"graph_seed\":"<<g<<",\"sampling_seed\":"<<s
              <<",\"input_fingerprint\":"<<weighted<<",\"topology_fingerprint\":"<<topology
              <<",\"repetition\":"<<rep<<",\"warmup\":"<<(rep==0?"true":"false")
              <<",\"wall_ns\":"<<wall<<",\"cpu_ns\":"<<cpu<<",\"utc_start_ns\":"<<utc_start<<",\"utc_end_ns\":"<<utc_end
              <<",\"phase_total_ns\":"<<total_phase<<",\"peak_live_usable_bytes\":"<<phases.peak_live_usable_bytes
              <<",\"returned_live_usable_bytes\":"<<phases.live_usable_bytes<<",\"phases\":";
            phase_json(phases);std::cout<<",\"work\":";work_json(work);
            std::cout<<",\"work_proxy\":"<<benchmark_work::total_work_proxy(work)<<",\"validation\":\"pass\"}\n"<<std::flush;
        }
        require(fingerprint(graph,n,true)==weighted,"input graph mutated");
        return 0;
    } catch(const std::exception& e) { std::cerr<<"diagnostic: "<<e.what()<<'\n';return 1; }
}
