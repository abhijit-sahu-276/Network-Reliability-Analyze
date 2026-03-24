#pragma once

#include <cstddef>
#include <cstdint>
#include <vector>

#include "graph.h"

struct ReliabilityEstimate {
    double value = 0.0;
    bool usedMonteCarlo = false;
    std::size_t trials = 0;
    double ciLow = 0.0;
    double ciHigh = 0.0;
};

struct CriticalEdgeInfo {
    std::size_t edgeIndex = 0;
    Edge edge{};
    double reliabilityWithoutEdge = 0.0;
    double drop = 0.0;
};

struct EdgeSuggestion {
    bool found = false;
    int u = -1;
    int v = -1;
    double proposedProbability = 0.0;
    double estimatedReliability = 0.0;
    double improvement = 0.0;
};

class ReliabilityEngine {
public:
    static bool exactFeasible(const Graph& graph, std::uint64_t stateLimit = (1ULL << 22));
    static double computeExact(const Graph& graph);
    static ReliabilityEstimate computeMonteCarlo(const Graph& graph, std::size_t trials, std::uint32_t seed = 0);
    static ReliabilityEstimate computeBestEstimate(const Graph& graph, std::size_t monteCarloTrials);
    static std::vector<CriticalEdgeInfo> criticalEdges(const Graph& graph, std::size_t monteCarloTrials);
    static EdgeSuggestion suggestEdgeToAdd(const Graph& graph, double edgeProbability, std::size_t monteCarloTrials);
};
