#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "graph.h"

struct FailureSimulationResult {
    std::vector<char> active;
    bool connected = false;
};

class SimulationEngine {
public:
    static FailureSimulationResult runSingleTrial(const Graph& graph, std::uint32_t seed = 0);
    static double runEmpiricalReliability(const Graph& graph, std::size_t trials, std::uint32_t seed = 0);
};
