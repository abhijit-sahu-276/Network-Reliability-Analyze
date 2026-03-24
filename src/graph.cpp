#include "graph.h"

#include <algorithm>
#include <queue>
#include <sstream>
#include <unordered_set>

namespace {
std::uint64_t edgeKey(int a, int b) {
    const int u = std::min(a, b);
    const int v = std::max(a, b);
    return (static_cast<std::uint64_t>(u) << 32U) | static_cast<std::uint32_t>(v);
}
}  // namespace

Graph::Graph(int nodes) : n_(nodes) {}

int Graph::nodeCount() const { return n_; }

std::size_t Graph::edgeCount() const { return edges_.size(); }

const std::vector<Edge>& Graph::edges() const { return edges_; }

bool Graph::addEdge(int u, int v, double probability) {
    if (n_ <= 0 || u < 0 || v < 0 || u >= n_ || v >= n_ || u == v) {
        return false;
    }
    if (probability < 0.0 || probability > 1.0) {
        return false;
    }
    if (hasEdge(u, v)) {
        return false;
    }
    edges_.push_back({u, v, probability});
    return true;
}

bool Graph::hasEdge(int u, int v) const {
    for (const Edge& edge : edges_) {
        if ((edge.u == u && edge.v == v) || (edge.u == v && edge.v == u)) {
            return true;
        }
    }
    return false;
}

bool Graph::isConnectedWithMask(std::uint64_t mask) const {
    std::vector<char> active(edges_.size(), 0);
    for (std::size_t i = 0; i < edges_.size(); ++i) {
        active[i] = static_cast<char>((mask >> i) & 1ULL);
    }
    return isConnectedByPredicate(active);
}

bool Graph::isConnectedWithActive(const std::vector<char>& active) const {
    if (active.size() != edges_.size()) {
        return false;
    }
    return isConnectedByPredicate(active);
}

Graph Graph::withoutEdge(std::size_t index) const {
    Graph copy(n_);
    copy.edges_ = edges_;
    if (index < copy.edges_.size()) {
        copy.edges_.erase(copy.edges_.begin() + static_cast<std::ptrdiff_t>(index));
    }
    return copy;
}

std::vector<std::pair<int, int>> Graph::missingEdges() const {
    std::vector<std::pair<int, int>> result;
    for (int u = 0; u < n_; ++u) {
        for (int v = u + 1; v < n_; ++v) {
            if (!hasEdge(u, v)) {
                result.push_back({u, v});
            }
        }
    }
    return result;
}

double Graph::averageEdgeProbability(double fallback) const {
    if (edges_.empty()) {
        return fallback;
    }
    double sum = 0.0;
    for (const Edge& edge : edges_) {
        sum += edge.probability;
    }
    return sum / static_cast<double>(edges_.size());
}

bool Graph::isValid() const { return validationError().empty(); }

std::string Graph::validationError() const {
    if (n_ <= 0) {
        return "Number of nodes must be positive.";
    }
    std::unordered_set<std::uint64_t> seen;
    for (const Edge& edge : edges_) {
        if (edge.u < 0 || edge.u >= n_ || edge.v < 0 || edge.v >= n_) {
            return "Edge endpoint is outside valid node range.";
        }
        if (edge.u == edge.v) {
            return "Self-loops are not allowed.";
        }
        if (edge.probability < 0.0 || edge.probability > 1.0) {
            return "Edge probability must be in [0, 1].";
        }
        const std::uint64_t key = edgeKey(edge.u, edge.v);
        if (seen.find(key) != seen.end()) {
            return "Duplicate undirected edges detected.";
        }
        seen.insert(key);
    }
    return "";
}

bool Graph::isConnectedByPredicate(const std::vector<char>& useEdge) const {
    if (n_ <= 0) {
        return false;
    }
    if (n_ == 1) {
        return true;
    }

    std::vector<std::vector<int>> adjacency(static_cast<std::size_t>(n_));
    for (std::size_t i = 0; i < edges_.size(); ++i) {
        if (!useEdge[i]) {
            continue;
        }
        const Edge& edge = edges_[i];
        adjacency[static_cast<std::size_t>(edge.u)].push_back(edge.v);
        adjacency[static_cast<std::size_t>(edge.v)].push_back(edge.u);
    }

    std::queue<int> q;
    std::vector<char> visited(static_cast<std::size_t>(n_), 0);
    q.push(0);
    visited[0] = 1;
    int visitedCount = 1;

    while (!q.empty()) {
        const int node = q.front();
        q.pop();
        for (int next : adjacency[static_cast<std::size_t>(node)]) {
            if (!visited[static_cast<std::size_t>(next)]) {
                visited[static_cast<std::size_t>(next)] = 1;
                ++visitedCount;
                q.push(next);
            }
        }
    }

    return visitedCount == n_;
}
