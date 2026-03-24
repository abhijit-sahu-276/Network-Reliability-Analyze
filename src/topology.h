#pragma once

#include <string>

#include "graph.h"

enum class TopologyType {
    Star,
    Ring,
    Mesh,
    Tree
};

TopologyType parseTopology(const std::string& name);
std::string topologyName(TopologyType type);
Graph createTopology(TopologyType type, int nodes, double probability);
