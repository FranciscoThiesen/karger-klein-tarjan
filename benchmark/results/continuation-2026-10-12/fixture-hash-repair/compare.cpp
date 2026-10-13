#define benchmark_continuation benchmark_continuation_before
#include "before.hpp"
#undef benchmark_continuation
#undef BENCHMARK_CONTINUATION_FIXTURES_HPP
#include "after.hpp"
#include <iostream>
#include <chrono>

std::uint64_t fingerprint(const benchmark_fixtures::Graph& graph, int n) {
    std::uint64_t value = UINT64_C(14695981039346656037);
    const auto append = [&](int number) {
        const auto bits = static_cast<std::uint32_t>(number);
        for (unsigned shift = 0; shift < 32; shift += 8) {
            value ^= (bits >> shift) & 0xffu;
            value *= UINT64_C(1099511628211);
        }
    };
    append(n);
    for (const auto& [u,v,w,id] : graph) { append(u); append(v); append(w); append(id); }
    return value;
}

int main(int argc, char**) {
    if (argc > 1) {
        const auto begin_old=std::chrono::steady_clock::now();
        const auto old=benchmark_continuation_before::make_fixture({"hierarchical_path",65536,64,0},17);
        const auto end_old=std::chrono::steady_clock::now();
        const auto begin_new=std::chrono::steady_clock::now();
        const auto now=benchmark_continuation::make_fixture({"hierarchical_path",65536,64,0},17);
        const auto end_new=std::chrono::steady_clock::now();
        if (old.graph!=now.graph || old.original_to_label!=now.original_to_label ||
            old.backbone_ids!=now.backbone_ids || old.hierarchy_levels!=now.hierarchy_levels)
            throw std::runtime_error("large fixture differs");
        const auto old_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(end_old-begin_old).count();
        const auto new_ns=std::chrono::duration_cast<std::chrono::nanoseconds>(end_new-begin_new).count();
        std::cout<<"variant,case_id,graph_seed,elapsed_ns,input_fingerprint,validation\n";
        std::cout<<"e1467be_identity_hash,hierarchical_path_n65536_d64_p0,17,"<<old_ns<<','<<fingerprint(old.graph,65536)<<",pass\n";
        std::cout<<"local_mix64_hash,hierarchical_path_n65536_d64_p0,17,"<<new_ns<<','<<fingerprint(now.graph,65536)<<",pass\n";
        std::cerr<<"Generation only: one old-then-new call each; exact tuples and metadata match. No solver timing.\n";
        return 0;
    }
    int checked=0;
    std::cout<<"case_id,graph_seed,input_fingerprint,validation\n";
    for (const char* family : {"hierarchical_path", "hierarchical_tree", "low_path", "random_path", "random_tree", "distance_path", "distance_tree"}) {
        for (int n : {32, 64, 256, 1024, 4096}) for (int density : {1, 4, 32}) {
            if (density*n > n*(n-1)/2) continue;
            const bool structured=std::string(family).find("random_")!=0 && std::string(family).find("distance_")!=0;
            const auto levels=structured && density>=4 ? std::vector<int>{0,1,125,1000} : std::vector<int>{0};
            for (int intrusion : levels) for (unsigned seed : {17u,42u,999u}) {
                const benchmark_continuation::Spec spec{family,n,density,intrusion};
                const auto old=benchmark_continuation_before::make_fixture({family,n,density,intrusion},seed);
                const auto now=benchmark_continuation::make_fixture(spec,seed);
                if (old.graph!=now.graph || old.original_to_label!=now.original_to_label ||
                    old.backbone_ids!=now.backbone_ids || old.hierarchy_levels!=now.hierarchy_levels)
                    throw std::runtime_error("changed fixture: "+benchmark_continuation::case_id(spec));
                std::cout<<benchmark_continuation::case_id(spec)<<','<<seed<<','
                         <<fingerprint(now.graph,n)<<",pass\n";
                ++checked;
            }
        }
    }
    std::cerr << "Old/new exact tuples and metadata match for " << checked << " fixtures\n";
}
