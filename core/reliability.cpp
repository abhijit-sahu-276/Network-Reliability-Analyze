#include "reliability.h"

#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>

namespace {
double clampProbability(double value) {
    if (value < 0.0) {
        return 0.0;
    }
    if (value > 1.0) {
        return 1.0;
    }
    return value;
}
}  // namespace

bool ReliabilityEngine::exactFeasible(const Graph& graph, std::uint64_t stateLimit) {
    const std::size_t m = graph.edgeCount();
    if (m >= 63) {
        return false;
    }
    const std::uint64_t states = (m == 0) ? 1ULL : (1ULL << m);
    return states <= stateLimit;
}

double ReliabilityEngine::computeExact(const Graph& graph) {
    if (!graph.isValid()) {
        throw std::invalid_argument("Invalid graph: " + graph.validationError());
    }

    const int n = graph.nodeCount();
    const std::size_t m = graph.edgeCount();
    if (n <= 1) {
        return 1.0;
    }
    if (m == 0) {
        return 0.0;
    }
    if (m >= 63) {
        throw std::invalid_argument("Exact reliability is supported only for up to 62 edges.");
    }

    const auto& edges = graph.edges();
    const std::uint64_t states = 1ULL << m;
    double reliability = 0.0;

    for (std::uint64_t mask = 0; mask < states; ++mask) {
        double stateProbability = 1.0;
        for (std::size_t i = 0; i < m; ++i) {
            const bool active = ((mask >> i) & 1ULL) != 0ULL;
            const double p = edges[i].probability;
            stateProbability *= active ? p : (1.0 - p);
            if (stateProbability == 0.0) {
                break;
            }
        }
        if (stateProbability == 0.0) {
            continue;
        }
        if (graph.isConnectedWithMask(mask)) {
            reliability += stateProbability;
        }
    }

    return clampProbability(reliability);
}

ReliabilityEstimate ReliabilityEngine::computeMonteCarlo(const Graph& graph, std::size_t trials, std::uint32_t seed) {
    if (!graph.isValid()) {
        throw std::invalid_argument("Invalid graph: " + graph.validationError());
    }
    if (trials == 0) {
        throw std::invalid_argument("Monte Carlo trials must be >= 1.");
    }

    const auto& edges = graph.edges();
    std::mt19937 rng(seed == 0 ? std::random_device{}() : seed);
    std::uniform_real_distribution<double> random01(0.0, 1.0);
    std::vector<char> active(edges.size(), 0);

    std::size_t connectedCount = 0;
    for (std::size_t trial = 0; trial < trials; ++trial) {
        for (std::size_t i = 0; i < edges.size(); ++i) {
            active[i] = static_cast<char>(random01(rng) < edges[i].probability);
        }
        if (graph.isConnectedWithActive(active)) {
            ++connectedCount;
        }
    }

    const double estimate = static_cast<double>(connectedCount) / static_cast<double>(trials);
    const double variance = estimate * (1.0 - estimate);
    const double margin = 1.96 * std::sqrt(variance / static_cast<double>(trials));

    ReliabilityEstimate result;
    result.value = clampProbability(estimate);
    result.usedMonteCarlo = true;
    result.trials = trials;
    result.ciLow = clampProbability(estimate - margin);
    result.ciHigh = clampProbability(estimate + margin);
    return result;
}

ReliabilityEstimate ReliabilityEngine::computeBestEstimate(const Graph& graph, std::size_t monteCarloTrials) {
    if (exactFeasible(graph)) {
        ReliabilityEstimate exactResult;
        exactResult.value = computeExact(graph);
        exactResult.usedMonteCarlo = false;
        exactResult.trials = 0;
        exactResult.ciLow = exactResult.value;
        exactResult.ciHigh = exactResult.value;
        return exactResult;
    }
    return computeMonteCarlo(graph, std::max<std::size_t>(monteCarloTrials, 1000), 0);
}

std::vector<CriticalEdgeInfo> ReliabilityEngine::criticalEdges(const Graph& graph, std::size_t monteCarloTrials) {
    std::vector<CriticalEdgeInfo> result;
    if (graph.edgeCount() == 0) {
        return result;
    }

    const double baseline = computeBestEstimate(graph, monteCarloTrials).value;
    for (std::size_t i = 0; i < graph.edgeCount(); ++i) {
        const Graph removed = graph.withoutEdge(i);
        const double reliabilityWithout = computeBestEstimate(removed, monteCarloTrials).value;
        result.push_back({i, graph.edges()[i], reliabilityWithout, baseline - reliabilityWithout});
    }

    std::sort(result.begin(), result.end(), [](const CriticalEdgeInfo& a, const CriticalEdgeInfo& b) {
        return a.drop > b.drop;
    });
    return result;
}

EdgeSuggestion ReliabilityEngine::suggestEdgeToAdd(const Graph& graph, double edgeProbability, std::size_t monteCarloTrials) {
    EdgeSuggestion best;
    const auto candidates = graph.missingEdges();
    if (candidates.empty()) {
        return best;
    }

    const double baseline = computeBestEstimate(graph, monteCarloTrials).value;
    const double p = clampProbability(edgeProbability);

    // Avoid spending too much time when the candidate set is huge.
    std::size_t candidateCap = candidates.size();
    if (candidateCap > 300) {
        candidateCap = 300;
    }

    for (std::size_t i = 0; i < candidateCap; ++i) {
        const int u = candidates[i].first;
        const int v = candidates[i].second;
        Graph augmented = graph;
        if (!augmented.addEdge(u, v, p)) {
            continue;
        }
        const double reliability = computeBestEstimate(augmented, monteCarloTrials).value;
        const double improvement = reliability - baseline;

        if (!best.found || improvement > best.improvement) {
            best.found = true;
            best.u = u;
            best.v = v;
            best.proposedProbability = p;
            best.estimatedReliability = reliability;
            best.improvement = improvement;
        }
    }

    return best;
}
