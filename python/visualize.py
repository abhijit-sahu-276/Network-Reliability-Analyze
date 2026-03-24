#!/usr/bin/env python3
"""
Visualization utility for the Advanced Network Reliability Analyzer.

Examples:
  python python/visualize.py --topology ring --nodes 8 --edge-prob 0.9
  python python/visualize.py --topology custom --nodes 5 --edges "0-1:0.9,1-2:0.8,2-3:0.95,3-4:0.9,4-0:0.85"
  python python/visualize.py --topology mesh --nodes 6 --failure-prob 0.15 --output mesh_trial.png
"""

import argparse
import random
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import networkx as nx


EdgeSpec = Tuple[int, int, float]


def parse_custom_edges(spec: str) -> List[EdgeSpec]:
    if not spec.strip():
        return []
    edges: List[EdgeSpec] = []
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        left, prob_str = token.split(":")
        u_str, v_str = left.split("-")
        edges.append((int(u_str), int(v_str), float(prob_str)))
    return edges


def build_topology(topology: str, nodes: int, edge_prob: float, custom_edges: List[EdgeSpec]) -> List[EdgeSpec]:
    if topology == "custom":
        return custom_edges
    if topology == "star":
        return [(0, v, edge_prob) for v in range(1, nodes)]
    if topology == "ring":
        if nodes <= 1:
            return []
        edges: List[EdgeSpec] = []
        for u in range(nodes):
            v = (u + 1) % nodes
            if u < v:
                edges.append((u, v, edge_prob))
            elif v < u and (v, u, edge_prob) not in edges:
                edges.append((v, u, edge_prob))
        return edges
    if topology == "mesh":
        return [(u, v, edge_prob) for u in range(nodes) for v in range(u + 1, nodes)]
    if topology == "tree":
        return [((v - 1) // 2, v, edge_prob) for v in range(1, nodes)]
    raise ValueError(f"Unsupported topology: {topology}")


def connected_with_active_edges(nodes: int, active_edges: List[Tuple[int, int]]) -> bool:
    if nodes <= 1:
        return True
    graph = nx.Graph()
    graph.add_nodes_from(range(nodes))
    graph.add_edges_from(active_edges)
    return nx.is_connected(graph)


def simulate_state(edges: List[EdgeSpec], failure_prob: Optional[float]) -> Dict[Tuple[int, int], bool]:
    state: Dict[Tuple[int, int], bool] = {}
    for u, v, p in edges:
        if failure_prob is None:
            active = random.random() < p
        else:
            active = random.random() >= failure_prob
        state[(u, v)] = active
    return state


def main() -> None:
    parser = argparse.ArgumentParser(description="Network reliability visualization helper")
    parser.add_argument("--topology", choices=["custom", "star", "ring", "mesh", "tree"], default="ring")
    parser.add_argument("--nodes", type=int, default=6)
    parser.add_argument("--edge-prob", type=float, default=0.9)
    parser.add_argument("--edges", type=str, default="")
    parser.add_argument("--failure-prob", type=float, default=None)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=str, default="")
    args = parser.parse_args()

    if args.nodes <= 0:
        raise ValueError("nodes must be positive")
    if not (0.0 <= args.edge_prob <= 1.0):
        raise ValueError("edge-prob must be in [0,1]")
    if args.failure_prob is not None and not (0.0 <= args.failure_prob <= 1.0):
        raise ValueError("failure-prob must be in [0,1]")

    random.seed(args.seed)
    custom_edges = parse_custom_edges(args.edges)
    edges = build_topology(args.topology, args.nodes, args.edge_prob, custom_edges)

    graph = nx.Graph()
    graph.add_nodes_from(range(args.nodes))
    for u, v, p in edges:
        graph.add_edge(u, v, probability=p)

    active_state = simulate_state(edges, args.failure_prob)
    active_edges = [edge for edge, is_active in active_state.items() if is_active]
    failed_edges = [edge for edge, is_active in active_state.items() if not is_active]
    connected = connected_with_active_edges(args.nodes, active_edges)

    pos = nx.spring_layout(graph, seed=args.seed)
    plt.figure(figsize=(10, 7))
    nx.draw_networkx_nodes(graph, pos, node_size=750, node_color="#F8F5E9", edgecolors="#1F2937", linewidths=1.5)
    nx.draw_networkx_labels(graph, pos, font_size=11, font_weight="bold")

    if active_edges:
        nx.draw_networkx_edges(graph, pos, edgelist=active_edges, width=3.2, edge_color="#0EA5A4")
    if failed_edges:
        nx.draw_networkx_edges(graph, pos, edgelist=failed_edges, width=2.2, edge_color="#DC2626", style="dashed")

    edge_labels = {(u, v): f"{p:.2f}" for u, v, p in edges}
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=9)

    status = "CONNECTED" if connected else "DISCONNECTED"
    plt.title(
        f"{args.topology.upper()} topology | Nodes={args.nodes} | Status={status}",
        fontsize=13,
        fontweight="bold",
    )
    plt.axis("off")
    plt.tight_layout()

    if args.output:
        plt.savefig(args.output, dpi=180)
        print(f"Saved figure to: {args.output}")
    else:
        plt.show()

    print("Simulation summary")
    print(f"  Topology: {args.topology}")
    print(f"  Nodes: {args.nodes}, Edges: {len(edges)}")
    print(f"  Connected in sampled state: {connected}")
    print("  Active edges:", active_edges)
    print("  Failed edges:", failed_edges)


if __name__ == "__main__":
    main()
