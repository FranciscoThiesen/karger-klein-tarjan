#define KKT_ENABLE_PHASE_STATS
#include "common/phase_stats.hpp"
#include <cassert>

// Test accounting transitions without depending on scheduler-sensitive durations.
int main() {
    using namespace kkt_phase;
    Stats stats;
    {
        Collector collector(stats);
        allocated(5,16);
        {
            Scope outer(Phase::contraction);
            allocated(17,32);
            {
                Scope inner(Phase::minimum_scan);
                deallocated(16);
                assert(current==Phase::minimum_scan);
            }
            assert(current==Phase::contraction);
            deallocated(32);
        }
        assert(current==Phase::api);
        assert(stats.live_usable_bytes==0 && stats.peak_live_usable_bytes==48);
    }
    assert(active==nullptr);
    assert(stats.invalid_free_accounting==0);
    assert(stats.phases[static_cast<std::size_t>(Phase::api)].requested_bytes==5);
    assert(stats.phases[static_cast<std::size_t>(Phase::contraction)].allocations==1);
    assert(stats.phases[static_cast<std::size_t>(Phase::minimum_scan)].freed_usable_bytes==16);
    std::uint64_t sum=0;
    for (const auto& entry:stats.phases) sum+=entry.wall_ns;
    assert(sum>0);
    const auto before=stats.live_usable_bytes;
    allocated(100,128);deallocated(128);
    assert(stats.live_usable_bytes==before); // hooks outside a collector are inert
    Stats second;
    { Collector collector(second); deallocated(1); }
    assert(second.invalid_free_accounting==1);
}
