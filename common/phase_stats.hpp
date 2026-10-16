#ifndef KKT_PHASE_STATS_HPP
#define KKT_PHASE_STATS_HPP

// Opt-in diagnostics only. With the flag absent, scope arguments disappear.
// Exclusive wall time is attributed at phase transitions; it is not an
// instruction counter or a hardware-cache profile. Allocation diagnostics are
// supplied separately by the diagnostic executable's operator new/delete.
#include <array>
#include <chrono>
#include <cassert>
#include <cstddef>
#include <cstdint>

namespace kkt_phase {
enum class Phase : std::size_t {
    api, input, recursion, contraction, minimum_scan, sampling, isolation,
    forest_recovery, partition, tree_setup, fbt, lca_build,
    queries, query_gather, mark_scatter, path_solve, median_table, path_walk, filtering, output, count
};
inline constexpr std::array<const char*, static_cast<std::size_t>(Phase::count)> names = {
    "api", "input", "recursion", "contraction", "minimum_scan", "sampling", "isolation",
    "forest_recovery", "partition", "tree_setup", "fbt", "lca_build",
    "queries", "query_gather", "mark_scatter", "path_solve", "median_table", "path_walk", "filtering", "output"
};
struct Entry {
    std::uint64_t wall_ns = 0, calls = 0;
    std::uint64_t allocations = 0, requested_bytes = 0, usable_bytes = 0;
    std::uint64_t deallocations = 0, freed_usable_bytes = 0;
};
struct Stats {
    std::array<Entry, names.size()> phases{};
    std::uint64_t live_usable_bytes = 0, peak_live_usable_bytes = 0;
    std::uint64_t invalid_free_accounting = 0;
};

#ifdef KKT_ENABLE_PHASE_STATS
using Clock = std::chrono::steady_clock;
inline thread_local Stats* active = nullptr;
inline thread_local Phase current = Phase::api;
inline thread_local Clock::time_point last;

inline void charge(Clock::time_point now) {
    active->phases[static_cast<std::size_t>(current)].wall_ns +=
        static_cast<std::uint64_t>(std::chrono::duration_cast<std::chrono::nanoseconds>(now-last).count());
    last = now;
}
class Collector {
    Stats* previous_;
    Phase previous_phase_;
    Clock::time_point previous_last_;
public:
    explicit Collector(Stats& stats) : previous_(active), previous_phase_(current), previous_last_(last) {
        assert(!active && "phase collectors must not be nested");
        active=&stats; current=Phase::api; last=Clock::now();
    }
    ~Collector() { charge(Clock::now()); active=previous_; current=previous_phase_; last=previous_last_; }
    Collector(const Collector&)=delete;
    Collector& operator=(const Collector&)=delete;
};
class Scope {
    Stats* stats_;
    Phase previous_;
public:
    explicit Scope(Phase phase) : stats_(active), previous_(current) {
        if (stats_) { charge(Clock::now()); current=phase; ++stats_->phases[static_cast<std::size_t>(phase)].calls; }
    }
    ~Scope() { if (stats_) { charge(Clock::now()); current=previous_; } }
    Scope(const Scope&)=delete;
    Scope& operator=(const Scope&)=delete;
};
inline void allocated(std::size_t requested, std::size_t usable) {
    if (!active) return;
    auto& entry=active->phases[static_cast<std::size_t>(current)];
    ++entry.allocations; entry.requested_bytes+=requested; entry.usable_bytes+=usable;
    active->live_usable_bytes+=usable;
    if (active->live_usable_bytes>active->peak_live_usable_bytes)
        active->peak_live_usable_bytes=active->live_usable_bytes;
}
inline void deallocated(std::size_t usable) {
    if (!active) return;
    auto& entry=active->phases[static_cast<std::size_t>(current)];
    ++entry.deallocations; entry.freed_usable_bytes+=usable;
    if (usable>active->live_usable_bytes) ++active->invalid_free_accounting;
    else active->live_usable_bytes-=usable;
}
#endif
} // namespace kkt_phase

#ifdef KKT_ENABLE_PHASE_STATS
#define KKT_PHASE_JOIN_INNER(a,b) a##b
#define KKT_PHASE_JOIN(a,b) KKT_PHASE_JOIN_INNER(a,b)
#define KKT_PHASE(name) ::kkt_phase::Scope KKT_PHASE_JOIN(kkt_phase_scope_,__LINE__)(::kkt_phase::Phase::name)
#else
#define KKT_PHASE(name) ((void)0)
#endif
#endif
