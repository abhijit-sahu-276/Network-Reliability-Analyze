#include "topology.h"

#include <algorithm>
#include <cctype>
#include <stdexcept>

namespace {
std::string toLower(std::string input) {
    std::transform(input.begin(), input.end(), input.begin(), [](unsigned char c) {
        return static_cast<char>(std::tolower(c));
    });
    return input;
}
}  // namespace

TopologyType parseTopology(const std::string& name) {
    const std::string normalized = toLower(name);
    if (normalized == "star") {
        return TopologyType::Star;
    }
    if (normalized == "ring") {
        return TopologyType::Ring;
    }
    if (normalized == "mesh") {
        return TopologyType::Mesh;
    }
    if (normalized == "tree") {
        return TopologyType::Tree;
    }
    throw std::invalid_argument("Unknown topology name: " + name);
}

std::string topologyName(TopologyType type) {
    switch (type) {
        case TopologyType::Star:
            return "Star";
        case TopologyType::Ring:
            return "Ring";
        case TopologyType::Mesh:
            return "Mesh";
        case TopologyType::Tree:
            return "Tree";
    }
    return "Unknown";
}

Graph createTopology(TopologyType type, int nodes, double probability) {
    Graph graph(nodes);
    if (nodes <= 1) {
        return graph;
    }

    switch (type) {
        case TopologyType::Star: {
            for (int node = 1; node < nodes; ++node) {
                graph.addEdge(0, node, probability);
            }
            break;
        }
        case TopologyType::Ring: {
            for (int node = 0; node < nodes; ++node) {
                const int next = (node + 1) % nodes;
                if (!graph.hasEdge(node, next)) {
                    graph.addEdge(node, next, probability);
                }
            }
            break;
        }
        case TopologyType::Mesh: {
            for (int u = 0; u < nodes; ++u) {
                for (int v = u + 1; v < nodes; ++v) {
                    graph.addEdge(u, v, probability);
                }
            }
            break;
        }
        case TopologyType::Tree: {
            for (int node = 1; node < nodes; ++node) {
                const int parent = (node - 1) / 2;  // Deterministic binary-tree style layout.
                graph.addEdge(parent, node, probability);
            }
            break;
        }
    }

    return graph;
}
