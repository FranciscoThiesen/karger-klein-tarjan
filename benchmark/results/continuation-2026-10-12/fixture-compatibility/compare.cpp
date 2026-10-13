#define benchmark_continuation benchmark_continuation_before
#include "before.hpp"
#undef benchmark_continuation
#undef BENCHMARK_CONTINUATION_FIXTURES_HPP
#include "continuation_fixtures.hpp"
#include <iostream>

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

int main() {
    int checked=0;
    for (const char* family : {"hierarchical_path", "hierarchical_tree", "low_path", "random_path", "random_tree"}) {
        for (int n : {32, 64, 256, 1024, 4096}) for (int density : {1, 4, 32}) {
            if (density*n > n*(n-1)/2) continue;
            const bool structured=std::string(family).find("random_")!=0;
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
