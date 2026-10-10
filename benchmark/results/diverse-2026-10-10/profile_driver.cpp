// Sampling driver only: use the exact benchmark fixture and existing objects.
#define main diverse_benchmark_original_main
#include "../../diverse_benchmark.cpp"
#undef main
#include <unistd.h>

int main() {
    const auto graph = make_graph(Case{"random_32", 65536}, 17, false);
    std::cout << "READY pid=" << getpid() << " n=65536 m=" << graph.size() << std::endl;
    const auto stop = Clock::now() + std::chrono::seconds(20);
    std::size_t checksum = 0;
    unsigned int iteration = 0;
    do {
        const auto result = [&] {
            problem input(65536, graph);
            return kkt(input, sampling_seeds[iteration % sampling_seeds.size()]);
        }();
        checksum += result.size();
        ++iteration;
    } while (Clock::now() < stop);
    std::cout << "DONE iterations=" << iteration << " size_checksum=" << checksum << std::endl;
}
