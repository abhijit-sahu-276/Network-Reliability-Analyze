#pragma once

#include <cstddef>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

struct Edge {
    int u;
    int v;
    double probability;
};

class Graph {
public:
    explicit Graph(int nodes = 0);

    int nodeCount() const;
    std::size_t edgeCount() const;
    const std::vector<Edge>& edges() const;

    bool addEdge(int u, int v, double probability);
    bool hasEdge(int u, int v) const;
    bool isConnectedWithMask(std::uint64_t mask) const;
    bool isConnectedWithActive(const std::vector<char>& active) const;
    Graph withoutEdge(std::size_t index) const;
    std::vector<std::pair<int, int>> missingEdges() const;
    double averageEdgeProbability(double fallback = 0.90) const;

    bool isValid() const;
    std::string validationError() const;

private:
    int n_;
    std::vector<Edge> edges_;

    bool isConnectedByPredicate(const std::vector<char>& useEdge) const;
};
