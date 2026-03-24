#include <algorithm>
#include <exception>
#include <iomanip>
#include <iostream>
#include <limits>
#include <string>
#include <vector>

#include "graph.h"
#include "reliability.h"
#include "simulation.h"
#include "topology.h"

namespace {

template <typename T>
T readNumber(const std::string& prompt, T minValue, T maxValue) {
    T value{};
    while (true) {
        std::cout << prompt;
        if (std::cin >> value && value >= minValue && value <= maxValue) {
            return value;
        }
        std::cout << "Invalid input. Enter a value in range [" << minValue << ", " << maxValue << "].\n";
        std::cin.clear();
        std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
    }
}

int readMenuChoice(int minChoice, int maxChoice) { return readNumber<int>("Enter choice: ", minChoice, maxChoice); }

void printGraph(const Graph& graph) {
    std::cout << "\nNetwork Summary\n";
    std::cout << "Nodes: " << graph.nodeCount() << "\n";
    std::cout << "Edges: " << graph.edgeCount() << "\n";
    for (std::size_t i = 0; i < graph.edgeCount(); ++i) {
        const Edge& e = graph.edges()[i];
        std::cout << "  e" << i << ": (" << e.u << ", " << e.v << ")  p=" << std::fixed << std::setprecision(4)
                  << e.probability << "\n";
    }
}

Graph inputCustomGraph() {
    const int nodes = readNumber<int>("Number of nodes: ", 1, 1000);
    const int maxEdges = (nodes * (nodes - 1)) / 2;
    const int edges = readNumber<int>("Number of edges: ", 0, maxEdges);

    Graph graph(nodes);
    std::cout << "Node indexing: 0 to " << nodes - 1 << "\n";
    for (int i = 0; i < edges; ++i) {
        while (true) {
            std::cout << "Edge " << i + 1 << " (u v p): ";
            int u = 0;
            int v = 0;
            double p = 0.0;
            if (!(std::cin >> u >> v >> p)) {
                std::cout << "Invalid format. Use: <u> <v> <probability>\n";
                std::cin.clear();
                std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
                continue;
            }
            if (graph.addEdge(u, v, p)) {
                break;
            }
            std::cout << "Invalid edge. Ensure no duplicates, no self-loops, and probability in [0,1].\n";
        }
    }
    return graph;
}

Graph inputPredefinedTopology() {
    std::cout << "\nSelect topology:\n";
    std::cout << "1. Star\n";
    std::cout << "2. Ring\n";
    std::cout << "3. Mesh\n";
    std::cout << "4. Tree\n";
    const int choice = readMenuChoice(1, 4);

    const int nodes = readNumber<int>("Number of nodes: ", 1, 1000);
    const double p = readNumber<double>("Link reliability probability p [0..1]: ", 0.0, 1.0);

    TopologyType topology = TopologyType::Star;
    if (choice == 2) {
        topology = TopologyType::Ring;
    } else if (choice == 3) {
        topology = TopologyType::Mesh;
    } else if (choice == 4) {
        topology = TopologyType::Tree;
    }

    return createTopology(topology, nodes, p);
}

void printEstimate(const ReliabilityEstimate& estimate, const std::string& label) {
    std::cout << std::fixed << std::setprecision(6);
    if (!estimate.usedMonteCarlo) {
        std::cout << label << " (Exact): " << estimate.value << "\n";
    } else {
        std::cout << label << " (Monte Carlo): " << estimate.value << "\n";
        std::cout << "95% CI: [" << estimate.ciLow << ", " << estimate.ciHigh << "], trials=" << estimate.trials
                  << "\n";
    }
}

void analyzeGraph(const Graph& graph) {
    if (!graph.isValid()) {
        std::cout << "Graph validation failed: " << graph.validationError() << "\n";
        return;
    }

    printGraph(graph);
    const std::size_t trials = readNumber<std::size_t>("Monte Carlo trials for large graphs (>=1000): ", 1000, 2000000);

    const ReliabilityEstimate estimate = ReliabilityEngine::computeBestEstimate(graph, trials);
    std::cout << "\nReliability Analysis\n";
    printEstimate(estimate, "Network reliability");

    std::cout << "\nRandom Failure Simulation (one trial)\n";
    const FailureSimulationResult sim = SimulationEngine::runSingleTrial(graph);
    std::cout << "Connectivity status: " << (sim.connected ? "CONNECTED" : "DISCONNECTED") << "\n";
    for (std::size_t i = 0; i < graph.edgeCount(); ++i) {
        const Edge& e = graph.edges()[i];
        std::cout << "  e" << i << " (" << e.u << "," << e.v << "): " << (sim.active[i] ? "UP" : "FAILED") << "\n";
    }

    std::cout << "\nCritical Link Analysis\n";
    const std::size_t criticalTrials = std::max<std::size_t>(1000, trials / 2);
    const auto critical = ReliabilityEngine::criticalEdges(graph, criticalTrials);
    const std::size_t topK = std::min<std::size_t>(5, critical.size());
    if (topK == 0) {
        std::cout << "No edges available for criticality analysis.\n";
    } else {
        for (std::size_t i = 0; i < topK; ++i) {
            const auto& item = critical[i];
            std::cout << i + 1 << ". Edge (" << item.edge.u << "," << item.edge.v << ") "
                      << "drop=" << std::fixed << std::setprecision(6) << item.drop
                      << ", reliability_without=" << item.reliabilityWithoutEdge << "\n";
        }
    }

    std::cout << "\nOptimization Suggestion\n";
    const double suggestionP = readNumber<double>(
        "Probability to assume for a newly added edge [0..1] (tip: use avg edge p): ", 0.0, 1.0);
    const auto suggestion = ReliabilityEngine::suggestEdgeToAdd(graph, suggestionP, criticalTrials);
    if (!suggestion.found) {
        std::cout << "No candidate edge available to add.\n";
    } else {
        std::cout << "Add edge (" << suggestion.u << "," << suggestion.v << ") with p=" << suggestion.proposedProbability
                  << "\n";
        std::cout << "Estimated new reliability=" << suggestion.estimatedReliability
                  << ", improvement=" << suggestion.improvement << "\n";
    }
}

void compareTopologies() {
    const int nodes = readNumber<int>("Number of nodes for comparison: ", 1, 1000);
    const double p = readNumber<double>("Uniform edge reliability p [0..1]: ", 0.0, 1.0);
    const std::size_t trials = readNumber<std::size_t>("Monte Carlo trials for large graphs (>=1000): ", 1000, 2000000);

    struct Row {
        std::string name;
        double reliability = 0.0;
        bool monteCarlo = false;
        std::size_t edges = 0;
    };

    std::vector<Row> rows;
    for (TopologyType topology : {TopologyType::Star, TopologyType::Ring, TopologyType::Mesh, TopologyType::Tree}) {
        const Graph graph = createTopology(topology, nodes, p);
        const auto estimate = ReliabilityEngine::computeBestEstimate(graph, trials);
        rows.push_back({topologyName(topology), estimate.value, estimate.usedMonteCarlo, graph.edgeCount()});
    }

    std::sort(rows.begin(), rows.end(), [](const Row& a, const Row& b) { return a.reliability > b.reliability; });

    std::cout << "\nTopology Comparison\n";
    std::cout << std::left << std::setw(12) << "Topology" << std::setw(10) << "Edges" << std::setw(16) << "Reliability"
              << "Method\n";
    for (const auto& row : rows) {
        std::cout << std::left << std::setw(12) << row.name << std::setw(10) << row.edges << std::setw(16)
                  << std::fixed << std::setprecision(6) << row.reliability
                  << (row.monteCarlo ? "MonteCarlo" : "Exact") << "\n";
    }

    if (!rows.empty()) {
        std::cout << "\nBest topology: " << rows.front().name << "\n";
        std::cout << "Worst topology: " << rows.back().name << "\n";
    }
}

}  // namespace

int main() {
    std::cout << "Advanced Network Reliability Analyzer\n";
    std::cout << "-------------------------------------\n";

    while (true) {
        std::cout << "\nMenu\n";
        std::cout << "1. Analyze custom network\n";
        std::cout << "2. Analyze predefined topology\n";
        std::cout << "3. Compare topologies\n";
        std::cout << "4. Exit\n";

        const int choice = readMenuChoice(1, 4);
        try {
            if (choice == 1) {
                const Graph graph = inputCustomGraph();
                analyzeGraph(graph);
            } else if (choice == 2) {
                const Graph graph = inputPredefinedTopology();
                analyzeGraph(graph);
            } else if (choice == 3) {
                compareTopologies();
            } else {
                std::cout << "Exiting.\n";
                break;
            }
        } catch (const std::exception& ex) {
            std::cout << "Error: " << ex.what() << "\n";
        }
    }

    return 0;
}
