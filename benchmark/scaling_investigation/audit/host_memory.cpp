// Separate host calibration. This does not execute or instrument KKT.
#include <algorithm>
#include <array>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <sys/resource.h>
#include <time.h>
#include <unistd.h>
#include <vector>

namespace {
constexpr std::uint64_t visits = (UINT64_C(1) << 24) + 8;
constexpr std::uint32_t seed = UINT32_C(0x31415926);
constexpr std::array<std::size_t, 7> footprints{
    16*1024, 64*1024, 256*1024, 1024*1024, 4*1024*1024, 16*1024*1024, 64*1024*1024};
using Positions = std::array<std::uint32_t, 8>;

void require(bool condition, const char* message) {
    if (!condition) throw std::runtime_error(message);
}

std::uint64_t cpu_ns() {
    timespec value{};
    require(clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &value)==0, "CPU clock failed");
    return std::uint64_t(value.tv_sec)*UINT64_C(1000000000)+std::uint64_t(value.tv_nsec);
}

// Unbiased, explicitly 32-bit bounded draw; used only during untimed setup.
std::uint32_t bounded(std::mt19937& rng, std::uint32_t bound) {
    require(bound>0, "empty shuffle bound");
    const std::uint32_t threshold=(std::uint32_t(0)-bound)%bound;
    std::uint32_t word;
    do { word=static_cast<std::uint32_t>(rng()); } while (word<threshold);
    return word%bound;
}

// Final values are checked and printed. The noinline boundary and memory
// barriers prevent loop motion across the clocks; final-machine-code review
// remains a required gate to verify dependent loads and independent chains.
template<std::size_t K>
__attribute__((noinline)) Positions chase(const std::uint32_t* next, Positions position,
                                         std::uint64_t rounds) {
    static_assert(K==1 || K==4 || K==8);
    for (std::uint64_t round=0; round<rounds; ++round)
        for (std::size_t chain=0; chain<K; ++chain)
            position[chain]=next[position[chain]];
    return position;
}

__attribute__((noinline)) std::uint64_t scan(const std::uint32_t* next, std::size_t mask,
                                            std::uint64_t count) {
    std::uint64_t sum=0;
    for (std::uint64_t i=0; i<count; ++i) sum+=next[std::size_t(i)&mask];
    return sum;
}

void footprint(std::size_t bytes, const char* size_order) {
    require(bytes%sizeof(std::uint32_t)==0, "invalid footprint");
    const std::size_t n=bytes/sizeof(std::uint32_t);
    require(n>0 && (n&(n-1))==0 && n<=std::numeric_limits<std::uint32_t>::max(), "invalid index domain");
    std::vector<std::uint32_t> next(n);
    std::array<Positions, 3> starts{}, expected{};
    std::uint64_t fingerprint=UINT64_C(14695981039346656037), expected_scan=0;
    {
        // The shuffled order builds one complete cycle, not several short cycles.
        std::vector<std::uint32_t> order(n);
        std::iota(order.begin(),order.end(),0u);
        std::mt19937 rng(seed^static_cast<std::uint32_t>(bytes));
        for (std::size_t i=n; i>1; --i) std::swap(order[i-1],order[bounded(rng,static_cast<std::uint32_t>(i))]);
        for (std::size_t i=0; i<n; ++i) next[order[i]]=order[(i+1)&(n-1)];
        std::vector<unsigned char> seen(n,0);
        std::uint32_t at=0;
        for (std::size_t i=0; i<n; ++i) {
            require(at<n && !seen[at], "not a single full permutation cycle");
            seen[at]=1; at=next[at];
        }
        require(at==0, "cycle did not close");
        constexpr std::array<std::size_t,3> chains{1,4,8};
        for (std::size_t mode=0; mode<chains.size(); ++mode) {
            const auto k=chains[mode];
            require(visits%k==0, "unequal logical load budget");
            for (std::size_t chain=0; chain<k; ++chain) {
                const std::size_t rank=chain*(n/k);
                starts[mode][chain]=order[rank];
                expected[mode][chain]=order[(rank+visits/k)%n];
                require(starts[mode][chain]!=expected[mode][chain], "zero-work final-position witness");
            }
        }
        // Each next array is a permutation of [0,n). Full scan cycles therefore
        // have this independently known sum; only the short suffix is read.
        expected_scan=(visits/n)*(std::uint64_t(n)*(n-1)/2);
        for (std::size_t i=0; i<visits%n; ++i) expected_scan+=next[i];
        for (auto value:next) { fingerprint^=value; fingerprint*=UINT64_C(1099511628211); }
    } // Order and seen buffers are destroyed before any measured kernel call.

    // Repeat 0 is warmup; rotate all four positions through the four repeats.
    // Array construction, checks, output and destruction are outside timing.
    for (int repetition=0; repetition<4; ++repetition) {
        for (int slot=0; slot<4; ++slot) {
            const int mode=(slot+repetition)%4;
            const int chains=mode==0 ? 1 : mode==1 ? 4 : mode==2 ? 8 : 0;
            Positions result{}; std::uint64_t checksum=0;
            asm volatile("" ::: "memory");
            const auto wall_start=std::chrono::steady_clock::now();
            const auto cpu_start=cpu_ns();
            if (mode==0) result=chase<1>(next.data(),starts[0],visits);
            else if (mode==1) result=chase<4>(next.data(),starts[1],visits/4);
            else if (mode==2) result=chase<8>(next.data(),starts[2],visits/8);
            else checksum=scan(next.data(),n-1,visits);
            asm volatile("" ::: "memory");
            const auto cpu_end=cpu_ns();
            const auto wall_end=std::chrono::steady_clock::now();
            const auto wall=std::chrono::duration_cast<std::chrono::nanoseconds>(wall_end-wall_start).count();
            require(wall>0 && cpu_end>cpu_start, "invalid clock duration");
            if (mode<3) require(result==expected[mode], "incorrect final pointer positions");
            else require(checksum==expected_scan, "incorrect contiguous checksum");
            std::cout << "{\"schema\":\"host_memory_calibration_v1\",\"size_order\":\"" << size_order
                      << "\",\"mode\":\"" << (mode==3 ? "scan" : "chase") << "\",\"chains\":" << chains
                      << ",\"bytes\":" << bytes << ",\"indices\":" << n << ",\"seed\":" << seed
                      << ",\"fingerprint\":" << fingerprint << ",\"repetition\":" << repetition
                      << ",\"warmup\":" << (repetition==0 ? "true" : "false")
                      << ",\"logical_loads\":" << visits << ",\"rounds\":" << (chains ? visits/chains : visits)
                      << ",\"wall_ns\":" << wall << ",\"process_cpu_start_ns\":" << cpu_start
                      << ",\"process_cpu_end_ns\":" << cpu_end << ",\"cpu_ns\":" << cpu_end-cpu_start
                      << ",\"checksum\":" << checksum << ",\"positions\":[";
            for (std::size_t i=0; i<result.size(); ++i) std::cout << (i ? "," : "") << result[i];
            std::cout << "],\"validation\":\"pass\"}\n" << std::flush;
        }
    }
}
} // namespace

int main(int argc, char** argv) {
    try {
        require(argc==2, "usage: host_memory ascending|descending");
        const std::string order=argv[1];
        require(order=="ascending" || order=="descending", "undeclared size order");
        const rlimit limit{240,240};
        require(setrlimit(RLIMIT_CPU,&limit)==0, "cannot set CPU limit");
        alarm(285); // Supplementary: the parent still owns 300 s wall/group cleanup.
        if (order=="ascending") for (auto bytes:footprints) footprint(bytes,argv[1]);
        else for (auto it=footprints.rbegin(); it!=footprints.rend(); ++it) footprint(*it,argv[1]);
        alarm(0);
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n'; return 1;
    }
}
