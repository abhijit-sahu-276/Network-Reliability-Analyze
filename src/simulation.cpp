#include "simulation.h"

#include <algorithm>
#include <random>
#include <stdexcept>

FailureSimulationResult SimulationEngine::runSingleTrial(const Graph& graph, std::uint32_t seed) {
    if (!graph.isValid()) {
        throw std::invalid_argument("Invalid graph: " + graph.validationError());
    }

    std::mt19937 rng(seed == 0 ? std::random_device{}() : seed);
    std::uniform_real_distribution<double> random01(0.0, 1.0);

    FailureSimulationResult result;
    result.active.resize(graph.edgeCount(), 0);
    for (std::size_t i = 0; i < graph.edgeCount(); ++i) {
        result.active[i] = static_cast<char>(random01(rng) < graph.edges()[i].probability);
    }
    result.connected = graph.isConnectedWithActive(result.active);
    return result;
}

double SimulationEngine::runEmpiricalReliability(const Graph& graph, std::size_t trials, std::uint32_t seed) {
    if (trials == 0) {
        throw std::invalid_argument("Trials must be >= 1.");
    }
    std::mt19937 rng(seed == 0 ? std::random_device{}() : seed);
    std::uniform_real_distribution<double> random01(0.0, 1.0);

    std::size_t connected = 0;
    std::vector<char> active(graph.edgeCount(), 0);
    for (std::size_t t = 0; t < trials; ++t) {
        for (std::size_t i = 0; i < graph.edgeCount(); ++i) {
            active[i] = static_cast<char>(random01(rng) < graph.edges()[i].probability);
        }
        if (graph.isConnectedWithActive(active)) {
            ++connected;
        }
    }

    return static_cast<double>(connected) / static_cast<double>(trials);
}
